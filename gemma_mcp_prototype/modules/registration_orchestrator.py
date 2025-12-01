"""
Registration Orchestrator - Voice-based user registration state machine.

Coordinates the complete voice registration flow:
1. Prompt for name
2. Record name with VAD
3. Transcribe with Whisper
4. Confirm with user
5. Request camera permission
6. Capture photo
7. Complete registration
"""

import time
from typing import Optional, Tuple
from enum import Enum

from .voice_activity_detector import VoiceActivityDetector
from .whisper_transcription_engine import WhisperTranscriptionEngine


class RegistrationState(Enum):
    """States in the registration flow."""
    IDLE = "idle"
    PROMPT_NAME = "prompt_name"
    RECORD_NAME = "record_name"
    TRANSCRIBE_NAME = "transcribe_name"
    CONFIRM_NAME = "confirm_name"
    RECORD_CONFIRMATION = "record_confirmation"
    TRANSCRIBE_CONFIRMATION = "transcribe_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"


class RegistrationOrchestrator:
    """
    Orchestrates voice-based user registration flow.

    Manages the complete state machine for capturing user name via voice,
    confirming it, and coordinating with camera capture for face enrollment.
    """

    def __init__(
        self,
        tts_speak_func,
        whisper_model: str = "base",
        whisper_device: str = "cpu",
        whisper_compute_type: str = "float32",
        max_retries: int = 3
    ):
        """
        Initialize Registration Orchestrator.

        Args:
            tts_speak_func: Function to call for text-to-speech (e.g., speech.speak)
            whisper_model: Whisper model size (tiny, base, small, medium)
            whisper_device: Device for Whisper inference (cpu, cuda)
            whisper_compute_type: Whisper compute type (float32, float16, int8)
            max_retries: Maximum retry attempts for name capture
        """
        self.tts_speak = tts_speak_func
        self.max_retries = max_retries

        # Initialize components
        self.vad = VoiceActivityDetector(
            sample_rate=16000,
            vad_mode=3,
            silence_duration_sec=1.0,
            min_speech_sec=0.4,
            timeout_sec=15.0
        )

        self.whisper = WhisperTranscriptionEngine(
            model_name=whisper_model,
            device=whisper_device,
            compute_type=whisper_compute_type
        )

        # State
        self.state = RegistrationState.IDLE

    def _looks_like_full_name(self, text: str) -> bool:
        """
        Heuristic check if text looks like a full name.

        Args:
            text: Transcribed text

        Returns:
            True if text looks like a valid full name
        """
        if not text or len(text.strip()) == 0:
            return False

        # Must have at least 2 words
        words = text.strip().split()
        if len(words) < 2:
            return False

        # Each word should be reasonable length (1-40 chars)
        if not all(1 <= len(w) <= 40 for w in words):
            return False

        return True

    def _extract_confirmation(self, text: str) -> Optional[bool]:
        """
        Extract yes/no confirmation from transcribed text.

        Args:
            text: Transcribed confirmation text

        Returns:
            True for yes, False for no, None if unclear
        """
        text_lower = text.lower().strip()

        # Positive responses
        if any(word in text_lower for word in ["yes", "yeah", "yep", "correct", "right", "sure"]):
            return True

        # Negative responses
        if any(word in text_lower for word in ["no", "nope", "wrong", "incorrect", "again"]):
            return False

        return None

    def capture_and_confirm_name(self) -> Optional[str]:
        """
        Capture user's full name with VAD and confirm with user.

        Implements the complete name capture flow:
        1. Prompt: "Please say your full name after the beep"
        2. Record name with VAD
        3. Transcribe with Whisper
        4. Confirm: "I heard {name}. Is that correct?"
        5. Record yes/no response
        6. Retry if needed

        Returns:
            Confirmed name string, or None if failed/cancelled
        """
        for attempt in range(self.max_retries):
            print(f"[Registration] Name capture attempt {attempt + 1}/{self.max_retries}", flush=True)

            # State: PROMPT_NAME
            self.state = RegistrationState.PROMPT_NAME
            self.tts_speak("Please say your full name after the beep.")
            time.sleep(0.25)

            # State: RECORD_NAME
            self.state = RegistrationState.RECORD_NAME
            success, audio = self.vad.record_speech(beep=True)

            if not success or audio is None:
                self.tts_speak("I didn't catch that. Please try again.")
                time.sleep(0.5)
                continue

            # State: TRANSCRIBE_NAME
            self.state = RegistrationState.TRANSCRIBE_NAME
            self.tts_speak("Processing your name now.")
            name_text = self.whisper.transcribe(audio, beam_size=5)

            print(f"[Registration] Transcribed name: '{name_text}'", flush=True)

            # Check if it looks like a full name
            if not self._looks_like_full_name(name_text):
                print("[Registration] Transcription doesn't look like a full name", flush=True)
                self.tts_speak("I couldn't capture your full name clearly. Please try again.")
                time.sleep(0.5)
                continue

            # State: CONFIRM_NAME
            self.state = RegistrationState.CONFIRM_NAME
            self.tts_speak(f"I heard {name_text}. Is that correct? Say yes to confirm or no to try again.")

            # State: RECORD_CONFIRMATION
            self.state = RegistrationState.RECORD_CONFIRMATION
            success, conf_audio = self.vad.record_speech(beep=False)

            if not success or conf_audio is None:
                self.tts_speak("No confirmation heard. Let's try again.")
                time.sleep(0.5)
                continue

            # State: TRANSCRIBE_CONFIRMATION
            self.state = RegistrationState.TRANSCRIBE_CONFIRMATION
            conf_text = self.whisper.transcribe(conf_audio, beam_size=5)
            print(f"[Registration] Confirmation transcription: '{conf_text}'", flush=True)

            # Extract confirmation
            confirmed = self._extract_confirmation(conf_text)

            if confirmed is True:
                # User confirmed the name
                print(f"[Registration] Name confirmed: '{name_text}'", flush=True)
                self.state = RegistrationState.COMPLETED
                return name_text
            elif confirmed is False:
                # User rejected - try again
                self.tts_speak("Okay, let's try again.")
                time.sleep(0.5)
                continue
            else:
                # Unclear response - assume no and retry
                self.tts_speak("I didn't understand your response. Let's try again.")
                time.sleep(0.5)
                continue

        # Exhausted all retries
        self.state = RegistrationState.FAILED
        self.tts_speak("I'm having trouble capturing your name. Please try the registration again later.")
        return None

    def run_registration_flow(
        self,
        permission_manager,
        camera_manager,
        mcp_facade,
        access_token: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Run the complete voice registration flow.

        This is the main entry point that coordinates all steps:
        1. Capture and confirm name
        2. Request camera permission
        3. Capture photo
        4. Register with MCP server

        Args:
            permission_manager: PermissionManager instance for camera access
            camera_manager: WebcamManager instance for photo capture
            mcp_facade: SyncMCPFacade instance for registration
            access_token: OAuth access token for MCP

        Returns:
            Tuple of (success, name)
            - success: True if registration completed, False otherwise
            - name: Confirmed name if successful, None otherwise
        """
        print("[Registration] Starting voice registration flow", flush=True)

        # Step 1: Capture and confirm name
        name = self.capture_and_confirm_name()

        if name is None:
            print("[Registration] Name capture failed", flush=True)
            return False, None

        # Step 2: Request camera permission
        self.tts_speak("Great. I have saved your name. Now I need to take a photo to complete your registration.")
        print("[Registration] Requesting camera permission", flush=True)

        if not permission_manager.request_camera_permission():
            print("[Registration] Camera permission denied", flush=True)
            self.tts_speak("Camera permission denied. Registration cancelled.")
            self.state = RegistrationState.FAILED
            return False, None

        # Step 3: Initialize camera with retry logic
        print("[Registration] Initializing camera", flush=True)
        if not camera_manager.initialize():
            print("[Registration] Camera initialization failed", flush=True)
            self.tts_speak("Camera initialization failed. Please try again later.")
            self.state = RegistrationState.FAILED
            return False, None

        # Step 4: Capture photo
        self.tts_speak("Please look at the camera.")
        time.sleep(1.0)  # Give user time to position

        success, image_data = camera_manager.capture_to_base64()

        if not success or not image_data:
            print("[Registration] Photo capture failed", flush=True)
            self.tts_speak("Photo capture failed. Please try again.")
            camera_manager.release()
            self.state = RegistrationState.FAILED
            return False, None

        # Step 5: Register with MCP
        print(f"[Registration] Registering user: {name}", flush=True)

        try:
            result = mcp_facade.register_user(
                access_token=access_token,
                name=name,
                image_data=image_data,
                metadata={"registration_type": "voice"}
            )

            if result.get("status") == "success":
                user_data = result.get("user", {})
                user_id = user_data.get("id", "unknown")

                print(f"[Registration] Registration successful: {user_id}", flush=True)
                self.tts_speak(f"Registration complete. Welcome, {name}!")

                camera_manager.release()
                self.state = RegistrationState.COMPLETED
                return True, name
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"[Registration] Registration failed: {error_msg}", flush=True)
                self.tts_speak("Registration failed. Please try again.")

                camera_manager.release()
                self.state = RegistrationState.FAILED
                return False, None

        except Exception as e:
            print(f"[Registration] Registration error: {e}", flush=True)
            self.tts_speak("Registration error. Please try again.")

            camera_manager.release()
            self.state = RegistrationState.FAILED
            return False, None

    def reset(self) -> None:
        """Reset orchestrator to idle state."""
        self.state = RegistrationState.IDLE
        print("[Registration] Orchestrator reset to idle", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"RegistrationOrchestrator(state={self.state.value}, whisper={self.whisper})"
