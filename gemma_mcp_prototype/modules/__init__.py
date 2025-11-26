"""
Gemma Facial Recognition - Modules Package

Contains the core modules for the voice-activated facial recognition system:
- speech: Voice recognition and text-to-speech
- vision: Webcam capture utilities
- mcp_client: MCP client wrapper for Skyy Facial Recognition server
- permission: User permission handling
"""

from .speech import SpeechManager
from .vision import WebcamManager
from .mcp_client import SkyyMCPClient
from .permission import PermissionManager

__all__ = [
    'SpeechManager',
    'WebcamManager', 
    'SkyyMCPClient',
    'PermissionManager'
]
