"""
realtime_whisper_name_capture.py

Requirements:
  pip install sounddevice soundfile numpy webrtcvad pyttsx3 faster-whisper noisereduce

Usage:
  python realtime_whisper_name_capture.py
"""

import sounddevice as sd
import numpy as np
import webrtcvad
import time
import queue
import sys
import soundfile as sf
import pyttsx3

# Optional: noise reduction (improves accuracy in noisy rooms)
try:
    import noisereduce as nr
    HAVE_NOISEREDUCE = True
except Exception:
    HAVE_NOISEREDUCE = False

# faster-whisper (Whisper medium)
try:
    from faster_whisper import WhisperModel
except Exception as e:
    print("faster-whisper not installed or failed to import:", e)
    print("pip install faster-whisper")
    raise

# ---------------- CONFIG ----------------
SAMPLE_RATE = 16000               # Whisper expects 16k
CHANNELS = 1
VAD_MODE = 3                      # 0-3, 3 is most aggressive
FRAME_DURATION_MS = 30            # frame size for the VAD: 10, 20 or 30 ms
SILENCE_AFTER_SPEECH_SEC = 1.0    # stop when this much silence observed after speech end
MIN_SPEECH_SEC = 0.4              # minimum speech length to accept as a name
WHISPER_MODEL_NAME = "medium"     # 'medium' recommended for names
DEVICE = "cuda" if False else "cpu"  # change to "cuda" if you have GPU
# ----------------------------------------

# Init TTS
tts = pyttsx3.init()
tts.setProperty("rate", 160)

def speak(text):
    """Simple synchronous TTS with small pause to reduce device contention"""
    time.sleep(0.12)
    tts.say(text)
    tts.runAndWait()
    time.sleep(0.12)

# Initialize Whisper model (faster-whisper)
print(f"[INFO] Loading Whisper model: {WHISPER_MODEL_NAME} on {DEVICE} ...")
whisper_model = WhisperModel(WHISPER_MODEL_NAME, device=DEVICE, compute_type="float32")
print("[INFO] Whisper model loaded.")

# VAD setup
vad = webrtcvad.Vad(VAD_MODE)
frame_size = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # samples per frame

# Helper: chunk raw bytes into VAD frames
def frame_generator(frames, frame_duration_ms=FRAME_DURATION_MS):
    """Yield consecutive fixed-size frames (bytes) for VAD; frames: numpy int16 chunks"""
    # frames is a list of numpy arrays int16
    data = np.concatenate(frames, axis=0).reshape(-1)
    i = 0
    bytes_per_sample = 2
    frame_bytes = frame_size * bytes_per_sample
    data_bytes = data.tobytes()
    while i + frame_bytes <= len(data_bytes):
        yield data_bytes[i:i+frame_bytes]
        i += frame_bytes

def is_speech_frame(frame_bytes):
    return vad.is_speech(frame_bytes, SAMPLE_RATE)

# Recording helper using blocking InputStream and collecting small frames into a queue
def record_name_vad():
    """Prompts user to speak a full name and returns numpy float32 array (mono, -1..1)"""
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            # print status but don't throw
            print("[sounddevice status]", status, file=sys.stderr)
        # indata dtype is int16 if dtype specified; keep int16
        q.put(indata.copy())

    # Use small blocksize that aligns with frame_size
    blocksize = frame_size

    # Start stream
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16",
                        blocksize=blocksize, callback=callback):
        print("[INFO] Listening (say your full name)...")
        # Wait for user to start speaking using VAD
        pre_speech_buffers = []
        speech_started = False
        speech_buffers = []
        silence_start_time = None
        start_time = time.time()
        while True:
            try:
                chunk = q.get(timeout=5.0)
            except queue.Empty:
                # no audio; keep waiting
                continue

            pre_speech_buffers.append(chunk)
            # Maintain a limited pre-speech buffer (~1.5s)
            if sum(b.shape[0] for b in pre_speech_buffers) > SAMPLE_RATE * 2:
                pre_speech_buffers.pop(0)

            # Convert the latest small chunk(s) into bytes for VAD checks
            # We'll use only most recent frames up to a second for detection
            recent = pre_speech_buffers[-int(1.0 / (FRAME_DURATION_MS/1000)):]  # last ~1s
            # Check any speech in recent frames
            has_speech = False
            for fbytes in frame_generator(recent):
                if is_speech_frame(fbytes):
                    has_speech = True
                    break

            if not speech_started:
                if has_speech:
                    # speech has started
                    speech_started = True
                    print("[INFO] Speech started")
                    # Move buffered recent audio to speech_buffers to preserve leading samples
                    speech_buffers.extend(pre_speech_buffers)
                    pre_speech_buffers = []
                    silence_start_time = None
                else:
                    # keep waiting for speech
                    continue
            else:
                # Already started—append the chunk
                speech_buffers.append(chunk)
                # Evaluate if chunk contains any speech frames
                recent_frames = list(frame_generator([chunk]))
                any_speech = any(is_speech_frame(b) for b in recent_frames)
                if any_speech:
                    silence_start_time = None
                else:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elapsed_silence = time.time() - silence_start_time
                    if elapsed_silence >= SILENCE_AFTER_SPEECH_SEC:
                        # end of speech detected
                        print("[INFO] End of speech detected (silence).")
                        break

            # safety timeout (avoid infinite loop)
            if time.time() - start_time > 15.0:
                print("[WARN] Recording timeout reached.")
                break

    if len(speech_buffers) == 0:
        return None

    # concatenate int16 frames into int16 numpy array
    int16_arr = np.concatenate(speech_buffers, axis=0).reshape(-1)
    # compute speech length
    speech_duration = int16_arr.shape[0] / SAMPLE_RATE
    print(f"[INFO] Captured {speech_duration:.2f}s of audio.")

    if speech_duration < MIN_SPEECH_SEC:
        print("[WARN] Speech too short.")
        return None

    # optional noise reduction (works on float)
    float_audio = (int16_arr.astype(np.float32) / 32768.0)
    if HAVE_NOISEREDUCE:
        try:
            # estimate noise from first 0.25s if available
            n_noise = int(0.25 * SAMPLE_RATE)
            if float_audio.size > n_noise * 2:
                noise_clip = float_audio[:n_noise]
                reduced = nr.reduce_noise(y=float_audio, y_noise=noise_clip, sr=SAMPLE_RATE)
                float_audio = reduced
        except Exception as e:
            print("[WARN] noisereduce failed:", e)

    return float_audio.astype(np.float32)

