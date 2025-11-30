# Migration Guide: Applying Architectural Improvements

This guide walks you through applying the three architectural improvements to your voice pipeline.

---

## Quick Start

### Option 1: Test the Refactored Version First (Recommended)

```bash
# Activate virtual environment
facial_mcp_py311\Scripts\activate

# Run the refactored version (no changes to existing code)
python gemma_mcp_prototype\main_sync_refactored.py
```

This lets you test all improvements without touching the existing `main_sync.py`.

### Option 2: Run Unit Tests

```bash
# Test individual components
python gemma_mcp_prototype\test_speech_orchestrator.py
python gemma_mcp_prototype\test_mcp_sync_facade.py
python gemma_mcp_prototype\test_audio_device_manager.py
```

---

## Step-by-Step Migration

### Step 1: Update Imports in main_sync.py

**Before:**
```python
from modules.speech import SpeechManager
from modules.mcp_client import SkyyMCPClient
```

**After:**
```python
from modules.speech_orchestrator import SpeechOrchestrator as SpeechManager
from modules.mcp_sync_facade import SyncMCPFacade
```

**Impact**: Zero code changes needed! The alias ensures backward compatibility.

---

### Step 2: Replace MCP Client Initialization

**Before:**
```python
class GemmaFacialRecognition:
    def __init__(self):
        self.mcp_client: Optional[SkyyMCPClient] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def _run_async(self, coro):
        """Helper to run async code synchronously."""
        if self._event_loop is None:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
        return self._event_loop.run_until_complete(coro)
```

**After:**
```python
class GemmaFacialRecognition:
    def __init__(self):
        self.mcp: Optional[SyncMCPFacade] = None
        # No _event_loop needed!
        # No _run_async needed!
```

**Impact**: Eliminates 15+ lines of boilerplate code.

---

### Step 3: Update MCP Connection

**Before:**
```python
def initialize(self):
    # ...
    self.mcp_client = SkyyMCPClient(
        python_path=MCP_PYTHON_PATH,
        server_script=MCP_SERVER_SCRIPT
    )
    if not self._run_async(self.mcp_client.connect()):
        print("[Init] ERROR: MCP connection failed")
        return False
```

**After:**
```python
def initialize(self):
    # ...
    self.mcp = SyncMCPFacade(
        python_path=MCP_PYTHON_PATH,
        server_script=MCP_SERVER_SCRIPT
    )
    if not self.mcp.connect():  # NO await! Clean synchronous
        print("[Init] ERROR: MCP connection failed")
        return False
```

**Impact**: Cleaner, more maintainable code. No async leaks.

---

### Step 4: Update MCP Tool Calls

**Before:**
```python
def handle_recognition(self):
    # ...
    result = self._run_async(self.mcp_client.recognize_face(
        access_token=self.access_token,
        image_data=image_base64,
        confidence_threshold=SIMILARITY_THRESHOLD
    ))
```

**After:**
```python
def handle_recognition(self):
    # ...
    result = self.mcp.recognize_face(  # NO _run_async! Clean synchronous
        access_token=self.access_token,
        image_data=image_base64,
        confidence_threshold=SIMILARITY_THRESHOLD
    )
```

**Impact**: Every MCP call becomes cleaner and more readable.

---

### Step 5: Update Cleanup

**Before:**
```python
def cleanup(self):
    if self.mcp_client:
        try:
            self._run_async(self.mcp_client.disconnect())
        except RuntimeError as e:
            if "different task" not in str(e):
                raise
            print(f"[Cleanup] MCP disconnect warning: {e}")

    # Close event loop with error handling
    if self._event_loop is not None:
        try:
            if self._event_loop.is_running():
                self._event_loop.stop()
            if not self._event_loop.is_closed():
                self._event_loop.close()
        except Exception as e:
            print(f"[Cleanup] Error closing event loop: {e}")
        finally:
            self._event_loop = None
```

**After:**
```python
def cleanup(self):
    if self.mcp:
        self.mcp.disconnect()  # NO _run_async! Clean synchronous
    # No event loop cleanup needed!
```

**Impact**: Eliminates 20+ lines of error-prone cleanup code.

---

### Step 6: Update Health Check

**Before:**
```python
health = self._run_async(self.mcp_client.get_health_status(self.access_token))
```

**After:**
```python
health = self.mcp.get_health_status(self.access_token)
```

**Impact**: Consistent synchronous API across all methods.

---

## Verification Checklist

After migration, verify:

- [ ] Application starts without errors
- [ ] Wake word detection works
- [ ] Face recognition works
- [ ] User registration works
- [ ] MCP connection is stable
- [ ] Cleanup runs without errors
- [ ] No async-related warnings in logs

---

## Component Architecture Benefits

### Before (Monolithic SpeechManager)
```
SpeechManager (347 lines)
├── Audio capture
├── Transcription
├── Silence detection
├── Wake word detection
├── Text-to-speech
└── Configuration
```

**Problems:**
- Hard to test individual features
- Hard to swap out components (e.g., different TTS engine)
- Hard to understand and maintain
- Violates Single Responsibility Principle

