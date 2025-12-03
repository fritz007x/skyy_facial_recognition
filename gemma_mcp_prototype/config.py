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
WAKE_WORD = "skyy recognize me"

# Alternative wake words that will also trigger recognition
WAKE_WORD_ALTERNATIVES = ["sky recognize me", "sky recognise me", "skyy recognise me"]

# Registration wake word
REGISTRATION_WAKE_WORD = "skyy remember me"

# Alternative registration wake words
REGISTRATION_WAKE_WORD_ALTERNATIVES = ["sky remember me", "sky remember me", "skyy remember me"]

# Deletion wake word
DELETION_WAKE_WORD = "skyy forget me"

# Alternative deletion wake words
DELETION_WAKE_WORD_ALTERNATIVES = ["sky forget me", "skyy delete me", "sky delete me"]

# Update wake word
UPDATE_WAKE_WORD = "skyy update me"

# Alternative update wake words
UPDATE_WAKE_WORD_ALTERNATIVES = [
    "sky update me",
    "skyy update my profile",
    "sky update my profile",
    "skyy change my information",
    "sky change my information"
]

# ============================================================================
# Voice Registration Configuration
# ============================================================================

# Whisper model for name transcription
# Options: "tiny", "base", "small", "medium", "large"
# "base" is a good balance of speed and accuracy for names
WHISPER_MODEL = "base"

# Whisper device (cpu or cuda)
WHISPER_DEVICE = "cpu"

# Whisper compute type
# Options: "float32", "float16", "int8"
# Use "float32" for CPU, "float16" for GPU
WHISPER_COMPUTE_TYPE = "float32"

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
# Reduced from 30 to 10 for faster startup on modern webcams
WARMUP_FRAMES = 10

# ============================================================================
# Speech Configuration
# ============================================================================

# Text-to-speech rate (words per minute)
SPEECH_RATE = 150

# Text-to-speech volume (0.0 to 1.0)
SPEECH_VOLUME = 1.0

# Energy threshold for wake word detection
# Lower = more sensitive (detects quieter speech)
# Higher = less sensitive (filters out background noise)
# Typical values: 50-100 (quiet), 100-200 (normal), 200-400 (noisy)
ENERGY_THRESHOLD = 100

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

# ============================================================================
# LLM Confirmation Parser Configuration
# ============================================================================

# Enable LLM-based confirmation parsing (uses Gemma 3 via Ollama)
# If disabled or Ollama is unavailable, falls back to rule-based keyword matching
ENABLE_LLM_CONFIRMATION = True

# Model to use for confirmation parsing
# Options: "gemma3:4b" (faster), "gemma3:12b" (better understanding)
# Recommendation: Use 4b for low-latency confirmations
LLM_CONFIRMATION_MODEL = "gemma3:4b"

# Timeout for LLM confirmation requests (seconds)
# Keep this low to avoid delays in voice flows
LLM_CONFIRMATION_TIMEOUT = 2.0

# Temperature for LLM confirmation parsing
# Lower = more deterministic, higher = more creative
# Recommendation: Keep low (0.1) for consistent yes/no parsing
LLM_CONFIRMATION_TEMPERATURE = 0.1

# Maximum tokens to generate for confirmation parsing
# We only need "YES", "NO", or "UNCLEAR", so keep this very low
LLM_CONFIRMATION_MAX_TOKENS = 10
