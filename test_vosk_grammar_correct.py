"""
Test to verify the CORRECT grammar format for Vosk.

Based on the error: "Expecting array of strings, got: '{"grammar": [...]}"
The fix is to pass a JSON array directly, NOT wrapped in a dict.
"""

import json
import numpy as np
from pathlib import Path
from vosk import Model, KaldiRecognizer

print("=" * 70)
print("  VOSK CORRECT GRAMMAR FORMAT TEST")
print("=" * 70)

# Load model
model_path = Path(__file__).parent / "vosk-model-small-en-us-0.15"
print(f"\n[Setup] Loading Vosk model from: {model_path}")

if not model_path.exists():
    print(f"ERROR: Model not found at {model_path}")
    exit(1)

model = Model(str(model_path))
print("[Setup] [OK] Model loaded successfully")

# Test configurations
sample_rate = 16000
wake_words = ["hello gemma", "hey gemma", "hi gemma", "gemma"]

print("\n" + "=" * 70)
print("TEST 1: WRONG FORMAT (current implementation)")
print("=" * 70)
print("[Test 1] This is what the current code does (INCORRECT):")
grammar_dict = {"grammar": wake_words}
grammar_json_wrong = json.dumps(grammar_dict)
print(f"[Test 1] Grammar JSON (WRONG): {grammar_json_wrong}")
print("[Test 1] Vosk expects: a JSON array, not a dict")
print("[Test 1] This will cause: 'Expecting array of strings' warning + segfault")

print("\n" + "=" * 70)
print("TEST 2: CORRECT FORMAT (direct JSON array)")
print("=" * 70)
try:
    print("[Test 2] Creating grammar as DIRECT JSON array (no dict wrapper)...")
    grammar_json_correct = json.dumps(wake_words)  # Just the list, no dict!
    print(f"[Test 2] Grammar JSON (CORRECT): {grammar_json_correct}")

    print("[Test 2] Creating KaldiRecognizer with correct format...")
    recognizer = KaldiRecognizer(model, sample_rate, grammar_json_correct)
    print("[Test 2] [OK] Recognizer created successfully!")

    # Test with actual audio
    print("[Test 2] Testing with dummy audio (silence)...")
    dummy_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
    audio_bytes = dummy_audio.tobytes()

    if recognizer.AcceptWaveform(audio_bytes):
        result = json.loads(recognizer.Result())
    else:
        result = json.loads(recognizer.FinalResult())

    print(f"[Test 2] Result: {result}")
    print("[Test 2] [OK] Recognition completed successfully!")

    del recognizer
    print("[Test 2] [OK] ALL TESTS PASSED!")

except Exception as e:
    print(f"[Test 2] [X] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("SOLUTION SUMMARY")
print("=" * 70)
print("WRONG (current code):")
print('  grammar_dict = {"grammar": wake_words}')
print('  grammar_json = json.dumps(grammar_dict)')
print('  # Produces: {"grammar": ["hello gemma", ...]}  <- WRONG!')
print()
print("CORRECT (fix):")
print('  grammar_json = json.dumps(wake_words)')
print('  # Produces: ["hello gemma", ...]  <- CORRECT!')
print("=" * 70)
