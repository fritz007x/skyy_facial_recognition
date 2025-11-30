"""
Test pyttsx3 engine initialization and audio output.
"""

import pyttsx3
import time

def test_basic_tts():
    """Test basic TTS functionality."""
    print("\n=== Test 1: Basic TTS ===")
    print("Initializing engine...")

    engine = pyttsx3.init()

    # Get engine properties
    print(f"Engine: {engine}")
    print(f"Rate: {engine.getProperty('rate')}")
    print(f"Volume: {engine.getProperty('volume')}")

    # Get available voices
    voices = engine.getProperty('voices')
    print(f"\nAvailable voices ({len(voices)}):")
    for i, voice in enumerate(voices):
        print(f"  {i}: {voice.name}")
        print(f"      ID: {voice.id}")
        print(f"      Languages: {voice.languages}")

    # Set properties
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    print("\n--- Speaking test message ---")
    engine.say("This is a test. Can you hear me?")
    print("Calling runAndWait()...")
    engine.runAndWait()
    print("runAndWait() completed.")

    time.sleep(1)

    print("\n--- Speaking permission message ---")
    engine.say("I'd like to take your photo to see if I recognize you. Is that okay?")
    print("Calling runAndWait()...")
    engine.runAndWait()
    print("runAndWait() completed.")

def test_multiple_messages():
    """Test speaking multiple messages in sequence."""
    print("\n\n=== Test 2: Multiple Messages ===")

    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    messages = [
        "First message.",
        "Second message.",
        "Third message.",
    ]

    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}] Speaking: '{msg}'")
        engine.say(msg)
        engine.runAndWait()
        time.sleep(0.5)

def test_engine_reuse():
    """Test reusing the same engine instance."""
    print("\n\n=== Test 3: Engine Reuse ===")

    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    print("\nFirst call:")
    engine.say("First call to the engine.")
    engine.runAndWait()

    time.sleep(0.5)

    print("\nSecond call (same instance):")
    engine.say("Second call to the same engine instance.")
    engine.runAndWait()

    time.sleep(0.5)

    print("\nThird call (same instance):")
    engine.say("Third call to the same engine instance.")
    engine.runAndWait()

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("  PYTTSX3 TTS ENGINE TEST")
        print("=" * 60)

        test_basic_tts()
        time.sleep(1)

        test_multiple_messages()
        time.sleep(1)

        test_engine_reuse()

        print("\n\n" + "=" * 60)
        print("  ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
