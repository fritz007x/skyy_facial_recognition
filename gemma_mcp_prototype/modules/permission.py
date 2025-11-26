"""
Permission module for handling user consent.

Provides voice-based permission requests for:
- Camera access
- User registration
- Data processing

Logs all permission decisions for audit purposes.
"""

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
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": permission_type,
            "granted": granted,
            "details": details or {}
        }
        self.permissions_log.append(log_entry)
        
        status = "GRANTED" if granted else "DENIED"
        print(f"[Permission] {permission_type}: {status}")
    
    def request_camera_permission(self) -> bool:
        """
        Request permission to use camera for face capture.
        
        Speaks the request and listens for affirmative response.
        
        Returns:
            True if user grants permission
        """
        granted = self.speech.ask_permission(
            "I'd like to take your photo to see if I recognize you. Is that okay?"
        )
        
        self._log_permission("camera_capture", granted)
        
        if granted:
            self.speech.speak("Great! Look at the camera.")
        else:
            self.speech.speak("No problem. Let me know if you change your mind.")
        
        return granted
    
    def request_registration_permission(self, name: str) -> bool:
        """
        Request permission to register a new user.
        
        Args:
            name: User's name to include in the request
            
        Returns:
            True if user grants permission
        """
        granted = self.speech.ask_permission(
            f"I don't recognize you yet. Would you like me to remember you, {name}?"
        )
        
        self._log_permission("registration", granted, {"name": name})
        
        if granted:
            self.speech.speak(f"Okay {name}, I'll remember you.")
        else:
            self.speech.speak("No problem. You can register anytime by saying 'Hello Gemma'.")
        
        return granted
    
    def request_deletion_permission(self, name: str) -> bool:
        """
        Request permission to delete user data.
        
        Args:
            name: User's name to include in the request
            
        Returns:
            True if user confirms deletion
        """
        granted = self.speech.ask_permission(
            f"Are you sure you want me to forget {name}? This cannot be undone."
        )
        
        self._log_permission("deletion", granted, {"name": name})
        
        if granted:
            self.speech.speak("Understood. I'll remove their information.")
        else:
            self.speech.speak("Okay, I'll keep the information.")
        
        return granted
    
    def request_update_permission(self, name: str, changes: str) -> bool:
        """
        Request permission to update user information.
        
        Args:
            name: User's name
            changes: Description of changes to be made
            
        Returns:
            True if user confirms update
        """
        granted = self.speech.ask_permission(
            f"I'll update the information for {name}. {changes} Is that correct?"
        )
        
        self._log_permission("update", granted, {"name": name, "changes": changes})
        
        return granted
    
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
