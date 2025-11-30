# Gemma 3n timm Dependency - Quick Reference

## The Error

```
TimmWrapperModel requires the timm library but it was not found in your environment.
You can install it with pip: `pip install timm`.
Please note that you may need to restart your runtime after installation.
```

## The Fix (30 seconds)

```bash
# Activate virtual environment
facial_mcp_py311\Scripts\activate

# Install timm
pip install timm>=0.9.0

# Verify
python -c "import timm; print('timm:', timm.__version__)"
```

## Why timm is Required

Gemma 3n is a **unified multimodal model** (audio + vision + text).

Even for audio-only use:
- Model architecture includes vision components
- Uses `TimmWrapperModel` from the timm library
- Cannot load without it

Think of it like a Swiss Army knife - it has all the tools built-in, even if you only use the scissors.

## Complete Gemma 3n Setup

```bash
# Activate environment
facial_mcp_py311\Scripts\activate

# Install all dependencies
pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub pyttsx3

# Check everything is ready
python check_gemma3n_dependencies.py

# Run assistant
python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav
```

## Verify Installation

```bash
# Quick check
python -c "import timm; print('timm:', timm.__version__)"

# Full check
python check_gemma3n_dependencies.py
```

Expected output:
```
[OK] timm
    Required: 0.9.0+
    Found:    0.9.16
```

## What Changed

### Updated Files

1. **requirements.txt** - Added timm dependency
2. **src/gemma3n_native_audio_assistant.py** - Added dependency checker
3. **GEMMA3N_QUICKSTART.md** - Updated installation instructions
4. **GEMMA3N_HUGGINGFACE_AUTH.md** - Updated setup steps
5. **check_gemma3n_dependencies.py** - NEW: Dependency verification tool

### Before

```bash
pip install transformers>=4.53.0 torch torchaudio huggingface-hub
# ❌ Missing timm - will fail at model load time
```

### After

```bash
pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub
# ✓ Includes timm - will work correctly
```

## Troubleshooting

### Still getting the error?

1. Check you're in the right environment:
   ```bash
   where python
   # Should show: ...\facial_mcp_py311\Scripts\python.exe
   ```

2. Verify timm is installed in THIS environment:
   ```bash
   pip list | findstr timm
   ```

3. If not found, install it:
   ```bash
   pip install timm>=0.9.0
   ```

### Import Error

If you get `ImportError: cannot import name 'timm'`:

```bash
# Reinstall timm
pip install --force-reinstall timm>=0.9.0
```

### Wrong Version

If you have an old version:

```bash
# Upgrade
pip install --upgrade timm>=0.9.0
```

## Additional Resources

- **GEMMA3N_TIMM_DEPENDENCY_FIX.md** - Complete technical documentation
- **GEMMA3N_QUICKSTART.md** - Full setup guide
- **check_gemma3n_dependencies.py** - Dependency verification tool
- **timm GitHub:** https://github.com/huggingface/pytorch-image-models

## Summary

The `timm` library is **required** for Gemma 3n models. Install it with:

```bash
pip install timm>=0.9.0
```

Then verify with:

```bash
python check_gemma3n_dependencies.py
```

That's it!
