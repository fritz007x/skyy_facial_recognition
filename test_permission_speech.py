"""
Test script to debug permission request speech issue.
"""

import sys
from pathlib import Path

# Add gemma_mcp_prototype to path
sys.path.insert(0, str(Path(__file__).parent / "gemma_mcp_prototype"))

from modules.speech import SpeechManager

def test_direct_speak():
    """Test direct speak() method."""
    print("\n=== Test 1: Direct speak() ===")
    speech = SpeechManager(rate=150, volume=1.0)
    speech.speak("This is a direct speech test.")
    print("Test 1 completed.\n")

def test_ask_permission():
    """Test ask_permission() method."""
    print("\n=== Test 2: ask_permission() ===")
    speech = SpeechManager(rate=150, volume=1.0)

    # This should speak the prompt
    result = speech.ask_permission("I'd like to take your photo to see if I recognize you. Is that okay?")
    print(f"Permission granted: {result}")
    print("Test 2 completed.\n")

def test_permission_manager():
    """Test PermissionManager.request_camera_permission()."""
    print("\n=== Test 3: PermissionManager ===")
    from modules.permission import PermissionManager

    speech = SpeechManager(rate=150, volume=1.0)
    permission = PermissionManager(speech)

    # This should speak the permission request
    result = permission.request_camera_permission()
    print(f"Camera permission granted: {result}")
    print("Test 3 completed.\n")

if __name__ == "__main__":
    print("Testing permission speech flow...")
    print("You will hear 3 different tests.\n")

    try:
        test_direct_speak()
        print("Waiting 2 seconds before next test...")
        import time
        time.sleep(2)

        # Skip Test 2 - it requires microphone input
        print("Skipping Test 2 (requires microphone)...\n")

        # Test 3 - just the speech part, not the listening
        print("\n=== Test 3: Direct Permission Speech ===")
        from modules.permission import PermissionManager
        speech = SpeechManager(rate=150, volume=1.0)

        # Call speak directly to test if TTS works
        speech.speak("I'd like to take your photo to see if I recognize you. Is that okay?")
        print("Permission prompt spoken.")
        print("Test 3 completed.\n")

    except KeyboardInterrupt:
        print("\nTest interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
