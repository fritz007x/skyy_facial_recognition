"""
Configuration constants for Gemma Facial Recognition prototype.

These settings should be adjusted to match your local environment.
"""

import platform
from pathlib import Path

# ============================================================================
# Project Paths
# ============================================================================

# Get the project root directory (parent of this config file's directory)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Python interpreter in the virtual environment
# Cross-platform compatible: Windows uses Scripts/, Linux/Mac use bin/
VENV_NAME = "facial_mcp_py311"

if platform.system() == "Windows":
    MCP_PYTHON_PATH = PROJECT_ROOT / VENV_NAME / "Scripts" / "python.exe"
else:  # Linux, macOS, etc.
    MCP_PYTHON_PATH = PROJECT_ROOT / VENV_NAME / "bin" / "python"

# MCP Server script path
MCP_SERVER_SCRIPT = PROJECT_ROOT / "src" / "skyy_facial_recognition_mcp.py"

# ============================================================================
# Ollama / Gemma Configuration
# ============================================================================

# Ollama model to use for greeting generation
# Options: "gemma3:4b" (faster), "gemma3:12b" (better reasoning)
OLLAMA_MODEL = "gemma3:4b"

# Ollama host (default local installation)
OLLAMA_HOST = "http://localhost:11434"

# ============================================================================
# Voice Trigger Configuration
# ============================================================================

# Primary wake word
WAKE_WORD = "hello gemma"

# Alternative wake words that will also trigger recognition
WAKE_WORD_ALTERNATIVES = ["hey gemma", "hi gemma", "gemma"]

# ============================================================================
# Camera Configuration
# ============================================================================

# Camera device index (0 is usually the default webcam)
CAMERA_INDEX = 0

# Capture resolution
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480

# Number of frames to skip for camera warmup
# This helps ensure consistent image quality
WARMUP_FRAMES = 30

# ============================================================================
# Speech Configuration
# ============================================================================

# Text-to-speech rate (words per minute)
SPEECH_RATE = 150

# Text-to-speech volume (0.0 to 1.0)
SPEECH_VOLUME = 1.0

# ============================================================================
# Recognition Thresholds
# ============================================================================

# Similarity threshold for face recognition
# This is the DISTANCE threshold (lower = stricter matching)
# - < 0.20: Very strong match (same person)
# - 0.20-0.25: Strong match (likely same person)  
# - 0.25-0.40: Weak match (possibly same person)
# - > 0.40: No match (different people)
SIMILARITY_THRESHOLD = 0.25

# Minimum confidence for face detection
MIN_DETECTION_CONFIDENCE = 0.5
