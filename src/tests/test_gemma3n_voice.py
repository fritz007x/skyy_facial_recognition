"""
Automated Test for Gemma 3n Voice Assistant

This test generates the wake word "Hello Gemma" using TTS and tests:
1. TTS generation of wake word
2. Gemma 3n speech recognition
3. Wake word detection
4. Full voice recognition workflow

Tests the complete pipeline without requiring manual voice input.
"""

import asyncio
import sys
import json
import base64
import tempfile
import wave
import struct
from pathlib import Path
from typing import Optional, Dict, Any
import time

# TTS for generating test audio
try:
    import pyttsx3
except ImportError:
    print("ERROR: pyttsx3 not installed")
    print("Install with: pip install pyttsx3")
    sys.exit(1)

# Audio processing
try:
    import soundfile as sf
    import numpy as np
except ImportError:
    print("ERROR: soundfile not installed")
    print("Install with: pip install soundfile numpy")
    sys.exit(1)

# Ollama for Gemma 3n
try:
    import ollama
except ImportError:
    print("ERROR: ollama not installed")
    print("Install with: pip install ollama")
    sys.exit(1)

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from oauth_config import OAuthConfig


class Gemma3nVoiceTester:
    """Automated tester for Gemma 3n voice assistant."""

    def __init__(self):
        """Initialize tester."""
        self.tts_engine = pyttsx3.init()
        self.sample_rate = 16000  # 16kHz for speech
        self.test_audio_path = None

        # Configure TTS for clear speech
        self._configure_tts()

    def _configure_tts(self):
        """Configure TTS for optimal test audio generation."""
        # Use default voice (usually clearest)
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Use first voice (usually Microsoft David or similar)
            self.tts_engine.setProperty('voice', voices[0].id)

        # Set speech rate (slightly slower for clarity)
        self.tts_engine.setProperty('rate', 150)

        # Set volume
        self.tts_engine.setProperty('volume', 1.0)

    def generate_wake_word_audio(self, text: str = "Hello Gemma") -> str:
        """
        Generate audio of wake word using TTS.

        Args:
            text: Text to convert to speech

        Returns:
            Path to generated WAV file
        """
        print(f"\n[Test] Generating TTS audio: \"{text}\"")

        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        # Generate speech and save to file
        self.tts_engine.save_to_file(text, temp_path)
        self.tts_engine.runAndWait()

        # Wait for file to be fully written
        time.sleep(0.5)

        # Verify file was created
        if not Path(temp_path).exists():
            raise FileNotFoundError(f"TTS failed to create audio file: {temp_path}")

        file_size = Path(temp_path).stat().st_size
        print(f"[Test] Generated audio file: {temp_path} ({file_size} bytes)")

        self.test_audio_path = temp_path
        return temp_path

    def convert_audio_to_16khz(self, input_path: str) -> str:
        """
        Convert audio to 16kHz mono WAV (Gemma 3n optimal format).

        Args:
            input_path: Path to input audio file

        Returns:
            Path to converted audio file
        """
        print(f"[Test] Converting audio to 16kHz mono...")

        # Read audio file
        audio_data, original_sr = sf.read(input_path)

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Resample to 16kHz if necessary
        if original_sr != self.sample_rate:
            # Simple resampling (for test purposes)
            import scipy.signal
            num_samples = int(len(audio_data) * self.sample_rate / original_sr)
            audio_data = scipy.signal.resample(audio_data, num_samples)

        # Save converted audio
        output_path = input_path.replace('.wav', '_16khz.wav')
        sf.write(output_path, audio_data, self.sample_rate)

        print(f"[Test] Converted audio: {output_path}")

        return output_path

    def test_gemma3n_transcription(self, audio_path: str, expected_text: str = "hello gemma") -> bool:
        """
        Test Gemma 3n speech recognition.

        Args:
            audio_path: Path to audio file
            expected_text: Expected transcription (lowercase)

        Returns:
            True if transcription matches expected text
        """
        print(f"\n[Test] Testing Gemma 3n transcription...")

        try:
            # Get available Gemma models
            response = ollama.list()
            model_names = [model.model for model in response.models]
            gemma_models = [m for m in model_names if 'gemma' in m.lower()]

            if not gemma_models:
                print("[ERROR] No Gemma models found")
                print("Install with: ollama pull gemma3n:2b-e2b")
                return False

            gemma_model = gemma_models[0]
            print(f"[Test] Using model: {gemma_model}")

            # Read audio file as bytes
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()

            # Transcribe using Gemma 3n
            print(f"[Test] Sending audio to Gemma 3n ({len(audio_bytes)} bytes)...")

            ollama_response = ollama.generate(
                model=gemma_model,
                prompt="Transcribe the following audio to text. Only output the transcribed text, nothing else:",
                images=[audio_bytes],
                stream=False
            )

            transcription = ollama_response['response'].strip().lower()
            print(f"[Test] Gemma 3n transcribed: \"{transcription}\"")

            # Check if expected text is in transcription
            success = expected_text in transcription

            if success:
                print(f"[OK] Transcription matches expected text!")
                return True
            else:
                print(f"[FAIL] Expected '{expected_text}' not found in transcription")
                print(f"[FAIL] Got: '{transcription}'")
                return False

        except Exception as e:
            print(f"[ERROR] Gemma 3n transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_wake_word_detection(self) -> bool:
        """
        Test complete wake word detection pipeline.

        Returns:
            True if wake word is detected successfully
        """
        print("\n" + "=" * 70)
        print("TEST: Wake Word Detection Pipeline")
        print("=" * 70)

        try:
            # Step 1: Generate wake word audio
            print("\n[Step 1/3] Generating wake word audio with TTS...")
            audio_path = self.generate_wake_word_audio("Hello Gemma")

            # Step 2: Convert to optimal format
            print("\n[Step 2/3] Converting audio to 16kHz mono...")
            converted_path = self.convert_audio_to_16khz(audio_path)

            # Step 3: Test Gemma 3n transcription
            print("\n[Step 3/3] Testing Gemma 3n transcription...")
            success = self.test_gemma3n_transcription(converted_path, "hello gemma")

            # Cleanup
            try:
                Path(audio_path).unlink()
                Path(converted_path).unlink()
            except:
                pass

            return success

        except Exception as e:
            print(f"\n[ERROR] Wake word detection test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_alternative_wake_phrases(self) -> Dict[str, bool]:
        """
        Test various wake phrase variations.

        Returns:
            Dictionary of phrase -> success
        """
        print("\n" + "=" * 70)
        print("TEST: Alternative Wake Phrase Variations")
        print("=" * 70)

        phrases = [
            ("Hello Gemma", "hello gemma"),
            ("Hey Gemma", "hey gemma"),
            ("Hi Gemma", "hi gemma"),
        ]

        results = {}

        for spoken_text, expected_text in phrases:
            print(f"\n[Testing] \"{spoken_text}\"")

            try:
                # Generate audio
                audio_path = self.generate_wake_word_audio(spoken_text)
                converted_path = self.convert_audio_to_16khz(audio_path)

                # Test transcription
                success = self.test_gemma3n_transcription(converted_path, expected_text)
                results[spoken_text] = success

                # Cleanup
                try:
                    Path(audio_path).unlink()
                    Path(converted_path).unlink()
                except:
                    pass

            except Exception as e:
                print(f"[ERROR] Failed to test '{spoken_text}': {e}")
                results[spoken_text] = False

        return results

    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        total = len(results)
        passed = sum(1 for v in results.values() if v)
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        print("\nDetailed Results:")
        for phrase, success in results.items():
            status = "[OK]" if success else "[FAIL]"
            print(f"  {status} {phrase}")

        print("\n" + "=" * 70)

        if failed == 0:
            print("All tests passed! Gemma 3n voice recognition is working correctly.")
        else:
            print(f"Warning: {failed} test(s) failed. Check Gemma 3n configuration.")

        print("=" * 70)


def main():
    """Run automated voice tests."""
    print("\n" + "=" * 70)
    print("         GEMMA 3N VOICE ASSISTANT - AUTOMATED TEST")
    print("=" * 70)
    print("\nThis test generates wake word audio using TTS and validates")
    print("Gemma 3n's speech recognition capabilities.")
    print("\n" + "=" * 70)

    # Create tester
    tester = Gemma3nVoiceTester()

    # Run tests
    all_results = {}

    # Test 1: Basic wake word detection
    print("\n\n### TEST 1: Basic Wake Word Detection ###")
    basic_success = tester.test_wake_word_detection()
    all_results["Basic Wake Word (Hello Gemma)"] = basic_success

    # Test 2: Alternative phrases
    print("\n\n### TEST 2: Alternative Wake Phrases ###")
    phrase_results = tester.test_alternative_wake_phrases()
    all_results.update(phrase_results)

    # Print summary
    tester.print_summary(all_results)

    # Return exit code
    all_passed = all(all_results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        # Check Ollama availability
        print("\n[System] Checking Ollama availability...")
        try:
            models = ollama.list()
            print("[OK] Ollama is running")
        except Exception as e:
            print(f"[ERROR] Ollama not available: {e}")
            print("\nMake sure:")
            print("  1. Ollama is installed (https://ollama.ai)")
            print("  2. Ollama service is running")
            print("  3. Gemma 3n is pulled: ollama pull gemma3n:2b-e2b")
            sys.exit(1)

        # Run tests
        exit_code = main()
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
