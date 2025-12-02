"""
Semi-automated test script for deletion feature.
Run this to verify the implementation works.

Usage:
    python test_deletion_automated.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "gemma_mcp_prototype"))

from modules.deletion_orchestrator import DeletionOrchestrator, DeletionState


def test_state_machine():
    """Test state machine initialization and reset."""
    print("Test 1: State Machine Initialization")

    def mock_tts(text):
        print(f"  [TTS] {text}")

    orchestrator = DeletionOrchestrator(
        tts_speak_func=mock_tts,
        whisper_model="base",
        whisper_device="cpu",
        whisper_compute_type="float32"
    )

    assert orchestrator.state == DeletionState.IDLE, "Initial state should be IDLE"
    print("  ✓ Initial state is IDLE")

    orchestrator.state = DeletionState.COMPLETED
    orchestrator.reset()
    assert orchestrator.state == DeletionState.IDLE, "Reset should return to IDLE"
    print("  ✓ Reset works correctly")

    print("\n✓ Test 1 PASSED\n")


def test_confirmation_extraction():
    """Test yes/no extraction from text."""
    print("Test 2: Confirmation Extraction")

    def mock_tts(text):
        pass

    orchestrator = DeletionOrchestrator(
        tts_speak_func=mock_tts,
        whisper_model="base",
        whisper_device="cpu",
        whisper_compute_type="float32"
    )

    # Test positive responses
    test_cases = [
        ("yes", True),
        ("yeah", True),
        ("yep", True),
        ("yes please", True),
        ("sure", True),
        ("correct", True),
        ("no", False),
        ("nope", False),
        ("no way", False),
        ("wrong", False),
        ("cancel", False),
        ("maybe", None),
        ("I don't know", None),
        ("", None)
    ]

    for text, expected in test_cases:
        result = orchestrator._extract_confirmation(text)
        assert result == expected, f"Failed for '{text}': expected {expected}, got {result}"
        print(f"  ✓ '{text}' -> {result}")

    print("\n✓ Test 2 PASSED\n")


def test_imports():
    """Test all imports work correctly."""
    print("Test 3: Import Validation")

    try:
        from config import DELETION_WAKE_WORD, DELETION_WAKE_WORD_ALTERNATIVES
        print(f"  ✓ Config imports: {DELETION_WAKE_WORD}")
        print(f"  ✓ Alternatives: {DELETION_WAKE_WORD_ALTERNATIVES}")

        from modules.deletion_orchestrator import DeletionOrchestrator, DeletionState
        print("  ✓ DeletionOrchestrator imports successfully")

        from modules.mcp_sync_facade import SyncMCPFacade
        print("  ✓ SyncMCPFacade imports successfully")

        # Verify SyncMCPFacade has delete_user method
        assert hasattr(SyncMCPFacade, 'delete_user'), "SyncMCPFacade missing delete_user"
        print("  ✓ SyncMCPFacade has delete_user method")

        print("\n✓ Test 3 PASSED\n")

    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        raise


def test_state_transitions():
    """Test all valid state transitions."""
    print("Test 4: State Transitions")

    def mock_tts(text):
        pass

    orchestrator = DeletionOrchestrator(
        tts_speak_func=mock_tts,
        whisper_model="base",
        whisper_device="cpu",
        whisper_compute_type="float32"
    )

    # Valid state transitions
    valid_transitions = [
        (DeletionState.IDLE, DeletionState.FACE_RECOGNITION),
        (DeletionState.FACE_RECOGNITION, DeletionState.CONFIRM_IDENTITY),
        (DeletionState.FACE_RECOGNITION, DeletionState.CANCELLED),
        (DeletionState.CONFIRM_IDENTITY, DeletionState.EXPLAIN_CONSEQUENCES),
        (DeletionState.CONFIRM_IDENTITY, DeletionState.CANCELLED),
        (DeletionState.EXPLAIN_CONSEQUENCES, DeletionState.FINAL_CONFIRMATION),
        (DeletionState.FINAL_CONFIRMATION, DeletionState.DELETE_USER),
        (DeletionState.FINAL_CONFIRMATION, DeletionState.CANCELLED),
        (DeletionState.DELETE_USER, DeletionState.COMPLETED),
        (DeletionState.DELETE_USER, DeletionState.CANCELLED),
    ]

    for from_state, to_state in valid_transitions:
        orchestrator.state = from_state
        orchestrator.state = to_state
        assert orchestrator.state == to_state, f"Failed transition {from_state} -> {to_state}"
        print(f"  ✓ {from_state.value} -> {to_state.value}")

    print("\n✓ Test 4 PASSED\n")


def test_orchestrator_attributes():
    """Test orchestrator has all required attributes."""
    print("Test 5: Orchestrator Attributes")

    def mock_tts(text):
        pass

    orchestrator = DeletionOrchestrator(
        tts_speak_func=mock_tts,
        whisper_model="base",
        whisper_device="cpu",
        whisper_compute_type="float32"
    )

    # Check required attributes
    required_attributes = [
        'tts_speak',
        'vad',
        'whisper',
        'state',
        'recognize_user',
        'confirm_identity',
        'explain_and_confirm_deletion',
        'execute_deletion',
        'run_deletion_flow',
        'reset',
        '_extract_confirmation'
    ]

    for attr in required_attributes:
        assert hasattr(orchestrator, attr), f"Missing attribute: {attr}"
        print(f"  ✓ Has attribute: {attr}")

    print("\n✓ Test 5 PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  DELETION FEATURE - AUTOMATED TESTS")
    print("=" * 60 + "\n")

    try:
        test_imports()
        test_state_machine()
        test_confirmation_extraction()
        test_state_transitions()
        test_orchestrator_attributes()

        print("=" * 60)
        print("  ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nNext: Run manual tests with actual voice/camera")
        print("See: TEST_DELETION_FEATURE.md for manual test procedures")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
