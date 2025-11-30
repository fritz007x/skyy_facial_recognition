"""
Test Speech Recognition -> TTS Flow

This script tests the complete speech recognition and TTS flow
to isolate any issues in the speech.py module.
"""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.speech import SpeechManager

def test_1_basic_tts():
    """Test 1: Basic TTS (no microphone, no async)"""
    print("\n" + "="*60)
    print("TEST 1: Basic TTS (Sync Context)")
    print("="*60)

    speech = SpeechManager()

    print("\n[Test] Speaking test message...")
    speech.speak("Test one. This is basic text to speech.")

    print("[Test] If you heard that, TTS works in sync context!")
    input("\nPress Enter to continue to Test 2...")

def test_2_microphone_then_tts():
    """Test 2: Use microphone, then TTS"""
    print("\n" + "="*60)
    print("TEST 2: Microphone -> TTS (Sync Context)")
    print("="*60)

    speech = SpeechManager()

    print("\n[Test] Say anything within 5 seconds...")
    response = speech.listen_for_response(timeout=5.0)

    if response:
        print(f"[Test] You said: '{response}'")
        print("[Test] Now testing TTS after microphone use...")
        speech.speak(f"You said: {response}")
        print("[Test] If you heard that, TTS works after microphone!")
    else:
        print("[Test] No response detected. Testing TTS anyway...")
        speech.speak("No response was detected.")

    input("\nPress Enter to continue to Test 3...")

def test_3_wake_word_then_tts():
    """Test 3: Wake word detection, then TTS"""
    print("\n" + "="*60)
    print("TEST 3: Wake Word Detection -> TTS (Sync Context)")
    print("="*60)

    speech = SpeechManager()

    print("\n[Test] Say 'hello test' within 10 seconds...")
    detected, transcription = speech.listen_for_wake_word(
        wake_words=["hello test"],
        timeout=10.0
    )

    if detected:
        print(f"[Test] Wake word detected in: '{transcription}'")
        print("[Test] Now testing TTS after wake word detection...")
        speech.speak("Wake word detected! This is a test message.")
        print("[Test] If you heard that, wake word → TTS works!")
    else:
        print(f"[Test] Wake word not detected. Heard: '{transcription}'")
        speech.speak("Wake word was not detected.")

    input("\nPress Enter to continue to Test 4...")

async def test_4_async_context():
    """Test 4: TTS in async context (like main.py)"""
    print("\n" + "="*60)
    print("TEST 4: TTS in Async Context")
    print("="*60)

    speech = SpeechManager()

    print("\n[Test] Testing TTS from async function...")
    speech.speak("Test four. This is text to speech from async context.")

    # Give it time to complete
    await asyncio.sleep(2)

    print("[Test] If you heard that, TTS works in async context!")

async def test_5_async_wake_word_then_tts():
    """Test 5: Full flow in async context (simulates main.py)"""
    print("\n" + "="*60)
    print("TEST 5: Full Flow in Async Context (Simulates main.py)")
    print("="*60)

    speech = SpeechManager()

    # Initial message (like startup)
    print("\n[Test] Initial message...")
    speech.speak("I am ready. Say hello test within ten seconds.")
    await asyncio.sleep(3)

    # Listen for wake word
    print("\n[Test] Listening for wake word...")
    detected, transcription = speech.listen_for_wake_word(
        wake_words=["hello test"],
        timeout=10.0
    )

    if detected:
        print(f"[Test] Wake word detected: '{transcription}'")

        # THIS IS THE CRITICAL TEST - TTS after wake word in async context
        print("[Test] Speaking message after wake word detection...")
        speech.speak("Wake word detected! Testing speech after microphone use in async context.")

        await asyncio.sleep(2)

        # Ask permission (simulates the actual flow)
        print("\n[Test] Testing ask_permission flow...")
        granted = speech.ask_permission("Can I proceed with the test?")

        if granted:
            speech.speak("Permission granted. Thank you!")
        else:
            speech.speak("Permission denied. No problem!")

        await asyncio.sleep(2)

    else:
        print(f"[Test] Wake word not detected. Heard: '{transcription}'")
        speech.speak("Wake word not detected.")
        await asyncio.sleep(2)

    print("\n[Test] Test 5 complete!")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SPEECH RECOGNITION -> TTS FLOW TESTS")
    print("="*60)
    print("\nThis will run 5 tests to isolate speech issues.")
    print("Make sure your speakers are ON and volume is UP!")
    input("\nPress Enter to start...")

    try:
        # Test 1: Basic TTS
        test_1_basic_tts()

        # Test 2: Microphone → TTS
        test_2_microphone_then_tts()

        # Test 3: Wake word → TTS
        test_3_wake_word_then_tts()

        # Test 4: Async TTS
        print("\n[Test] Running async test 4...")
        asyncio.run(test_4_async_context())
        input("\nPress Enter to continue to Test 5...")

        # Test 5: Full flow in async (simulates main.py)
        print("\n[Test] Running async test 5...")
        asyncio.run(test_5_async_wake_word_then_tts())

        print("\n" + "="*60)
        print("ALL TESTS COMPLETE")
        print("="*60)
        print("\nResults:")
        print("  - If you heard all messages: Everything works!")
        print("  - If you heard some but not others: Note which failed")
        print("  - If you heard none: Check speakers/volume")

    except KeyboardInterrupt:
        print("\n\n[Test] Tests interrupted by user.")
    except Exception as e:
        print(f"\n\n[Test] ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
