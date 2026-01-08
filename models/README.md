# ML Models

This directory contains machine learning models used by the face recognition system.

## InsightFace Models

The InsightFace `buffalo_l` model is automatically downloaded on first run to:
```
~/.insightface/models/buffalo_l/
```

### Required Model Files
- `det_10g.onnx` - Face detection model
- `w600k_r50.onnx` - Face recognition/embedding model

### Manual Download

If automatic download fails, you can manually download the models:

1. Download from InsightFace model zoo
2. Extract to `~/.insightface/models/buffalo_l/`

## Whisper Models (Voice Assistant)

For the voice assistant, Whisper models are downloaded automatically by OpenAI's whisper library.

Default model: `base.en` (English-optimized, ~150MB)

### Model Sizes
- `tiny.en` - 39MB, fastest
- `base.en` - 142MB, balanced (default)
- `small.en` - 484MB, more accurate
- `medium.en` - 1.5GB, high accuracy

## Notes

- Models are gitignored to keep repository size manageable
- All models are downloaded automatically on first use
- Ensure sufficient disk space (~500MB for basic setup)
