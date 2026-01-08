"""
Update Orchestrator - Voice-activated user profile update state machine.

Coordinates the complete user update flow:
1. Face recognition to authenticate user
2. Confirm identity via voice
3. Fetch and present current profile
4. Select fields to update
5. Capture new name with VAD
6. Confirm new name with user
7. Preview changes
8. Final confirmation
9. Execute update via MCP

SAFETY FEATURES:
- Face authentication required (must be physically present)
- Identity verification via voice
- Explicit preview of all changes before applying
- Final confirmation step
- Rollback on any error (atomic updates)
"""

import time
from typing import Optional, Tuple, Dict, Any
from enum import Enum

from .voice_activity_detector import VoiceActivityDetector
from .whisper_transcription_engine import WhisperTranscriptionEngine
from .llm_confirmation_parser import LLMConfirmationParser


class UpdateState(Enum):
    """States in the user update flow."""
    IDLE = "idle"
    FACE_RECOGNITION = "face_recognition"
    CONFIRM_IDENTITY = "confirm_identity"
    FETCH_PROFILE = "fetch_profile"
    PRESENT_PROFILE = "present_profile"
    SELECT_UPDATE_FIELDS = "select_update_fields"
    CAPTURE_NEW_NAME = "capture_new_name"
    TRANSCRIBE_NEW_NAME = "transcribe_new_name"
    CONFIRM_NEW_NAME = "confirm_new_name"
    PREVIEW_CHANGES = "preview_changes"
    FINAL_CONFIRMATION = "final_confirmation"
    EXECUTE_UPDATE = "execute_update"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UpdateOrchestrator:
    """
    Orchestrates voice-activated user profile update flow.

    Manages the complete state machine for:
    1. Authenticating user via face recognition
    2. Confirming user identity via voice
    3. Fetching current profile data
    4. Presenting current information to user
    5. Capturing new profile data (name, metadata)
    6. Previewing changes before applying
    7. Executing update via MCP with rollback on failure

    ARCHITECTURAL PATTERN:
    Follows the same orchestrator pattern as RegistrationOrchestrator
    and DeletionOrchestrator for consistency and maintainability.
    """

    def __init__(
        self,
        tts_speak_func,
        whisper_model: str = "base",
        whisper_device: str = "cpu",
        whisper_compute_type: str = "float32",
        max_retries: int = 3,
        enable_llm_confirmation: bool = True,
        ollama_host: str = "http://localhost:11434",
        llm_model: str = "gemma3:4b",
        llm_timeout: float = 2.0,
        llm_temperature: float = 0.1,
        llm_max_tokens: int = 10
    ):
        """
        Initialize Update Orchestrator.

        Args:
            tts_speak_func: Function to call for text-to-speech (e.g., speech.speak)
            whisper_model: Whisper model size (tiny, base, small, medium)
            whisper_device: Device for Whisper inference (cpu, cuda)
            whisper_compute_type: Whisper compute type (float32, float16, int8)
            max_retries: Maximum retry attempts for name capture
            enable_llm_confirmation: Use LLM for confirmation parsing (default: True)
            ollama_host: Ollama API endpoint (default: http://localhost:11434)
            llm_model: Ollama model for confirmations (default: gemma3:4b)
            llm_timeout: LLM request timeout in seconds (default: 2.0)
            llm_temperature: LLM temperature (default: 0.1)
            llm_max_tokens: Max tokens to generate (default: 10)
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
        self.state = UpdateState.IDLE

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

    def _extract_confirmation(self, text: str, question_context: Optional[str] = None) -> Optional[bool]:
        """
        Extract yes/no confirmation from transcribed text using LLM-based parsing.

        This method uses Gemma 3 via Ollama for natural language understanding,
        with graceful fallback to rule-based parsing if LLM is unavailable.

        Args:
            text: Transcribed confirmation text
            question_context: The question that was asked (helps LLM understand context)

        Returns:
            True for yes, False for no, None if unclear

        Example:
            >>> self._extract_confirmation("Sure thing!", "Is that correct?")
            True
            >>> self._extract_confirmation("Try again", "Is your name John?")
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
        Recognize user via face recognition for authentication.

        Args:
            camera_manager: WebcamManager instance for photo capture
            mcp_facade: SyncMCPFacade instance for recognition
            access_token: OAuth access token for MCP
            confidence_threshold: Maximum distance for recognition

        Returns:
            Tuple of (user_id, name, distance) if recognized, None otherwise
        """
        print("[Update] Starting face recognition for authentication", flush=True)
        self.state = UpdateState.FACE_RECOGNITION

        # Capture face image
        self.tts_speak("Please look at the camera so I can verify your identity.")
        time.sleep(1.0)  # Give user time to position

        success, image_data = camera_manager.capture_to_base64()

        if not success or not image_data:
            print("[Update] Photo capture failed", flush=True)
            self.tts_speak("I couldn't capture your image. Please try again later.")
            return None

        # Recognize face
        print("[Update] Recognizing face...", flush=True)
        self.tts_speak("Let me check who you are.")

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

                print(f"[Update] Recognized user: {name} (ID: {user_id}, distance: {distance:.3f})", flush=True)
                return (user_id, name, distance)

            elif status == "low_confidence":
                print("[Update] Recognition confidence too low", flush=True)
                self.tts_speak("I'm not confident in the recognition. Please ensure you're well-lit and facing the camera.")
                return None

            else:
                print(f"[Update] User not recognized: {status}", flush=True)
                self.tts_speak("I don't recognize you. Only registered users can update their profiles.")
                return None

        except Exception as e:
            print(f"[Update] Recognition error: {e}", flush=True)
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
        print(f"[Update] Confirming identity: {name}", flush=True)
        self.state = UpdateState.CONFIRM_IDENTITY

        # Ask for confirmation
        self.tts_speak(f"I recognized you as {name}. Is that correct? Say yes to confirm or no to cancel.")

        # Record confirmation
        success, audio = self.vad.record_speech(beep=False)

        if not success or audio is None:
            print("[Update] No confirmation audio captured", flush=True)
            self.tts_speak("I didn't hear a response. Update cancelled.")
            return False

        # Transcribe confirmation
        conf_text = self.whisper.transcribe(audio, beam_size=5)
        print(f"[Update] Identity confirmation transcription: '{conf_text}'", flush=True)

        # Extract yes/no with context
        question = f"I recognized you as {name}. Is that correct?"
        confirmed = self._extract_confirmation(conf_text, question_context=question)

        if confirmed is True:
            print("[Update] Identity confirmed", flush=True)
            return True
        elif confirmed is False:
            print("[Update] Identity not confirmed", flush=True)
            self.tts_speak("Identity not confirmed. Update cancelled.")
            return False
        else:
            print("[Update] Unclear confirmation response", flush=True)
            self.tts_speak("I didn't understand your response. Update cancelled.")
            return False

    def fetch_and_present_profile(
        self,
        mcp_facade,
        access_token: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile and present current information.

        Args:
            mcp_facade: SyncMCPFacade instance
            access_token: OAuth access token
            user_id: User ID to fetch

        Returns:
            User profile dictionary, or None if error
        """
        print(f"[Update] Fetching profile for user: {user_id}", flush=True)
        self.state = UpdateState.FETCH_PROFILE

        try:
            # Fetch profile via MCP
            result = mcp_facade.get_user_profile(
                access_token=access_token,
                user_id=user_id
            )

            # Check if this is an error response (has "status": "error")
            # Success responses have "user_id" field instead of "status"
            if result.get("status") == "error":
                error_msg = result.get("message", "Unknown error")
                print(f"[Update] Failed to fetch profile: {error_msg}", flush=True)
                self.tts_speak(f"Could not retrieve your profile: {error_msg}.")
                return None

            # Success case: result contains user data directly
            if "user_id" in result:
                profile = result
                print(f"[Update] Profile fetched: {profile.get('name')}", flush=True)

                # Present profile to user
                self.state = UpdateState.PRESENT_PROFILE
                name = profile.get("name", "User")
                self.tts_speak(f"Here is your current profile. Your name is {name}.")

                # Present metadata if it exists
                metadata = profile.get("metadata", {})
                if metadata:
                    self.tts_speak("You have the following information on file:")
                    for key, value in metadata.items():
                        # Remove "custom_" prefix from keys for display
                        display_key = key.replace("custom_", "").replace("_", " ").title()
                        self.tts_speak(f"{display_key}: {value}")

                return profile
            else:
                # Unexpected response format
                print(f"[Update] Unexpected response format: {result}", flush=True)
                self.tts_speak("Could not retrieve your profile. Please try again.")
                return None

        except Exception as e:
            print(f"[Update] Profile fetch error: {e}", flush=True)
            self.tts_speak("Error retrieving your profile. Please try again.")
            return None

    def select_update_fields(self) -> Optional[str]:
        """
        Ask user what they want to update with retry logic.

        Returns:
            "name", "metadata", "both", or None if cancelled/max retries exceeded
        """
        print("[Update] Asking user what to update", flush=True)
        self.state = UpdateState.SELECT_UPDATE_FIELDS

        selected = None

        # Retry loop for field selection
        for attempt in range(self.max_retries):
            print(f"[Update] Field selection attempt {attempt + 1}/{self.max_retries}", flush=True)

            # Ask for selection
            self.tts_speak("What would you like to update? You can say name, information, details, or both.")

            # Record response
            success, audio = self.vad.record_speech(beep=False)

            if not success or audio is None:
                print("[Update] No response to update selection", flush=True)
                self.tts_speak("I didn't hear anything. Please say 'name', 'information', 'details', or 'both'.")
                time.sleep(0.5)
                continue

            # Transcribe selection
            selection_text = self.whisper.transcribe(audio, beam_size=5)
            print(f"[Update] Selection transcription: '{selection_text}'", flush=True)

            if not selection_text:
                print("[Update] Transcription failed", flush=True)
                self.tts_speak("I couldn't understand that. Please repeat: name, information, details, or both.")
                time.sleep(0.5)
                continue

            # Parse for keywords - support various pronunciations and transcription variations
            selection_lower = selection_text.lower()
            # Remove extra spaces and normalize
            selection_normalized = ' '.join(selection_lower.split())

            # Check for keywords with flexibility (in order of specificity)
            # Support synonyms and common variations for better UX
            if "both" in selection_normalized:
                selected = "both"
            elif any(var in selection_normalized for var in [
                "metadata",           # Exact term
                "meet data",          # Whisper transcription variation
                "meta data",          # With space
                "information",        # Common synonym
                "info",               # Short form
                "data",               # Generic term
                "profile",            # User-centric synonym
                "details",            # Conversational synonym
                "properties",         # Technical synonym
                "attributes",         # Technical synonym
                "settings",           # User-friendly synonym
                "additional",         # Descriptive term
                "extra"               # Descriptive term
            ]):
                # More flexible metadata matching - includes synonyms and transcription variations
                selected = "metadata"
            elif "name" in selection_normalized:
                selected = "name"
            else:
                print(f"[Update] Could not parse update selection: '{selection_text}'", flush=True)
                self.tts_speak(f"I heard '{selection_text}' but that's not clear. Please say 'name', 'information', 'details', or 'both'.")
                time.sleep(0.5)
                continue

            # Keyword was recognized - now confirm the selection
            print(f"[Update] Recognized keyword: {selected}", flush=True)
            self.tts_speak(f"You want to update your {selected}. Is that correct?")
            success, conf_audio = self.vad.record_speech(beep=False)

            if not success or conf_audio is None:
                print("[Update] No confirmation response to selection", flush=True)
                self.tts_speak("I didn't catch your confirmation. Let me try again.")
                time.sleep(0.5)
                continue

            conf_text = self.whisper.transcribe(conf_audio, beam_size=5)
            print(f"[Update] Confirmation transcription: '{conf_text}'", flush=True)

            confirmed = self._extract_confirmation(
                conf_text,
                question_context=f"You want to update your {selected}. Is that correct?"
            )

            if confirmed is True:
                print(f"[Update] Selection confirmed: {selected}", flush=True)
                return selected
            elif confirmed is False:
                print("[Update] Selection rejected by user, retrying", flush=True)
                self.tts_speak("Okay, let's try again.")
                time.sleep(0.5)
                continue
            else:
                print("[Update] Confirmation unclear, retrying", flush=True)
                self.tts_speak("I didn't understand your confirmation. Let's try again.")
                time.sleep(0.5)
                continue

        # Exhausted all retries
        print(f"[Update] Max retries ({self.max_retries}) exhausted for field selection", flush=True)
        self.tts_speak("I'm having trouble understanding what you want to update. Please try the update again later.")
        return None

    def capture_and_confirm_new_name(self) -> Optional[str]:
        """
        Capture user's new name with VAD and confirm.

        Implements the complete name capture flow:
        1. Prompt: "Please say your new name after the beep"
        2. Record name with VAD
        3. Transcribe with Whisper
        4. Confirm: "I heard {name}. Is that correct?"
        5. Record yes/no response
        6. Retry if needed

        Returns:
            Confirmed name string, or None if failed/cancelled
        """
        for attempt in range(self.max_retries):
            print(f"[Update] Name capture attempt {attempt + 1}/{self.max_retries}", flush=True)

            # State: CAPTURE_NEW_NAME
            self.state = UpdateState.CAPTURE_NEW_NAME
            self.tts_speak("Please say your new name after the beep.")
            time.sleep(0.25)

            # Record name
            success, audio = self.vad.record_speech(beep=True)

            if not success or audio is None:
                self.tts_speak("I didn't catch that. Please try again.")
                time.sleep(0.5)
                continue

            # State: TRANSCRIBE_NEW_NAME
            self.state = UpdateState.TRANSCRIBE_NEW_NAME
            self.tts_speak("Processing your name now.")
            name_text = self.whisper.transcribe(audio, beam_size=5)

            print(f"[Update] Transcribed name: '{name_text}'", flush=True)

            # Check if it looks like a full name
            if not self._looks_like_full_name(name_text):
                print("[Update] Transcription doesn't look like a full name", flush=True)
                self.tts_speak("I couldn't capture your full name clearly. Please try again.")
                time.sleep(0.5)
                continue

            # State: CONFIRM_NEW_NAME
            self.state = UpdateState.CONFIRM_NEW_NAME
            self.tts_speak(f"I heard {name_text}. Is that correct? Say yes to confirm or no to try again.")

            # Record confirmation
            success, conf_audio = self.vad.record_speech(beep=False)

            if not success or conf_audio is None:
                self.tts_speak("No confirmation heard. Let's try again.")
                time.sleep(0.5)
                continue

            # Transcribe confirmation
            conf_text = self.whisper.transcribe(conf_audio, beam_size=5)
            print(f"[Update] Confirmation transcription: '{conf_text}'", flush=True)

            # Extract confirmation with context
            question = f"I heard {name_text}. Is that correct?"
            confirmed = self._extract_confirmation(conf_text, question_context=question)

            if confirmed is True:
                # User confirmed the name
                print(f"[Update] Name confirmed: '{name_text}'", flush=True)
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
        self.tts_speak("I'm having trouble capturing your new name. Please try the update again later.")
        return None

    def capture_and_confirm_new_metadata(self, current_metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Capture and confirm new metadata values from user.

        Args:
            current_metadata: Current metadata dict (optional)

        Returns:
            New metadata dict or None if cancelled
        """
        print("[Update] Capturing new metadata", flush=True)
        self.state = UpdateState.CAPTURE_NEW_NAME  # Reuse state for metadata capture

        new_metadata = {}
        current_metadata = current_metadata or {}

        # Present current metadata to user
        if current_metadata:
            self.tts_speak("Here are your current metadata fields:")
            for key, value in current_metadata.items():
                display_key = key.replace("custom_", "").replace("_", " ").title()
                self.tts_speak(f"{display_key}: {value}")
        else:
            self.tts_speak("You don't have any metadata yet. I can help you add some.")

        # Ask which fields to update
        self.tts_speak("Which metadata fields would you like to update? Say the field name, for example, department, position, or location.")

        for attempt in range(self.max_retries):
            # Record field names
            success, audio = self.vad.record_speech(beep=True)
            if not success or audio is None:
                self.tts_speak("I didn't catch that. Please say the metadata fields you want to update.")
                continue

            # Transcribe field selection
            field_text = self.whisper.transcribe(audio, beam_size=5)
            if not field_text:
                self.tts_speak("I didn't understand. Please repeat the fields you want to update.")
                continue

            print(f"[Update] Metadata fields selected: {field_text}", flush=True)
            self.tts_speak(f"You want to update: {field_text}. Is that correct?")

            # Confirm selection
            success, conf_audio = self.vad.record_speech(beep=False)
            if not success or conf_audio is None:
                self.tts_speak("Let's try again.")
                continue

            conf_text = self.whisper.transcribe(conf_audio, beam_size=5)
            confirmed = self._extract_confirmation(conf_text, question_context="metadata fields")

            if confirmed is True:
                break
            elif confirmed is False:
                self.tts_speak("Okay, let's try again.")
                time.sleep(0.5)
                continue
            else:
                self.tts_speak("I didn't understand. Let's try again.")
                time.sleep(0.5)
                continue

        # Now capture values for each field mentioned
        field_list = field_text.lower().split()

        for field_name in field_list:
            # Clean up field name
            field_key = f"custom_{field_name}"
            display_name = field_name.replace("_", " ").title()

            # Ask for new value
            self.tts_speak(f"What should your new {display_name} be?")

            for attempt in range(self.max_retries):
                success, audio = self.vad.record_speech(beep=True)
                if not success or audio is None:
                    self.tts_speak(f"I didn't catch your {display_name}. Please try again.")
                    continue

                value_text = self.whisper.transcribe(audio, beam_size=5)
                if not value_text or len(value_text.strip()) == 0:
                    self.tts_speak(f"Please say your {display_name}.")
                    continue

                # Confirm the value
                self.tts_speak(f"I heard {value_text} for {display_name}. Is that correct?")
                success, conf_audio = self.vad.record_speech(beep=False)
                if not success or conf_audio is None:
                    self.tts_speak("Let's try again.")
                    continue

                conf_text = self.whisper.transcribe(conf_audio, beam_size=5)
                confirmed = self._extract_confirmation(conf_text, question_context=f"{display_name} value")

                if confirmed is True:
                    # Value confirmed - store it
                    new_metadata[field_key] = value_text
                    self.tts_speak(f"Got it. Your {display_name} is now {value_text}.")
                    break
                elif confirmed is False:
                    self.tts_speak(f"Let's try again for {display_name}.")
                    continue
                else:
                    self.tts_speak("I didn't understand. Let's try again.")
                    continue

        if not new_metadata:
            self.tts_speak("No metadata was updated.")
            return None

        print(f"[Update] New metadata: {new_metadata}", flush=True)
        return new_metadata

    def preview_changes(
        self,
        current_profile: Dict[str, Any],
        new_name: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Speak preview of changes that will be applied.

        Args:
            current_profile: Current user profile
            new_name: New name (optional)
            new_metadata: New metadata (optional)
        """
        print("[Update] Previewing changes", flush=True)
        self.state = UpdateState.PREVIEW_CHANGES

        current_name = current_profile.get("name", "User")

        if new_name:
            self.tts_speak(f"Your name will change from {current_name} to {new_name}.")

        if new_metadata:
            self.tts_speak("Your metadata will be updated with the following:")
            for key, value in new_metadata.items():
                display_key = key.replace("custom_", "").replace("_", " ").title()
                self.tts_speak(f"{display_key}: {value}")

        self.tts_speak("These changes will be saved to your profile.")

    def get_final_confirmation(self) -> bool:
        """
        Get final confirmation to apply changes.

        Returns:
            True if user confirms, False otherwise
        """
        print("[Update] Requesting final confirmation", flush=True)
        self.state = UpdateState.FINAL_CONFIRMATION

        self.tts_speak("Apply these changes to your profile? Say yes to confirm or no to cancel.")

        # Record final confirmation
        success, audio = self.vad.record_speech(beep=False)

        if not success or audio is None:
            print("[Update] No final confirmation audio captured", flush=True)
            self.tts_speak("No confirmation received. Update cancelled.")
            return False

        # Transcribe confirmation
        conf_text = self.whisper.transcribe(audio, beam_size=5)
        print(f"[Update] Final confirmation transcription: '{conf_text}'", flush=True)

        # Extract yes/no
        question = "Apply these changes to your profile?"
        confirmed = self._extract_confirmation(conf_text, question_context=question)

        if confirmed is True:
            print("[Update] Final confirmation received", flush=True)
            return True
        elif confirmed is False:
            print("[Update] Update cancelled by user", flush=True)
            self.tts_speak("Update cancelled. Your profile has not been changed.")
            return False
        else:
            print("[Update] Unclear final confirmation", flush=True)
            self.tts_speak("I didn't understand your response. Update cancelled for safety.")
            return False

    def execute_update(
        self,
        mcp_facade,
        access_token: str,
        user_id: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute user update via MCP.

        Args:
            mcp_facade: SyncMCPFacade instance
            access_token: OAuth access token
            user_id: User ID to update
            name: New name (optional)
            metadata: New metadata (optional)

        Returns:
            True if update successful, False otherwise
        """
        print(f"[Update] Executing update for user: {user_id}", flush=True)
        self.state = UpdateState.EXECUTE_UPDATE

        self.tts_speak("Updating your profile now. Please wait.")

        try:
            result = mcp_facade.update_user(
                access_token=access_token,
                user_id=user_id,
                name=name,
                metadata=metadata
            )

            status = result.get("status", "error")
            message = result.get("message", "Unknown error")

            if status == "success":
                print(f"[Update] Update successful: {message}", flush=True)
                self.tts_speak("Your profile has been updated successfully.")
                self.state = UpdateState.COMPLETED
                return True
            else:
                print(f"[Update] Update failed: {status} - {message}", flush=True)
                self.tts_speak(f"Update failed. {message}. Please try again.")
                self.state = UpdateState.CANCELLED
                return False

        except Exception as e:
            print(f"[Update] Update error: {e}", flush=True)
            self.tts_speak("An error occurred during update. Please try again later.")
            self.state = UpdateState.CANCELLED
            return False

    def run_update_flow(
        self,
        permission_manager,
        camera_manager,
        mcp_facade,
        access_token: str,
        confidence_threshold: float = 0.25
    ) -> Tuple[bool, Optional[str]]:
        """
        Run the complete user update flow.

        This is the main entry point that coordinates all steps:
        1. Request camera permission
        2. Recognize user via face
        3. Confirm identity via voice
        4. Fetch and present profile
        5. Select what to update
        6. Capture new information
        7. Preview changes
        8. Get final confirmation
        9. Execute update

        Args:
            permission_manager: PermissionManager instance for camera access
            camera_manager: WebcamManager instance for photo capture
            mcp_facade: SyncMCPFacade instance for recognition and update
            access_token: OAuth access token for MCP
            confidence_threshold: Maximum distance for face recognition

        Returns:
            Tuple of (success, user_id)
            - success: True if update completed, False otherwise
            - user_id: Updated user ID if successful, None otherwise
        """
        print("[Update] Starting user update flow", flush=True)

        # Step 1: Request camera permission
        self.tts_speak("I need to verify your identity before updating your profile.")
        print("[Update] Requesting camera permission", flush=True)

        if not permission_manager.request_camera_permission():
            print("[Update] Camera permission denied", flush=True)
            self.tts_speak("Camera permission denied. Update cancelled.")
            self.state = UpdateState.CANCELLED
            return False, None

        # Step 2: Initialize camera
        print("[Update] Initializing camera", flush=True)
        if not camera_manager.initialize():
            print("[Update] Camera initialization failed", flush=True)
            self.tts_speak("Camera initialization failed. Please try again later.")
            self.state = UpdateState.CANCELLED
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
            self.state = UpdateState.CANCELLED
            return False, None

        user_id, name, distance = recognition_result

        # Step 4: Confirm identity
        if not self.confirm_identity(name):
            # Identity not confirmed - error already spoken
            camera_manager.release()
            self.state = UpdateState.CANCELLED
            return False, None

        # Step 5: Fetch and present profile
        profile = self.fetch_and_present_profile(
            mcp_facade=mcp_facade,
            access_token=access_token,
            user_id=user_id
        )

        if profile is None:
            # Fetch failed - error already spoken
            camera_manager.release()
            self.state = UpdateState.CANCELLED
            return False, None

        # Step 6: Select what to update
        selection = self.select_update_fields()

        if selection is None:
            # Selection cancelled/failed
            camera_manager.release()
            self.state = UpdateState.CANCELLED
            return False, None

        # Step 7: Capture new information based on selection
        new_name = None
        new_metadata = None

        if selection in ["name", "both"]:
            new_name = self.capture_and_confirm_new_name()
            if new_name is None:
                camera_manager.release()
                self.state = UpdateState.CANCELLED
                return False, None

        if selection in ["metadata", "both"]:
            current_meta = profile.get("metadata", {})
            new_metadata = self.capture_and_confirm_new_metadata(current_meta)
            if new_metadata is None and selection == "metadata":
                # User cancelled metadata capture and only updating metadata
                camera_manager.release()
                self.state = UpdateState.CANCELLED
                return False, None

        # Step 8: Preview changes
        self.preview_changes(
            current_profile=profile,
            new_name=new_name,
            new_metadata=new_metadata
        )

        # Step 9: Get final confirmation
        if not self.get_final_confirmation():
            # Final confirmation not received
            camera_manager.release()
            self.state = UpdateState.CANCELLED
            return False, None

        # Step 10: Execute update
        success = self.execute_update(
            mcp_facade=mcp_facade,
            access_token=access_token,
            user_id=user_id,
            name=new_name,
            metadata=new_metadata
        )

        # Cleanup
        camera_manager.release()

        if success:
            return True, user_id
        else:
            return False, None

    def reset(self) -> None:
        """Reset orchestrator to idle state."""
        self.state = UpdateState.IDLE
        print("[Update] Orchestrator reset to idle", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"UpdateOrchestrator(state={self.state.value}, whisper={self.whisper})"
