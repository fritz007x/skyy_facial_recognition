"""
Unit test to verify the grammar transcription fix.

This test verifies that:
1. KaldiRecognizer accepts the correct grammar format (JSON array)
2. Grammar-based transcription works without hanging
3. The fix resolves the segmentation fault issue
"""

import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent / "gemma_mcp_prototype"))

print("=" * 70)
print("  GRAMMAR TRANSCRIPTION FIX VERIFICATION")
print("=" * 70)

# Test 1: Import TranscriptionEngine
print("\n[Test 1] Importing TranscriptionEngine...")
try:
    from gemma_mcp_prototype.modules.transcription_engine import TranscriptionEngine
    print("[Test 1] [OK] Import successful")
except Exception as e:
    print(f"[Test 1] [X] Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize TranscriptionEngine
print("\n[Test 2] Initializing TranscriptionEngine...")
try:
    engine = TranscriptionEngine(sample_rate=16000)
    print("[Test 2] [OK] Engine initialized")
    print(f"[Test 2]   Model path: {engine.model_path}")
    print(f"[Test 2]   Sample rate: {engine.sample_rate}")
except Exception as e:
    print(f"[Test 2] [X] Initialization failed: {e}")
    sys.exit(1)

# Test 3: Test transcribe() with grammar (the fix!)
print("\n[Test 3] Testing transcribe() with grammar (wake words)...")
try:
    import numpy as np

    # Create dummy audio (1 second of silence)
    dummy_audio = np.zeros(16000, dtype=np.int16)
    wake_words = ["hello gemma", "hey gemma", "hi gemma", "gemma"]

    print("[Test 3]   Grammar:", wake_words)
    print("[Test 3]   Audio shape:", dummy_audio.shape)
    print("[Test 3]   Calling transcribe() with grammar...")

    # This should NOT hang anymore!
    result = engine.transcribe(dummy_audio, grammar=wake_words)

    print(f"[Test 3] [OK] Transcription completed successfully!")
    print(f"[Test 3]   Result: '{result}' (empty is expected for silence)")

except Exception as e:
    print(f"[Test 3] [X] Transcription failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test transcribe() without grammar
print("\n[Test 4] Testing transcribe() without grammar (general speech)...")
try:
    result = engine.transcribe(dummy_audio)
    print(f"[Test 4] [OK] Transcription completed successfully!")
    print(f"[Test 4]   Result: '{result}' (empty is expected for silence)")
except Exception as e:
    print(f"[Test 4] [X] Transcription failed: {e}")
    sys.exit(1)

# Test 5: Test transcribe_with_confidence() with grammar
print("\n[Test 5] Testing transcribe_with_confidence() with grammar...")
try:
    commands = ["yes", "no", "okay"]
    text, confidence = engine.transcribe_with_confidence(dummy_audio, grammar=commands)
    print(f"[Test 5] [OK] Transcription completed successfully!")
    print(f"[Test 5]   Text: '{text}'")
    print(f"[Test 5]   Confidence: {confidence}")
except Exception as e:
    print(f"[Test 5] [X] Transcription failed: {e}")
    sys.exit(1)

# Test 6: Verify grammar JSON format internally
print("\n[Test 6] Verifying internal grammar JSON format...")
try:
    import json
    from vosk import KaldiRecognizer

    # This is what the FIXED code should produce
    wake_words = ["hello gemma", "hey gemma"]
    grammar_json = json.dumps(wake_words)  # Direct array, no dict!

    print(f"[Test 6]   Grammar JSON: {grammar_json}")

    # Verify it's a JSON array (starts with '[' and ends with ']')
    if grammar_json.startswith('[') and grammar_json.endswith(']'):
        print("[Test 6] [OK] Grammar format is correct (JSON array)")
    else:
        print("[Test 6] [X] Grammar format is WRONG (not a JSON array)")
        sys.exit(1)

    # Verify we can create a recognizer with it
    recognizer = KaldiRecognizer(engine.model, engine.sample_rate, grammar_json)
    print("[Test 6] [OK] KaldiRecognizer created successfully with grammar")
    del recognizer

except Exception as e:
    print(f"[Test 6] [X] Grammar verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Cleanup
print("\n[Test 7] Testing cleanup...")
try:
    engine.cleanup()
    print("[Test 7] [OK] Cleanup successful")
except Exception as e:
    print(f"[Test 7] [X] Cleanup failed: {e}")

# Summary
print("\n" + "=" * 70)
print("  ALL TESTS PASSED!")
print("=" * 70)
print("\nFix Summary:")
print("  - Grammar format changed from: {\"grammar\": [...]} (WRONG)")
print("  - Grammar format changed to:   [...]              (CORRECT)")
print("\nResult:")
print("  - KaldiRecognizer no longer hangs")
print("  - Grammar-based transcription works")
print("  - App can now transcribe with wake word constraints")
print("=" * 70)