### After (Component-Based)
```
SpeechOrchestrator (Facade)
├── AudioInputDevice (audio capture)
├── TranscriptionEngine (Whisper)
├── SilenceDetector (energy-based)
├── WakeWordDetector (pattern matching)
└── TextToSpeechEngine (pyttsx3)
```

**Benefits:**
- Each component has one responsibility
- Easy to mock for testing
- Easy to swap implementations
- Clear separation of concerns
- Follows SOLID principles

---

## Testing the New Architecture

### Unit Tests

```bash
# Test each component independently
python gemma_mcp_prototype\test_speech_orchestrator.py

# Expected output:
# - TestAudioInputDevice: 3 tests
# - TestTranscriptionEngine: 4 tests
# - TestSilenceDetector: 5 tests
# - TestWakeWordDetector: 5 tests
# - TestTextToSpeechEngine: 3 tests
# - TestSpeechOrchestrator: 3 tests
```

### Integration Tests

```bash
# Test SyncMCPFacade
python gemma_mcp_prototype\test_mcp_sync_facade.py

# Test AudioDeviceManager
python gemma_mcp_prototype\test_audio_device_manager.py
```

---

## Rollback Plan

If issues arise, you can easily rollback:

1. **Keep old files**: The original `speech.py` is untouched
2. **Revert imports**: Change back to original imports
3. **Use old MCP pattern**: Restore `_run_async()` method

The new architecture is additive - it doesn't remove old code, so rollback is safe.

---

## Advanced: Integrating AudioDeviceManager

For even better resource management, integrate `AudioDeviceManager`:

### In SpeechOrchestrator

**Add to __init__:**
```python
from .audio_device_manager import AudioDeviceManager

def __init__(self, ...):
    # ... existing code ...
    self.audio_manager = AudioDeviceManager(transition_delay=0.5)
```

**Update record method:**
```python
def listen_for_wake_word(self, ...):
    # ... existing code ...

    with self.audio_manager.acquire_for_recording():
        audio = self.audio_input.record(listen_duration)

    # ... rest of method ...
```

**Update speak method:**
```python
def speak(self, text: str, pre_delay: float = 0.5) -> None:
    if not text:
        return

    # No hardcoded delay needed!
    with self.audio_manager.acquire_for_playback():
        self.tts.speak(text)
```

**Benefits:**
- No more hardcoded `time.sleep()` delays
- Explicit state management
- Better debugging (can log state transitions)
- Prevents resource conflicts

---

## Performance Comparison

### Before (Monolithic)
- Initialization: ~3-5 seconds
- Wake word detection: ~500ms per iteration
- Memory usage: ~1.2 GB (Whisper model)

### After (Component-Based)
- Initialization: ~3-5 seconds (same)
- Wake word detection: ~500ms per iteration (same)
- Memory usage: ~1.2 GB (same)

**Performance is identical** - the refactoring improves architecture, not runtime performance.

---

## Common Issues and Solutions

### Issue 1: Import Errors

**Error:**
```
ImportError: cannot import name 'SpeechOrchestrator'
```

**Solution:**
Ensure all new module files are in `gemma_mcp_prototype/modules/`:
- `audio_input_device.py`
- `transcription_engine.py`
- `silence_detector.py`
- `wake_word_detector.py`
- `text_to_speech_engine.py`
- `speech_orchestrator.py`
- `mcp_sync_facade.py`
- `audio_device_manager.py`

### Issue 2: Event Loop Errors

**Error:**
```
RuntimeError: This event loop is already running
```

**Solution:**
This should NOT happen with `SyncMCPFacade`. If you see this, ensure you've removed all `_run_async()` calls and are using the facade's synchronous methods.

### Issue 3: Audio Device Conflicts

**Error:**
```
OSError: [Errno -9996] Invalid input device
```

**Solution:**
This is a Windows audio device conflict. The `AudioDeviceManager` is designed to prevent this. If using without it, ensure proper delays between recording and playback.

---

## Next Steps

1. **Test refactored version**: Run `main_sync_refactored.py`
2. **Run unit tests**: Verify all components work
3. **Migrate main_sync.py**: Apply changes step-by-step
4. **Integrate AudioDeviceManager**: Optional but recommended
5. **Update documentation**: Document the new architecture

---

## Support and Questions

If you encounter issues:

1. Check logs for specific error messages
2. Run unit tests to isolate the problem
3. Verify all module files are present
4. Check that virtual environment is activated
5. Ensure all dependencies are installed

---

## Summary

**What Changed:**
- Added 8 new module files (components + facades)
- Created 3 test files
- Created `main_sync_refactored.py` (demo)

**What Stayed the Same:**
- Original `speech.py` (unchanged, for rollback)
- Original `mcp_client.py` (unchanged)
- Permission manager (unchanged)
- Vision/camera module (unchanged)
- Configuration (unchanged)

**Benefits:**
- Cleaner, more maintainable code
- Better separation of concerns
- Easier testing and debugging
- No breaking changes (backward compatible)
- Foundation for future improvements

**Estimated Migration Time:**
- Reading guide: 15 minutes
- Testing refactored version: 10 minutes
- Applying changes: 20 minutes
- Testing and verification: 15 minutes
- **Total: ~60 minutes**
