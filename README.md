# Skyy Facial Recognition Integration via MCP

## Overview

This project enhances the Skyy AI platform by developing a facial recognition capability that integrates with Skyy's existing orchestration system through the Model Context Protocol (MCP). The solution enables Skyy to recognize and greet users automatically, creating a personalized interaction experience while maintaining local processing and data privacy.

## Vision

*"MCP-integrated facial recognition for personalized Skyy interactions"*


## Technical Stack

- **Facial Recognition**: InsightFace with buffalo_l model pack
- **Vector Database**: ChromaDB for facial embeddings storage
- **Computer Vision**: OpenCV for camera interface
- **Protocol**: Model Context Protocol (MCP) for Skyy integration
- **Language**: Python 3.x

## Project Components

### 1. Camera Interface Layer
- Real-time image capture
- Frame processing capabilities

### 2. Facial Recognition Engine
- Face detection and analysis
- Feature extraction and embedding generation
- Face matching with confidence scoring

### 3. Data Storage Layer
- Local ChromaDB vector database
- Metadata management (names, timestamps)
- JSON-based indexing structure

### 4. MCP Integration Layer
- Command processing and routing
- Event triggering and response management


## Setup Instructions

### Prerequisites
- **Python 3.11.9** (Required - other versions may not work with pre-compiled binaries)
- Webcam or compatible camera device
- Windows/Linux/macOS
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fritz007x/skyy_facial_recognition.git
   cd skyy_facial_recognition
   ```

2. **Verify Python version**

   **IMPORTANT:** Ensure you're using Python 3.11.9. If you have multiple Python versions installed, specify the correct one:

   ```bash
   # Check Python version
   python --version
   # Should output: Python 3.11.9
   ```

   If you have multiple Python versions, use the full path or py launcher:

   Windows:
   ```bash
   # Using py launcher (recommended)
   py -3.11 --version

   # Or use full path
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe --version
   ```

   Linux/macOS:
   ```bash
   python3.11 --version
   ```

3. **Create and activate virtual environment**

   Windows:
   ```bash
   # If using default python (already version 3.11.9)
   python -m venv facial_mcp_py311

   # OR if you have multiple versions, use py launcher
   py -3.11 -m venv facial_mcp_py311

   # Activate
   facial_mcp_py311\Scripts\activate
   ```

   Linux/macOS:
   ```bash
   python3.11 -m venv facial_mcp_py311
   source facial_mcp_py311/bin/activate
   ```

   **Verify the virtual environment is using Python 3.11.9:**
   ```bash
   python --version  # Should show Python 3.11.9
   ```

4. **Install dependencies**

   **Windows (no C++ compiler) - REQUIRED METHOD:**

   InsightFace 0.7.3 has NO pre-compiled binary on PyPI. You **MUST** use the included wheel file:

   ```bash
   # Install NumPy 1.x FIRST (before other packages)
   pip install "numpy>=1.26.0,<2.0.0"

   # Install InsightFace from the included wheel file
   pip install insightface-0.7.3-cp311-cp311-win_amd64.whl

   # Install remaining dependencies
   pip install -r requirements.txt
   ```

   > **Critical:** The wheel file `insightface-0.7.3-cp311-cp311-win_amd64.whl` is included in the repository.
   > If you don't see it, download it from GitHub Releases or see troubleshooting section below.

   **Linux/macOS or Windows with C++ build tools:**
   ```bash
   pip install -r requirements.txt
   ```

   > **Note:** The wheel file name `cp311` indicates it's compiled for Python 3.11. If you get a "not supported wheel" error, verify your Python version with `python --version`

5. **Verify installation**
   ```bash
   python src/test_insightface_upgrade.py
   ```

   This will verify:
   - InsightFace version 0.7.3 or higher is installed
   - FaceAnalysis model can initialize
   - All dependencies are working correctly

### Troubleshooting Installation

**"numpy.dtype size changed, may indicate binary incompatibility":**
- This means NumPy 2.x was installed, but InsightFace wheel requires NumPy 1.x
- **Solution:**
  ```bash
  pip uninstall numpy opencv-python opencv-python-headless -y
  pip install "numpy>=1.26.0,<2.0.0"
  pip install insightface-0.7.3-cp311-cp311-win_amd64.whl
  pip install -r requirements.txt
  ```
- The requirements.txt uses NumPy 1.x and opencv-python 4.10.x (compatible versions)

**Wheel file not found after cloning:**
- The wheel file `insightface-0.7.3-cp311-cp311-win_amd64.whl` should be in the repository root
- If missing, download from: [GitHub Releases](https://github.com/fritz007x/skyy_facial_recognition/releases)
- Or download from PyPI and build: `pip download insightface==0.7.3` (requires C++ tools to wheel the tarball)
- Verify file size: Should be approximately 852KB

**"Microsoft Visual C++ 14.0 is required":**
- This means you tried `pip install insightface` which attempts to compile from source
- **Solution:** Use the wheel file: `pip install insightface-0.7.3-cp311-cp311-win_amd64.whl`
- **Important:** InsightFace 0.7.3 has NO pre-compiled binary on PyPI - the wheel file is the only option for Windows without C++ compiler

**"Not a supported wheel" error:**
- Verify Python version: `python --version` (must be 3.11.x)
- The wheel file `cp311` is ONLY for Python 3.11
- If you have a different Python version, you need to either:
  1. Install Python 3.11.9, or
  2. Install C++ build tools to compile from source

**"Old version of InsightFace installed":**
- Uninstall first: `pip uninstall insightface`
- Install from wheel: `pip install insightface-0.7.3-cp311-cp311-win_amd64.whl`
- Verify: `pip show insightface` (should show version 0.7.3)

**Missing models on first run:**
- InsightFace downloads ~200MB of models on first initialization to `~/.insightface/models/buffalo_l/`
- This is normal and only happens once

### Running the MCP Server

The MCP server provides tools for facial recognition that can be integrated with MCP-compatible clients.

**Start the server:**
```bash
# Make sure virtual environment is activated
facial_mcp_py311\Scripts\activate  # Windows
# or: source facial_mcp_py311/bin/activate  # Linux/macOS

