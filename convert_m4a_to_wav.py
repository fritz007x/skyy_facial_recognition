"""
Convert M4A to WAV for Whisper Processing

Simple converter using pydub to convert M4A audio to WAV format.
"""

import sys
from pathlib import Path

try:
    from pydub import AudioSegment
except ImportError:
    print("ERROR: pydub not installed")
    print("Install with: pip install pydub")
    sys.exit(1)


def convert_m4a_to_wav(input_path: Path, output_path: Path = None) -> Path:
    """
    Convert M4A file to WAV format.

    Args:
        input_path: Path to M4A file
        output_path: Optional output path (defaults to input name with .wav)

    Returns:
        Path to output WAV file
    """
    if output_path is None:
        output_path = input_path.with_suffix('.wav')

    print(f"[Converter] Input: {input_path}")
    print(f"[Converter] Output: {output_path}")

    try:
        # Load M4A file
        print("[Converter] Loading M4A audio...")
        audio = AudioSegment.from_file(str(input_path), format="m4a")

        # Export as WAV
        print("[Converter] Converting to WAV...")
        audio.export(
            str(output_path),
            format="wav",
            parameters=["-ar", "16000", "-ac", "1"]  # 16kHz mono
        )

        file_size = output_path.stat().st_size
        print(f"[Converter] Conversion complete!")
        print(f"[Converter] Output size: {file_size:,} bytes")

        return output_path

    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("\nUsage: python convert_m4a_to_wav.py <input.m4a> [output.wav]")
        print("\nExample:")
        print("  python convert_m4a_to_wav.py 'Voice Recording.m4a'")
        print("  python convert_m4a_to_wav.py input.m4a output.wav")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not input_file.exists():
        print(f"[ERROR] Input file not found: {input_file}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("M4A TO WAV CONVERTER")
    print("=" * 70 + "\n")

    output_path = convert_m4a_to_wav(input_file, output_file)

    print("\n" + "=" * 70)
    print(f"[SUCCESS] WAV file created: {output_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
