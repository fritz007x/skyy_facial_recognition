"""
Permission module for handling user consent.

Provides voice-based permission requests for:
- Camera access
- User registration
- Data processing

Uses Gemma 3 LLM for natural language confirmation parsing.
Logs all permission decisions for audit purposes.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from .voice_activity_detector import VoiceActivityDetector
from .whisper_transcription_engine import WhisperTranscriptionEngine
from .llm_confirmation_parser import LLMConfirmationParser


class PermissionManager:
    """
    Handles user permission requests and logging.

    Uses voice interaction with Gemma 3 LLM for natural language
    confirmation parsing before performing operations like camera
    capture or registration.

    Features:
    - Voice Activity Detection (VAD) for automatic speech detection
    - Whisper AI for accurate speech-to-text transcription
    - Gemma 3 LLM for understanding natural yes/no responses
    - Graceful fallback to rule-based parsing if LLM unavailable
    """

    def __init__(
        self,
        speech_manager,
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
        Initialize permission manager with LLM-based confirmation parsing.

        Args:
            speech_manager: SpeechManager instance for voice interaction
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
        self.speech = speech_manager
        self.permissions_log: List[Dict[str, Any]] = []

        # Initialize Voice Activity Detector for automatic speech detection
        self.vad = VoiceActivityDetector(
            sample_rate=16000,
            vad_mode=3,
            silence_duration_sec=1.0,
            min_speech_sec=0.4,
            timeout_sec=10.0
        )

        # Initialize Whisper for accurate transcription
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
    
    def _log_permission(self, permission_type: str, granted: bool, details: Dict[str, Any] = None) -> None:
        """
        Log a permission decision.

        Args:
            permission_type: Type of permission requested
            granted: Whether permission was granted
            details: Additional details about the request
        """
        # Implement log rotation to prevent unbounded memory growth
        # Keep only the last 1000 entries
        if len(self.permissions_log) >= 1000:
            self.permissions_log = self.permissions_log[-900:]

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": permission_type,
            "granted": granted,
            "details": details or {}
        }
        self.permissions_log.append(log_entry)
        
        status = "GRANTED" if granted else "DENIED"
        print(f"[Permission] {permission_type}: {status}")
    
    def ask_permission(
        self,
        prompt: str,
        log_type: str = "general",
        granted_message: Optional[str] = None,
        denied_message: Optional[str] = None
    ) -> bool:
        """
        Ask a permission question with natural language understanding.

        This flow uses Gemma 3 LLM for understanding natural yes/no responses:
        1. Speak the permission prompt
        2. Use VAD to automatically detect when user starts/stops speaking
        3. Transcribe response with Whisper AI
        4. Parse with Gemma 3 LLM for semantic understanding
        5. Gracefully fallback to rule-based parsing if LLM unavailable

        Args:
            prompt: The question to ask the user
            log_type: Type of permission for logging (default: "general")
            granted_message: Optional message to speak if permission granted
            denied_message: Optional message to speak if permission denied

        Returns:
            True if user gives affirmative response (including natural variations)

        Example:
            granted = permission.ask_permission(
                "Can I take your photo?",
                "camera",
                granted_message="Great! Look at the camera.",
                denied_message="No problem."
            )

        Natural responses understood:
            Affirmative: "Yes", "Sure", "Go ahead", "Absolutely", "I'm good with that"
            Negative: "No", "Not really", "Maybe not", "I'd rather not"
        """
        # Speak the permission prompt
        print(f"[Permission] Asking: '{prompt}'", flush=True)
        self.speech.speak(prompt)

        # Small delay to ensure TTS completes fully before listening
        time.sleep(0.3)

        # Use VAD to record response (automatic speech detection)
        print("[Permission] Listening for response...", flush=True)
        success, audio = self.vad.record_speech(beep=False)

        if not success or audio is None:
            print("[Permission] No response detected.", flush=True)
            self._log_permission(
                log_type,
                False,
                {"prompt": prompt, "response": "none", "error": "no_audio"}
            )
            if denied_message:
                self.speech.speak(denied_message)
            return False

        # Transcribe response with Whisper
        print("[Permission] Transcribing response...", flush=True)
        response_text = self.whisper.transcribe(audio, beam_size=5)
        print(f"[Permission] Response transcribed: '{response_text}'", flush=True)

        # Parse with LLM for natural language understanding
        confirmed = self.llm_parser.parse_confirmation(response_text, question_context=prompt)

        # Log the permission decision
        self._log_permission(
            log_type,
            confirmed is True,
            {"prompt": prompt, "response": response_text, "parsed": confirmed}
        )

        # Speak appropriate feedback
        if confirmed is True and granted_message:
            self.speech.speak(granted_message)
        elif confirmed is False and denied_message:
            self.speech.speak(denied_message)
        elif confirmed is None:
            # Unclear response - default to denied for safety
            print("[Permission] Unclear response, defaulting to denied.", flush=True)
            if denied_message:
                self.speech.speak(denied_message)

        return confirmed is True
    
    def request_camera_permission(self) -> bool:
        """
        Request permission to use camera for face capture.

        Returns:
            True if user grants permission
        """
        return self.ask_permission(
            "I'd like to take your photo to see if I recognize you. Is that okay?",
            log_type="camera_capture",
            granted_message="Great! Look at the camera.",
            denied_message="No problem. Let me know if you change your mind."
        )
    
    def request_registration_permission(self, name: str) -> bool:
        """
        Request permission to register a new user.

        Args:
            name: User's name to include in the request

        Returns:
            True if user grants permission
        """
        return self.ask_permission(
            f"I don't recognize you yet. Would you like me to remember you, {name}?",
            log_type="registration",
            granted_message=f"Okay {name}, I'll remember you.",
            denied_message="No problem. You can register anytime by saying 'Hello Gemma'."
        )
    
    def request_deletion_permission(self, name: str) -> bool:
        """
        Request permission to delete user data.

        Args:
            name: User's name to include in the request

        Returns:
            True if user confirms deletion
        """
        return self.ask_permission(
            f"Are you sure you want me to forget {name}? This cannot be undone.",
            log_type="deletion",
            granted_message="Understood. I'll remove their information.",
            denied_message="Okay, I'll keep the information."
        )

    def request_update_permission(self, name: str, changes: str) -> bool:
        """
        Request permission to update user information.

        Args:
            name: User's name
            changes: Description of changes to be made

        Returns:
            True if user confirms update
        """
        return self.ask_permission(
            f"I'll update the information for {name}. {changes} Is that correct?",
            log_type="update"
        )

    def get_permissions_log(self) -> List[Dict[str, Any]]:
        """
        Get all logged permissions.
        
        Returns:
            List of permission log entries
        """
        return self.permissions_log.copy()
    
    def clear_permissions_log(self) -> None:
        """Clear the permissions log."""
        self.permissions_log.clear()
        print("[Permission] Log cleared")
