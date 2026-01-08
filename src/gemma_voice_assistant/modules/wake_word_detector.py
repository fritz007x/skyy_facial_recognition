"""
Wake Word Detector Module - Component for wake word detection.

Detects wake words in transcribed text.
Part of the refactored speech architecture following Single Responsibility Principle.
"""

from typing import List


class WakeWordDetector:
    """
    Detects wake words in transcribed text.

    Responsibilities:
    - Match wake words against transcribed text
    - Handle case-insensitive matching
    - Support multiple wake word alternatives

    Does NOT handle:
    - Audio capture (handled by AudioInputDevice)
    - Transcription (handled by TranscriptionEngine)
    - Response listening (handled by SpeechOrchestrator)
    """

    def __init__(self):
        """Initialize wake word detector."""
        pass

    def contains_wake_word(self, text: str, wake_words: List[str]) -> bool:
        """
        Check if the text contains any of the specified wake words.

        Args:
            text: Transcribed text to check
            wake_words: List of wake words to match (case-insensitive)

        Returns:
            True if any wake word is found in the text, False otherwise

        Example:
            >>> detector = WakeWordDetector()
            >>> detector.contains_wake_word("Skyy, recognize me", ["skyy recognize me"])
            True
            >>> detector.contains_wake_word("Just talking", ["skyy recognize me"])
            False
        """
        if not text or not wake_words:
            return False

        # Normalize text to lowercase for case-insensitive matching
        text_lower = text.lower().strip()

        # Check each wake word
        for wake_word in wake_words:
            wake_word_lower = wake_word.lower().strip()
            if wake_word_lower in text_lower:
                return True

        return False

    def find_wake_word(self, text: str, wake_words: List[str]) -> str:
        """
        Find which wake word was detected in the text.

        Args:
            text: Transcribed text to check
            wake_words: List of wake words to match

        Returns:
            The first wake word found, or empty string if none found

        Example:
            >>> detector = WakeWordDetector()
            >>> detector.find_wake_word("Sky, recognize me!", ["skyy recognize me", "sky recognize me"])
            "sky recognize me"
        """
        if not text or not wake_words:
            return ""

        text_lower = text.lower().strip()

        for wake_word in wake_words:
            wake_word_lower = wake_word.lower().strip()
            if wake_word_lower in text_lower:
                return wake_word

        return ""

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "WakeWordDetector()"
