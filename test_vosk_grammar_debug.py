"""
Debug script to identify why KaldiRecognizer hangs with grammar.

Tests different grammar formats and initialization approaches.
"""

import json
import numpy as np
from pathlib import Path
from vosk import Model, KaldiRecognizer

print("=" * 70)
print("  VOSK GRAMMAR DEBUG TEST")
print("=" * 70)

# Load model
model_path = Path(__file__).parent / "vosk-model-small-en-us-0.15"
print(f"\n[Step 1] Loading Vosk model from: {model_path}")

if not model_path.exists():
    print(f"ERROR: Model not found at {model_path}")
    exit(1)

model = Model(str(model_path))
print("[Step 1] [OK] Model loaded successfully")

# Test configurations
sample_rate = 16000
wake_words = ["hello gemma", "hey gemma", "hi gemma", "gemma"]

print("\n" + "=" * 70)
print("TEST 1: Create recognizer WITHOUT grammar (baseline)")
print("=" * 70)
try:
    print("[Test 1] Creating KaldiRecognizer(model, sample_rate)...")
    recognizer = KaldiRecognizer(model, sample_rate)
    print("[Test 1] [OK] Recognizer created successfully WITHOUT grammar")
    del recognizer
except Exception as e:
    print(f"[Test 1] [X] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 2: Create recognizer WITH grammar (current implementation)")
print("=" * 70)
try:
    print("[Test 2] Creating grammar dict...")
    grammar_dict = {"grammar": wake_words}
    grammar_json = json.dumps(grammar_dict)
    print(f"[Test 2] Grammar JSON: {grammar_json}")

    print("[Test 2] Creating KaldiRecognizer(model, sample_rate, grammar_json)...")
    print("[Test 2] WARNING: This may hang if there's a bug...")

    # Try with timeout simulation
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("KaldiRecognizer creation timed out after 5 seconds")

    # Note: signal.alarm only works on Unix, not Windows
    # On Windows, we'll just wait and see if it hangs

    recognizer = KaldiRecognizer(model, sample_rate, grammar_json)
    print("[Test 2] [OK] Recognizer created successfully WITH grammar")
    del recognizer
except TimeoutError as e:
    print(f"[Test 2] [X] TIMEOUT: {e}")
except Exception as e:
    print(f"[Test 2] [X] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 3: Alternative grammar format (list instead of dict)")
print("=" * 70)
try:
    print("[Test 3] Creating grammar as direct list...")
    grammar_json = json.dumps(wake_words)
    print(f"[Test 3] Grammar JSON: {grammar_json}")

    print("[Test 3] Creating KaldiRecognizer(model, sample_rate, grammar_json)...")
    recognizer = KaldiRecognizer(model, sample_rate, grammar_json)
    print("[Test 3] [OK] Recognizer created successfully with list format")
    del recognizer
except Exception as e:
    print(f"[Test 3] [X] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 4: Using SetGrammar() method instead of constructor")
print("=" * 70)
try:
    print("[Test 4] Creating recognizer without grammar first...")
    recognizer = KaldiRecognizer(model, sample_rate)
    print("[Test 4] [OK] Base recognizer created")

    print("[Test 4] Calling SetGrammar() method...")
    grammar_dict = {"grammar": wake_words}
    grammar_json = json.dumps(grammar_dict)

    if hasattr(recognizer, 'SetGrammar'):
        recognizer.SetGrammar(grammar_json)
        print("[Test 4] [OK] Grammar set using SetGrammar() method")
    else:
        print("[Test 4] [X] SetGrammar() method not available")

    del recognizer
except Exception as e:
    print(f"[Test 4] [X] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 5: JSGF grammar format (more standard)")
print("=" * 70)
try:
    print("[Test 5] Creating JSGF-style grammar...")
    # JSGF format: #JSGF V1.0; grammar commands; public <command> = word1 | word2;
    jsgf_grammar = """
    #JSGF V1.0;
    grammar wake;
    public <wake> = hello gemma | hey gemma | hi gemma | gemma;
    """
    print(f"[Test 5] JSGF Grammar:\n{jsgf_grammar}")

    print("[Test 5] Creating KaldiRecognizer with JSGF...")
    recognizer = KaldiRecognizer(model, sample_rate, jsgf_grammar.strip())
    print("[Test 5] [OK] Recognizer created with JSGF format")
    del recognizer
except Exception as e:
    print(f"[Test 5] [X] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 6: Check Vosk version and capabilities")
print("=" * 70)
try:
    import vosk
    print(f"[Test 6] Vosk version: {vosk.__version__ if hasattr(vosk, '__version__') else 'unknown'}")
    print(f"[Test 6] Vosk location: {vosk.__file__}")

    # Check KaldiRecognizer signature
    import inspect
    sig = inspect.signature(KaldiRecognizer.__init__)
    print(f"[Test 6] KaldiRecognizer.__init__ signature: {sig}")

except Exception as e:
    print(f"[Test 6] [X] Failed: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("If Test 1 passes but Test 2 hangs, the issue is with grammar JSON format.")
print("If Test 3 or 4 works, we should use that approach instead.")
print("If Test 5 works, we need to use JSGF format instead of JSON.")
print("=" * 70)
