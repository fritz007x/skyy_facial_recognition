"""
Whisper Transcription Engine - Free-form speech transcription using faster-whisper.

Provides lazy-loading Whisper model for accurate name transcription.
Uses faster-whisper for efficient CPU/GPU inference.
"""

import numpy as np
from typing import Optional

try:
    from faster_whisper import WhisperModel
    HAVE_FASTER_WHISPER = True
except ImportError:
    HAVE_FASTER_WHISPER = False
    print("[Whisper] WARNING: faster-whisper not installed. Voice registration will not work.")
    print("[Whisper] Install with: pip install faster-whisper")


class WhisperTranscriptionEngine:
    """
    Faster-whisper based transcription for free-form speech.

    Provides lazy-loading model initialization to avoid startup delay
    when not using voice registration features.
    """

    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "float32",
        language: str = "en"
    ):
        """
        Initialize Whisper Transcription Engine.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device for inference (cpu, cuda)
            compute_type: Computation precision (float32, float16, int8)
            language: Default language for transcription
        """
        if not HAVE_FASTER_WHISPER:
            raise ImportError(
                "faster-whisper is required for voice registration. "
                "Install with: pip install faster-whisper"
            )

        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language

        # Lazy loading - model initialized on first use
        self._model: Optional[WhisperModel] = None
        self._model_loaded = False

    def _ensure_model_loaded(self) -> None:
        """
        Load Whisper model if not already loaded (lazy initialization).

        Raises:
            RuntimeError: If model loading fails
        """
        if self._model_loaded:
            return

        print(f"[Whisper] Loading model: {self.model_name} on {self.device}...", flush=True)

        try:
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            self._model_loaded = True
            print("[Whisper] Model loaded successfully", flush=True)
        except Exception as e:
            print(f"[Whisper] ERROR: Failed to load model: {e}", flush=True)
            raise RuntimeError(f"Failed to load Whisper model: {e}")

    def transcribe(
        self,
        audio: np.ndarray,
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = False,
        grammar: Optional[list] = None
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Float32 numpy array (mono, -1.0 to 1.0)
            language: Language code (default: self.language)
            beam_size: Beam size for beam search (higher = more accurate, slower)
            vad_filter: Whether to use VAD filter in Whisper
            grammar: List of acceptable phrases (used by speech_orchestrator for wake word matching)

        Returns:
            Transcribed text string (stripped of whitespace)
        """
        # Ensure model is loaded
        self._ensure_model_loaded()

        if self._model is None:
            raise RuntimeError("Whisper model not loaded")

        # Use default language if not specified
        if language is None:
            language = self.language

        print("[Whisper] Transcribing audio...", flush=True)

        try:
            # Transcribe with faster-whisper
            segments, info = self._model.transcribe(
                audio,
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter
            )

            # Join all segments
            text = " ".join([seg.text.strip() for seg in segments]).strip()

            print(f"[Whisper] Transcription: '{text}'", flush=True)

            # Apply grammar filtering if provided (used by speech_orchestrator for wake word matching)
            if grammar:
                text_lower = text.lower().strip()
                # Check if any grammar phrase is in the transcription
                for phrase in grammar:
                    phrase_lower = phrase.lower().strip()
                    if phrase_lower in text_lower:
                        print(f"[Whisper] Grammar validation: '{text}' matches '{phrase}'", flush=True)
                        return text
                # No grammar match found
                print(f"[Whisper] Grammar validation failed: '{text}' does not match any of {grammar}", flush=True)
                return ""

            return text

        except Exception as e:
            print(f"[Whisper] ERROR: Transcription failed: {e}", flush=True)
            return ""

    def is_loaded(self) -> bool:
        """
        Check if model is loaded.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._model_loaded

    def unload(self) -> None:
        """
        Unload model to free memory.
        """
        if self._model is not None:
            print("[Whisper] Unloading model...", flush=True)
            del self._model
            self._model = None
            self._model_loaded = False
            print("[Whisper] Model unloaded", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "loaded" if self._model_loaded else "not loaded"
        return f"WhisperTranscriptionEngine(model={self.model_name}, device={self.device}, status={status})"
