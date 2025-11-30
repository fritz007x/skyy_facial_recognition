"""
Audio Device Manager - Explicit resource lifecycle management for audio devices.

Replaces hardcoded time.sleep() delays with explicit state management
for audio device transitions (recording ↔ playback).

Follows the State Machine pattern for resource management.
"""

import time
from enum import Enum
from contextlib import contextmanager
from typing import Generator


class AudioDeviceState(Enum):
    """Audio device states."""
    IDLE = "idle"
    RECORDING = "recording"
    PLAYING = "playing"


class AudioDeviceManager:
    """
    Manages audio device state transitions and resource acquisition.

    Provides explicit control over audio device lifecycle to prevent conflicts
    between recording (microphone) and playback (speakers/TTS) on Windows.

    Design Pattern: State Machine with Resource Management

    States:
        - IDLE: No active audio operations
        - RECORDING: Microphone is in use
        - PLAYING: Speakers/TTS is in use

    Transitions:
        IDLE -> RECORDING -> IDLE
        IDLE -> PLAYING -> IDLE
        (No direct RECORDING -> PLAYING transitions - must go through IDLE)

    Usage:
        manager = AudioDeviceManager(transition_delay=0.5)

        # Recording
        with manager.acquire_for_recording():
            audio = record_from_microphone()

        # Text-to-speech
        with manager.acquire_for_playback():
            speak_text("Hello")
    """

    def __init__(self, transition_delay: float = 0.5):
        """
        Initialize audio device manager.

        Args:
            transition_delay: Delay in seconds when transitioning between states
                             This allows the audio device to fully release before
                             the next operation (prevents device conflicts on Windows)
        """
        self._current_state = AudioDeviceState.IDLE
        self._transition_delay = transition_delay
        self._last_release_time: float = 0.0

        print(
            f"[AudioDeviceManager] Initialized (transition_delay={transition_delay}s)",
            flush=True
        )

    def _wait_for_transition(self) -> None:
        """
        Wait for the configured transition delay if needed.

        This ensures enough time has passed since the last release
        to prevent audio device conflicts.
        """
        if self._last_release_time > 0:
            elapsed = time.time() - self._last_release_time
            remaining = self._transition_delay - elapsed

            if remaining > 0:
                print(
                    f"[AudioDeviceManager] Waiting {remaining:.2f}s for device transition",
                    flush=True
                )
                time.sleep(remaining)

    def _transition_to(self, new_state: AudioDeviceState) -> None:
        """
        Transition to a new audio device state.

        Args:
            new_state: Target state to transition to

        Raises:
            RuntimeError: If transition is invalid
        """
        # Validate transition
        if self._current_state == new_state:
            print(
                f"[AudioDeviceManager] Already in state: {new_state.value}",
                flush=True
            )
            return

        if self._current_state != AudioDeviceState.IDLE:
            raise RuntimeError(
                f"Cannot transition from {self._current_state.value} to {new_state.value}. "
                f"Must release current resource first."
            )

        # Wait for transition delay if needed
        self._wait_for_transition()

        # Perform transition
        old_state = self._current_state
        self._current_state = new_state
        print(
            f"[AudioDeviceManager] State transition: {old_state.value} -> {new_state.value}",
            flush=True
        )

    def _release(self) -> None:
        """
        Release the current audio device resource.

        Transitions back to IDLE state and records the release time.
        """
        if self._current_state == AudioDeviceState.IDLE:
            return

        old_state = self._current_state
        self._current_state = AudioDeviceState.IDLE
        self._last_release_time = time.time()

        print(
            f"[AudioDeviceManager] Released: {old_state.value} -> idle",
            flush=True
        )

    @contextmanager
    def acquire_for_recording(self) -> Generator[None, None, None]:
        """
        Acquire audio device for recording (microphone input).

        Context manager that ensures proper state transitions.

        Yields:
            None

        Example:
            with manager.acquire_for_recording():
                audio = sd.rec(...)
                sd.wait()

        Raises:
            RuntimeError: If device is already in use
        """
        try:
            self._transition_to(AudioDeviceState.RECORDING)
            yield
        finally:
            self._release()

    @contextmanager
    def acquire_for_playback(self) -> Generator[None, None, None]:
        """
        Acquire audio device for playback (speakers/TTS output).

        Context manager that ensures proper state transitions.

        Yields:
            None

        Example:
            with manager.acquire_for_playback():
                engine.say(text)
                engine.runAndWait()

        Raises:
            RuntimeError: If device is already in use
        """
        try:
            self._transition_to(AudioDeviceState.PLAYING)
            yield
        finally:
            self._release()

    def get_state(self) -> AudioDeviceState:
        """
        Get the current audio device state.

        Returns:
            Current state (IDLE, RECORDING, or PLAYING)
        """
        return self._current_state

    def is_idle(self) -> bool:
        """
        Check if the audio device is idle.

        Returns:
            True if device is in IDLE state, False otherwise
        """
        return self._current_state == AudioDeviceState.IDLE

    def set_transition_delay(self, delay: float) -> None:
        """
        Update the transition delay.

        Args:
            delay: New delay in seconds (must be >= 0)
        """
        if delay < 0:
            raise ValueError("Transition delay must be non-negative")

        old_delay = self._transition_delay
        self._transition_delay = delay
        print(
            f"[AudioDeviceManager] Transition delay updated: {old_delay}s -> {delay}s",
            flush=True
        )

    def reset(self) -> None:
        """
        Force reset to IDLE state.

        Use this only in exceptional circumstances (e.g., error recovery).
        Normal code should use context managers which handle cleanup automatically.
        """
        print("[AudioDeviceManager] Force reset to IDLE", flush=True)
        self._current_state = AudioDeviceState.IDLE
        self._last_release_time = 0.0

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AudioDeviceManager(state={self._current_state.value}, "
            f"transition_delay={self._transition_delay}s)"
        )
