# Gemma 3n Quick Start Guide

This is a condensed guide to get you started with Gemma 3n models quickly.

## Prerequisites

- Python 3.11+
- Virtual environment activated
- Hugging Face account (free)

## 3-Minute Setup

### 1. Install Dependencies

```bash
# Activate virtual environment
facial_mcp_py311\Scripts\activate

# Install required packages (including timm - CRITICAL for Gemma 3n)
pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub
```

**Why timm is required:**
- Gemma 3n is a unified multimodal model (audio + vision + text)
- The `timm` (PyTorch Image Models) library provides TimmWrapperModel
- Required even for audio-only use due to Gemma 3n's architecture
- Without it, you'll get: `TimmWrapperModel requires the timm library`

### 2. Authenticate with Hugging Face

**Option A: CLI Login (Recommended)**

```bash
# Install CLI
pip install huggingface-hub

# Login
huggingface-cli login
# Paste your token when prompted
```

**Option B: Environment Variable**

```cmd
# Windows CMD
set HF_TOKEN=hf_your_token_here

# Windows PowerShell
$env:HF_TOKEN = "hf_your_token_here"
```

### 3. Request Model Access

1. Visit: [https://huggingface.co/google/gemma-3n-E2B-it](https://huggingface.co/google/gemma-3n-E2B-it)
2. Click "Request Access"
3. Accept terms (instant approval)

### 4. Get Your Token

1. Go to: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Name: "gemma3n-dev"
4. Type: "Read"
5. Copy the token (starts with `hf_`)

### 5. Test Authentication

```bash
python test_hf_auth.py
```

You should see:
```
[OK] Authenticated as: your_username
[OK] Access granted to google/gemma-3n-E2B-it
[SUCCESS] You are properly authenticated!
```

### 6. Run the Assistant

```bash
python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav
```

## Common Errors

### "401 Client Error" / "GatedRepoError"

**Problem:** Not authenticated or no access to model

**Fix:**
1. Login: `huggingface-cli login`
2. Request access: Visit model page, click "Request Access"
3. Verify: `python test_hf_auth.py`

### "Token is invalid"

**Problem:** Token expired or incorrect

**Fix:**
1. Generate new token at [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Re-login: `huggingface-cli login`

### "transformers not installed" or "TimmWrapperModel requires the timm library"

**Problem:** Missing dependencies

**Fix:**
```bash
pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub
```

**Note:** The `timm` library is CRITICAL for Gemma 3n - it's a unified multimodal model that requires vision processing components even for audio-only use.

## Model Variants

- **E2B-it** (2 billion params): Faster, less RAM (~4GB), good for testing
- **E4B-it** (4 billion params): Better accuracy, more RAM (~6GB), production

```bash
# Use E2B (default)
python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav

# Use E4B (better quality)
python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav --model google/gemma-3n-E4B-it
```

## What Happens on First Run?

1. Authentication check (instant)
2. Model download (~2-4 GB, one-time, 5-15 minutes)
3. Model loading into memory (~30-60 seconds)
4. Assistant starts

Subsequent runs are much faster (model cached locally).

## Full Documentation

For detailed instructions, troubleshooting, and security best practices:
- [GEMMA3N_HUGGINGFACE_AUTH.md](GEMMA3N_HUGGINGFACE_AUTH.md) - Complete authentication guide
- [GEMMA3N_NATIVE_AUDIO_GUIDE.md](GEMMA3N_NATIVE_AUDIO_GUIDE.md) - Full assistant documentation

## Help

If you're still stuck:
1. Run: `python test_hf_auth.py` for diagnostics
2. Check: [GEMMA3N_HUGGINGFACE_AUTH.md](GEMMA3N_HUGGINGFACE_AUTH.md) for detailed troubleshooting
3. Verify: Your Hugging Face account has access approved for the model
