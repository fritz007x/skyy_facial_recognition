"""
Microphone Test Script

Tests microphone access and recording functionality.
Used to verify audio input before running voice assistant.

Requirements:
- sounddevice
- soundfile
- numpy
"""

import sys
import tempfile
from pathlib import Path

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}")
    print("\nInstall with:")
    print("  pip install sounddevice soundfile numpy")
    sys.exit(1)


def list_audio_devices():
    """List all available audio input devices."""
    print("\n" + "=" * 70)
    print("AVAILABLE AUDIO DEVICES")
    print("=" * 70)

    try:
        devices = sd.query_devices()

        print(f"\nFound {len(devices)} audio device(s):\n")

        for idx, device in enumerate(devices):
            device_type = []
            if device['max_input_channels'] > 0:
                device_type.append("INPUT")
            if device['max_output_channels'] > 0:
                device_type.append("OUTPUT")

            type_str = "/".join(device_type) if device_type else "NONE"

            print(f"[{idx}] {device['name']}")
            print(f"    Type: {type_str}")
            print(f"    Input Channels: {device['max_input_channels']}")
            print(f"    Output Channels: {device['max_output_channels']}")
            print(f"    Default Sample Rate: {device['default_samplerate']} Hz")
            print()

        # Show default devices
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')

        print(f"Default INPUT device: {default_input['name']}")
        print(f"Default OUTPUT device: {default_output['name']}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to query audio devices: {e}")
        return False


def test_microphone_recording(duration: float = 3.0, sample_rate: int = 16000):
    """
    Test microphone by recording audio and saving to file.

    Args:
        duration: Recording duration in seconds
        sample_rate: Sample rate in Hz (16000 for speech)

    Returns:
        True if recording successful, False otherwise
    """
    print("\n" + "=" * 70)
    print("MICROPHONE RECORDING TEST")
    print("=" * 70)

    print(f"\nRecording for {duration} seconds at {sample_rate} Hz...")
    print("Please speak into your microphone NOW!\n")

    try:
        # Record audio
        print("[Recording] Speak now...")
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,  # Mono
            dtype='float32'
        )
        sd.wait()  # Wait for recording to complete
        print("[Recording] Complete!\n")

        # Check if audio was captured
        max_amplitude = np.max(np.abs(audio_data))
        print(f"Audio Statistics:")
        print(f"  Duration: {duration}s")
        print(f"  Sample Rate: {sample_rate} Hz")
        print(f"  Samples: {len(audio_data)}")
        print(f"  Max Amplitude: {max_amplitude:.4f}")

        if max_amplitude < 0.001:
            print("\n[WARNING] Very low audio level detected!")
            print("Possible issues:")
            print("  - Microphone not connected")
            print("  - Microphone muted")
            print("  - Wrong input device selected")
            print("  - Microphone too far away")
            return False

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = Path(temp_file.name)

        sf.write(str(temp_path), audio_data, sample_rate)

        file_size = temp_path.stat().st_size
        print(f"\nAudio saved to: {temp_path}")
        print(f"File size: {file_size} bytes")

        # Cleanup
        try:
            temp_path.unlink()
            print("Temporary file cleaned up")
        except:
            pass

        print("\n[OK] Microphone is working correctly!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Recording failed: {e}")
        print("\nPossible issues:")
        print("  - Microphone not connected")
        print("  - Microphone permissions denied")
        print("  - Audio driver issues")
        return False


def test_microphone_permissions():
    """Test if microphone permissions are granted."""
    print("\n" + "=" * 70)
    print("MICROPHONE PERMISSIONS TEST")
    print("=" * 70)

    try:
        # Try to access default input device
        default_input = sd.query_devices(kind='input')

        if default_input['max_input_channels'] == 0:
            print("\n[ERROR] No input channels available on default device")
            print("The default device may not be an input device.")
            return False

        print(f"\n[OK] Default input device accessible:")
        print(f"     {default_input['name']}")
        print(f"     Channels: {default_input['max_input_channels']}")
        return True

    except Exception as e:
        print(f"\n[ERROR] Cannot access microphone: {e}")
        print("\nOn Windows, check:")
        print("  Settings > Privacy > Microphone")
        print("  Ensure 'Allow apps to access your microphone' is ON")
        return False


def main():
    """Run all microphone tests."""
    print("\n" + "=" * 70)
    print("         MICROPHONE TEST SUITE")
    print("         For Gemma Voice Assistant")
    print("=" * 70)

    results = {}

    # Test 1: List devices
    print("\n\n### TEST 1: Audio Device Detection ###")
    results['device_detection'] = list_audio_devices()

    # Test 2: Permissions
    print("\n\n### TEST 2: Microphone Permissions ###")
    results['permissions'] = test_microphone_permissions()

    # Test 3: Recording (only if permissions OK)
    if results['permissions']:
        print("\n\n### TEST 3: Microphone Recording ###")
        results['recording'] = test_microphone_recording(duration=3.0)
    else:
        print("\n\n### TEST 3: Microphone Recording ###")
        print("[SKIPPED] Permissions test failed")
        results['recording'] = False

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    print("\nDetailed Results:")
    for test_name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {test_name.replace('_', ' ').title()}")

    print("\n" + "=" * 70)

    if failed == 0:
        print("All tests passed! Your microphone is ready for voice assistant.")
    else:
        print(f"Warning: {failed} test(s) failed.")
        print("\nTroubleshooting:")
        print("  1. Check microphone is connected")
        print("  2. Check Windows microphone permissions")
        print("  3. Close other apps using microphone")
        print("  4. Try different microphone/USB port")
        print("  5. Update audio drivers")

    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
