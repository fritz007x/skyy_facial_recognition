# Voice Pipeline Architecture Refactoring Guide

## Overview

This document outlines three critical architectural improvements to enhance maintainability, testability, and clean architecture principles in the voice-activated facial recognition system.

---

## Improvement 1: SyncMCPFacade Pattern

### Problem
`main_sync.py` uses `_run_async()` hack to bridge synchronous code with async MCP client, violating separation of concerns and making the code difficult to test.

### Solution Architecture

**Pattern**: Facade Pattern with Adapter Layer

```
┌─────────────────────────────────────────┐
│       main_sync.py (Synchronous)        │
│                                         │
│  - No asyncio imports                   │
│  - Clean synchronous API                │
└────────────────┬────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────┐
│       SyncMCPFacade (NEW)               │
│                                         │
│  + recognize_face(...)      : dict      │
│  + register_user(...)       : dict      │
│  + list_users(...)          : dict      │
│  + get_health_status(...)   : dict      │
│  + __enter__() / __exit__()             │
│                                         │
│  - _event_loop: AbstractEventLoop       │
│  - _run_async(coro)                     │
└────────────────┬────────────────────────┘
                 │
                 │ delegates to
                 ▼
┌─────────────────────────────────────────┐
│     SkyyMCPClient (Async - Unchanged)   │
│                                         │
│  async def connect()                    │
│  async def recognize_face(...)          │
│  async def register_user(...)           │
└─────────────────────────────────────────┘
```

### Key Design Decisions

1. **Persistent Event Loop**: Maintains single event loop throughout application lifecycle (prevents AsyncExitStack teardown)
2. **Context Manager Protocol**: Implements `__enter__`/`__exit__` for proper resource management
3. **Zero Breaking Changes**: Existing `main_sync.py` code remains fully compatible
4. **Thread-Safe**: Single event loop per instance prevents concurrency issues

---

## Improvement 2: SpeechManager Refactoring

### Problem
`SpeechManager` is a God Object (347 lines) violating Single Responsibility Principle. Mixes audio I/O, transcription, TTS, silence detection, and wake word logic.

### Solution Architecture

**Pattern**: Component-Based Architecture with Dependency Injection

```
                    ┌─────────────────────────┐
                    │   SpeechOrchestrator    │
                    │  (Facade/Coordinator)   │
                    │                         │
                    │  + listen_for_wake_word │
                    │  + listen_for_response  │
                    │  + speak                │
                    └───────────┬─────────────┘
                                │
                     ┌──────────┼──────────┐
                     │          │          │
        ┌────────────▼──┐  ┌────▼────────┐ │
        │ AudioInput    │  │ TextToSpeech│ │
        │ Device        │  │             │ │
        │               │  │ + speak()   │ │
        │ + record()    │  │ + set_voice │ │
        │ + get_energy  │  └─────────────┘ │
        └───────┬───────┘                  │
                │                          │
                │                          │
        ┌───────▼───────┐         ┌────────▼────────┐
        │ Silence       │         │ Transcription   │
        │ Detector      │         │ Engine          │
        │               │         │                 │
        │ + is_silence  │         │ + transcribe()  │
        └───────────────┘         └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │ WakeWord        │
                                  │ Detector        │
                                  │                 │
                                  │ + detect()      │
                                  └─────────────────┘
```

### Components

#### 1. AudioInputDevice
**Responsibility**: Audio capture and hardware interaction
**Interface**:
```python
class AudioInputDevice:
    def record(self, duration: float) -> np.ndarray
    def get_energy(self, audio: np.ndarray) -> float
    def validate() -> bool
    def get_device_info() -> dict
```

#### 2. TranscriptionEngine
**Responsibility**: Audio → Text conversion
**Interface**:
```python
class TranscriptionEngine:
    def transcribe(self, audio: np.ndarray) -> str
    def validate_audio(self, audio: np.ndarray) -> bool
    def cleanup() -> None
```

#### 3. SilenceDetector
**Responsibility**: Energy-based silence detection
**Interface**:
```python
class SilenceDetector:
    def is_silence(self, energy: float) -> bool
    def set_threshold(self, threshold: int) -> None
```

#### 4. WakeWordDetector
**Responsibility**: Wake word matching logic
**Interface**:
```python
class WakeWordDetector:
    def contains_wake_word(self, text: str, wake_words: List[str]) -> bool
```

#### 5. TextToSpeechEngine
**Responsibility**: Text → Audio synthesis
**Interface**:
```python
class TextToSpeechEngine:
    def speak(self, text: str) -> None
    def set_voice(self, voice_id: str) -> None
    def set_rate(self, rate: int) -> None
    def set_volume(self, volume: float) -> None
```

#### 6. SpeechOrchestrator
**Responsibility**: Coordinates components, maintains backward compatibility
**Interface**:
```python
class SpeechOrchestrator:
    # Backward compatible with existing SpeechManager API
    def listen_for_wake_word(...) -> Tuple[bool, str]
    def listen_for_response(...) -> str
    def speak(...) -> None
    def cleanup() -> None
```

### Migration Strategy

**Phase 1**: Create new components alongside existing `SpeechManager`
**Phase 2**: Create `SpeechOrchestrator` that delegates to components
**Phase 3**: Update `main_sync.py` to use `SpeechOrchestrator` (alias as `SpeechManager` for compatibility)
**Phase 4**: Remove old `SpeechManager` implementation

---

