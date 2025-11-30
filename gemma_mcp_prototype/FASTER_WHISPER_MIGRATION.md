# Migration to faster-whisper

This document describes the migration from `speech_recognition` (Google Speech Recognition API) to `faster-whisper` for speech transcription.

## Summary of Changes

### Library Replacement
- **Removed**: `speech_recognition` library (cloud-based, requires internet)
- **Added**: `faster-whisper` library (local, offline, faster)

### Benefits

1. **Offline Operation**: No internet required - all processing is local
2. **Faster Performance**: Uses CTranslate2 optimized inference
3. **Better Accuracy**: OpenAI Whisper model is state-of-the-art
4. **No API Limits**: No rate limiting or quota restrictions
5. **Privacy**: Audio never leaves your machine

### Performance Comparison

| Metric | speech_recognition | faster-whisper |
|--------|-------------------|----------------|
| Internet Required | Yes | No |
| Average Latency | ~1-3 seconds | ~0.5-1.5 seconds |
| Accuracy | Good | Excellent |
| Privacy | Cloud processing | Local only |
| Cost | Free tier limited | Completely free |

## Technical Changes

### modules/speech.py

**Before** (speech_recognition):
```python
import speech_recognition as sr

class SpeechManager:
    def __init__(self, rate: int = 150, volume: float = 1.0):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self._calibrate_microphone()

    def listen_for_wake_word(self, wake_words: List[str], timeout: Optional[float] = None):
        with self.microphone as source:
            audio = self.recognizer.listen(source, timeout=timeout)
        transcription = self.recognizer.recognize_google(audio, operation_timeout=10).lower()
        # ... check for wake words ...
```

**After** (faster-whisper):
```python
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

class SpeechManager:
    def __init__(self,
                 rate: int = 150,
                 volume: float = 1.0,
                 whisper_model: str = "base",
                 device: str = "cpu",
                 compute_type: str = "int8"):
        self.engine = pyttsx3.init()
        self.whisper = WhisperModel(whisper_model, device=device, compute_type=compute_type)
        self.sample_rate = 16000
        self.channels = 1

    def listen_for_wake_word(self, wake_words: List[str], timeout: Optional[float] = None):
        audio = sd.rec(int(5.0 * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='int16')
        sd.wait()
        transcription = self._transcribe_audio(audio)
        # ... check for wake words ...

    def _transcribe_audio(self, audio_data: np.ndarray) -> str:
        audio_float = audio_data.astype(np.float32) / 32768.0
        segments, info = self.whisper.transcribe(audio_float, language="en", beam_size=1, vad_filter=True)
        return " ".join([segment.text.strip() for segment in segments])
```

### New Parameters

The `SpeechManager` now accepts additional configuration parameters:

- `whisper_model`: Model size - "tiny", "base", "small", "medium", "large"
  - **tiny**: ~39M params, fastest, less accurate
  - **base**: ~74M params, good balance (default)
  - **small**: ~244M params, better accuracy
  - **medium**: ~769M params, high accuracy
  - **large**: ~1550M params, best accuracy, slowest

- `device`: "cpu" or "cuda" (GPU acceleration if available)
- `compute_type`: "int8", "int16", "float16", "float32"
  - **int8**: Fastest, lowest memory (default for CPU)
  - **float16**: Good for GPU
  - **float32**: Highest quality, slowest

### Removed Methods

- `_calibrate_microphone()`: No longer needed (sounddevice handles this)
- `_force_release_audio_devices()`: No longer needed (sounddevice auto-releases)

### Changed Behavior

1. **Listen Duration**: Wake word listening now records in fixed chunks (default 5 seconds) instead of variable-length recording. This is more predictable and efficient.

2. **Response Listening**: Changed from adaptive listening to fixed 10-second recording window for user responses.

3. **Error Handling**: Simplified - no more `WaitTimeoutError`, `UnknownValueError`, or `RequestError` from speech_recognition.

## Installation

Update your requirements:

```bash
pip uninstall speech_recognition  # Remove old library
pip install faster-whisper        # Install new library
```

Or use the updated `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Model Download

On first run, faster-whisper will automatically download the selected model:

- **tiny**: ~75 MB
- **base**: ~145 MB (default)
- **small**: ~488 MB
- **medium**: ~1.5 GB
- **large**: ~3 GB

Models are cached in `~/.cache/huggingface/hub/` and only downloaded once.

## Configuration Examples

### Fast and Lightweight (embedded systems, low-end hardware)
```python
speech = SpeechManager(whisper_model="tiny", compute_type="int8")
```

### Balanced (default - recommended for most users)
```python
speech = SpeechManager(whisper_model="base", compute_type="int8")
```

### High Accuracy (powerful CPUs)
```python
speech = SpeechManager(whisper_model="small", compute_type="int16")
```

### GPU Acceleration (if CUDA available)
```python
speech = SpeechManager(whisper_model="base", device="cuda", compute_type="float16")
```

## Backward Compatibility

The public API remains the same:
- `listen_for_wake_word(wake_words, timeout)` - Same signature
- `listen_for_response(timeout)` - Same signature
- `speak(text, pre_delay)` - Same signature

**No changes needed in calling code** (main_sync.py, permission.py, etc.)

## Testing

Test the new implementation:

```bash
cd gemma_mcp_prototype
python test_speech_in_async.py
```

You should notice:
- No internet requirement
- Faster response times
- Better accuracy
- No calibration delay

## Troubleshooting

### Model Download Fails
```
Error: Connection timeout downloading model
```
**Solution**: Check your internet connection. Models are downloaded from Hugging Face Hub.

### Slow Performance
```
Transcription taking >5 seconds
```
**Solution**: Use a smaller model (tiny or base) or enable GPU acceleration if available.

### Import Error
```
ModuleNotFoundError: No module named 'faster_whisper'
```
**Solution**: Install faster-whisper: `pip install faster-whisper`

### Audio Device Error
```
Error opening audio device
```
**Solution**: Check that no other application is using the microphone.

## Performance Tuning

For optimal performance based on your hardware:

### CPU-Only Systems (most common)
```python
SpeechManager(
    whisper_model="base",      # Good balance
    device="cpu",
    compute_type="int8"         # Fastest on CPU
)
```

### GPU Systems (NVIDIA with CUDA)
```python
SpeechManager(
    whisper_model="small",      # Better accuracy
    device="cuda",
    compute_type="float16"      # Optimal for GPU
)
```

### Low-Power Devices (Raspberry Pi, etc.)
```python
SpeechManager(
    whisper_model="tiny",       # Minimal resources
    device="cpu",
    compute_type="int8"
)
```

## References

- faster-whisper GitHub: https://github.com/SYSTRAN/faster-whisper
- Whisper Model Card: https://github.com/openai/whisper
- CTranslate2 Documentation: https://opennmt.net/CTranslate2/

---

**Date**: 2025-11-28
**Version**: 1.0
**Status**: Migration Complete
