"""
Text-to-Speech Engine Module - Component for speech synthesis.

Handles text-to-speech using pyttsx3.
Part of the refactored speech architecture following Single Responsibility Principle.
"""

import pyttsx3
from typing import Optional, List, Dict, Any


class TextToSpeechEngine:
    """
    Handles text-to-speech synthesis.

    Responsibilities:
    - Initialize and manage TTS engine
    - Speak text aloud
    - Configure voice, rate, and volume

    Does NOT handle:
    - Audio capture (handled by AudioInputDevice)
    - Transcription (handled by TranscriptionEngine)
    - Wake word detection (handled by WakeWordDetector)
    """

    def __init__(self, rate: int = 150, volume: float = 1.0):
        """
        Initialize text-to-speech engine.

        Args:
            rate: Speech rate in words per minute (default 150)
            volume: Speech volume from 0.0 to 1.0 (default 1.0)
        """
        self.engine = pyttsx3.init()
        self.set_rate(rate)
        self.set_volume(volume)
        print("[TTS] Text-to-speech engine initialized.", flush=True)

    def speak(self, text: str) -> None:
        """
        Speak the given text aloud.

        Args:
            text: Text to speak
        """
        if not text:
            return

        print(f"[TTS] Speaking: '{text}'", flush=True)
        self.engine.say(text)
        self.engine.runAndWait()

    def set_voice(self, voice_id: Optional[str] = None) -> None:
        """
        Set the TTS voice.

        Args:
            voice_id: Voice ID to use. If None, lists available voices.
        """
        voices = self.engine.getProperty('voices')

        if voice_id is None:
            print("[TTS] Available voices:", flush=True)
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})", flush=True)
            return

        for voice in voices:
            if voice_id in voice.id:
                self.engine.setProperty('voice', voice.id)
                print(f"[TTS] Voice set to: {voice.name}", flush=True)
                return

        print(f"[TTS] Voice not found: {voice_id}", flush=True)

    def set_rate(self, rate: int) -> None:
        """
        Set speech rate.

        Args:
            rate: Words per minute (typical range: 100-200)
        """
        self.engine.setProperty('rate', rate)
        print(f"[TTS] Rate set to: {rate} WPM", flush=True)

    def set_volume(self, volume: float) -> None:
        """
        Set speech volume.

        Args:
            volume: Volume level from 0.0 to 1.0
        """
        volume = max(0.0, min(1.0, volume))
        self.engine.setProperty('volume', volume)
        print(f"[TTS] Volume set to: {volume}", flush=True)

    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice information dictionaries
        """
        voices = self.engine.getProperty('voices')
        return [
            {
                'id': voice.id,
                'name': voice.name,
                'languages': voice.languages,
                'gender': getattr(voice, 'gender', None),
                'age': getattr(voice, 'age', None)
            }
            for voice in voices
        ]

    def cleanup(self) -> None:
        """
        Release TTS engine resources.

        Call this method when done with the TextToSpeechEngine.
        """
        print("[TTS] Releasing resources...", flush=True)
        if hasattr(self, 'engine') and self.engine is not None:
            try:
                self.engine.stop()
            except:
                pass  # Ignore errors during cleanup
            self.engine = None
        print("[TTS] Resources released.", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        rate = self.engine.getProperty('rate') if self.engine else 'N/A'
        volume = self.engine.getProperty('volume') if self.engine else 'N/A'
        return f"TextToSpeechEngine(rate={rate}, volume={volume})"
