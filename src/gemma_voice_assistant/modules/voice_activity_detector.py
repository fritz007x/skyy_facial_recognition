"""
Voice Activity Detector - VAD-based speech recording with automatic start/end detection.

Uses webrtcvad for robust voice activity detection and sounddevice for audio capture.
Records speech automatically when detected and stops after silence period.
"""

import sounddevice as sd
import numpy as np
import webrtcvad
import time
import queue
import sys
from typing import Optional, Tuple

try:
    import noisereduce as nr
    HAVE_NOISEREDUCE = True
except ImportError:
    HAVE_NOISEREDUCE = False


class VoiceActivityDetector:
    """
    VAD-based audio recorder with automatic speech detection.

    Records audio when speech is detected and automatically stops after
    a configurable silence duration. Optionally applies noise reduction.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        vad_mode: int = 3,
        frame_duration_ms: int = 30,
        silence_duration_sec: float = 1.0,
        min_speech_sec: float = 0.4,
        timeout_sec: float = 15.0
    ):
        """
        Initialize Voice Activity Detector.

        Args:
            sample_rate: Audio sample rate (8000, 16000, 32000, or 48000)
            channels: Number of audio channels (1 for mono)
            vad_mode: WebRTC VAD aggressiveness (0-3, 3 is most aggressive)
            frame_duration_ms: VAD frame duration (10, 20, or 30 ms)
            silence_duration_sec: Stop recording after this much silence
            min_speech_sec: Minimum speech duration to accept
            timeout_sec: Maximum recording duration (safety timeout)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.vad_mode = vad_mode
        self.frame_duration_ms = frame_duration_ms
        self.silence_duration_sec = silence_duration_sec
        self.min_speech_sec = min_speech_sec
        self.timeout_sec = timeout_sec

        # Initialize VAD
        self.vad = webrtcvad.Vad(vad_mode)

        # Calculate frame size
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)

    def _frame_generator(self, frames):
        """
        Generate fixed-size frames for VAD from numpy arrays.

        Args:
            frames: List of numpy int16 arrays

        Yields:
            Fixed-size byte frames for VAD
        """
        if not frames:
            return

        # Concatenate all frames
        data = np.concatenate(frames, axis=0).reshape(-1)
        data_bytes = data.tobytes()

        # Yield fixed-size frames
        frame_bytes = self.frame_size * 2  # 2 bytes per int16 sample
        i = 0
        while i + frame_bytes <= len(data_bytes):
            yield data_bytes[i:i + frame_bytes]
            i += frame_bytes

    def _is_speech_frame(self, frame_bytes: bytes) -> bool:
        """
        Check if frame contains speech.

        Args:
            frame_bytes: Audio frame as bytes

        Returns:
            True if speech detected, False otherwise
        """
        try:
            return self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception:
            return False

    def _apply_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction if available.

        Args:
            audio: Float32 audio array (-1.0 to 1.0)

        Returns:
            Noise-reduced audio (or original if noisereduce unavailable)
        """
        if not HAVE_NOISEREDUCE:
            return audio

        try:
            # Use first 0.25s as noise sample if available
            noise_duration = int(0.25 * self.sample_rate)
            if audio.size > noise_duration * 2:
                noise_clip = audio[:noise_duration]
                reduced = nr.reduce_noise(y=audio, y_noise=noise_clip, sr=self.sample_rate)
                return reduced
        except Exception as e:
            print(f"[VAD] Noise reduction failed: {e}", flush=True)

        return audio

    def record_speech(self, prompt_text: Optional[str] = None, beep: bool = True) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Record speech with automatic start/end detection.

        Args:
            prompt_text: Optional text to print before recording
            beep: Whether to print "Beep!" before recording

        Returns:
            Tuple of (success, audio_array)
            - success: True if valid speech captured, False otherwise
            - audio_array: Float32 numpy array (mono, -1.0 to 1.0) or None
        """
        if prompt_text:
            print(f"[VAD] {prompt_text}", flush=True)

        if beep:
            print("Beep!", flush=True)
            time.sleep(0.25)

        # Queue for audio chunks
        q = queue.Queue()

        def callback(indata, frames, time_info, status):
            """Audio callback - called for each audio block."""
            if status:
                print(f"[VAD] Audio status: {status}", file=sys.stderr, flush=True)
            q.put(indata.copy())

        # Start audio stream
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                blocksize=self.frame_size,
                callback=callback
            ):
                print("[VAD] Listening (speak now)...", flush=True)

                # Recording state
                pre_speech_buffers = []
                speech_started = False
                speech_buffers = []
                silence_start_time = None
                start_time = time.time()

                while True:
                    # Get audio chunk with timeout
                    try:
                        chunk = q.get(timeout=5.0)
                    except queue.Empty:
                        continue

                    if not speech_started:
                        # Build pre-speech buffer
                        pre_speech_buffers.append(chunk)

                        # Limit pre-speech buffer to ~2 seconds
                        if sum(b.shape[0] for b in pre_speech_buffers) > self.sample_rate * 2:
                            pre_speech_buffers.pop(0)

                        # Check for speech in recent frames (~1 second)
                        recent_frame_count = int(1.0 / (self.frame_duration_ms / 1000))
                        recent = pre_speech_buffers[-recent_frame_count:]

                        has_speech = False
                        for frame_bytes in self._frame_generator(recent):
                            if self._is_speech_frame(frame_bytes):
                                has_speech = True
                                break

                        if has_speech:
                            # Speech detected - start recording
                            speech_started = True
                            print("[VAD] Speech started", flush=True)
                            speech_buffers.extend(pre_speech_buffers)
                            pre_speech_buffers = []
                            silence_start_time = None
                    else:
                        # Already recording - append chunk
                        speech_buffers.append(chunk)

                        # Check if chunk contains speech
                        recent_frames = list(self._frame_generator([chunk]))
                        any_speech = any(self._is_speech_frame(fb) for fb in recent_frames)

                        if any_speech:
                            # Reset silence timer
                            silence_start_time = None
                        else:
                            # Start/continue silence timer
                            if silence_start_time is None:
                                silence_start_time = time.time()

                            elapsed_silence = time.time() - silence_start_time
                            if elapsed_silence >= self.silence_duration_sec:
                                # Silence detected - stop recording
                                print("[VAD] End of speech detected (silence)", flush=True)
                                break

                    # Safety timeout
                    if time.time() - start_time > self.timeout_sec:
                        print("[VAD] Recording timeout reached", flush=True)
                        break

        except Exception as e:
            print(f"[VAD] Recording error: {e}", flush=True)
            return False, None

        # Check if we captured any speech
        if len(speech_buffers) == 0:
            print("[VAD] No speech captured", flush=True)
            return False, None

        # Convert to float32 array
        int16_arr = np.concatenate(speech_buffers, axis=0).reshape(-1)
        speech_duration = int16_arr.shape[0] / self.sample_rate
        print(f"[VAD] Captured {speech_duration:.2f}s of audio", flush=True)

        # Check minimum duration
        if speech_duration < self.min_speech_sec:
            print("[VAD] Speech too short", flush=True)
            return False, None

        # Convert to float32 (-1.0 to 1.0)
        float_audio = int16_arr.astype(np.float32) / 32768.0

        # Apply noise reduction if available
        float_audio = self._apply_noise_reduction(float_audio)

        return True, float_audio.astype(np.float32)