## Improvement 3: AudioDeviceManager

### Problem
Hardcoded `time.sleep()` delays for audio device conflicts (microphone ↔ TTS switching). No explicit resource lifecycle.

### Solution Architecture

**Pattern**: Resource Manager with State Machine

```
┌────────────────────────────────────────┐
│       AudioDeviceManager               │
│                                        │
│  States:                               │
│    - IDLE                              │
│    - RECORDING                         │
│    - PLAYING                           │
│                                        │
│  + acquire_for_recording() -> context  │
│  + acquire_for_playback()  -> context  │
│  + release()                           │
│                                        │
│  Private:                              │
│  - _current_state: State               │
│  - _transition_delay: float            │
│  - _last_release_time: float           │
└────────────────────────────────────────┘
```

### State Transitions

```
    IDLE ──acquire_for_recording──> RECORDING
     ▲                                  │
     │                                  │
     └─────────release()────────────────┘

    IDLE ──acquire_for_playback──> PLAYING
     ▲                                │
     │                                │
     └─────────release()──────────────┘

    RECORDING ─────────────┐
                           │ (transition delay)
    PLAYING ───────────────┴──> IDLE
```

### Usage Example

```python
# Before (hardcoded delays)
sd.wait()
time.sleep(0.5)  # Magic number!
self.engine.say(text)

# After (explicit resource management)
with audio_mgr.acquire_for_recording():
    audio = sd.rec(...)
    sd.wait()

with audio_mgr.acquire_for_playback():
    engine.say(text)
    engine.runAndWait()
```

---

## Integration Points

### Updated main_sync.py structure

```python
from modules.speech_orchestrator import SpeechOrchestrator as SpeechManager
from modules.mcp_sync_facade import SyncMCPFacade

class GemmaFacialRecognition:
    def __init__(self):
        self.speech = None
        self.mcp_facade = None  # Replaces mcp_client + _run_async

    def initialize(self):
        # Speech with new architecture (backward compatible API)
        self.speech = SpeechManager(...)

        # MCP with synchronous facade
        self.mcp_facade = SyncMCPFacade(
            python_path=MCP_PYTHON_PATH,
            server_script=MCP_SERVER_SCRIPT
        )
        self.mcp_facade.connect()  # No await!

    def handle_recognition(self):
        # Synchronous calls - no _run_async needed
        result = self.mcp_facade.recognize_face(
            access_token=self.access_token,
            image_data=image_base64
        )

    def cleanup(self):
        self.mcp_facade.disconnect()  # No await!
```

---

## Testing Strategy

### Unit Tests

**SpeechOrchestrator Components**:
- Test each component in isolation with mocks
- `AudioInputDevice`: Mock `sounddevice.rec()`
- `TranscriptionEngine`: Mock `WhisperModel.transcribe()`
- `TextToSpeechEngine`: Mock `pyttsx3.Engine`

**SyncMCPFacade**:
- Mock `SkyyMCPClient` async methods
- Verify event loop creation/cleanup
- Test exception handling

**AudioDeviceManager**:
- Test state transitions
- Verify transition delays
- Test context manager protocol

### Integration Tests

- `test_speech_flow.py`: Full wake word → response flow
- `test_mcp_sync_facade.py`: Connect → call tool → disconnect
- `test_audio_device_manager.py`: Recording → TTS transitions

---

## Benefits Summary

### 1. SyncMCPFacade
- **Encapsulation**: Async complexity isolated in facade
- **Testability**: Easy to mock synchronous interface
- **Maintainability**: Clear separation of concerns
- **No Breaking Changes**: Drop-in replacement

### 2. SpeechManager Refactoring
- **Single Responsibility**: Each component has one job
- **Testability**: Mock individual components
- **Extensibility**: Easy to swap TTS/STT engines
- **Reusability**: Components can be used independently

### 3. AudioDeviceManager
- **Explicit Resource Control**: No magic delays
- **Debuggability**: Clear state machine logging
- **Reliability**: Proper transition handling
- **Platform Abstraction**: Can add OS-specific logic

---

## Implementation Order

1. **SyncMCPFacade** (1-2 hours)
   - Create `modules/mcp_sync_facade.py`
   - Update `main_sync.py` to use facade
   - Test with existing workflows

2. **SpeechManager Refactoring** (3-4 hours)
   - Create individual component files
   - Create `SpeechOrchestrator`
   - Run parallel with old `SpeechManager`
   - Switch after validation

3. **AudioDeviceManager** (2-3 hours)
   - Create `modules/audio_device_manager.py`
   - Integrate with `AudioInputDevice` and `TextToSpeechEngine`
   - Test state transitions

**Total Estimated Time**: 6-9 hours

---

## Backward Compatibility

All changes maintain 100% backward compatibility:

- `SpeechOrchestrator` can be imported as `SpeechManager`
- `SyncMCPFacade` has same method signatures as current `_run_async()` calls
- `permission.py` requires zero changes
- Existing tests continue to work

---

## Future Enhancements

1. **Pluggable STT Engines**: Easy to add Google Speech, Azure, etc.
2. **Audio Device Pooling**: Multiple audio streams
3. **Async Speech Pipeline**: For concurrent operations
4. **Metrics Collection**: Track component performance
5. **Circuit Breaker**: For Whisper/TTS failures

---

## References

- Clean Architecture by Robert C. Martin
- Domain-Driven Design by Eric Evans
- Gang of Four Design Patterns (Facade, Adapter, State)
