"""
Pre-Recorded Wake Word Test

Tests Whisper speech recognition using a pre-recorded "Hello Gemma" audio file
instead of generating it with TTS.

Usage:
    python test_prerecorded_wake_word.py <path_to_audio_file>

Example:
    python test_prerecorded_wake_word.py hello_gemma.wav
    python test_prerecorded_wake_word.py audio/hello_gemma.mp3

Requirements:
- whisper
- soundfile
- numpy
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

try:
    import whisper
except ImportError:
    print("ERROR: whisper not installed")
    print("Install with: pip install openai-whisper")
    sys.exit(1)

try:
    import soundfile as sf
    import numpy as np
except ImportError:
    print("ERROR: soundfile or numpy not installed")
    print("Install with: pip install soundfile numpy")
    sys.exit(1)


class PreRecordedWakeWordTester:
    """Test wake word detection using pre-recorded audio."""

    def __init__(self, audio_file: Path):
        """
        Initialize tester with audio file.

        Args:
            audio_file: Path to pre-recorded "Hello Gemma" audio
        """
        self.audio_file = audio_file
        self.sample_rate = 16000  # Target sample rate for Whisper

        # Load Whisper model
        print("\n[System] Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("[System] Whisper model loaded\n")

    def verify_audio_file(self) -> bool:
        """
        Verify the audio file exists and is readable.

        Returns:
            True if file is valid, False otherwise
        """
        print(f"[Test] Verifying audio file: {self.audio_file}")

        if not self.audio_file.exists():
            print(f"[ERROR] File not found: {self.audio_file}")
            return False

        if not self.audio_file.is_file():
            print(f"[ERROR] Not a file: {self.audio_file}")
            return False

        # Check file extension
        valid_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        if self.audio_file.suffix.lower() not in valid_extensions:
            print(f"[WARNING] Unexpected file extension: {self.audio_file.suffix}")
            print(f"[WARNING] Valid extensions: {', '.join(valid_extensions)}")
            print("[WARNING] Attempting to load anyway...")

        # Check file size
        file_size = self.audio_file.stat().st_size
        print(f"[Test] File size: {file_size:,} bytes")

        if file_size == 0:
            print("[ERROR] File is empty")
            return False

        if file_size > 10 * 1024 * 1024:  # 10MB
            print("[WARNING] File is very large (>10MB)")
            print("[WARNING] Wake word audio should typically be 1-3 seconds")

        print("[OK] Audio file verified\n")
        return True

    def analyze_audio(self) -> Optional[dict]:
        """
        Analyze the audio file properties.

        Returns:
            Dictionary with audio properties or None if failed
        """
        print("[Test] Analyzing audio properties...")

        try:
            # Load audio file
            audio_data, sample_rate = sf.read(str(self.audio_file))

            # Get audio properties
            duration = len(audio_data) / sample_rate
            channels = 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
            max_amplitude = np.max(np.abs(audio_data))
            rms = np.sqrt(np.mean(audio_data ** 2))

            properties = {
                'sample_rate': sample_rate,
                'duration': duration,
                'channels': channels,
                'samples': len(audio_data),
                'max_amplitude': max_amplitude,
                'rms': rms
            }

            # Display properties
            print(f"[Audio] Sample Rate: {sample_rate} Hz")
            print(f"[Audio] Duration: {duration:.2f} seconds")
            print(f"[Audio] Channels: {channels} ({'mono' if channels == 1 else 'stereo'})")
            print(f"[Audio] Samples: {len(audio_data):,}")
            print(f"[Audio] Max Amplitude: {max_amplitude:.4f}")
            print(f"[Audio] RMS Level: {rms:.4f}")

            # Warnings
            if duration < 0.5:
                print("[WARNING] Audio is very short (<0.5s)")
            elif duration > 5:
                print("[WARNING] Audio is long (>5s) - wake words should be brief")

            if max_amplitude < 0.01:
                print("[WARNING] Audio level is very low")
                print("[WARNING] May affect recognition accuracy")

            if sample_rate < 8000:
                print("[WARNING] Sample rate is low (<8kHz)")
                print("[WARNING] May affect recognition accuracy")

            print("[OK] Audio analysis complete\n")
            return properties

        except Exception as e:
            # soundfile doesn't support M4A/MP3 - that's OK, Whisper can handle it
            if self.audio_file.suffix.lower() in ['.m4a', '.mp3', '.aac']:
                print(f"[INFO] Skipping detailed audio analysis for {self.audio_file.suffix} format")
                print("[INFO] Whisper will process this format directly using ffmpeg")
                print("[OK] Format supported by Whisper\n")
                return {'format': self.audio_file.suffix, 'note': 'Analyzed by Whisper'}
            else:
                print(f"[ERROR] Failed to analyze audio: {e}")
                print(f"[WARNING] File format may not be supported")
                return None

    def test_whisper_transcription(self, expected_phrases: list = None) -> bool:
        """
        Test Whisper transcription of the audio file.

        Args:
            expected_phrases: List of expected phrases to check for

        Returns:
            True if transcription matches expected phrases
        """
        if expected_phrases is None:
            expected_phrases = ["hello gemma", "hey gemma", "hi gemma"]

        print("[Test] Testing Whisper transcription...")
        print(f"[Test] Expected phrases: {expected_phrases}\n")

        try:
            # Transcribe using Whisper
            print("[Whisper] Transcribing audio...")
            result = self.whisper_model.transcribe(str(self.audio_file))

            transcription = result['text'].strip()
            transcription_lower = transcription.lower()

            print(f"[Whisper] Raw transcription: \"{transcription}\"")
            print(f"[Whisper] Confidence: {result.get('language_probability', 'N/A')}")
            print(f"[Whisper] Detected language: {result.get('language', 'N/A')}\n")

            # Check for expected phrases
            matches = []
            for phrase in expected_phrases:
                if phrase in transcription_lower:
                    matches.append(phrase)

            if matches:
                print(f"[OK] Wake word detected!")
                print(f"[OK] Matched phrases: {matches}")
                return True
            else:
                print(f"[FAIL] Wake word not detected")
                print(f"[FAIL] Expected one of: {expected_phrases}")
                print(f"[FAIL] Got: \"{transcription}\"")
                return False

        except Exception as e:
            print(f"[ERROR] Whisper transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_full_test(self) -> bool:
        """
        Run complete wake word detection test.

        Returns:
            True if all tests pass
        """
        print("\n" + "=" * 70)
        print("PRE-RECORDED WAKE WORD TEST")
        print("Using Whisper Speech Recognition")
        print("=" * 70)
        print(f"\nAudio File: {self.audio_file}")
        print("=" * 70)

        # Step 1: Verify file
        print("\n[Step 1/3] Verifying audio file...")
        if not self.verify_audio_file():
            return False

        # Step 2: Analyze audio (optional for some formats)
        print("[Step 2/3] Analyzing audio properties...")
        properties = self.analyze_audio()
        # Continue even if analysis is limited (e.g., for M4A files)

        # Step 3: Test transcription
        print("[Step 3/3] Testing wake word detection...")
        success = self.test_whisper_transcription()

        return success


def find_audio_file() -> Optional[Path]:
    """
    Try to find "Hello Gemma" audio file in common locations.

    Returns:
        Path to audio file or None if not found
    """
    common_names = [
        "hello_gemma.wav",
        "hello_gemma.mp3",
        "hello-gemma.wav",
        "hello-gemma.mp3",
        "HelloGemma.wav",
        "wake_word.wav",
        "gemma.wav"
    ]

    common_dirs = [
        Path("."),
        Path("audio"),
        Path("test_audio"),
        Path("src/audio"),
        Path("assets"),
        Path("resources")
    ]

    for directory in common_dirs:
        for filename in common_names:
            audio_file = directory / filename
            if audio_file.exists():
                return audio_file

    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test wake word detection using pre-recorded audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_prerecorded_wake_word.py hello_gemma.wav
  python test_prerecorded_wake_word.py audio/wake_word.mp3
  python test_prerecorded_wake_word.py  # Auto-detect audio file
        """
    )

    parser.add_argument(
        'audio_file',
        type=str,
        nargs='?',
        help='Path to pre-recorded "Hello Gemma" audio file'
    )

    args = parser.parse_args()

    # Determine audio file path
    if args.audio_file:
        audio_file = Path(args.audio_file)
    else:
        print("\n[System] No audio file specified, searching for audio file...")
        audio_file = find_audio_file()

        if audio_file is None:
            print("\n[ERROR] No audio file found")
            print("\nSearched for:")
            print("  - hello_gemma.wav/mp3")
            print("  - hello-gemma.wav/mp3")
            print("  - wake_word.wav")
            print("  In directories: ., audio/, test_audio/, src/audio/")
            print("\nPlease specify audio file path:")
            print("  python test_prerecorded_wake_word.py <path_to_audio>")
            return 1

        print(f"[System] Found audio file: {audio_file}\n")

    # Run test
    try:
        tester = PreRecordedWakeWordTester(audio_file)
        success = tester.run_full_test()

        # Print summary
        print("\n" + "=" * 70)
        print("TEST RESULT")
        print("=" * 70)

        if success:
            print("\n[SUCCESS] Wake word detection test passed!")
            print("The audio file correctly triggers 'Hello Gemma' detection.")
        else:
            print("\n[FAILURE] Wake word detection test failed!")
            print("The audio file did not match expected wake word phrases.")

        print("\n" + "=" * 70)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
