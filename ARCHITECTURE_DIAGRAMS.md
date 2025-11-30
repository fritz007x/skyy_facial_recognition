# Architecture Diagrams

This document provides visual representations of the architectural improvements.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Improvement #1: SyncMCPFacade](#improvement-1-syncmcpfacade)
3. [Improvement #2: SpeechManager Refactoring](#improvement-2-speechmanager-refactoring)
4. [Improvement #3: AudioDeviceManager](#improvement-3-audiodevicemanager)
5. [Complete Call Flow](#complete-call-flow)
6. [Class Diagrams](#class-diagrams)
7. [Sequence Diagrams](#sequence-diagrams)

---

## System Overview

### High-Level Architecture (After Refactoring)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Application Layer                              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              GemmaFacialRecognition                          │  │
│  │  (Main orchestrator - fully synchronous)                     │  │
│  │                                                              │  │
│  │  - OAuth token management                                    │  │
│  │  - Wake word detection loop                                  │  │
│  │  - Recognition workflow                                      │  │
│  │  - Registration workflow                                     │  │
│  │  - Gemma 3 greeting generation                              │  │
│  └──────────────┬────────────────┬─────────────┬────────────────┘  │
│                 │                │             │                    │
└─────────────────┼────────────────┼─────────────┼────────────────────┘
                  │                │             │
                  │                │             │
        ┌─────────▼──────┐  ┌──────▼──────┐  ┌──▼──────────────┐
        │ SpeechManager  │  │ SyncMCP     │  │ PermissionMgr   │
        │ (Orchestrator) │  │ Facade      │  │                 │
        └─────────┬──────┘  └──────┬──────┘  └─────────────────┘
                  │                │
                  │                │
┌─────────────────┴────────────────┴─────────────────────────────────┐
│                    Component Layer                                  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ AudioInput   │  │Transcription │  │ TextToSpeech │             │
│  │ Device       │  │ Engine       │  │ Engine       │             │
│  └──────┬───────┘  └──────────────┘  └──────────────┘             │
│         │                                                           │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Silence      │  │ WakeWord     │  │ AudioDevice  │             │
│  │ Detector     │  │ Detector     │  │ Manager      │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────┐          │
│  │              SkyyMCPClient (Async)                   │          │
│  │  - Face recognition tools                            │          │
│  │  - User registration                                 │          │
│  │  - Database operations                               │          │
│  └──────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                   Infrastructure Layer                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ sounddevice  │  │ faster-      │  │ pyttsx3      │             │
│  │ (mic/audio)  │  │ whisper      │  │ (TTS)        │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ MCP SDK      │  │ Ollama       │  │ OpenCV       │             │
│  │ (stdio)      │  │ (Gemma 3)    │  │ (camera)     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Improvement #1: SyncMCPFacade

### Architectural Pattern: Facade + Adapter

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Application Code                                │
│                  (Fully Synchronous)                                │
│                                                                      │
│  def handle_recognition(self):                                      │
│      result = self.mcp.recognize_face(...)  ← Synchronous call     │
│                                                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Clean synchronous interface
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      SyncMCPFacade                                  │
│                   (Facade Pattern)                                  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │               Public API (Synchronous)                        │ │
│  │                                                               │ │
│  │  def connect(self) -> bool:                                  │ │
│  │      self._client = SkyyMCPClient(...)                       │ │
│  │      return self._run_async(self._client.connect())          │ │
│  │                                                               │ │
│  │  def recognize_face(self, ...) -> dict:                      │ │
│  │      return self._run_async(                                 │ │
│  │          self._client.recognize_face(...)                    │ │
│  │      )                                                        │ │
│  │                                                               │ │
│  │  def disconnect(self) -> None:                               │ │
│  │      self._run_async(self._client.disconnect())              │ │
│  │      self._event_loop.close()                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Private Implementation                           │ │
│  │                                                               │ │
│  │  _event_loop: AbstractEventLoop  ← Persistent                │ │
│  │  _client: SkyyMCPClient          ← Async client              │ │
│  │                                                               │ │
│  │  def _run_async(self, coro):     ← Adapter method            │ │
│  │      return self._event_loop.run_until_complete(coro)        │ │
│  └───────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Delegates to async client
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    SkyyMCPClient                                    │
│                  (Async - Unchanged)                                │
│                                                                      │
│  async def connect(self) -> bool: ...                               │
│  async def recognize_face(self, ...) -> dict: ...                   │
│  async def register_user(self, ...) -> dict: ...                    │
│  async def disconnect(self) -> None: ...                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Decisions

1. **Persistent Event Loop**: Single event loop prevents AsyncExitStack teardown
2. **Context Manager Support**: Implements `__enter__`/`__exit__` for RAII
3. **Error Handling**: Graceful cleanup even if server process terminates
4. **Thread Safety**: One loop per instance (not shared across threads)

---

## Improvement #2: SpeechManager Refactoring

### Component Architecture

```
                          ┌─────────────────────────────┐
                          │   SpeechOrchestrator        │
                          │   (Facade/Coordinator)      │
                          │                             │
                          │  Responsibilities:          │
                          │  • Coordinate workflow      │
                          │  • Component lifecycle      │
                          │  • Backward compatibility   │
                          └──────────────┬──────────────┘
                                         │
                                         │ Delegates to components
                                         │
               ┌─────────────────────────┼─────────────────────────┐
               │                         │                         │
               │                         │                         │
  ┌────────────▼────────┐   ┌────────────▼────────┐   ┌───────────▼───────┐
  │  AudioInputDevice   │   │ TranscriptionEngine │   │ TextToSpeechEngine│
  │                     │   │                     │   │                   │
  │  • Microphone       │   │  • Whisper model    │   │  • pyttsx3 TTS    │
  │  • Recording        │   │  • Audio → Text     │   │  • Text → Audio   │
  │  • Energy calc      │   │  • Validation       │   │  • Voice config   │
  │  • Device info      │   │  • Preprocessing    │   │  • Rate/volume    │
  └──────┬──────────────┘   └─────────────────────┘   └───────────────────┘
         │
         │ Uses
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
  ┌──────────────┐   ┌─────────────┐
  │ Silence      │   │ WakeWord    │
  │ Detector     │   │ Detector    │
  │              │   │             │
  │ • Threshold  │   │ • Pattern   │
  │ • is_silence │   │ • Matching  │
  └──────────────┘   └─────────────┘
```

### Data Flow: Wake Word Detection

```
1. SpeechOrchestrator.listen_for_wake_word()
   │
   ├─► 2. AudioInputDevice.record(duration=5.0)
   │   │
   │   └─► sounddevice.rec() → numpy array
   │
   ├─► 3. AudioInputDevice.get_energy(audio)
   │   │
   │   └─► np.abs(audio).mean() → energy level
   │
   ├─► 4. SilenceDetector.is_silence(energy)
   │   │
   │   └─► energy < threshold → True/False
   │
   ├─► 5. TranscriptionEngine.transcribe(audio)
   │   │
   │   ├─► validate_audio() → (valid, error_msg)
   │   ├─► prepare_audio() → float32 array
   │   └─► WhisperModel.transcribe() → text
   │
   └─► 6. WakeWordDetector.contains_wake_word(text, wake_words)
       │
       └─► "hello gemma" in text.lower() → True/False
```

### Component Interfaces

```python
# AudioInputDevice Interface
class AudioInputDevice:
    def record(duration: float) -> np.ndarray
    def get_energy(audio: np.ndarray) -> float
    def validate() -> bool
    def get_device_info() -> dict

# TranscriptionEngine Interface
class TranscriptionEngine:
    def transcribe(audio: np.ndarray) -> str
    def validate_audio(audio: np.ndarray) -> (bool, str)
    def cleanup() -> None

# SilenceDetector Interface
class SilenceDetector:
    def is_silence(energy: float) -> bool
    def set_threshold(threshold: int) -> None

# WakeWordDetector Interface
class WakeWordDetector:
    def contains_wake_word(text: str, wake_words: List[str]) -> bool
    def find_wake_word(text: str, wake_words: List[str]) -> str

# TextToSpeechEngine Interface
class TextToSpeechEngine:
    def speak(text: str) -> None
    def set_voice(voice_id: str) -> None
    def set_rate(rate: int) -> None
    def set_volume(volume: float) -> None
    def cleanup() -> None
```

---

## Improvement #3: AudioDeviceManager

### State Machine Diagram

```
                     ┌──────────────┐
                     │     IDLE     │ ◄────┐
                     └──────┬───────┘      │
                            │              │
              ┌─────────────┼─────────────┐│
              │             │             ││
              │             │             ││
  acquire_for_recording()   │   acquire_for_playback()
              │             │             ││
              ▼             │             ▼│
      ┌───────────┐         │      ┌──────────┐
      │ RECORDING │         │      │ PLAYING  │
      └─────┬─────┘         │      └────┬─────┘
            │               │           │
            │ release()     │           │ release()
            └───────────────┴───────────┘

State Transition Rules:
1. Only IDLE can transition to RECORDING or PLAYING
2. RECORDING/PLAYING must return to IDLE before next operation
3. Transition delay enforced when moving from IDLE to active state
4. Last release time tracked for delay calculation
```

### Context Manager Flow

```
User Code:                     AudioDeviceManager:
─────────────                  ───────────────────

with mgr.acquire_for_recording():
│                              _transition_to(RECORDING)
│                              │
│                              ├─► Check current_state == IDLE
│                              │
│                              ├─► _wait_for_transition()
│                              │   │
│                              │   └─► elapsed = now - last_release_time
│                              │       if elapsed < transition_delay:
│                              │           sleep(remaining)
│                              │
│                              └─► current_state = RECORDING
│
│  # User code executes
│  audio = sd.rec(...)
│  sd.wait()
│
│ (exit context)               _release()
                               │
                               ├─► current_state = IDLE
                               └─► last_release_time = now()
```

### Integration with Speech Components

```
┌─────────────────────────────────────────────────────────────┐
│              SpeechOrchestrator                             │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │ listen_for_wake_word():                            │    │
│  │                                                     │    │
│  │   with audio_mgr.acquire_for_recording():          │    │
│  │       audio = audio_input.record(duration)         │    │
│  │                                                     │    │
│  │   # Automatic transition delay before next op      │    │
│  │                                                     │    │
│  │   transcription = transcription.transcribe(audio)  │    │
│  │                                                     │    │
│  │   if wake_word_detected:                           │    │
│  │       with audio_mgr.acquire_for_playback():       │    │
│  │           tts.speak("Hello!")                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Components:                                                │
│  ├─► audio_manager: AudioDeviceManager                     │
│  ├─► audio_input: AudioInputDevice                         │
│  ├─► transcription: TranscriptionEngine                    │
│  └─► tts: TextToSpeechEngine                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Call Flow

### Wake Word Detection → Recognition → Registration

```
User speaks "Hello Gemma"
│
▼
┌────────────────────────────────────────────────────────────────────┐
│ main_sync.py: GemmaFacialRecognition.run()                        │
│                                                                     │
│  while True:                                                       │
│      detected, text = speech.listen_for_wake_word(...)            │
│      │                                                             │
│      └─► SpeechOrchestrator.listen_for_wake_word()                │
│          │                                                         │
│          ├─► with audio_mgr.acquire_for_recording():              │
│          │       audio = audio_input.record(5.0)                  │
│          │                                                         │
│          ├─► energy = audio_input.get_energy(audio)               │
│          │                                                         │
│          ├─► if silence_detector.is_silence(energy):              │
│          │       continue  # Skip transcription                   │
│          │                                                         │
│          ├─► text = transcription.transcribe(audio)               │
│          │   │                                                     │
│          │   └─► WhisperModel.transcribe() → "Hello Gemma"        │
│          │                                                         │
│          └─► if wake_word_detector.contains_wake_word(text):      │
│                  return (True, "Hello Gemma")                     │
│                                                                     │
│  if detected:                                                      │
│      handle_recognition()                                          │
│      │                                                             │
│      └─► permission.request_camera_permission()                   │
│          │                                                         │
│          ├─► with audio_mgr.acquire_for_playback():               │
│          │       tts.speak("Can I take your photo?")              │
│          │                                                         │
│          ├─► with audio_mgr.acquire_for_recording():              │
│          │       response = audio_input.record(10.0)              │
│          │                                                         │
│          └─► if "yes" in transcription.transcribe(response):      │
│                  # Permission granted                             │
│                                                                     │
│      camera.capture_to_base64() → image_data                      │
│                                                                     │
│      result = mcp.recognize_face(token, image_data)               │
│      │                                                             │
│      └─► SyncMCPFacade.recognize_face()                          │
│          │                                                         │
│          └─► _run_async(client.recognize_face())                  │
│              │                                                     │
│              └─► SkyyMCPClient (async)                            │
│                  └─► MCP Server → InsightFace → result            │
│                                                                     │
│      if result["status"] == "not_recognized":                     │
│          handle_registration_offer()                              │
│          │                                                         │
│          ├─► speech.speak("What's your name?")                    │
│          │                                                         │
│          ├─► name = speech.listen_for_response()                  │
│          │                                                         │
│          └─► mcp.register_user(token, name, image_data)           │
│                                                                     │
│      greeting = generate_greeting(result)                         │
│      speech.speak(greeting)                                        │
└────────────────────────────────────────────────────────────────────┘
```

---

## Class Diagrams

### SyncMCPFacade Class Diagram

```
┌─────────────────────────────────────────┐
│         SyncMCPFacade                   │
├─────────────────────────────────────────┤
│ - python_path: Path                     │
│ - server_script: Path                   │
│ - _client: SkyyMCPClient                │
│ - _event_loop: AbstractEventLoop        │
│ - _connected: bool                      │
├─────────────────────────────────────────┤
│ + __init__(python_path, server_script) │
│ + connect() -> bool                     │
│ + disconnect() -> None                  │
│ + recognize_face(...) -> dict           │
│ + register_user(...) -> dict            │
│ + get_user_profile(...) -> dict         │
│ + list_users(...) -> dict               │
│ + __enter__() -> Self                   │
│ + __exit__(...) -> bool                 │
│ - _ensure_event_loop() -> EventLoop     │
│ - _run_async(coro) -> Any               │
│ - _ensure_connected() -> None           │
└─────────────────────────────────────────┘
               │ uses
               ▼
┌─────────────────────────────────────────┐
│         SkyyMCPClient                   │
├─────────────────────────────────────────┤
│ - session: ClientSession                │
│ - _connected: bool                      │
├─────────────────────────────────────────┤
│ + async connect() -> bool               │
│ + async disconnect() -> None            │
│ + async recognize_face(...) -> dict     │
│ + async register_user(...) -> dict      │
└─────────────────────────────────────────┘
```

### Speech Components Class Diagram

```
┌───────────────────────────────────────────────────────────┐
│              SpeechOrchestrator                           │
├───────────────────────────────────────────────────────────┤
│ - audio_input: AudioInputDevice                           │
│ - transcription: TranscriptionEngine                      │
│ - silence_detector: SilenceDetector                       │
│ - wake_word_detector: WakeWordDetector                    │
│ - tts: TextToSpeechEngine                                 │
├───────────────────────────────────────────────────────────┤
│ + __init__(rate, volume, whisper_model, device)          │
│ + listen_for_wake_word(...) -> (bool, str)               │
│ + listen_for_response(...) -> str                         │
│ + speak(text) -> None                                     │
│ + cleanup() -> None                                       │
└───────┬───────────┬───────────┬───────────┬───────────────┘
        │           │           │           │
        │ has-a     │ has-a     │ has-a     │ has-a
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│AudioInput   │ │Transcr   │ │Silence   │ │TextToSpeech  │
│Device       │ │Engine    │ │Detector  │ │Engine        │
└─────────────┘ └──────────┘ └──────────┘ └──────────────┘
        │
        │ uses
        ▼
┌─────────────┐
│WakeWord     │
│Detector     │
└─────────────┘
```

---

## Sequence Diagrams

### Sequence: Wake Word Detection

```
User    SpeechOrchestrator    AudioInput    Transcription    WakeWordDetector
 │              │                  │              │                  │
 │  speaks      │                  │              │                  │
 ├─────────────►│                  │              │                  │
 │              │ record(5.0)      │              │                  │
 │              ├─────────────────►│              │                  │
 │              │                  │ sd.rec()     │                  │
 │              │                  ├──────┐       │                  │
 │              │                  │      │       │                  │
 │              │                  │◄─────┘       │                  │
 │              │       audio      │              │                  │
 │              │◄─────────────────┤              │                  │
 │              │                  │              │                  │
 │              │ transcribe(audio)│              │                  │
 │              ├─────────────────────────────────►│                  │
 │              │                  │              │ whisper.transcribe()
 │              │                  │              ├──────┐           │
 │              │                  │              │      │           │
 │              │                  │              │◄─────┘           │
 │              │               "Hello Gemma"     │                  │
 │              │◄─────────────────────────────────┤                  │
 │              │                  │              │                  │
 │              │ contains_wake_word("Hello Gemma", ["hello gemma"])│
 │              ├───────────────────────────────────────────────────►│
 │              │                  │              │        True      │
 │              │◄───────────────────────────────────────────────────┤
 │              │                  │              │                  │
 │  (True, text)│                  │              │                  │
 │◄─────────────┤                  │              │                  │
```

### Sequence: Face Recognition with MCP Facade

```
App    SyncMCPFacade    EventLoop    SkyyMCPClient    MCP Server
 │            │              │              │              │
 │ recognize_face(...)       │              │              │
 ├───────────►│              │              │              │
 │            │ _run_async(  │              │              │
 │            │   client.recognize_face())  │              │
 │            ├─────────────►│              │              │
 │            │              │ run_until_complete(coro)    │
 │            │              ├──────┐       │              │
 │            │              │      │       │              │
 │            │              │      │ await recognize_face()
 │            │              │      ├──────────────────────►│
 │            │              │      │       │              │
 │            │              │      │       │ call_tool()  │
 │            │              │      │       ├─────────────►│
 │            │              │      │       │              │
 │            │              │      │       │   result     │
 │            │              │      │       │◄─────────────┤
 │            │              │      │  result              │
 │            │              │◄─────┤       │              │
 │            │         result      │       │              │
 │            │◄────────────────────┤       │              │
 │   result   │              │              │              │
 │◄───────────┤              │              │              │
```

---

## Summary

These architectural improvements deliver:

1. **SyncMCPFacade**: Clean synchronous interface, no async leaks
2. **Component-Based Speech**: Single Responsibility, high testability
3. **AudioDeviceManager**: Explicit state management, no magic delays

**Result**: Cleaner, more maintainable, testable code with zero breaking changes.
