"""
Speech Orchestrator Module - Facade coordinating speech components.

Coordinates all speech-related components to provide a unified interface.
Maintains backward compatibility with the original SpeechManager API.

Part of the refactored speech architecture following Single Responsibility Principle.
"""

import time
from typing import Optional, Tuple, List

from .audio_input_device import AudioInputDevice
from .transcription_engine import TranscriptionEngine
from .silence_detector import SilenceDetector
from .wake_word_detector import WakeWordDetector
from .text_to_speech_engine import TextToSpeechEngine


class SpeechOrchestrator:
    """
    Facade that coordinates speech components.

    Maintains 100% backward compatibility with original SpeechManager API.
    Delegates to specialized components following Single Responsibility Principle.

    Components:
    - AudioInputDevice: Microphone recording
    - TranscriptionEngine: Speech-to-text with Whisper
    - SilenceDetector: Energy-based silence detection
    - WakeWordDetector: Wake word matching
    - TextToSpeechEngine: Text-to-speech synthesis
    """

    def __init__(
        self,
        rate: int = 150,
        volume: float = 1.0,
        model_path: Optional[str] = None
    ):
        """
        Initialize speech orchestrator with all components.

        Args:
            rate: Speech rate in words per minute (default 150)
            volume: Speech volume from 0.0 to 1.0 (default 1.0)
            model_path: Path to Vosk model (default: auto-detect)
        """
        print("[SpeechOrchestrator] Initializing components...", flush=True)

        # Audio I/O settings
        self.sample_rate = 16000  # Vosk expects 16kHz
        self.channels = 1  # Mono audio

        # Initialize components
        self.audio_input = AudioInputDevice(
            sample_rate=self.sample_rate,
            channels=self.channels
        )

        self.transcription = TranscriptionEngine(
            model_path=model_path,
            sample_rate=self.sample_rate
        )

        self.silence_detector = SilenceDetector(threshold=100)

        self.wake_word_detector = WakeWordDetector()

        self.tts = TextToSpeechEngine(rate=rate, volume=volume)

        print("[SpeechOrchestrator] All components initialized.", flush=True)

    def listen_for_wake_word(
        self,
        wake_words: List[str],
        timeout: Optional[float] = None,
        listen_duration: float = 5.0,
        energy_threshold: int = 100
    ) -> Tuple[bool, str]:
        """
        Listen continuously for wake word activation.

        BACKWARD COMPATIBLE with original SpeechManager API.

        Args:
            wake_words: List of acceptable wake phrases (e.g., ["skyy recognize me", "sky recognize me"])
            timeout: Optional timeout in seconds. None = listen indefinitely
            listen_duration: Duration to record audio for each listening attempt (default 5.0s)
            energy_threshold: Minimum audio energy to trigger transcription (default 100)

        Returns:
            Tuple of (detected: bool, transcription: str)
        """
        # Update silence detector threshold
        self.silence_detector.set_threshold(energy_threshold)

        # Normalize wake words
        wake_words = [w.lower().strip() for w in wake_words]
        print(f"[SpeechOrchestrator] Waiting for wake words: {wake_words}", flush=True)

        start_time = time.time()

        while True:
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False, ""

            try:
                # Record audio
                print("[SpeechOrchestrator] Recording...", flush=True)
                audio = self.audio_input.record(listen_duration)

                # Check audio energy for silence
                audio_energy = self.audio_input.get_energy(audio)

                if self.silence_detector.is_silence(audio_energy):
                    print(
                        f"[SpeechOrchestrator] Silence detected "
                        f"(energy: {audio_energy:.0f} < {energy_threshold}), "
                        f"skipping transcription",
                        flush=True
                    )
                    time.sleep(0.1)
                    continue

                print(f"[SpeechOrchestrator] Audio energy: {audio_energy:.0f}, transcribing...", flush=True)

                # Transcribe audio with grammar (only recognize wake words)
                transcription = self.transcription.transcribe(audio, grammar=wake_words)

                if transcription:
                    print(f"[SpeechOrchestrator] Heard: '{transcription}'", flush=True)
                    # Wake word already validated by grammar
                    return True, transcription
                else:
                    print("[SpeechOrchestrator] No speech detected.", flush=True)

                # Small delay before next attempt
                time.sleep(0.1)

            except KeyboardInterrupt:
                return False, ""
            except Exception as e:
                print(f"[SpeechOrchestrator] Error during listening: {e}", flush=True)
                time.sleep(0.5)

        return False, ""

    def listen_for_response(
        self,
        timeout: float = 5.0,
        listen_duration: float = 10.0
    ) -> str:
        """
        Listen for a user response (e.g., name, confirmation).

        BACKWARD COMPATIBLE with original SpeechManager API.

        Args:
            timeout: How long to wait before starting recording (for compatibility)
            listen_duration: Duration to record audio (default 10.0s)

        Returns:
            Transcribed text or empty string if nothing understood
        """
        print("[SpeechOrchestrator] Waiting for response...", flush=True)

        try:
            # Record audio
            audio = self.audio_input.record(listen_duration)

            # Transcribe
            transcription = self.transcription.transcribe(audio)

            if transcription:
                print(f"[SpeechOrchestrator] Response: '{transcription}'", flush=True)
                return transcription
            else:
                print("[SpeechOrchestrator] No speech detected.", flush=True)
                return "[unintelligible]"

        except Exception as e:
            print(f"[SpeechOrchestrator] Error: {e}", flush=True)
            return ""

    def listen_for_command(
        self,
        commands: List[str],
        timeout: float = 5.0
    ) -> Optional[str]:
        """
        Listen for a specific command using grammar-based recognition.

        Args:
            commands: List of valid commands (e.g., ["yes", "no", "okay"])
            timeout: Timeout in seconds

        Returns:
            Recognized command or None if not detected
        """
        print(f"[SpeechOrchestrator] Waiting for command: {commands}", flush=True)

        try:
            # Record audio
            audio = self.audio_input.record(timeout)

            # Transcribe with grammar (only recognize commands)
            transcription = self.transcription.transcribe(audio, grammar=commands)

            if transcription:
                print(f"[SpeechOrchestrator] Command: '{transcription}'", flush=True)
                return transcription
            else:
                print("[SpeechOrchestrator] No command detected.", flush=True)
                return None

        except Exception as e:
            print(f"[SpeechOrchestrator] Error: {e}", flush=True)
            return None

    def speak(self, text: str, pre_delay: float = 0.5) -> None:
        """
        Speak the given text using text-to-speech.

        BACKWARD COMPATIBLE with original SpeechManager API.

        Args:
            text: Text to speak aloud
            pre_delay: Delay before speaking (allows audio device to switch modes)
        """
        if not text:
            return

        # Delay to prevent audio device conflicts
        if pre_delay > 0:
            time.sleep(pre_delay)

        self.tts.speak(text)

    # =========================================================================
    # Configuration methods (backward compatible)
    # =========================================================================

    def set_voice(self, voice_id: Optional[str] = None) -> None:
        """Set the TTS voice. Backward compatible."""
        self.tts.set_voice(voice_id)

    def set_rate(self, rate: int) -> None:
        """Set speech rate. Backward compatible."""
        self.tts.set_rate(rate)

    def set_volume(self, volume: float) -> None:
        """Set speech volume. Backward compatible."""
        self.tts.set_volume(volume)

    def cleanup(self) -> None:
        """
        Release all component resources.

        BACKWARD COMPATIBLE with original SpeechManager API.
        """
        print("[SpeechOrchestrator] Shutting down components...", flush=True)

        # Cleanup components that have cleanup methods
        if hasattr(self, 'transcription'):
            self.transcription.cleanup()

        if hasattr(self, 'tts'):
            self.tts.cleanup()

        print("[SpeechOrchestrator] All components shut down.", flush=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"SpeechOrchestrator(\n"
            f"  audio_input={self.audio_input},\n"
            f"  transcription={self.transcription},\n"
            f"  silence_detector={self.silence_detector},\n"
            f"  tts={self.tts}\n"
            f")"
        )


# Backward compatibility alias
# This allows existing code to use:
#   from modules.speech_orchestrator import SpeechManager
# Instead of:
#   from modules.speech_orchestrator import SpeechOrchestrator
SpeechManager = SpeechOrchestrator
