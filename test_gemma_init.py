"""Test script for Gemma3nVoiceAssistant initialization."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    print("[Test] Importing Gemma3nVoiceAssistant...")
    from gemma3n_voice_assistant import Gemma3nVoiceAssistant

    print("[Test] Creating assistant instance (will check Ollama)...")
    assistant = Gemma3nVoiceAssistant()

    print(f"\n[SUCCESS] Assistant initialized successfully!")
    print(f"[Test] Selected model: {assistant.gemma_model}")

except SystemExit as e:
    print(f"\n[EXPECTED EXIT] SystemExit with code: {e.code}")
    print("This is expected if Ollama is not running or Gemma 3n is not installed")

except Exception as e:
    print(f"\n[ERROR] Failed to initialize assistant: {e}")
    print(f"[ERROR] Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
