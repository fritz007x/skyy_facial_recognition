# Gemma 3n Native Audio Processing Guide

This guide explains how to use Gemma 3n's native multimodal audio capabilities for voice-activated facial recognition.

## Two Approaches Available

### Option 1: Whisper-based (Current - Simple & Fast)
- ✅ Uses OpenAI Whisper for speech recognition
- ✅ Lightweight (~1.4GB model download)
- ✅ Fast inference (~0.5s per 3s audio)
- ✅ Works on CPU
- ❌ Doesn't use Gemma 3n's multimodal capabilities

**Files:**
- `src/gemma3n_voice_assistant.py` - Main assistant (Whisper)
- `test_gemma3n_full_integration.py` - Integration test (Whisper)

### Option 2: Gemma 3n Native Audio (New - True Multimodal)
- ✅ Uses Gemma 3n's Universal Speech Model (USM)
- ✅ True multimodal processing (audio → text natively)
- ✅ Supports 35+ languages for multimodal
- ✅ Same model for audio AND text
- ❌ Larger download (~5GB for E2B, ~8GB for E4B)
- ❌ Slower on CPU (⚠️ GPU highly recommended)

**Files:**
- `src/gemma3n_native_audio_assistant.py` - Native audio implementation

---

## Setup: Gemma 3n Native Audio

### 1. Install Dependencies

**Uncomment in `requirements.txt`:**
```python
# Voice Assistant - Option 2: Gemma 3n Native Audio (Hugging Face Transformers)
transformers>=4.53.0  # Remove the # to uncomment
torch>=2.0.0
torchaudio>=2.0.0
accelerate>=0.20.0
sentencepiece>=0.1.99
```

**Install:**
```bash
facial_mcp_py311\Scripts\activate
pip install transformers>=4.53.0 torch torchaudio accelerate sentencepiece
```

### 2. Model Download (First Run)

The model will auto-download on first use:

**E2B (2B parameters - Faster):**
- Size: ~5GB download
- RAM: ~4GB required
- Speed: Moderate

**E4B (4B parameters - More Accurate):**
- Size: ~8GB download
- RAM: ~6GB required
- Speed: Slower but better quality

**Note:** First run may take 10-30 minutes to download the model.

### 3. GPU Support (Highly Recommended)

**Without GPU:** Works but slow (~10-30 seconds per audio clip)

**With GPU (NVIDIA):**
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## Usage

### Basic Test (Pre-recorded Audio)

**First, convert your M4A to WAV:**
```bash
# Option A: Use online converter
# Visit: https://cloudconvert.com/m4a-to-wav
# Upload "Voice Recording.m4a"
# Download as "hello_gemma.wav"

# Option B: Install ffmpeg (recommended)
choco install ffmpeg
# Then Gemma 3n can handle M4A directly
```

**Run the test:**
```bash
# Using E2B (faster, 2B params)
facial_mcp_py311\Scripts\python.exe src\gemma3n_native_audio_assistant.py hello_gemma.wav

# Using E4B (better accuracy, 4B params)
facial_mcp_py311\Scripts\python.exe src\gemma3n_native_audio_assistant.py hello_gemma.wav --model google/gemma-3n-E4B-it
```

### Expected Output

```
[System] Loading Gemma 3n model: google/gemma-3n-E2B-it
[System] This may take several minutes on first run...
[System] Loading processor...
[System] Loading model weights...
[System] Model loaded successfully on device: cuda:0
[System] GPU: NVIDIA GeForce RTX 3080

======================================================================
      GEMMA 3N NATIVE AUDIO ASSISTANT - INTEGRATION TEST
======================================================================

Model: Using Gemma 3n with native audio processing
Audio File: hello_gemma.wav
Workflow: Native Audio → Wake Word → Face Recognition → TTS

======================================================================

[OAuth] Access token generated

[Gemma] Listening for 'Hello Gemma'...
[Gemma 3n] Processing audio with native audio model...
[Gemma 3n] Generating transcription...
[Gemma 3n] Transcribed: "hello gemma"
[Gemma] Wake word detected: 'hello gemma'

[SUCCESS] Wake word detected with Gemma 3n native audio!

[Gemma] Speaking: "Yes?"
[Gemma] Opening camera...
[Gemma] Image captured!
[Gemma] Connecting to MCP server...
[Gemma] Analyzing face...
[Gemma] Recognized: John Doe (confidence: 85.2%)
[Gemma] Speaking: "Hello, John Doe!"

======================================================================
[SUCCESS] Full integration test completed!
======================================================================
```

