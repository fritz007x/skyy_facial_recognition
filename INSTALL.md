# Installation Guide

## Quick Install (Windows - No C++ Compiler)

If you don't have C++ build tools installed, use pre-compiled binaries:

### Step 1: Create Virtual Environment

```bash
python -m venv facial_mcp_py311
facial_mcp_py311\Scripts\activate
```

### Step 2: Install InsightFace (Choose One Method)

**Method 1: Using --prefer-binary flag (Recommended)**
```bash
pip install insightface --prefer-binary
```

**Method 2: Using the included wheel file**
```bash
pip install insightface-0.7.3-cp311-cp311-win_amd64.whl
```

### Step 3: Install Other Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install fastmcp>=2.13.0 mcp>=1.20.0
pip install opencv-python>=4.12.0
pip install opencv-python-headless>=4.12.0
pip install Pillow>=12.0.0
pip install onnx>=1.19.0
pip install onnxruntime>=1.23.0
pip install numpy>=1.26.0
pip install pydantic>=2.12.0
pip install pydantic-settings>=2.11.0
```

### Step 4: Verify Installation

```bash
python src/test_insightface_upgrade.py
```

## Alternative: Install All at Once (Requires C++ Build Tools)

If you have Microsoft Visual C++ 14.0 or greater installed:

```bash
pip install -r requirements.txt
```

## For Linux/macOS

On Linux and macOS, InsightFace can be installed directly from PyPI:

```bash
python3.11 -m venv facial_mcp_py311
source facial_mcp_py311/bin/activate
pip install -r requirements.txt
```

## Troubleshooting

### "Microsoft Visual C++ 14.0 is required"

This error means you're trying to compile from source. Use the wheel file instead:
```bash
pip install insightface-0.7.3-cp311-cp311-win_amd64.whl
```

### "insightface-0.7.3-cp311-cp311-win_amd64.whl is not a supported wheel"

Make sure you're using Python 3.11 on a 64-bit Windows system:
```bash
python --version  # Should show Python 3.11.x
```

### Missing Models

On first run, InsightFace will download ~200MB of models to `~/.insightface/models/buffalo_l/`. This is normal and only happens once.
