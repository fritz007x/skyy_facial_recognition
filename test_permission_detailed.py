"""
Detailed test of the permission flow with debugging.
"""

import sys
from pathlib import Path
import time

# Add gemma_mcp_prototype to path
sys.path.insert(0, str(Path(__file__).parent / "gemma_mcp_prototype"))

from modules.speech import SpeechManager

def test_ask_permission_flow():
    """Test ask_permission() with detailed logging."""
    print("\n=== Testing ask_permission() flow ===\n")

    speech = SpeechManager(rate=150, volume=1.0)

    # Monkey-patch speak to add debugging
    original_speak = speech.speak

    def debug_speak(text):
        print(f"[DEBUG] speak() called with: '{text}'")
        print(f"[DEBUG] Calling engine.say()...")
        speech.engine.say(text)
        print(f"[DEBUG] Calling engine.runAndWait()...")
        speech.engine.runAndWait()
        print(f"[DEBUG] engine.runAndWait() completed")

    speech.speak = debug_speak

    # Monkey-patch listen_for_response to simulate response
    original_listen = speech.listen_for_response

    def debug_listen(timeout=5.0):
        print(f"[DEBUG] listen_for_response() called with timeout={timeout}")
        print(f"[DEBUG] Simulating user saying 'no'")
        return "no"  # Simulate negative response

    speech.listen_for_response = debug_listen

    # Now call ask_permission
    print("\n[TEST] Calling ask_permission()...")
    result = speech.ask_permission("I'd like to take your photo to see if I recognize you. Is that okay?")
    print(f"\n[TEST] ask_permission() returned: {result}")
    print(f"[TEST] Expected: False (because we simulated 'no')")

if __name__ == "__main__":
    try:
        test_ask_permission_flow()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
