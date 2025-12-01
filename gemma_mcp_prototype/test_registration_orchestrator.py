import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

# Mock dependencies that might not be installed
sys.modules['sounddevice'] = MagicMock()
sys.modules['webrtcvad'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['ollama'] = MagicMock()
sys.modules['vosk'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['insightface'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
sys.modules['pyttsx3'] = MagicMock()
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.client'] = MagicMock()
sys.modules['mcp.client.stdio'] = MagicMock()
sys.modules['numpy'] = MagicMock() # Mock numpy if needed, but it's usually present. Actually, numpy is used in the test, so don't mock it if it's installed. But if it's not... wait, numpy is standard. Let's assume numpy is there. If not, I'll mock it too.
# Actually, let's not mock numpy unless it fails, as the test uses it implicitly via the code.
# But wait, the test code itself doesn't use numpy directly, but the modules do.
# If numpy is missing, I should mock it. But usually it's there.
# Let's stick to the external libs.

from modules.registration_orchestrator import RegistrationOrchestrator, RegistrationState

class TestRegistrationOrchestrator(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_tts = MagicMock()
        self.orchestrator = RegistrationOrchestrator(
            tts_speak_func=self.mock_tts,
            whisper_model="base",
            whisper_device="cpu",
            whisper_compute_type="float32",
            max_retries=3
        )
        
        # Mock internal components to avoid actual initialization
        self.orchestrator.vad = MagicMock()
        self.orchestrator.whisper = MagicMock()

    def test_initialization(self):
        """Test initial state of the orchestrator."""
        self.assertEqual(self.orchestrator.state, RegistrationState.IDLE)
        self.assertEqual(self.orchestrator.max_retries, 3)

    def test_looks_like_full_name(self):
        """Test the heuristic check for full names."""
        # Valid names
        self.assertTrue(self.orchestrator._looks_like_full_name("John Doe"))
        self.assertTrue(self.orchestrator._looks_like_full_name("Mary Jane Smith"))
        
        # Invalid names
        self.assertFalse(self.orchestrator._looks_like_full_name("John"))  # Single word
        self.assertFalse(self.orchestrator._looks_like_full_name(""))      # Empty
        self.assertFalse(self.orchestrator._looks_like_full_name(None))    # None
        
        # Word length check (too long)
        long_word = "A" * 41
        self.assertFalse(self.orchestrator._looks_like_full_name(f"John {long_word}"))

    def test_extract_confirmation(self):
        """Test extraction of yes/no confirmation."""
        # Positive
        self.assertTrue(self.orchestrator._extract_confirmation("Yes"))
        self.assertTrue(self.orchestrator._extract_confirmation("yeah sure"))
        self.assertTrue(self.orchestrator._extract_confirmation("that is correct"))
        
        # Negative
        self.assertFalse(self.orchestrator._extract_confirmation("No"))
        self.assertFalse(self.orchestrator._extract_confirmation("nope"))
        self.assertFalse(self.orchestrator._extract_confirmation("that is wrong"))
        
        # Unclear
        self.assertIsNone(self.orchestrator._extract_confirmation("maybe"))
        self.assertIsNone(self.orchestrator._extract_confirmation("what?"))

    def test_capture_and_confirm_name_success(self):
        """Test successful name capture flow."""
        # Setup mocks
        self.orchestrator.vad.record_speech.side_effect = [
            (True, b'audio_name'),      # Name recording
            (True, b'audio_confirm')    # Confirmation recording
        ]
        
        self.orchestrator.whisper.transcribe.side_effect = [
            "John Doe",     # Name transcription
            "Yes correct"   # Confirmation transcription
        ]
        
        # Run
        name = self.orchestrator.capture_and_confirm_name()
        
        # Verify
        self.assertEqual(name, "John Doe")
        self.assertEqual(self.orchestrator.state, RegistrationState.COMPLETED)
        
        # Verify calls
        self.assertEqual(self.orchestrator.vad.record_speech.call_count, 2)
        self.assertEqual(self.orchestrator.whisper.transcribe.call_count, 2)
        self.mock_tts.assert_any_call("Please say your full name after the beep.")
        self.mock_tts.assert_any_call("I heard John Doe. Is that correct? Say yes to confirm or no to try again.")

    def test_capture_and_confirm_name_retry(self):
        """Test name capture with one retry (user says no)."""
        # Setup mocks
        self.orchestrator.vad.record_speech.side_effect = [
            (True, b'audio_wrong'),     # 1st name
            (True, b'audio_no'),        # 1st confirmation (no)
            (True, b'audio_right'),     # 2nd name
            (True, b'audio_yes')        # 2nd confirmation (yes)
        ]
        
        self.orchestrator.whisper.transcribe.side_effect = [
            "Wrong Name",   # 1st name
            "No",           # 1st confirmation
            "Right Name",   # 2nd name
            "Yes"           # 2nd confirmation
        ]
        
        # Run
        name = self.orchestrator.capture_and_confirm_name()
        
        # Verify
        self.assertEqual(name, "Right Name")
        self.assertEqual(self.orchestrator.state, RegistrationState.COMPLETED)
        self.mock_tts.assert_any_call("Okay, let's try again.")

    def test_capture_and_confirm_name_failure(self):
        """Test name capture failure after max retries."""
        # Setup mocks to always fail validation or confirmation
        self.orchestrator.vad.record_speech.return_value = (True, b'audio')
        self.orchestrator.whisper.transcribe.return_value = "InvalidName" # Single word -> invalid
        
        # Run
        name = self.orchestrator.capture_and_confirm_name()
        
        # Verify
        self.assertIsNone(name)
        self.assertEqual(self.orchestrator.state, RegistrationState.FAILED)
        self.mock_tts.assert_any_call("I'm having trouble capturing your name. Please try the registration again later.")

    def test_run_registration_flow_success(self):
        """Test the full registration flow integration."""
        # Mock external managers
        mock_perm = MagicMock()
        mock_cam = MagicMock()
        mock_mcp = MagicMock()
        
        # Setup success path
        mock_perm.request_camera_permission.return_value = True
        mock_cam.initialize.return_value = True
        mock_cam.capture_to_base64.return_value = (True, "base64_image")
        mock_mcp.register_user.return_value = {"status": "success", "user": {"id": "123"}}
        
        # Mock internal capture_and_confirm_name
        with patch.object(self.orchestrator, 'capture_and_confirm_name', return_value="John Doe"):
            success, name = self.orchestrator.run_registration_flow(
                mock_perm, mock_cam, mock_mcp, "token"
            )
            
            self.assertTrue(success)
            self.assertEqual(name, "John Doe")
            self.assertEqual(self.orchestrator.state, RegistrationState.COMPLETED)
            
            # Verify flow steps
            mock_perm.request_camera_permission.assert_called_once()
            mock_cam.initialize.assert_called_once()
            mock_cam.capture_to_base64.assert_called_once()
            mock_mcp.register_user.assert_called_once_with(
                access_token="token",
                name="John Doe",
                image_data="base64_image",
                metadata={"registration_type": "voice"}
            )
            mock_cam.release.assert_called()

    def test_run_registration_flow_camera_denied(self):
        """Test registration flow when camera permission is denied."""
        mock_perm = MagicMock()
        mock_cam = MagicMock()
        mock_mcp = MagicMock()
        
        mock_perm.request_camera_permission.return_value = False
        
        with patch.object(self.orchestrator, 'capture_and_confirm_name', return_value="John Doe"):
            success, name = self.orchestrator.run_registration_flow(
                mock_perm, mock_cam, mock_mcp, "token"
            )
            
            self.assertFalse(success)
            self.assertIsNone(name)
            self.assertEqual(self.orchestrator.state, RegistrationState.FAILED)
            self.mock_tts.assert_any_call("Camera permission denied. Registration cancelled.")

if __name__ == '__main__':
    unittest.main()