# Transcribe with faster-whisper
def transcribe_audio_float32(float_audio):
    """Takes numpy float32 audio (mono, -1..1) and returns transcript string"""
    # faster-whisper's transcribe supports feeding numpy array directly
    # Use a small beam size for quality; adjust as needed
    try:
        segments, info = whisper_model.transcribe(float_audio, beam_size=5)
        # join segments
        text = " ".join([seg.text.strip() for seg in segments]).strip()
        return text
    except Exception as e:
        print("[ERROR] Whisper transcription failed:", e)
        return ""

# Simple quality checks for name text
def looks_like_full_name(text):
    """Heuristic: at least two words, each reasonably short (<= 40 chars)"""
    if not text or len(text.strip()) == 0:
        return False
    words = text.strip().split()
    return len(words) >= 2 and all(1 <= len(w) <= 40 for w in words)

# Main flow
def capture_and_confirm_name():
    speak("Please say your full name after the beep.")
    print("Beep!")
    time.sleep(0.25)   # small gap

    audio = record_name_vad()
    if audio is None:
        speak("I didn't catch that. Please try again.")
        return None

    # Transcribe
    speak("Processing your name now.")
    name_text = transcribe_audio_float32(audio)
    print("[TRANSCRIPT]", name_text)

    if looks_like_full_name(name_text):
        speak(f"I heard {name_text}. Is that correct? Say yes to confirm or no to try again.")
        # simple listening for yes/no using the same VAD + quick transcribe
        # For brevity we record again short answer
        ans_audio = record_name_vad()
        if ans_audio:
            ans = transcribe_audio_float32(ans_audio).lower()
            print("[CONFIRM TRANSCRIPT]", ans)
            if "yes" in ans or "correct" in ans or ans.strip() == "yeah":
                speak("Great. I have saved your name.")
                return name_text
            else:
                speak("Okay, let's try again.")
                return None
        else:
            speak("No confirmation heard; let's try again later.")
            return None
    else:
        # fallback: ask to spell letters
        speak("I couldn't capture your full name clearly. Please spell your full name, one letter at a time, saying letters slowly after the beep.")
        time.sleep(0.25)
        spell_audio = record_name_vad()
        if spell_audio is None:
            speak("I didn't get that. Let's try the whole name again later.")
            return None
        spell_text = transcribe_audio_float32(spell_audio)
        print("[SPELL TRANSCRIPT]", spell_text)
        # naive extraction of letters from transcript (Whisper often transcribes spelled letters as letters or words)
        # Try to extract A..Z tokens
        letters = []
        for token in spell_text.replace(",", " ").replace(".", " ").split():
            token_upper = token.strip().upper()
            if len(token_upper) == 1 and token_upper.isalpha():
                letters.append(token_upper)
            else:
                # map common spelled-out words to letters (one, be ->? not reliable)
                # skip advanced mapping for brevity
                pass
        if len(letters) >= 2:
            spelled = "".join(letters)
            speak(f"I captured the spelling: {spelled}. Is that correct?")
            # No robust confirm implemented here; assume yes
            return spelled
        else:
            speak("Sorry, I couldn't parse the spelled name. Let's try again later.")
            return None

if __name__ == "__main__":
    try:
        while True:
            result = capture_and_confirm_name()
            if result:
                print("[FINAL NAME]", result)
                break
            # small pause between retries
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[EXIT] Interrupted by user.")
        sys.exit(0)
