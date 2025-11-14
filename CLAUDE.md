# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a face recognition system built with InsightFace for enrollment and real-time recognition. The project uses the InsightFace library's `buffalo_l` model for face detection and embedding generation, with a custom database system for storing and matching face embeddings.

**Core Technology Stack:**
- Python 3.11.9
- InsightFace 0.7.3
- OpenCV (cv2) for image processing and camera operations
- ONNX Runtime for model inference
- NumPy for embedding calculations

## Development Environment

**Virtual Environment:**
- Located in `facial_mcp_py311/` directory
- Created with Python 3.11.9
- Activate: `facial_mcp_py311\Scripts\activate` (Windows) or `source facial_mcp_py311/bin/activate` (Unix)

**Key Dependencies:**
- `insightface` (v0.7.3) - Face detection and recognition models
- `opencv-python` (cv2) - Image/video processing
- `onnxruntime` - Model inference engine
- `numpy` - Numerical operations

**Model Files:**
- Models stored in `~/.insightface/models/buffalo_l/`
- Required files: `det_10g.onnx` (detection), `w600k_r50.onnx` (recognition)
- Models auto-download on first run if not present

## Common Commands

**Activate virtual environment:**
```bash
facial_mcp_py311\Scripts\activate    # Windows
source facial_mcp_py311/bin/activate  # Unix/Mac
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Code Architecture

### Core Components

**Face Recognition System:**
The main system handles all face recognition operations. Key architectural decisions:

- **Database Structure**: Uses dual-file storage:
  - `face_db.pkl`: Pickled dictionary of `{user_id: embedding_vector}`
  - `metadata.json`: Human-readable metadata (names, enrollment dates, additional info)

- **Embedding Storage**: Face embeddings are NumPy arrays (512-dimensional vectors from InsightFace)
  - Stored directly in memory as dictionary
  - Persisted to disk using pickle for binary efficiency

- **Distance Calculation**: Uses cosine distance for face matching
  - Formula: `distance = 1 - cosine_similarity`
  - Range: 0 (identical) to 2 (opposite)
  - Default threshold: Typically around 0.4

**Face Recognition Workflow:**

1. **Enrollment Phase:**
   - Load image → Detect face → Extract 512-d embedding → Store with metadata
   - Multiple faces in image: Uses first detected face only (with warning)
   - Generates unique IDs

2. **Recognition Phase:**
   - Detect faces → Extract embeddings → Compare against database using cosine distance
   - Find best match below threshold → Return identity with confidence
   - Above threshold → Mark as "Unknown"

3. **Real-time Recognition:**
   - Continuous camera capture with OpenCV
   - Per-frame detection and matching
   - Visual overlay: Bounding boxes + labels + confidence scores
   - Press 'q' to quit

## Camera Configuration

- Default camera index: 0 (usually built-in webcam)
- Can specify alternative indices (1, 2, etc.) for external cameras
- Camera issues: Check device availability, try different indices, ensure no other apps using camera

## Threshold Tuning

The recognition threshold (cosine distance) is critical for accuracy:
- **Lower threshold** (e.g., 0.3): Stricter matching, fewer false positives, more "Unknown" results
- **Higher threshold** (e.g., 0.5): Looser matching, more recognitions, potential false positives
- **Default**: 0.4 is a good starting point
- Adjust based on lighting conditions, image quality, and use case requirements

## Known Issues and Quirks

1. **Model download on first run**: InsightFace downloads ~200MB of models on first initialization. This can appear as a hang - it's normal. If models are already downloaded manually, the system will use them directly.

2. **Windows path handling**: Uses standard path separators - no special handling needed for Windows backslashes.

## Testing Data

- Enrollment images should be in designated enrollment directory
- Filename convention: Use descriptive names (e.g., `john_doe.jpg`)
- Database created in specified `database_path` parameter location
