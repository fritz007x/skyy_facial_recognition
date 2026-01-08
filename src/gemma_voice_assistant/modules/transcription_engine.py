"""
Transcription Engine Module - Component for speech-to-text using Vosk.

Handles audio transcription with optional grammar support.
Part of the refactored speech architecture following Single Responsibility Principle.
"""

import json
import numpy as np
from pathlib import Path
from typing import Optional, List
from vosk import Model, KaldiRecognizer


class TranscriptionEngine:
    """
    Manages speech-to-text transcription using Vosk.

    Responsibilities:
    - Load and manage Vosk model
    - Transcribe audio with or without grammar constraints
    - Provide confidence scores
    - Validate audio data before transcription

    Does NOT handle:
    - Audio capture (handled by AudioInputDevice)
    - Silence detection (handled by SilenceDetector)
    - Wake word logic (handled by WakeWordDetector)
    """

    def __init__(self, model_path: Optional[str] = None, sample_rate: int = 16000):
        """
        Initialize transcription engine with Vosk model.

        Args:
            model_path: Path to Vosk model directory (default: auto-detect)
            sample_rate: Audio sample rate in Hz (default 16000)
        """
        self.sample_rate = sample_rate

        # Auto-detect model path if not provided
        if model_path is None:
            project_root = Path(__file__).parent.parent.parent
            model_path = project_root / "vosk-model-small-en-us-0.15"

        if not Path(model_path).exists():
            raise RuntimeError(f"Vosk model not found at: {model_path}")

        print(f"[Transcription] Loading Vosk model from: {model_path}", flush=True)
        self.model = Model(str(model_path))
        self.model_path = str(model_path)
        print("[Transcription] Vosk model loaded successfully.", flush=True)

    def validate_audio(self, audio: np.ndarray) -> tuple[bool, str]:
        """
        Validate audio data before transcription.

        Args:
            audio: Audio data as numpy array

        Returns:
            Tuple of (is_valid: bool, error_message: str)
            If valid, error_message is empty string
        """
        # Check for None or empty
        if audio is None or audio.size == 0:
            return False, "Empty audio data"

        # Check for invalid values (NaN or Inf)
        if np.any(np.isnan(audio)) or np.any(np.isinf(audio)):
            return False, "Audio contains invalid values (NaN or Inf)"

        # Check minimum length (0.1 seconds)
        min_samples = int(0.1 * self.sample_rate)
        if audio.size < min_samples:
            return False, f"Audio too short ({audio.size} < {min_samples} samples)"

        return True, ""

    def _prepare_audio(self, audio: np.ndarray) -> bytes:
        """
        Prepare audio data for Vosk (convert to int16 bytes).

        Args:
            audio: Raw audio data (int16 or float32)

        Returns:
            Audio data as int16 bytes
        """
        # Convert to int16 if needed
        if audio.dtype != np.int16:
            # Assume float32 in range [-1, 1], convert to int16
            audio_int16 = (audio * 32767).astype(np.int16)
        else:
            audio_int16 = audio

        # Flatten to 1D if stereo
        if len(audio_int16.shape) > 1:
            audio_int16 = audio_int16.flatten()

        return audio_int16.tobytes()

    def transcribe(self, audio: np.ndarray, grammar: Optional[List[str]] = None) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (int16 or float32)
            grammar: Optional list of valid phrases for constrained recognition

        Returns:
            Transcribed text or empty string if nothing detected

        Example:
            # Full model (general speech)
            text = engine.transcribe(audio)

            # With grammar (specific commands)
            text = engine.transcribe(audio, grammar=["yes", "no", "okay"])
        """
        # Validate audio
        is_valid, error_msg = self.validate_audio(audio)
        if not is_valid:
            print(f"[Transcription] {error_msg}", flush=True)
            return ""

        try:
            # Prepare audio
            audio_bytes = self._prepare_audio(audio)

            # Create recognizer with or without grammar
            if grammar:
                # Vosk expects a direct JSON array, NOT {"grammar": [...]}
                # Correct format: ["skyy recognize me", "sky recognize me"]
                # Incorrect format: {"grammar": ["skyy recognize me", "sky recognize me"]}
                grammar_json = json.dumps(grammar)
                recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar_json)
                recognizer.SetMaxAlternatives(0)
                recognizer.SetWords(False)
            else:
                recognizer = KaldiRecognizer(self.model, self.sample_rate)
                recognizer.SetWords(True)

            # Process audio
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.FinalResult())

            # Extract text
            text = result.get("text", "").strip()
            return text

        except Exception as e:
            print(f"[Transcription] Error: {e}", flush=True)
            return ""

    def transcribe_with_confidence(
        self,
        audio: np.ndarray,
        grammar: Optional[List[str]] = None
    ) -> tuple[str, float]:
        """
        Transcribe audio and return text with confidence score.

        Args:
            audio: Audio data as numpy array (int16 or float32)
            grammar: Optional list of valid phrases

        Returns:
            Tuple of (text, confidence) where confidence is 0.0-1.0
        """
        # Validate audio
        is_valid, error_msg = self.validate_audio(audio)
        if not is_valid:
            print(f"[Transcription] {error_msg}", flush=True)
            return "", 0.0

        try:
            # Prepare audio
            audio_bytes = self._prepare_audio(audio)

            # Create recognizer
            if grammar:
                # Vosk expects a direct JSON array, NOT {"grammar": [...]}
                grammar_json = json.dumps(grammar)
                recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar_json)
            else:
                recognizer = KaldiRecognizer(self.model, self.sample_rate)

            # Process audio
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.FinalResult())

            # Extract text and confidence
            text = result.get("text", "").strip()
            confidence = result.get("confidence", 0.0)

            return text, confidence

        except Exception as e:
            print(f"[Transcription] Error: {e}", flush=True)
            return "", 0.0

    def validate(self) -> bool:
        """
        Check if the transcription engine is ready.

        Returns:
            True if model is loaded and ready
        """
        return hasattr(self, 'model') and self.model is not None

    def cleanup(self) -> None:
        """
        Release model resources.

        Call this when done to free memory.
        """
        print("[Transcription] Releasing model resources...", flush=True)
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            self.model = None
        print("[Transcription] Resources released.", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "ready" if self.validate() else "not initialized"
        return f"TranscriptionEngine(model='vosk', sr={self.sample_rate}, status='{status}')"
