# Gemma 3n Voice Assistant Setup Guide

This guide walks you through setting up the Gemma 3n voice-activated facial recognition assistant.

## Prerequisites

- Windows 10/11
- Python 3.11 (already installed in `facial_mcp_py311/`)
- Microphone
- Webcam
- Speakers/headphones
- At least 4GB RAM (for Gemma 3n 2B model)

## Step 1: Install Ollama

Ollama is required to run Gemma 3n locally.

1. **Download Ollama**:
   - Visit: https://ollama.ai
   - Download the Windows installer
   - Run the installer

2. **Verify Installation**:
   ```bash
   ollama --version
   ```

## Step 2: Download Gemma 3n Model

Choose one model based on your system resources:

### Option A: Gemma 3n 2B (Recommended - Lower Memory)
```bash
ollama pull gemma3n:2b-e2b
```
- **Memory**: ~3GB RAM
- **Speed**: Faster
- **Accuracy**: Good

### Option B: Gemma 3n 4B (Higher Accuracy)
```bash
ollama pull gemma3n:4b-e4b
```
- **Memory**: ~5GB RAM
- **Speed**: Slower
- **Accuracy**: Better

**Download time**: 5-15 minutes depending on your internet speed.

## Step 3: Install Python Dependencies

```bash
# Activate virtual environment
facial_mcp_py311\Scripts\activate

# Install voice assistant dependencies
pip install ollama sounddevice soundfile pyttsx3
```

## Step 4: Test Ollama and Gemma 3n

```bash
# Start Ollama service (if not running)
ollama serve

# Test Gemma 3n in another terminal
ollama run gemma3n:2b-e2b "Hello, how are you?"
```

You should see a response from Gemma 3n.

## Step 5: Run Gemma 3n Voice Assistant

```bash
# Make sure virtual environment is activated
facial_mcp_py311\Scripts\activate

# Run the voice assistant
python src\gemma3n_voice_assistant.py
```

## Usage

1. **Start the assistant**: Run the script (Step 5)
2. **Say the wake word**: "Hello Gemma"
3. **Get recognized**: Gemma will capture your face and greet you by name
4. **Repeat**: Say "Hello Gemma" whenever you want recognition

### Example Interaction

```
You: "Hello Gemma"
Gemma: "Yes?"
[Camera captures your face]
[MCP server recognizes you]
Gemma: "Hello, John Doe!"
```

## Workflow

```
Voice Input → Gemma 3n (Speech Recognition) → Wake Word Detected
                                                       ↓
                                               Webcam Capture
                                                       ↓
                                          MCP Server (Face Recognition)
                                                       ↓
                                          Text-to-Speech Greeting
```

## Troubleshooting

### "Gemma 3n not found in Ollama"
```bash
# Pull the model
ollama pull gemma3n:2b-e2b
```

### "Failed to connect to Ollama"
```bash
# Start Ollama service
ollama serve
```

### "No audio devices detected"
- Check microphone is connected
- Verify microphone permissions in Windows Settings
- Test with: `python -c "import sounddevice; print(sounddevice.query_devices())"`

### "No webcam detected"
- Check webcam is connected
- Close other apps using the webcam
- Test with: `python src\webcam_capture.py`

### Poor transcription accuracy
- Speak clearly and at normal volume
- Reduce background noise
- Position microphone closer
- Try the 4B model for better accuracy: `ollama pull gemma3n:4b-e4b`

## Performance Tips

1. **First Run**: Model loading takes 10-30 seconds
2. **Subsequent Runs**: Faster due to caching
3. **Wake Word Detection**: 3-second audio chunks processed
4. **Recognition Speed**: ~2-3 seconds total (audio → face recognition → response)

## Technical Details

### Gemma 3n Capabilities

- **Native Audio Understanding**: No need for external speech recognition APIs
- **Multimodal Input**: Supports audio, image, video, and text
- **Local Processing**: All computation happens on your device
- **Privacy**: No data sent to cloud services
- **Languages**: 140 text languages, 35 multimodal languages

### Audio Processing

- **Sample Rate**: 16kHz
- **Channels**: Mono
- **Format**: WAV
- **Chunk Size**: 3 seconds per wake word check
- **Gemma 3n Processing**: ~160ms per audio token

### Integration Points

1. **Gemma 3n** (Ollama) → Speech-to-Text
2. **OpenCV** → Webcam Capture
3. **MCP Server** → Facial Recognition
4. **pyttsx3** → Text-to-Speech

## Alternative: Using Hugging Face

If you prefer Hugging Face Transformers instead of Ollama:

```python
# Install transformers
pip install transformers torch

# Load Gemma 3n
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained("google/gemma-3n-2b-e2b")
tokenizer = AutoTokenizer.from_pretrained("google/gemma-3n-2b-e2b")
```

(Implementation would need to be modified for HF API)

## System Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4GB | 8GB+ |
| Storage | 3GB free | 10GB free |
| CPU | Dual-core | Quad-core+ |
| GPU | None (CPU-only) | Optional (faster) |
| Microphone | Any USB/built-in | Quality USB mic |
| Webcam | 720p | 1080p |

## Next Steps

- Register users: `python src\webcam_capture.py` (option 1)
- Batch enrollment: `python src\batch_enroll.py`
- Test recognition: `python src\gemma3n_voice_assistant.py`

## Support

- **Gemma 3n Documentation**: https://developers.googleblog.com/en/introducing-gemma-3n-developer-guide/
- **Ollama Docs**: https://ollama.ai/docs
- **MCP Server Issues**: Check audit logs in `audit_logs/`

---

**Note**: Gemma 3n is an open-source model from Google. Make sure you comply with the [Gemma Terms of Use](https://ai.google.dev/gemma/terms).
