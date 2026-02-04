"""
Deletion Orchestrator - Voice-activated user profile deletion state machine.

Coordinates the complete user deletion flow with multi-step confirmation:
1. Face recognition to identify user
2. Confirm identity
3. Explain consequences
4. Final confirmation
5. Delete user profile
6. Confirm deletion

SAFETY FEATURES:
- Multi-step confirmation to prevent accidental deletion
- Clear explanation of what will be deleted
- Face recognition for authentication
- Explicit consent at each step
"""

import time
from typing import Optional, Tuple
from enum import Enum

from .voice_activity_detector import VoiceActivityDetector
from .whisper_transcription_engine import WhisperTranscriptionEngine
from .llm_confirmation_parser import LLMConfirmationParser


class DeletionState(Enum):
    """States in the user deletion flow."""
    IDLE = "idle"
    FACE_RECOGNITION = "face_recognition"
    CONFIRM_IDENTITY = "confirm_identity"
    EXPLAIN_CONSEQUENCES = "explain_consequences"
    FINAL_CONFIRMATION = "final_confirmation"
    DELETE_USER = "delete_user"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeletionOrchestrator:
    """
    Orchestrates voice-activated user profile deletion flow.

    Manages the complete state machine for:
    1. Authenticating user via face recognition
    2. Confirming user identity via voice
    3. Explaining deletion consequences
    4. Obtaining final confirmation
    5. Executing deletion via MCP

    ARCHITECTURAL PATTERN:
    Follows the same orchestrator pattern as RegistrationOrchestrator
    for consistency and maintainability.
    """

    def __init__(
        self,
        tts_speak_func,
        whisper_model: str = "base",
        whisper_device: str = "cpu",
        whisper_compute_type: str = "float32",
        enable_llm_confirmation: bool = True,
        ollama_host: str = "http://localhost:11434",
        llm_model: str = "gemma3:4b",
        llm_timeout: float = 2.0,
        llm_temperature: float = 0.1,
        llm_max_tokens: int = 10
    ):
        """
        Initialize Deletion Orchestrator.

        Args:
            tts_speak_func: Function to call for text-to-speech (e.g., speech.speak)
            whisper_model: Whisper model size (tiny, base, small, medium)
            whisper_device: Device for Whisper inference (cpu, cuda)
            whisper_compute_type: Whisper compute type (float32, float16, int8)
            enable_llm_confirmation: Use LLM for confirmation parsing (default: True)
            ollama_host: Ollama API endpoint (default: http://localhost:11434)
            llm_model: Ollama model for confirmations (default: gemma3:4b)
            llm_timeout: LLM request timeout in seconds (default: 2.0)
            llm_temperature: LLM temperature (default: 0.1)
            llm_max_tokens: Max tokens to generate (default: 10)
        """
        self.tts_speak = tts_speak_func

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

        # Initialize LLM confirmation parser
        self.llm_parser = LLMConfirmationParser(
            ollama_host=ollama_host,
            model_name=llm_model,
            enable_llm=enable_llm_confirmation,
            timeout_sec=llm_timeout,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )

        # State
        self.state = DeletionState.IDLE

    def _extract_confirmation(self, text: str, question_context: Optional[str] = None) -> Optional[bool]:
        """
        Extract yes/no confirmation from transcribed text using LLM-based parsing.

        This method now uses Gemma 3 via Ollama for natural language understanding,
        with graceful fallback to rule-based parsing if LLM is unavailable.

        Args:
            text: Transcribed confirmation text
            question_context: The question that was asked (helps LLM understand context)

        Returns:
            True for yes, False for no, None if unclear

        Example:
            >>> self._extract_confirmation("Sure thing!", "Is that correct?")
            True
            >>> self._extract_confirmation("Not really", "Do you want to proceed?")
            False
        """
        return self.llm_parser.parse_confirmation(text, question_context)

    def recognize_user(
        self,
        camera_manager,
        mcp_facade,
        access_token: str,
        confidence_threshold: float = 0.25
    ) -> Optional[Tuple[str, str, float]]:
        """
        Recognize user via face recognition.

        Args:
            camera_manager: WebcamManager instance for photo capture
            mcp_facade: SyncMCPFacade instance for recognition
            access_token: OAuth access token for MCP
            confidence_threshold: Maximum distance for recognition

        Returns:
            Tuple of (user_id, name, distance) if recognized, None otherwise
        """
        print("[Deletion] Starting face recognition for authentication", flush=True)
        self.state = DeletionState.FACE_RECOGNITION

        # Capture face image
        self.tts_speak("Please look at the camera so I can confirm your identity.")
        time.sleep(1.0)  # Give user time to position

        success, image_data = camera_manager.capture_to_base64()

        if not success or not image_data:
            print("[Deletion] Photo capture failed", flush=True)
            self.tts_speak("I couldn't capture your image. Please try again later.")
            return None

        # Recognize face
        print("[Deletion] Recognizing face...", flush=True)
        self.tts_speak("Let me take a look.")

        try:
            result = mcp_facade.recognize_face(
                access_token=access_token,
                image_data=image_data,
                confidence_threshold=confidence_threshold
            )

            status = result.get("status", "error")

            if status == "recognized":
                user = result.get("user", {})
                user_id = user.get("user_id", "")
                name = user.get("name", "")
                distance = result.get("distance", 1.0)

                print(f"[Deletion] Recognized user: {name} (ID: {user_id}, distance: {distance:.3f})", flush=True)
                return (user_id, name, distance)

            elif status == "low_confidence":
                print("[Deletion] Recognition confidence too low", flush=True)
                self.tts_speak("I'm not confident in the recognition. Please ensure you're well-lit and facing the camera.")
                return None

            else:
                print(f"[Deletion] User not recognized: {status}", flush=True)
                self.tts_speak("I don't recognize you. Only registered users can delete their profiles.")
                return None

        except Exception as e:
            print(f"[Deletion] Recognition error: {e}", flush=True)
            self.tts_speak("Recognition error. Please try again later.")
            return None

    def confirm_identity(self, name: str) -> bool:
        """
        Confirm user identity via voice.

        Args:
            name: Recognized user's name

        Returns:
            True if user confirms identity, False otherwise
        """
        print(f"[Deletion] Confirming identity: {name}", flush=True)
        self.state = DeletionState.CONFIRM_IDENTITY

        # Ask for confirmation
        self.tts_speak(f"I recognized you as {name}. Is that correct? Say yes to confirm or no to cancel.")

        # Record confirmation
        success, audio = self.vad.record_speech(beep=False)

        if not success or audio is None:
            print("[Deletion] No confirmation audio captured", flush=True)
            self.tts_speak("I didn't hear a response. Deletion cancelled.")
            return False

        # Transcribe confirmation
        conf_text = self.whisper.transcribe(audio, beam_size=5)
        print(f"[Deletion] Identity confirmation transcription: '{conf_text}'", flush=True)

        # Extract yes/no with context
        question = f"I recognized you as {name}. Is that correct?"
        confirmed = self._extract_confirmation(conf_text, question_context=question)

        if confirmed is True:
            print("[Deletion] Identity confirmed", flush=True)
            return True
        elif confirmed is False:
            print("[Deletion] Identity not confirmed", flush=True)
            self.tts_speak("Identity not confirmed. Deletion cancelled.")
            return False
        else:
            print("[Deletion] Unclear confirmation response", flush=True)
            self.tts_speak("I didn't understand your response. Deletion cancelled.")
            return False

    def explain_and_confirm_deletion(self, name: str) -> bool:
        """
        Explain deletion consequences and get final confirmation.

        Args:
            name: User's name

        Returns:
            True if user confirms deletion, False otherwise
        """
        print("[Deletion] Explaining consequences and requesting final confirmation", flush=True)
        self.state = DeletionState.EXPLAIN_CONSEQUENCES

        # Explain what will be deleted
        self.tts_speak(
            f"{name}, this will permanently delete all your data from the system, "
            "including your face profile and all associated information. "
            "This action cannot be undone. "
            "Say yes to proceed with deletion, or no to cancel."
        )

        # State: Final confirmation
        self.state = DeletionState.FINAL_CONFIRMATION

        # Record final confirmation
        success, audio = self.vad.record_speech(beep=False)

        if not success or audio is None:
            print("[Deletion] No final confirmation audio captured", flush=True)
            self.tts_speak("No confirmation received. Deletion cancelled.")
            return False

        # Transcribe confirmation
        conf_text = self.whisper.transcribe(audio, beam_size=5)
        print(f"[Deletion] Final confirmation transcription: '{conf_text}'", flush=True)

        # Extract yes/no with context
        question = "Say yes to proceed with deletion, or no to cancel."
        confirmed = self._extract_confirmation(conf_text, question_context=question)

        if confirmed is True:
            print("[Deletion] Final confirmation received", flush=True)
            return True
        elif confirmed is False:
            print("[Deletion] Deletion cancelled by user", flush=True)
            self.tts_speak("Deletion cancelled. Your data has been preserved.")
            return False
        else:
            print("[Deletion] Unclear final confirmation", flush=True)
            self.tts_speak("I didn't understand your response. Deletion cancelled for safety.")
            return False

    def execute_deletion(
        self,
        mcp_facade,
        access_token: str,
        user_id: str,
        name: str
    ) -> bool:
        """
        Execute user deletion via MCP.

        Args:
            mcp_facade: SyncMCPFacade instance
            access_token: OAuth access token
            user_id: User ID to delete
            name: User's name (for confirmation message)

        Returns:
            True if deletion successful, False otherwise
        """
        print(f"[Deletion] Executing deletion for user: {user_id}", flush=True)
        self.state = DeletionState.DELETE_USER

        self.tts_speak("Deleting your profile now. Please wait.")

        try:
            result = mcp_facade.delete_user(
                access_token=access_token,
                user_id=user_id
            )

            status = result.get("status", "error")
            message = result.get("message", "Unknown error")

            if status == "success":
                print(f"[Deletion] Deletion successful: {message}", flush=True)
                self.tts_speak(f"Your profile has been successfully deleted, {name}. Goodbye.")
                self.state = DeletionState.COMPLETED
                return True
            else:
                print(f"[Deletion] Deletion failed: {status} - {message}", flush=True)
                self.tts_speak(f"Deletion failed. {message}. Please contact support if this persists.")
                self.state = DeletionState.CANCELLED
                return False

        except Exception as e:
            print(f"[Deletion] Deletion error: {e}", flush=True)
            self.tts_speak("An error occurred during deletion. Please try again later.")
            self.state = DeletionState.CANCELLED
            return False

    def run_deletion_flow(
        self,
        permission_manager,
        camera_manager,
        mcp_facade,
        access_token: str,
        confidence_threshold: float = 0.25
    ) -> Tuple[bool, Optional[str]]:
        """
        Run the complete user deletion flow.

        This is the main entry point that coordinates all steps:
        1. Request camera permission
        2. Recognize user via face
        3. Confirm identity via voice
        4. Explain consequences
        5. Get final confirmation
        6. Execute deletion

        Args:
            permission_manager: PermissionManager instance for camera access
            camera_manager: WebcamManager instance for photo capture
            mcp_facade: SyncMCPFacade instance for recognition and deletion
            access_token: OAuth access token for MCP
            confidence_threshold: Maximum distance for face recognition

        Returns:
            Tuple of (success, user_id)
            - success: True if deletion completed, False otherwise
            - user_id: Deleted user ID if successful, None otherwise
        """
        print("[Deletion] Starting user deletion flow", flush=True)

        # Step 1: Request camera permission
        print("[Deletion] Requesting camera permission", flush=True)

        if not permission_manager.request_camera_permission():
            print("[Deletion] Camera permission denied", flush=True)
            self.state = DeletionState.CANCELLED
            return False, None

        # Step 2: Initialize camera
        print("[Deletion] Initializing camera", flush=True)
        if not camera_manager.initialize():
            print("[Deletion] Camera initialization failed", flush=True)
            self.tts_speak("Camera initialization failed. Please try again later.")
            self.state = DeletionState.CANCELLED
            return False, None

        # Step 3: Recognize user
        recognition_result = self.recognize_user(
            camera_manager=camera_manager,
            mcp_facade=mcp_facade,
            access_token=access_token,
            confidence_threshold=confidence_threshold
        )

        if recognition_result is None:
            # Recognition failed - error already spoken
            camera_manager.release()
            self.state = DeletionState.CANCELLED
            return False, None

        user_id, name, distance = recognition_result

        # Step 4: Confirm identity
        if not self.confirm_identity(name):
            # Identity not confirmed - error already spoken
            camera_manager.release()
            self.state = DeletionState.CANCELLED
            return False, None

        # Step 5: Explain and get final confirmation
        if not self.explain_and_confirm_deletion(name):
            # Final confirmation not received - error already spoken
            camera_manager.release()
            self.state = DeletionState.CANCELLED
            return False, None

        # Step 6: Execute deletion
        success = self.execute_deletion(
            mcp_facade=mcp_facade,
            access_token=access_token,
            user_id=user_id,
            name=name
        )

        # Cleanup
        camera_manager.release()

        if success:
            return True, user_id
        else:
            return False, None

    def reset(self) -> None:
        """Reset orchestrator to idle state."""
        self.state = DeletionState.IDLE
        print("[Deletion] Orchestrator reset to idle", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"DeletionOrchestrator(state={self.state.value}, whisper={self.whisper})"
