"""
Permission module for handling user consent.

Provides voice-based permission requests for:
- Camera access
- User registration
- Data processing

Logs all permission decisions for audit purposes.
"""

import time
from typing import List, Dict, Any
from datetime import datetime


class PermissionManager:
    """
    Handles user permission requests and logging.
    
    Uses voice interaction to request and receive user consent
    before performing operations like camera capture or registration.
    """
    
    def __init__(self, speech_manager):
        """
        Initialize permission manager.
        
        Args:
            speech_manager: SpeechManager instance for voice interaction
        """
        self.speech = speech_manager
        self.permissions_log: List[Dict[str, Any]] = []
    
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
    
    def ask_permission(self, prompt: str, log_type: str = "general",
                       granted_message: str = None, denied_message: str = None) -> bool:
        """
        Ask a permission question, provide feedback, and log the response.

        This is the complete permission flow: asks the question, listens for response,
        checks for affirmative words, speaks appropriate feedback, and logs the decision.

        Args:
            prompt: The question to ask the user
            log_type: Type of permission for logging (default: "general")
            granted_message: Optional message to speak if permission granted
            denied_message: Optional message to speak if permission denied

        Returns:
            True if user gives affirmative response

        Example:
            granted = permission.ask_permission(
                "Can I take your photo?",
                "camera",
                granted_message="Great! Look at the camera.",
                denied_message="No problem."
            )
        """
        # Speak the prompt
        print(f"[Permission] Asking: '{prompt}'", flush=True)
        self.speech.speak(prompt)

        # Small delay to ensure TTS completes fully before listening
        time.sleep(0.3)

        # Listen for command using grammar-based recognition (more accurate)
        affirmative_commands = ["yes", "yeah", "sure", "okay", "ok", "yep", "yup"]
        negative_commands = ["no", "nope", "nah"]
        all_commands = affirmative_commands + negative_commands

        response = self.speech.listen_for_command(all_commands, timeout=5.0)

        if not response:
            print("[Permission] No valid response detected.", flush=True)
            self._log_permission(log_type, False, {"prompt": prompt, "response": "none"})
            if denied_message:
                self.speech.speak(denied_message)
            return False

        # Check if response is affirmative
        granted = response.lower() in [cmd.lower() for cmd in affirmative_commands]

        # Log the permission decision
        self._log_permission(log_type, granted, {"prompt": prompt, "response": response})

        # Speak appropriate feedback
        if granted and granted_message:
            self.speech.speak(granted_message)
        elif not granted and denied_message:
            self.speech.speak(denied_message)

        return granted
    
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
