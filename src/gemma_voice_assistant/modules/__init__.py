"""
Gemma Facial Recognition - Modules Package (Refactored Architecture)

Contains the core modules for the voice-activated facial recognition system:

Refactored Components:
- speech_orchestrator: Facade coordinating all speech components
- audio_input_device: Microphone recording with cleanup
- transcription_engine: Vosk-based STT with grammar support
- text_to_speech_engine: pyttsx3 wrapper
- wake_word_detector: Wake word validation
- silence_detector: Energy-based silence detection
- mcp_sync_facade: Synchronous MCP client wrapper

Shared Components:
- vision: Webcam capture utilities
- permission: User permission handling
"""

from .speech_orchestrator import SpeechOrchestrator
from .mcp_sync_facade import SyncMCPFacade
from .vision import WebcamManager
from .permission import PermissionManager

__all__ = [
    'SpeechOrchestrator',
    'SyncMCPFacade',
    'WebcamManager',
    'PermissionManager'
]
