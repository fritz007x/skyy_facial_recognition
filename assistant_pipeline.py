"""
assistant_pipeline_smallmodel.py

- Uses a SMALL Vosk model (no grammar support)
- Wake-word detection by checking Vosk transcripts for keywords
- Streaming capture with queue
- Noise reduction (noisereduce) on post-wake chunk
- Optional faster-whisper for higher-quality transcription if installed
- Safe TTS via pyttsx3
- Ctrl+C safe
"""

import sounddevice as sd
import soundfile as sf
import queue
import threading
import time
import numpy as np
import json
import os
import sys
import traceback

# optional faster-whisper
USE_FASTER_WHISPER = False
try:
    from faster_whisper import WhisperModel
    USE_FASTER_WHISPER = True
except Exception:
    USE_FASTER_WHISPER = False

from vosk import Model as VoskModel, KaldiRecognizer
import pyttsx3
import noisereduce as nr

# -------- CONFIG --------
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_SECONDS = 0.5                  # chunk size pushed to queue
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_SECONDS)
RECORD_SECONDS_AFTER_WAKE = 4        # seconds to capture after wakeword
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"  # adjust path
WAKE_WORDS = ["hey assistant", "okay assistant", "assistant", "computer"]  # lowercased
AUDIO_QUEUE_MAX = 100
TTS_RATE = 160
TTS_VOICE_NAME = None  # set to a substring of a voice name if you want a specific voice
# ------------------------

if not os.path.exists(VOSK_MODEL_PATH):
    raise FileNotFoundError(f"Vosk model not found at {VOSK_MODEL_PATH}. Download and unzip a small model.")

# Initialize TTS
tts = pyttsx3.init()
tts.setProperty("rate", TTS_RATE)
if TTS_VOICE_NAME:
    for v in tts.getProperty("voices"):
        if TTS_VOICE_NAME.lower() in v.name.lower():
            tts.setProperty("voice", v.id)
            break

def safe_speak(text):
    """Synchronous TTS with a small pause to reduce device contention."""
    time.sleep(0.12)  # allow mic to be released
    tts.say(text)
    tts.runAndWait()
    time.sleep(0.12)

# Load Vosk (small model)
vosk_model = VoskModel(VOSK_MODEL_PATH)

# Recognizer used for streaming wake detection and small transcript checks
# (no grammar argument for small model)
wake_recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)

# Fallback recognizer for full chunk
def vosk_transcribe_int16_bytes(int16_bytes):
    rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)
    if rec.AcceptWaveform(int16_bytes):
        res = json.loads(rec.Result())
    else:
        res = json.loads(rec.FinalResult())
    return res.get("text", "").strip()

# Optional: faster-whisper initialization
whisper_model = None
if USE_FASTER_WHISPER:
    try:
        device = "cpu"
        if os.environ.get("USE_CUDA"):
            device = "cuda"
        # use small or tiny model if you want lighter resource usage
        whisper_model = WhisperModel("small", device=device, compute_type="float32")
        print("[INFO] faster-whisper available (small).")
    except Exception as e:
        print("[WARN] faster-whisper init failed, falling back to Vosk.", e)
        whisper_model = None

# Queue & threading
audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAX)
terminate_event = threading.Event()

def audio_producer():
    """Callback-based input stream that pushes frames into a queue."""
    def callback(indata, frames, time_info, status):
        if status:
            print("[audio callback] status:", status, file=sys.stderr)
        try:
            # use int16 dtype for Vosk compatibility
            audio_queue.put(indata.copy(), block=False)
        except queue.Full:
            # drop frames when full
            pass

    # open input stream; blocksize=FRAME_SAMPLES ensures we get chunks ~FRAME_SECONDS
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16",
                        blocksize=FRAME_SAMPLES, callback=callback):
        print("[PRODUCER] stream started.")
        while not terminate_event.is_set():
            time.sleep(0.1)
    print("[PRODUCER] stream stopped.")

def bytes_from_frames(frames_list):
    if len(frames_list) == 0:
        return b""
    arr = np.concatenate(frames_list, axis=0).reshape(-1, CHANNELS)
    return arr.tobytes()

def frames_to_float32(frames_list):
    arr = np.concatenate(frames_list, axis=0).reshape(-1, CHANNELS).astype(np.int16)
    float_arr = (arr.astype(np.float32) / 32768.0).flatten()
    return float_arr

