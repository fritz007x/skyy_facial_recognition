"""
Test suite for SpeechOrchestrator and component-based architecture.

Tests each component in isolation and integration with the orchestrator.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import components
from modules.audio_input_device import AudioInputDevice
from modules.transcription_engine import TranscriptionEngine
from modules.silence_detector import SilenceDetector
from modules.wake_word_detector import WakeWordDetector
from modules.text_to_speech_engine import TextToSpeechEngine
from modules.speech_orchestrator import SpeechOrchestrator


class TestAudioInputDevice(unittest.TestCase):
    """Test AudioInputDevice component."""

    @patch('modules.audio_input_device.sd.query_devices')
    def test_initialization_success(self, mock_query):
        """Test successful initialization."""
        mock_query.return_value = {'name': 'Test Microphone'}
        device = AudioInputDevice()
        self.assertEqual(device.sample_rate, 16000)
        self.assertEqual(device.channels, 1)

    @patch('modules.audio_input_device.sd.query_devices')
    def test_initialization_no_device(self, mock_query):
        """Test initialization with no audio device."""
        mock_query.return_value = None
        with self.assertRaises(RuntimeError):
            AudioInputDevice()

    @patch('modules.audio_input_device.sd.rec')
    @patch('modules.audio_input_device.sd.wait')
    @patch('modules.audio_input_device.sd.query_devices')
    def test_record_audio(self, mock_query, mock_wait, mock_rec):
        """Test audio recording."""
        mock_query.return_value = {'name': 'Test Microphone'}
        mock_rec.return_value = np.zeros((16000, 1), dtype=np.int16)

        device = AudioInputDevice()
        audio = device.record(duration=1.0)

        self.assertIsNotNone(audio)
        mock_rec.assert_called_once()
        mock_wait.assert_called_once()

    @patch('modules.audio_input_device.sd.query_devices')
    def test_get_energy(self, mock_query):
        """Test energy calculation."""
        mock_query.return_value = {'name': 'Test Microphone'}
        device = AudioInputDevice()

        # Silent audio
        silent = np.zeros((1000,), dtype=np.int16)
        self.assertEqual(device.get_energy(silent), 0.0)

        # Loud audio
        loud = np.full((1000,), 1000, dtype=np.int16)
        self.assertEqual(device.get_energy(loud), 1000.0)


class TestTranscriptionEngine(unittest.TestCase):
    """Test TranscriptionEngine component."""

    @patch('modules.transcription_engine.WhisperModel')
    def test_initialization(self, mock_whisper):
        """Test engine initialization."""
        engine = TranscriptionEngine(model_size="base")
        self.assertEqual(engine.model_size, "base")
        mock_whisper.assert_called_once()

    @patch('modules.transcription_engine.WhisperModel')
    def test_validate_audio_empty(self, mock_whisper):
        """Test validation with empty audio."""
        engine = TranscriptionEngine()
        is_valid, msg = engine.validate_audio(np.array([]))
        self.assertFalse(is_valid)
        self.assertIn("Empty", msg)

    @patch('modules.transcription_engine.WhisperModel')
    def test_validate_audio_invalid_values(self, mock_whisper):
        """Test validation with NaN/Inf."""
        engine = TranscriptionEngine()
        invalid = np.array([1.0, np.nan, 2.0])
        is_valid, msg = engine.validate_audio(invalid)
        self.assertFalse(is_valid)
        self.assertIn("invalid", msg)

    @patch('modules.transcription_engine.WhisperModel')
    def test_validate_audio_too_short(self, mock_whisper):
        """Test validation with too-short audio."""
        engine = TranscriptionEngine(sample_rate=16000)
        short = np.zeros(100)  # Less than 0.1s at 16kHz
        is_valid, msg = engine.validate_audio(short)
        self.assertFalse(is_valid)
        self.assertIn("too short", msg)

    @patch('modules.transcription_engine.WhisperModel')
    def test_validate_audio_valid(self, mock_whisper):
        """Test validation with valid audio."""
        engine = TranscriptionEngine(sample_rate=16000)
        valid = np.zeros(16000)  # 1 second of audio
        is_valid, msg = engine.validate_audio(valid)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")


class TestSilenceDetector(unittest.TestCase):
    """Test SilenceDetector component."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = SilenceDetector(threshold=100)
        self.assertEqual(detector.get_threshold(), 100)

    def test_is_silence_below_threshold(self):
        """Test silence detection below threshold."""
        detector = SilenceDetector(threshold=100)
        self.assertTrue(detector.is_silence(50))

    def test_is_silence_above_threshold(self):
        """Test silence detection above threshold."""
        detector = SilenceDetector(threshold=100)
        self.assertFalse(detector.is_silence(150))

    def test_is_silence_at_threshold(self):
        """Test silence detection at threshold."""
        detector = SilenceDetector(threshold=100)
        self.assertTrue(detector.is_silence(100))

    def test_set_threshold(self):
        """Test threshold update."""
        detector = SilenceDetector(threshold=100)
        detector.set_threshold(200)
        self.assertEqual(detector.get_threshold(), 200)


