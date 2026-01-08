"""
Audio Input Device Module - Component for audio capture.

Handles microphone access and audio recording operations.
Part of the refactored speech architecture following Single Responsibility Principle.
"""

import sounddevice as sd
import numpy as np
import time
from typing import Optional, Dict, Any


class AudioInputDevice:
    """
    Manages microphone input and audio capture.

    Responsibilities:
    - Validate audio input device availability
    - Record audio from microphone
    - Calculate audio energy levels
    - Provide device information

    Does NOT handle:
    - Transcription (handled by TranscriptionEngine)
    - Silence detection (handled by SilenceDetector)
    - Wake word logic (handled by WakeWordDetector)
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        Initialize audio input device.

        Args:
            sample_rate: Audio sample rate in Hz (default 16000 for Whisper)
            channels: Number of audio channels (1=mono, 2=stereo, default 1)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._device_info: Optional[Dict[str, Any]] = None

        # Validate device on initialization
        self._validate_device()

    def _validate_device(self) -> None:
        """
        Validate that an audio input device is available.

        Raises:
            RuntimeError: If no audio input device is found
        """
        try:
            device = sd.query_devices(kind='input')
            if device is None:
                raise RuntimeError("No audio input device available")
            self._device_info = device
            print(f"[AudioInput] Device validated: {device['name']}", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize audio device: {e}")

    def record(self, duration: float) -> np.ndarray:
        """
        Record audio from the microphone.

        Args:
            duration: Recording duration in seconds

        Returns:
            Recorded audio as numpy array (dtype=int16)

        Raises:
            RuntimeError: If recording fails
        """
        try:
            num_samples = int(duration * self.sample_rate)
            audio = sd.rec(
                num_samples,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to complete

            # Give audio device time to fully release (Windows DirectSound/WASAPI)
            time.sleep(0.3)  # 300ms cleanup delay for audio subsystem

            return audio
        except Exception as e:
            raise RuntimeError(f"Audio recording failed: {e}")

    def get_energy(self, audio: np.ndarray) -> float:
        """
        Calculate the energy level of audio data.

        Energy is calculated as the mean absolute amplitude.

        Args:
            audio: Audio data as numpy array

        Returns:
            Average energy level (0.0 for silence, higher for louder audio)
        """
        if audio is None or audio.size == 0:
            return 0.0

        return float(np.abs(audio).mean())

    def validate(self) -> bool:
        """
        Check if the audio device is still valid and accessible.

        Returns:
            True if device is accessible, False otherwise
        """
        try:
            device = sd.query_devices(kind='input')
            return device is not None
        except Exception:
            return False

    def get_device_info(self) -> Dict[str, Any]:
        """
        Get information about the current audio input device.

        Returns:
            Dictionary containing device information (name, channels, sample rate, etc.)
        """
        if self._device_info is None:
            self._validate_device()
        return dict(self._device_info) if self._device_info else {}

    def __repr__(self) -> str:
        """String representation for debugging."""
        device_name = self._device_info.get('name', 'Unknown') if self._device_info else 'Unknown'
        return f"AudioInputDevice(device='{device_name}', sr={self.sample_rate}, channels={self.channels})"
