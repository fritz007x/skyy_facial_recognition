"""
Speech module for voice recognition and text-to-speech using Vosk.

Uses:
- Vosk library with grammar for accurate wake word and command detection
- sounddevice for microphone audio capture
- pyttsx3 for local text-to-speech
"""

import sounddevice as sd
import numpy as np
import pyttsx3
import time
import json
from pathlib import Path
from typing import Optional, Tuple, List
from vosk import Model, KaldiRecognizer


class SpeechManager:
    """
    Handles voice recognition and speech synthesis using Vosk.

    Features:
    - Grammar-based wake word detection (fast, accurate)
    - Grammar-based command recognition (yes/no responses)
    - Full model for general speech (names, etc.)
    - Local text-to-speech (no cloud required)
    """

    def __init__(self,
                 rate: int = 150,
                 volume: float = 1.0,
                 model_path: str = None):
        """
        Initialize speech manager.

        Args:
            rate: Speech rate in words per minute (default 150)
            volume: Speech volume from 0.0 to 1.0 (default 1.0)
            model_path: Path to Vosk model directory (default: auto-detect)
        """
        # Initialize text-to-speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)

        # Validate audio input device
        print("[Microphone] Validating audio input device...", flush=True)
        try:
            input_device = sd.query_devices(kind='input')
            if input_device is None:
                raise RuntimeError("No audio input device available")
            print(f"[Microphone] Using input device: {input_device['name']}", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize audio device: {e}")

        # Initialize Vosk model
        if model_path is None:
            # Auto-detect model in project directory
            project_root = Path(__file__).parent.parent.parent
            model_path = project_root / "vosk-model-small-en-us-0.15"

        if not Path(model_path).exists():
            raise RuntimeError(f"Vosk model not found at: {model_path}")

        print(f"[Microphone] Loading Vosk model from: {model_path}", flush=True)
        self.model = Model(str(model_path))
        print("[Microphone] Vosk model loaded successfully.", flush=True)

        # Audio capture settings
        self.sample_rate = 16000  # Vosk expects 16kHz audio
        self.channels = 1  # Mono audio

    def listen_for_wake_word(
        self,
        wake_words: List[str],
        timeout: Optional[float] = None,
        listen_duration: float = 5.0,
        energy_threshold: int = 100
    ) -> Tuple[bool, str]:
        """
        Listen for wake word using grammar-based recognition.

        Args:
            wake_words: List of acceptable wake phrases (e.g., ["hello gemma", "hey gemma"])
            timeout: Optional timeout in seconds. None = listen indefinitely
            listen_duration: Duration to record audio for each listening attempt (default 5.0s)
            energy_threshold: Minimum audio energy to trigger transcription (default 100)

        Returns:
            Tuple of (detected: bool, transcription: str)
        """
        # Create grammar for wake words
        grammar = {
            "grammar": wake_words
        }
        grammar_json = json.dumps(grammar)

        # Create recognizer with grammar
        recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar_json)
        recognizer.SetMaxAlternatives(0)
        recognizer.SetWords(False)

        print(f"[Listen] Waiting for wake words: {wake_words}", flush=True)

        start_time = time.time()

        while True:
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False, ""

            try:
                # Record audio from microphone
                print("[Listen] Recording...", flush=True)
                audio = sd.rec(
                    int(listen_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='int16'
                )
                sd.wait()  # Wait for recording to complete

                # Give audio device time to fully release (Windows DirectSound/WASAPI)
                time.sleep(0.3)  # 300ms cleanup delay for audio subsystem

                # Energy-based silence detection to save CPU
                audio_energy = np.abs(audio).mean()

                if audio_energy < energy_threshold:
                    print(f"[Listen] Silence detected (energy: {audio_energy:.0f} < {energy_threshold}), skipping transcription", flush=True)
                    time.sleep(0.1)
                    continue

                print(f"[Listen] Audio energy: {audio_energy:.0f}, transcribing...", flush=True)

                # Convert audio to bytes for Vosk
                audio_bytes = (audio * 32767).astype(np.int16).tobytes()

                # Process with Vosk
                if recognizer.AcceptWaveform(audio_bytes):
                    result = json.loads(recognizer.Result())
                else:
                    result = json.loads(recognizer.FinalResult())

                transcription = result.get("text", "").strip()

                if transcription:
                    print(f"[Recognition] Heard: '{transcription}'", flush=True)
                    # Wake word detected by grammar
                    return True, transcription
                else:
                    print("[Recognition] No speech detected.", flush=True)

                # Small delay before next listening attempt
                time.sleep(0.1)

                # Reset recognizer for next attempt
                recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar_json)
                recognizer.SetMaxAlternatives(0)
                recognizer.SetWords(False)

            except KeyboardInterrupt:
                return False, ""
            except Exception as e:
                print(f"[Recognition] Error during listening: {e}", flush=True)
                time.sleep(0.5)  # Brief pause before retry

        return False, ""

    def listen_for_response(self, timeout: float = 5.0, listen_duration: float = 10.0) -> str:
        """
        Listen for a user response using full model (for general speech like names).

        Args:
            listen_duration: Duration to record audio (default 10.0s for longer responses)

        Returns:
            Transcribed text or empty string if nothing understood
        """
        print("[Listen] Waiting for response...", flush=True)

        try:
            # Create recognizer without grammar (full model)
            recognizer = KaldiRecognizer(self.model, self.sample_rate)
            recognizer.SetWords(True)

            # Record audio from microphone
            audio = sd.rec(
                int(listen_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to complete

            # Give audio device time to fully release (Windows DirectSound/WASAPI)
            time.sleep(0.3)  # 300ms cleanup delay for audio subsystem

            # Convert audio to bytes for Vosk
            audio_bytes = (audio * 32767).astype(np.int16).tobytes()

            # Process with Vosk
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.FinalResult())

            transcription = result.get("text", "").strip()

            if transcription:
                print(f"[Recognition] Response: '{transcription}'", flush=True)
                return transcription
            else:
                print("[Recognition] No speech detected.", flush=True)
                return "[unintelligible]"

        except Exception as e:
            print(f"[Recognition] Error: {e}", flush=True)
            return ""

    def listen_for_command(self, commands: List[str], timeout: float = 5.0) -> Optional[str]:
        """
        Listen for a specific command using grammar-based recognition.

        Args:
            commands: List of valid commands (e.g., ["yes", "no", "okay"])
            timeout: Timeout in seconds

        Returns:
            Recognized command or None if not detected
        """
        print(f"[Listen] Waiting for command: {commands}", flush=True)

        try:
            # Create grammar for commands
            grammar = {
                "grammar": commands
            }
            grammar_json = json.dumps(grammar)

            # Create recognizer with grammar
            recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar_json)
            recognizer.SetMaxAlternatives(0)
            recognizer.SetWords(False)

            # Record audio from microphone
            audio = sd.rec(
                int(timeout * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to complete

            # Give audio device time to fully release (Windows DirectSound/WASAPI)
            time.sleep(0.3)  # 300ms cleanup delay for audio subsystem

            # Convert audio to bytes for Vosk
            audio_bytes = (audio * 32767).astype(np.int16).tobytes()

            # Process with Vosk
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.FinalResult())

            transcription = result.get("text", "").strip()

            if transcription:
                print(f"[Recognition] Command: '{transcription}'", flush=True)
                return transcription
            else:
                print("[Recognition] No command detected.", flush=True)
                return None

        except Exception as e:
            print(f"[Recognition] Error: {e}", flush=True)
            return None

    def speak(self, text: str, pre_delay: float = 0.5) -> None:
        """
        Speak the given text using text-to-speech.

        Args:
            text: Text to speak aloud
            pre_delay: Delay before speaking (allows audio device to switch from recording to playback)
        """
        if not text:
            return

        # Small delay to allow microphone to fully release before TTS
        # This prevents audio device conflicts on Windows
        if pre_delay > 0:
            time.sleep(pre_delay)

        print(f"[Speech] Speaking: '{text}'", flush=True)
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
            print("[Config] Available voices:")
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})")
            return

        for voice in voices:
            if voice_id in voice.id:
                self.engine.setProperty('voice', voice.id)
                print(f"[Config] Voice set to: {voice.name}")
                return

        print(f"[Config] Voice not found: {voice_id}")

    def set_rate(self, rate: int) -> None:
        """
        Set speech rate.

        Args:
            rate: Words per minute (typical range: 100-200)
        """
        self.engine.setProperty('rate', rate)
        print(f"[Config] Rate set to: {rate} WPM")

    def set_volume(self, volume: float) -> None:
        """
        Set speech volume.

        Args:
            volume: Volume level from 0.0 to 1.0
        """
        volume = max(0.0, min(1.0, volume))
        self.engine.setProperty('volume', volume)
        print(f"[Config] Volume set to: {volume}")

    def cleanup(self) -> None:
        """
        Release Vosk model and TTS engine resources.

        Call this method when done with the SpeechManager to free up memory.
        """
        print("[Cleanup] Releasing speech resources...", flush=True)

        # Release Vosk model
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            self.model = None

        # Release TTS engine
        if hasattr(self, 'engine') and self.engine is not None:
            try:
                self.engine.stop()
            except:
                pass  # Ignore errors during cleanup
            self.engine = None

        print("[Cleanup] Speech resources released.", flush=True)
