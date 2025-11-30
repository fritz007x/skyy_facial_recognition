"""
Interactive test - FULLY SYNCHRONOUS (no asyncio).

This tests the complete speech flow without any async/await.
You can speak to the microphone to test the full flow.
"""

import sys
import time
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.speech import SpeechManager
from modules.permission import PermissionManager

def test_synchronous_speech_flow():
    """Test completely synchronous speech flow (no async)."""
    print("\n" + "="*60)
    print("INTERACTIVE TTS TEST - FULLY SYNCHRONOUS")
    print("="*60)

    speech = SpeechManager()
    permission = PermissionManager(speech)

    # Test 1: Wake word detection (no initial greeting - starts immediately)
    print("\n[Test 1] Listening for wake word (no initial greeting)...")
    print("[Test] Say 'hello' (or 'hello gemma', 'hey') within 10 seconds...")

    detected, transcription = speech.listen_for_wake_word(
        wake_words=["hello", "hello test", "hello gemma", "hey"],
        timeout=10.0
    )

    if detected:
        print(f"\n[Test] Wake word detected in: '{transcription}'")

        # THIS IS THE CRITICAL TEST - speak after wake word
        print("\n[Test 2] Speaking test message after wake word detection...")
        speech.speak("Wake word detected! Testing speech output after microphone use.")

        time.sleep(1)

        # Test 3: Permission flow
        print("\n[Test 3] Testing ask_permission flow (via PermissionManager)...")
        print("[Test] You will hear a question. Say 'yes' or 'no'...")

        time.sleep(1)

        granted = permission.ask_permission(
            "I'd like to take your photo to see if I recognize you. Is that okay?",
            log_type="camera_test"
        )

        if granted:
            print("\n[Test] Permission granted!")
            speech.speak("Thank you! Permission granted.")
        else:
            print("\n[Test] Permission denied.")
            speech.speak("No problem! Permission denied.")

        time.sleep(1)

        print("\n[Test] SUCCESS! All TTS messages worked!")
        print("[Test] If you heard all messages clearly, the fix is working!")

    else:
        print(f"\n[Test] Wake word not detected. Heard: '{transcription}'")
        print("[Test] Try running the test again and say 'hello' clearly.")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE SPEECH TEST - FULLY SYNCHRONOUS")
    print("="*60)
    print("\nThis test is 100% synchronous (no asyncio) to isolate TTS issues.")
    print("\nYou will:")
    print("  1. Say 'hello' (or 'hello gemma', 'hey') to trigger wake word")
    print("  2. Hear a test message after wake word (THE CRITICAL TEST)")
    print("  3. Hear a permission question and respond with 'yes' or 'no'")
    print("\nNO initial greeting - starts listening immediately!")
    print("Make sure your microphone and speakers are working!")

    input("\nPress Enter to start the test...")

    try:
        test_synchronous_speech_flow()
    except KeyboardInterrupt:
        print("\n\n[Test] Interrupted by user.")
    except Exception as e:
        print(f"\n\n[Test] ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n[Test] Test complete.")
