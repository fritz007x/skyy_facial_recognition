"""
Test for microphone/speaker conflict in speech flow.
"""

import speech_recognition as sr
import pyttsx3
import time

def test_speak_then_listen():
    """Test speaking then listening with the same microphone."""
    print("\n=== Test: Speak then Listen ===\n")

    # Initialize TTS
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    # Initialize speech recognition
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    print("[1] Calibrating microphone...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
    print("[1] Microphone calibrated.\n")

    print("[2] Speaking...")
    engine.say("I'd like to take your photo to see if I recognize you. Is that okay?")
    engine.runAndWait()
    print("[2] Speaking completed.\n")

    print("[3] Waiting 0.5 seconds...")
    time.sleep(0.5)

    print("[4] Listening for response (5 second timeout)...")
    with microphone as source:
        try:
            audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=10)
            print("[4] Audio captured, attempting recognition...")

            try:
                transcription = recognizer.recognize_google(audio)
                print(f"[4] Heard: '{transcription}'")
            except sr.UnknownValueError:
                print("[4] Could not understand response")
            except sr.RequestError as e:
                print(f"[4] Recognition error: {e}")

        except sr.WaitTimeoutError:
            print("[4] Timeout - no response detected")

    print("\n[TEST] Completed.\n")

def test_concurrent_init():
    """Test if creating TTS and SR together causes issues."""
    print("\n=== Test: Concurrent Initialization ===\n")

    print("[1] Creating speech recognition first...")
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    print("[1] SR created.\n")

    print("[2] Creating TTS...")
    engine = pyttsx3.init()
    print("[2] TTS created.\n")

    print("[3] Calibrating microphone...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
    print("[3] Calibrated.\n")

    print("[4] Speaking test message...")
    engine.say("Test message for concurrent initialization.")
    engine.runAndWait()
    print("[4] Spoken.\n")

    print("[TEST] Completed.\n")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("  MICROPHONE/SPEAKER CONFLICT TEST")
        print("=" * 60)

        test_concurrent_init()
        time.sleep(1)

        test_speak_then_listen()

        print("\n" + "=" * 60)
        print("  ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
