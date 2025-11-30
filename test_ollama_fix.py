"""Test script for Ollama model listing fix."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    # Test just the Ollama check part
    import ollama

    print("[Test] Testing Ollama connection...")
    response = ollama.list()

    print(f"[Test] Response type: {type(response)}")
    print(f"[Test] Has 'models' attribute: {hasattr(response, 'models')}")

    if hasattr(response, 'models'):
        model_names = [model.model for model in response.models]
        print(f"[Test] Found {len(model_names)} models: {', '.join(model_names)}")

        gemma_models = [m for m in model_names if 'gemma' in m.lower() and '3' in m]
        print(f"[Test] Found {len(gemma_models)} Gemma 3 models: {', '.join(gemma_models)}")

        if gemma_models:
            print(f"[Test] Would use model: {gemma_models[0]}")
            print("\n[SUCCESS] Ollama model listing works correctly!")
        else:
            print("\n[WARNING] No Gemma 3 models found, but listing works!")
    else:
        print("[ERROR] Response doesn't have 'models' attribute")

except Exception as e:
    print(f"[ERROR] Failed: {e}")
    print(f"[ERROR] Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
