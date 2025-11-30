"""
Simulate the exact scenario from the Gemma MCP prototype.
"""

import sys
from pathlib import Path

# Add gemma_mcp_prototype to path
sys.path.insert(0, str(Path(__file__).parent / "gemma_mcp_prototype"))

from modules.speech import SpeechManager
from modules.permission import PermissionManager

def test_exact_flow():
    """
    Simulate the exact flow that happens in main.py:
    1. Initialize SpeechManager
    2. Initialize PermissionManager
    3. Call request_camera_permission()
    """

    print("\n" + "=" * 60)
    print("  EXACT SCENARIO SIMULATION")
    print("=" * 60 + "\n")

    print("[STEP 1] Initializing SpeechManager...")
    speech = SpeechManager(rate=150, volume=1.0)
    print("[STEP 1] SpeechManager initialized.\n")

    print("[STEP 2] Initializing PermissionManager...")
    permission = PermissionManager(speech)
    print("[STEP 2] PermissionManager initialized.\n")

    print("[STEP 3] Calling request_camera_permission()...")
    print("           (This should speak the permission request)")
    print("           Expected speech: 'I'd like to take your photo to see if I recognize you. Is that okay?'")
    print()

    # Monkey-patch listen_for_response to avoid waiting for real input
    original_listen = speech.listen_for_response

    def mock_listen(timeout=5.0):
        print(f"[MOCK] listen_for_response() called (simulating 'yes')")
        return "yes"

    speech.listen_for_response = mock_listen

    # Call the actual method
    result = permission.request_camera_permission()

    print()
    print(f"[STEP 3] request_camera_permission() returned: {result}")
    print()

    print("=" * 60)
    print("  TEST COMPLETED")
    print("=" * 60)
    print()
    print("EXPECTED CONSOLE OUTPUT:")
    print("  [Speech] Speaking: 'I'd like to take your photo...'")
    print("  [Permission] camera_capture: GRANTED")
    print("  [Speech] Speaking: 'Great! Look at the camera.'")
    print()
    print("If you heard both speech messages, the system is working.")
    print("If you didn't hear them, check your Windows audio settings.")
    print()

if __name__ == "__main__":
    try:
        test_exact_flow()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