# Run the server
python src/skyy_facial_recognition_mcp.py
```

The server will expose the following tools:
- `skyy_register_user` - Register a new user with facial data
- `skyy_recognize_face` - Recognize a registered user from an image
- `skyy_list_users` - List all registered users
- `skyy_get_user_profile` - Get detailed user profile
- `skyy_update_user` - Update user information
- `skyy_delete_user` - Delete a user from the database
- `skyy_get_database_stats` - Get database statistics

### Testing with Webcam Capture Tool

For interactive testing and demonstration, use the webcam capture tool:

```bash
# Activate virtual environment
facial_mcp_py311\Scripts\activate  # Windows
# or: source facial_mcp_py311/bin/activate  # Linux/macOS

# Run the interactive tool
python src/webcam_capture.py
```

**Available modes:**

1. **Capture & Register User** - Capture an image from webcam and optionally register a new user
   - Position yourself in front of the camera
   - Press SPACE to capture
   - Choose whether to register
   - If registering, enter name and optional metadata

2. **Recognize Face** - Capture an image and recognize who it is
   - Set confidence threshold (default: 0.25)
   - Position yourself in front of camera
   - Press SPACE to capture
   - See recognition results

3. **Live Recognition** - Continuous face recognition from webcam feed
   - Press 'r' to recognize the current frame
   - Press 'q' to quit
   - Real-time overlay shows last recognition result

4. **List Registered Users** - View all users in the database

5. **Database Statistics** - View database stats and metrics

### Running Automated Tests

To test all MCP server functionality:

```bash
python src/test_mcp_client.py
```

This will:
- Connect to the MCP server
- Test all available tools
- Register a test user
- Perform face recognition
- Display results for each operation

## Project Structure

```
skyy_facial_recognition/
├── src/
│   ├── skyy_facial_recognition_mcp.py  # MCP server implementation
│   ├── webcam_capture.py               # Interactive testing tool
│   ├── test_mcp_client.py             # Automated test suite
│   └── test_insightface_upgrade.py    # Installation verification
├── skyy_face_data/                     # User database (auto-created)
│   ├── index.json                      # User metadata
│   └── images/                         # Face image storage
├── facial_mcp_py311/                   # Python virtual environment
├── requirements.txt                    # Project dependencies
└── README.md                          # This file
```

## Project Status

✅ **Functional MVP**

Current features:
- MCP server with 7 tools for facial recognition
- Interactive webcam testing interface
- User registration and recognition
- Database management
- Automated testing suite

## Development Roadmap

- [x] Phase 1: Research and Design
- [x] Phase 2: Core Development
  - [x] Facial recognition engine setup
  - [x] Database implementation
  - [x] MCP integration layer
- [x] Phase 3: Integration and Testing
- [ ] Phase 4: Presentation and Demonstration

## Privacy & Security

This project maintains a **local-first architecture**:
- All facial data stored locally
- No external API calls for recognition
- User data remains on device

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Model Context Protocol (MCP)
- InsightFace library


---
