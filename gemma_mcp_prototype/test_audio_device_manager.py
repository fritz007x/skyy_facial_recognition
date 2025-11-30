"""
Test suite for AudioDeviceManager.

Tests state transitions and resource management.
"""

import unittest
import time
from modules.audio_device_manager import AudioDeviceManager, AudioDeviceState


class TestAudioDeviceManager(unittest.TestCase):
    """Test AudioDeviceManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = AudioDeviceManager(transition_delay=0.5)
        self.assertEqual(manager.get_state(), AudioDeviceState.IDLE)
        self.assertTrue(manager.is_idle())

    def test_acquire_for_recording(self):
        """Test acquiring device for recording."""
        manager = AudioDeviceManager(transition_delay=0.1)

        with manager.acquire_for_recording():
            self.assertEqual(manager.get_state(), AudioDeviceState.RECORDING)
            self.assertFalse(manager.is_idle())

        # After context, should be back to IDLE
        self.assertEqual(manager.get_state(), AudioDeviceState.IDLE)
        self.assertTrue(manager.is_idle())

    def test_acquire_for_playback(self):
        """Test acquiring device for playback."""
        manager = AudioDeviceManager(transition_delay=0.1)

        with manager.acquire_for_playback():
            self.assertEqual(manager.get_state(), AudioDeviceState.PLAYING)
            self.assertFalse(manager.is_idle())

        # After context, should be back to IDLE
        self.assertEqual(manager.get_state(), AudioDeviceState.IDLE)
        self.assertTrue(manager.is_idle())

    def test_transition_delay(self):
        """Test that transition delay is applied."""
        manager = AudioDeviceManager(transition_delay=0.2)

        # First acquisition
        with manager.acquire_for_recording():
            pass

        # Second acquisition - should have delay
        start = time.time()
        with manager.acquire_for_playback():
            pass
        elapsed = time.time() - start

        # Should have waited at least the transition delay
        self.assertGreaterEqual(elapsed, 0.15)  # Allow some tolerance

    def test_nested_acquisition_error(self):
        """Test that nested acquisition raises error."""
        manager = AudioDeviceManager(transition_delay=0.1)

        with manager.acquire_for_recording():
            with self.assertRaises(RuntimeError):
                with manager.acquire_for_playback():
                    pass

    def test_set_transition_delay(self):
        """Test updating transition delay."""
        manager = AudioDeviceManager(transition_delay=0.5)
        manager.set_transition_delay(1.0)
        self.assertEqual(manager._transition_delay, 1.0)

    def test_set_transition_delay_negative(self):
        """Test that negative delay raises error."""
        manager = AudioDeviceManager()
        with self.assertRaises(ValueError):
            manager.set_transition_delay(-0.5)

    def test_reset(self):
        """Test force reset."""
        manager = AudioDeviceManager(transition_delay=0.1)

        # Manually set to recording state
        manager._current_state = AudioDeviceState.RECORDING

        # Reset should force back to IDLE
        manager.reset()
        self.assertEqual(manager.get_state(), AudioDeviceState.IDLE)

    def test_sequential_operations(self):
        """Test sequential recording and playback operations."""
        manager = AudioDeviceManager(transition_delay=0.05)

        # Record
        with manager.acquire_for_recording():
            self.assertEqual(manager.get_state(), AudioDeviceState.RECORDING)

        # Play
        with manager.acquire_for_playback():
            self.assertEqual(manager.get_state(), AudioDeviceState.PLAYING)

        # Record again
        with manager.acquire_for_recording():
            self.assertEqual(manager.get_state(), AudioDeviceState.RECORDING)

        # Should be idle after all operations
        self.assertTrue(manager.is_idle())

    def test_exception_in_context_still_releases(self):
        """Test that resource is released even if exception occurs."""
        manager = AudioDeviceManager(transition_delay=0.1)

        try:
            with manager.acquire_for_recording():
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still be back to IDLE
        self.assertTrue(manager.is_idle())

    def test_multiple_managers_independent(self):
        """Test that multiple managers work independently."""
        manager1 = AudioDeviceManager(transition_delay=0.1)
        manager2 = AudioDeviceManager(transition_delay=0.1)

        with manager1.acquire_for_recording():
            self.assertEqual(manager1.get_state(), AudioDeviceState.RECORDING)
            self.assertEqual(manager2.get_state(), AudioDeviceState.IDLE)

            with manager2.acquire_for_playback():
                self.assertEqual(manager1.get_state(), AudioDeviceState.RECORDING)
                self.assertEqual(manager2.get_state(), AudioDeviceState.PLAYING)

        self.assertTrue(manager1.is_idle())
        self.assertTrue(manager2.is_idle())


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("AUDIO DEVICE MANAGER TESTS")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAudioDeviceManager)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