def wakeword_consumer():
    """Pull frames and perform lightweight wake-word detection using Vosk transcripts."""
    buffer_frames = []
    print("[WAKE] detector started.")
    while not terminate_event.is_set():
        try:
            frame = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        buffer_frames.append(frame)
        # keep a limited history (e.g., 4 seconds)
        max_hist = int(4 / FRAME_SECONDS)
        if len(buffer_frames) > max_hist:
            buffer_frames.pop(0)

        # feed current frame(s) to recognizer incrementally
        try:
            # we use just the latest few frames to check for wake words quickly
            recent_bytes = bytes_from_frames(buffer_frames[-max_hist:])
            if wake_recognizer.AcceptWaveform(recent_bytes):
                res = json.loads(wake_recognizer.Result())
                text = res.get("text", "")
                if text:
                    text_low = text.lower()
                    # check for wake words
                    for ww in WAKE_WORDS:
                        if ww in text_low:
                            print(f"[WAKE] detected '{ww}' in '{text}'")
                            # handle command (blocking call) but it's safe because producer continues in separate thread
                            handle_active_command()
                            buffer_frames = []
                            wake_recognizer.Reset()
                            break
            else:
                # partial result ignored (could be used to speed detection)
                pass
        except Exception as e:
            print("[WAKE] error:", e)
            wake_recognizer.Reset()

    print("[WAKE] detector stopped.")

def handle_active_command():
    """Collect post-wake audio, apply noise reduction, run ASR (whisper preferred), and reply with TTS."""
    print("[COMMAND] collecting audio for", RECORD_SECONDS_AFTER_WAKE, "seconds...")
    frames_needed = int(RECORD_SECONDS_AFTER_WAKE / FRAME_SECONDS)
    collected = []
    start_time = time.time()
    while len(collected) < frames_needed and not terminate_event.is_set():
        try:
            f = audio_queue.get(timeout=1.0)
            collected.append(f)
        except queue.Empty:
            # if no audio arrives for a while, break
            if time.time() - start_time > RECORD_SECONDS_AFTER_WAKE + 1.0:
                break

    if not collected:
        print("[COMMAND] no audio collected.")
        return

    # Save raw for debugging
    raw_arr = np.concatenate(collected, axis=0).astype(np.int16).reshape(-1, CHANNELS)
    sf.write("last_command_raw.wav", raw_arr, SAMPLE_RATE)
    print("[COMMAND] saved last_command_raw.wav")

    # Float32 mono for noise reduction / whisper
    float_audio = frames_to_float32(collected)

    # Noise reduction
    n_noise = int(0.25 * SAMPLE_RATE)  # use first 250ms as noise estimate when available
    if float_audio.shape[0] > n_noise * 2:
        noise_sample = float_audio[:n_noise]
        reduced = nr.reduce_noise(y=float_audio, sr=SAMPLE_RATE, y_noise=noise_sample)
    else:
        reduced = float_audio

    # Save preprocessed
    int16_audio = (reduced * 32767).astype(np.int16)
    sf.write("last_command_preprocessed.wav", int16_audio, SAMPLE_RATE)
    print("[COMMAND] saved last_command_preprocessed.wav")

    transcript = ""

    # Prefer faster-whisper if available
    if USE_FASTER_WHISPER and whisper_model is not None:
        try:
            print("[ASR] running faster-whisper...")
            # faster-whisper expects numpy float32 array (shape [n])
            segments, info = whisper_model.transcribe(reduced, beam_size=5)
            transcript = " ".join([s.text.strip() for s in segments]).strip()
            print("[ASR] whisper ->", transcript)
        except Exception as e:
            print("[ASR] faster-whisper failed:", e)
            transcript = ""

    # Fallback to Vosk if no transcript yet
    if not transcript:
        try:
            print("[ASR] running Vosk fallback...")
            transcript = vosk_transcribe_int16_bytes(int16_audio.tobytes())
            print("[ASR] vosk ->", transcript)
        except Exception as e:
            print("[ASR] Vosk error:", e)
            transcript = ""

    # Simple response behavior (you can replace with a command-handler)
    response = f"You said: {transcript}." if transcript else "Sorry, I did not understand that."
    print("[RESPONSE]", response)

    # Ensure mic scope settled before TTS
    time.sleep(0.15)
    try:
        safe_speak(response)
    except Exception as e:
        print("[TTS] error:", e)

def main():
    print("=== Assistant (small-model) starting ===")
    # start producer
    producer = threading.Thread(target=audio_producer, daemon=True)
    producer.start()
    # start wake consumer
    wake_thread = threading.Thread(target=wakeword_consumer, daemon=True)
    wake_thread.start()

    try:
        safe_speak("Assistant ready. Say the wake words to begin.")
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[MAIN] KeyboardInterrupt, shutting down...")
        terminate_event.set()
        time.sleep(0.5)
    except Exception:
        traceback.print_exc()
        terminate_event.set()
        time.sleep(0.5)
    print("[MAIN] exited.")

if __name__ == "__main__":
    main()