class TestWakeWordDetector(unittest.TestCase):
    """Test WakeWordDetector component."""

    def test_contains_wake_word_found(self):
        """Test wake word detection - found."""
        detector = WakeWordDetector()
        text = "Hello Gemma, how are you?"
        wake_words = ["hello gemma", "hey gemma"]
        self.assertTrue(detector.contains_wake_word(text, wake_words))

    def test_contains_wake_word_not_found(self):
        """Test wake word detection - not found."""
        detector = WakeWordDetector()
        text = "Just talking here"
        wake_words = ["hello gemma", "hey gemma"]
        self.assertFalse(detector.contains_wake_word(text, wake_words))

    def test_contains_wake_word_case_insensitive(self):
        """Test case-insensitive wake word detection."""
        detector = WakeWordDetector()
        text = "HELLO GEMMA"
        wake_words = ["hello gemma"]
        self.assertTrue(detector.contains_wake_word(text, wake_words))

    def test_find_wake_word(self):
        """Test finding specific wake word."""
        detector = WakeWordDetector()
        text = "Hey Gemma, what's up?"
        wake_words = ["hello gemma", "hey gemma"]
        found = detector.find_wake_word(text, wake_words)
        self.assertEqual(found, "hey gemma")

    def test_find_wake_word_not_found(self):
        """Test finding wake word when none present."""
        detector = WakeWordDetector()
        text = "Nothing here"
        wake_words = ["hello gemma"]
        found = detector.find_wake_word(text, wake_words)
        self.assertEqual(found, "")


class TestTextToSpeechEngine(unittest.TestCase):
    """Test TextToSpeechEngine component."""

    @patch('modules.text_to_speech_engine.pyttsx3.init')
    def test_initialization(self, mock_init):
        """Test TTS engine initialization."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine

        tts = TextToSpeechEngine(rate=150, volume=0.8)

        mock_init.assert_called_once()
        mock_engine.setProperty.assert_any_call('rate', 150)
        mock_engine.setProperty.assert_any_call('volume', 0.8)

    @patch('modules.text_to_speech_engine.pyttsx3.init')
    def test_speak(self, mock_init):
        """Test speaking text."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine

        tts = TextToSpeechEngine()
        tts.speak("Hello world")

        mock_engine.say.assert_called_once_with("Hello world")
        mock_engine.runAndWait.assert_called_once()

    @patch('modules.text_to_speech_engine.pyttsx3.init')
    def test_speak_empty(self, mock_init):
        """Test speaking empty text (should do nothing)."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine

        tts = TextToSpeechEngine()
        tts.speak("")

        mock_engine.say.assert_not_called()


class TestSpeechOrchestrator(unittest.TestCase):
    """Test SpeechOrchestrator integration."""

    @patch('modules.speech_orchestrator.TextToSpeechEngine')
    @patch('modules.speech_orchestrator.TranscriptionEngine')
    @patch('modules.speech_orchestrator.AudioInputDevice')
    def test_initialization(self, mock_audio, mock_transcription, mock_tts):
        """Test orchestrator initialization."""
        orchestrator = SpeechOrchestrator()

        # Verify all components were initialized
        mock_audio.assert_called_once()
        mock_transcription.assert_called_once()
        mock_tts.assert_called_once()

    @patch('modules.speech_orchestrator.TextToSpeechEngine')
    @patch('modules.speech_orchestrator.TranscriptionEngine')
    @patch('modules.speech_orchestrator.AudioInputDevice')
    def test_speak(self, mock_audio, mock_transcription, mock_tts):
        """Test speak method."""
        mock_tts_instance = Mock()
        mock_tts.return_value = mock_tts_instance

        orchestrator = SpeechOrchestrator()
        orchestrator.speak("Hello")

        mock_tts_instance.speak.assert_called_once_with("Hello")

    @patch('modules.speech_orchestrator.TextToSpeechEngine')
    @patch('modules.speech_orchestrator.TranscriptionEngine')
    @patch('modules.speech_orchestrator.AudioInputDevice')
    def test_cleanup(self, mock_audio, mock_transcription, mock_tts):
        """Test cleanup method."""
        mock_trans_instance = Mock()
        mock_tts_instance = Mock()
        mock_transcription.return_value = mock_trans_instance
        mock_tts.return_value = mock_tts_instance

        orchestrator = SpeechOrchestrator()
        orchestrator.cleanup()

        mock_trans_instance.cleanup.assert_called_once()
        mock_tts_instance.cleanup.assert_called_once()


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("SPEECH ORCHESTRATOR COMPONENT TESTS")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAudioInputDevice))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptionEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSilenceDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestWakeWordDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestTextToSpeechEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSpeechOrchestrator))

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
