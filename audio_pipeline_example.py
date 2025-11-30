import sounddevice as sd
import soundfile as sf
import numpy as np
import pyttsx3
from vosk import Model, KaldiRecognizer
import json
import time
import sys

# -------------------------------
# 1. Initialize TTS
# -------------------------------
tts = pyttsx3.init()

def speak(text):
    """
    Safe synchronous TTS; guaranteed to release audio device.
    """
    tts.say(text)
    tts.runAndWait()
    # Give OS a moment to fully release the audio output device
   # time.sleep(0.15)

# -------------------------------
# 2. Load Offline Vosk Model
# -------------------------------
model_path = "vosk-model-small-en-us-0.15"
model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

# -------------------------------
# 3. Initial TTS prompt
# -------------------------------
print("Hello! Please speak after the beep.")
print("Beep!")
#time.sleep(0.4)  # let TTS release device before recording

# -------------------------------
# 4. Record Microphone Audio
# -------------------------------
duration = 4  # seconds
sample_rate = 16000

print("Recording...")
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
sd.wait()  # ensures microphone is fully released after this line
print("Recording done.")

# Save audio for debugging / visualization
sf.write("voice_input.wav", audio, sample_rate)

# Flatten and convert to bytes for Vosk
audio_bytes = audio.tobytes()

# -------------------------------
# 5. Offline Speech Recognition
# -------------------------------
print("Recognizing...")
if recognizer.AcceptWaveform(audio_bytes):
    result_json = recognizer.Result()
else:
    result_json = recognizer.FinalResult()

result = json.loads(result_json)
recognized_text = result.get("text", "").strip()

print("You said:", recognized_text if recognized_text else "[unrecognized]")

# -------------------------------
# 6. TTS Response
# -------------------------------
if recognized_text:
    speak(f"You said: {recognized_text}. Nice to hear that.")
else:
    speak("Sorry. I did not understand you.")

# -------------------------------
# 7. Ask for Camera Permission
# -------------------------------
print("\n" + "="*60)
print("CAMERA PERMISSION REQUEST")
print("="*60)

speak("I'd like to take your photo to see if I recognize you. Is that okay?")
time.sleep(0.5)  # Ensure TTS fully completes before recording

# Record permission response
print("\nListening for your response (say 'yes' or 'no')...")
print("Recording permission response...")
permission_audio = sd.rec(int(3 * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
sd.wait()
print("Recording done.")

# Convert to bytes for Vosk
permission_audio_bytes = permission_audio.tobytes()

# Reset recognizer for new audio
recognizer = KaldiRecognizer(model, 16000)

# Recognize permission response
print("Recognizing permission response...")
if recognizer.AcceptWaveform(permission_audio_bytes):
    permission_result_json = recognizer.Result()
else:
    permission_result_json = recognizer.FinalResult()

permission_result = json.loads(permission_result_json)
permission_text = permission_result.get("text", "").strip()

print("\n" + "="*60)
print("PERMISSION RESPONSE:")
print(f"  User said: '{permission_text if permission_text else '[unrecognized]'}'")
print("="*60)

# Check for affirmative response
affirmative_words = ["yes", "yeah", "sure", "okay", "ok", "yep", "go ahead", "please", "alright", "fine"]
permission_granted = any(word in permission_text.lower() for word in affirmative_words)

if permission_granted:
    print("  Status: PERMISSION GRANTED")
    speak("Great! I'll take your photo now.")
else:
    print("  Status: PERMISSION DENIED")
    speak("No problem. Let me know if you change your mind.")

print("="*60)