---

## Technical Details

### Audio Requirements (Gemma 3n)

- **Sample Rate:** 16kHz (automatically converted)
- **Channels:** Mono (stereo auto-converted to mono)
- **Format:** Float32, normalized to [-1, 1] range
- **Duration:** Up to 30 seconds recommended
- **Token Cost:** 6.25 tokens per second of audio

### How It Works

1. **Audio Loading:**
   ```python
   waveform, sr = torchaudio.load("audio.wav")
   # Auto-converts to 16kHz mono float32
   ```

2. **Gemma 3n Processing:**
   ```python
   messages = [{
       "role": "user",
       "content": [
           {"type": "audio", "audio": "audio.wav"},
           {"type": "text", "text": "Transcribe this audio."}
       ]
   }]
   ```

3. **Native Transcription:**
   - Audio → Universal Speech Model (USM) encoder
   - USM features → Gemma 3n decoder
   - Output: Transcribed text

### Performance Comparison

| Method | Model Size | RAM | Speed (3s audio) | Accuracy |
|--------|-----------|-----|------------------|----------|
| **Whisper (base)** | 1.4GB | 2GB | ~0.5s | Excellent |
| **Gemma 3n E2B (CPU)** | 5GB | 4GB | ~15s | Good |
| **Gemma 3n E2B (GPU)** | 5GB | 2GB VRAM | ~2s | Good |
| **Gemma 3n E4B (CPU)** | 8GB | 6GB | ~30s | Excellent |
| **Gemma 3n E4B (GPU)** | 8GB | 4GB VRAM | ~3s | Excellent |

---

## Comparison: Whisper vs Gemma 3n Native

### When to Use Whisper (Option 1)
- ✅ Quick prototyping
- ✅ CPU-only systems
- ✅ English-only wake words
- ✅ Don't need multimodal integration
- ✅ Want fastest inference

### When to Use Gemma 3n Native (Option 2)
- ✅ Have GPU available
- ✅ Want true multimodal AI
- ✅ Need multilingual support (35+ languages)
- ✅ Want to use same model for text/audio/vision
- ✅ Future-proofing (when you add more Gemma 3n features)
- ✅ Educational/research purposes

---

## Troubleshooting

### "Model not found" Error
```bash
# Clear Hugging Face cache and re-download
rm -rf ~/.cache/huggingface/
# Re-run script to download fresh
```

### "Out of memory" Error (CPU)
```python
# Use smaller E2B model instead of E4B
python src\gemma3n_native_audio_assistant.py audio.wav --model google/gemma-3n-E2B-it
```

### "Out of memory" Error (GPU)
```python
# Enable CPU offloading
# Edit gemma3n_native_audio_assistant.py line 119:
device_map="balanced"  # Instead of "auto"
```

### Very Slow Transcription
```
CPU inference is slow. Install GPU support:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### "transformers version too old"
```bash
pip install --upgrade transformers
# Need >=4.53.0 for Gemma 3n audio support
```

---

## Next Steps

### Live Microphone Input

To use live microphone instead of pre-recorded audio:

1. Record audio in real-time using `sounddevice`
2. Save to temporary WAV file
3. Process with Gemma 3n native audio

**Example modification** (add to `gemma3n_native_audio_assistant.py`):
```python
import sounddevice as sd
import tempfile

def record_audio_live(duration=3):
    """Record from microphone."""
    audio_data = sd.rec(
        int(duration * 16000),
        samplerate=16000,
        channels=1,
        dtype='float32'
    )
    sd.wait()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    sf.write(temp_file.name, audio_data, 16000)
    return temp_file.name

# Then use with Gemma 3n
audio_file = record_audio_live(duration=3)
transcription = assistant.transcribe_with_gemma3n(audio_file)
```

---

## Additional Resources

- **Gemma 3n Documentation:** https://ai.google.dev/gemma/docs/capabilities/audio
- **Hugging Face Model:** https://huggingface.co/google/gemma-3n-E2B-it
- **Transformers Docs:** https://huggingface.co/docs/transformers/model_doc/gemma3n
- **Universal Speech Model (USM):** https://arxiv.org/abs/2303.01037

---

## Summary

You now have **two options** for voice recognition:

1. **Whisper** (current) - Fast, simple, CPU-friendly
2. **Gemma 3n Native** (new) - True multimodal, GPU-recommended

Both integrate seamlessly with your MCP facial recognition server!

Choose based on your hardware and whether you want to leverage Gemma 3n's native multimodal capabilities.
