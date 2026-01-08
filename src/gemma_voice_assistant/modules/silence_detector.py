"""
Silence Detector Module - Component for audio silence detection.

Detects silence based on audio energy thresholds.
Part of the refactored speech architecture following Single Responsibility Principle.
"""


class SilenceDetector:
    """
    Detects silence in audio based on energy threshold.

    Responsibilities:
    - Determine if audio energy indicates silence
    - Manage energy threshold configuration

    Does NOT handle:
    - Audio capture (handled by AudioInputDevice)
    - Energy calculation (handled by AudioInputDevice)
    - Transcription (handled by TranscriptionEngine)
    """

    def __init__(self, threshold: int = 100):
        """
        Initialize silence detector.

        Args:
            threshold: Energy threshold below which audio is considered silence
                      Lower = more sensitive (detects quieter speech)
                      Higher = less sensitive (filters out background noise)
                      Typical values: 50-100 (quiet), 100-200 (normal), 200-400 (noisy)
        """
        self.threshold = threshold
        print(f"[SilenceDetector] Initialized with threshold: {threshold}", flush=True)

    def is_silence(self, energy: float) -> bool:
        """
        Determine if the given energy level indicates silence.

        Args:
            energy: Audio energy level (from AudioInputDevice.get_energy())

        Returns:
            True if energy is below threshold (silence), False otherwise
        """
        return energy < self.threshold

    def set_threshold(self, threshold: int) -> None:
        """
        Update the silence detection threshold.

        Args:
            threshold: New energy threshold value
        """
        old_threshold = self.threshold
        self.threshold = threshold
        print(f"[SilenceDetector] Threshold updated: {old_threshold} -> {threshold}", flush=True)

    def get_threshold(self) -> int:
        """
        Get the current silence detection threshold.

        Returns:
            Current threshold value
        """
        return self.threshold

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"SilenceDetector(threshold={self.threshold})"
