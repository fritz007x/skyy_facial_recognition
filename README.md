# Skyy Facial Recognition Integration via MCP

## Overview

This project enhances the Skyy AI platform by developing a facial recognition capability that integrates with Skyy's existing orchestration system through the Model Context Protocol (MCP). The solution enables Skyy to recognize and greet users automatically, creating a personalized interaction experience while maintaining local processing and data privacy.

## Vision

*"MCP-integrated facial recognition for personalized Skyy interactions"*


## Technical Stack

- **Facial Recognition**: InsightFace 0.7.3 with buffalo_l model pack
- **Vector Database**: ChromaDB with HNSW indexing for scalable similarity search
- **Authentication**: OAuth 2.1 Client Credentials flow with JWT tokens
- **Audit Logging**: Loguru with structured JSON logging and 30-day retention
- **Health Monitoring**: Component health checks with degraded mode operation
- **Computer Vision**: OpenCV for camera interface
- **Voice AI**: Gemma 3n with native multimodal audio understanding
- **Protocol**: Model Context Protocol (MCP) for AI integration
- **Language**: Python 3.11.9

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
   pip install "numpy==1.26.4"

   # Install InsightFace from the wheel file WITHOUT dependencies
   # (--no-deps prevents pip from uninstalling/reinstalling numpy)
   pip install --no-deps insightface-0.7.3-cp311-cp311-win_amd64.whl

   # Install remaining dependencies
   pip install -r requirements.txt
   ```


   **Linux/macOS or Windows with C++ build tools:**
   ```bash
   # Install NumPy first
   pip install "numpy==1.26.4"

   # Install all dependencies (including building InsightFace from source)
   pip install -r requirements.txt
   ```

   > **Note:** The wheel file name `cp311` indicates it's compiled for Python 3.11. If you get a "not supported wheel" error, verify your Python version with `python --version`

5. **Verify installation**
   ```bash
   python src/tests/test_insightface_upgrade.py
   ```

   This will verify:
   - InsightFace version 0.7.3 or higher is installed
   - FaceAnalysis model can initialize
   - All dependencies are working correctly

### Troubleshooting Installation (optional)

**"numpy.dtype size changed, may indicate binary incompatibility":**
- This means NumPy 2.x was installed, but InsightFace wheel requires NumPy 1.x
- **Solution:**
  ```bash
  pip uninstall numpy opencv-python opencv-python-headless insightface -y
  pip install "numpy==1.26.4"
  pip install --no-deps insightface-0.7.3-cp311-cp311-win_amd64.whl
  pip install -r requirements.txt
  ```
- The `--no-deps` flag prevents the wheel from reinstalling numpy

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

**IMPORTANT:** The MCP server must be running in a separate terminal for the webcam capture tool to work.

**Start the server (Terminal 1):**
```bash
# Make sure virtual environment is activated
facial_mcp_py311\Scripts\activate  # Windows
# or: source facial_mcp_py311/bin/activate  # Linux/macOS

# Run the server
python src/skyy_facial_recognition_mcp.py
```

Keep this terminal running. The server will expose the following tools:
- `skyy_register_user` - Register a new user with facial data
- `skyy_recognize_face` - Recognize a registered user from an image
- `skyy_list_users` - List all registered users
- `skyy_get_user_profile` - Get detailed user profile
- `skyy_update_user` - Update user information
- `skyy_delete_user` - Delete a user from the database
- `skyy_get_database_stats` - Get database statistics

### Testing with Webcam Capture Tool

For interactive testing and demonstration, use the webcam capture tool.

**IMPORTANT:** Open a NEW terminal (Terminal 2) while keeping the MCP server running in Terminal 1.

**Run the webcam tool (Terminal 2):**
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

To test all MCP server functionality, ensure the MCP server is running in Terminal 1, then run the test in a separate terminal.

**Run automated tests (Terminal 2):**
```bash
# Make sure virtual environment is activated
facial_mcp_py311\Scripts\activate  # Windows
# or: source facial_mcp_py311/bin/activate  # Linux/macOS

python src/tests/test_mcp_client.py
```

This will:
- Connect to the MCP server
- Test all available tools
- Register a test user
- Perform face recognition
- Display results for each operation

## OAuth 2.1 Authentication

The MCP server implements OAuth 2.1 Client Credentials flow with JWT tokens for secure authentication. All MCP tools require a valid access token.


### Security Features

- **RS256 JWT Tokens**: Cryptographically signed with RSA 2048-bit keys
- **Token Expiration**: Tokens expire after 60 minutes
- **Secure Storage**: Private keys and client secrets stored in `oauth_data/` (excluded from git)
- **Client Credentials Flow**: Server-to-server authentication without user interaction

### Testing OAuth Implementation

Run the comprehensive OAuth test suite to verify the implementation:

```bash
# Activate virtual environment
facial_mcp_py311\Scripts\activate  # Windows

# Run OAuth tests
python src/tests/test_oauth.py
```

The test suite validates:
- RSA key generation and loading
- Client creation and management
- Token generation and validation
- Invalid/expired token handling
- Authentication decorator functionality

**Example output:**
```
======================================================================
                         OAuth 2.1 Test Suite
======================================================================

> Test 1: RSA Key Generation and Loading
  [OK] RSA keys generated and loaded successfully
  [i] Private key: oauth_data\private_key.pem
  [i] Public key: oauth_data\public_key.pem

...

Total Tests:  9
Passed:       9
Failed:       0

Success Rate: 100.0%

[OK] ALL TESTS PASSED!
```


## Project Structure

```
skyy_facial_recognition/
├── src/
│   ├── skyy_facial_recognition_mcp.py  # MCP server implementation
│   ├── webcam_capture.py               # Interactive testing tool
│   ├── oauth_config.py                 # OAuth 2.1 configuration
│   ├── oauth_middleware.py             # Authentication decorator
│   ├── oauth_admin.py                  # OAuth CLI management tool
│   ├── tests/
│   │   ├── test_mcp_client.py          # Automated MCP test suite
│   │   └── test_oauth.py               # OAuth test suite
│   └── test_insightface_upgrade.py     # Installation verification
├── skyy_face_data/                     # User database (auto-created)
│   ├── index.json                      # User metadata
│   └── images/                         # Face image storage
├── oauth_data/                         # OAuth keys and clients (gitignored)
│   ├── private_key.pem                 # RSA private key
│   ├── public_key.pem                  # RSA public key
│   └── clients.json                    # OAuth client credentials
├── facial_mcp_py311/                   # Python virtual environment
├── requirements.txt                    # Project dependencies
└── README.md                          # This file
```

## Production-Grade Features

### Health Check System

The MCP server includes comprehensive health monitoring for production reliability:

**Component Monitoring:**
- **InsightFace**: Model loading and face recognition functionality
- **ChromaDB**: Vector database connectivity and operations
- **OAuth**: Authentication system availability

**Health States:**
- **HEALTHY**: All components operational
- **DEGRADED**: ChromaDB unavailable, registrations queued for later processing
- **UNAVAILABLE**: Critical component failure

**Features:**
```bash
# Check health status
python src/check_health.py

# Run with health checks enabled (default)
python src/skyy_facial_recognition_mcp.py
```

**Degraded Mode:** When ChromaDB is unavailable, the system:
- Queues new registrations for later processing
- Returns helpful error messages for recognition attempts
- Automatically processes queued registrations when ChromaDB recovers

See [docs/HEALTH_CHECK_USAGE.md](docs/HEALTH_CHECK_USAGE.md) for details.

### Audit Logging

All biometric operations are logged for security compliance and forensic investigation:

**Logged Operations:**
- User registrations (with detection scores and quality metrics)
- Face recognition attempts (successful and failed)
- User profile updates and deletions
- Database queries and statistics
- All MCP tool invocations (32 audit points total)

**Log Features:**
- **Structured JSON format** for easy parsing
- **Daily rotation** with compression
- **30-day retention** (configurable)
- **PII redaction** options for privacy compliance
- **Client identification** for multi-client environments

**Log Location:**
```
audit_logs/
├── audit.log              # Current audit log
├── audit.2024-01-15.log   # Previous day (compressed)
└── application.log        # Application logs
```

**Example audit entry:**
```json
{
  "timestamp": "2024-01-16T10:30:45.123Z",
  "event_type": "registration",
  "outcome": "success",
  "client_id": "webcam_client",
  "user_id": "john_doe_1",
  "user_name": "John Doe",
  "biometric_data": {
    "detection_score": 0.98,
    "face_quality": "high"
  }
}
```

### Batch Enrollment

Automate user enrollment from a directory of images:

```bash
# Enroll all users from a folder
python src/batch_enroll.py

# Specify custom directory
python src/batch_enroll.py --dir path/to/enrollment/images

# Skip existing users
python src/batch_enroll.py --skip-existing
```

**Features:**
- Automatic OAuth authentication
- Progress tracking with statistics
- Duplicate detection (skips existing users)
- Health check integration (supports degraded mode)
- Detailed success/failure reporting

**Supported formats:** JPG, JPEG, PNG
**Filename convention:** Image filename becomes user name (e.g., `john_doe.jpg` → "John Doe")

### ChromaDB Vector Database

Production-grade vector storage for facial embeddings:

**Features:**
- **HNSW indexing**: Fast similarity search (O(log n) complexity)
- **Scalable**: Handles thousands of users efficiently
- **Persistent storage**: Data survives server restarts
- **Metadata support**: Store additional user information
- **Distance metrics**: Cosine similarity for face matching

**Database Location:**
```
chromadb_data/
└── chroma.sqlite3    # Vector database file
```

**Performance:**
- Recognition: ~10-50ms for 1000 users
- Much faster than linear search O(n)
- Automatic index optimization

## Voice Assistant with Gemma 3n

This project includes a production-ready voice-activated facial recognition assistant using Google's Gemma 3n models with native multimodal audio processing capabilities.

### Features

- **Native audio understanding**: Gemma 3n processes audio directly (no Whisper/external models needed)
- **Continuous listening**: Real-time microphone input with 3-second chunks
- **Wake word detection**: Responds to "Hello Gemma", "Hey Gemma", or "Hi Gemma"
- **MCP integration**: Automatic face recognition via MCP server
- **Text-to-speech**: Personalized greetings with recognized user names
- **Multiple model support**: E2B (faster, 2B params) or E4B (more accurate, 4B params)
- **GPU acceleration**: Automatic CUDA detection for faster processing

### Workflow

```
[Microphone] → [Gemma 3n Audio] → [Wake Word Detection]
                                          ↓
                                    [Webcam Capture]
                                          ↓
                                    [MCP Recognition]
                                          ↓
                                    [TTS Greeting: "Hello, {name}!"]
```

### Quick Start

**1. Install dependencies:**
```bash
# Core dependencies
pip install transformers>=4.53.0 torch torchaudio

# Required for Gemma 3n multimodal
pip install timm>=0.9.0 librosa>=0.11.0

# Audio and voice
pip install sounddevice soundfile pyttsx3

# HuggingFace and MCP
pip install huggingface-hub opencv-python mcp
```

**2. Authenticate with Hugging Face:**

Gemma 3n models are GATED and require authentication:

```bash
# Get token from: https://huggingface.co/settings/tokens
# Request access: https://huggingface.co/google/gemma-3n-E2B-it

# Login (recommended)
huggingface-cli login

# OR set environment variable
set HF_TOKEN=hf_your_token_here  # Windows
export HF_TOKEN=hf_your_token_here  # Linux/Mac
```

**3. Verify setup:**
```bash
# Test authentication
python test_hf_auth.py

# Check dependencies
python check_gemma3n_dependencies.py
```

**4. Run live voice assistant:**
```bash
# Start with E2B model (faster, recommended for CPU)
python src/gemma3n_live_voice_assistant.py

# Or use E4B model (more accurate, requires more resources)
python src/gemma3n_live_voice_assistant.py --model google/gemma-3n-E4B-it

# Adjust audio chunk duration (default 3.0s)
python src/gemma3n_live_voice_assistant.py --duration 2.5
```

### Model Comparison

| Feature | E2B (2B params) | E4B (4B params) |
|---------|-----------------|-----------------|
| **Accuracy** | Good | Excellent ✅ |
| **Speed (CPU)** | ~15s/3s audio | ~30s/3s audio |
| **Speed (GPU)** | ~2s/3s audio | ~3-4s/3s audio |
| **Download size** | ~10 GB | ~15 GB |
| **RAM required (CPU)** | ~8 GB | ~16 GB ⚠️ |
| **VRAM (GPU)** | ~4 GB | ~8 GB |
| **Loading time (CPU)** | 2-3 minutes | 20-40 minutes ⚠️ |
| **Loading time (GPU)** | 30-60 seconds | 1-2 minutes |
| **Best for** | CPU systems ✅ | GPU systems only |

**⚠️ Important:** E4B requires significant resources and is **not recommended for CPU-only systems**. Use E2B for CPU deployment.

### Usage Example

```bash
$ python src/gemma3n_live_voice_assistant.py

[System] Initializing Gemma 3n Voice Assistant
[System] Model: google/gemma-3n-E2B-it
[System] Device: cuda
[System] Authenticated with Hugging Face
[System] Model loaded successfully
[System] OAuth configured

======================================================================
         GEMMA 3N LIVE VOICE ASSISTANT
         Voice-Activated Facial Recognition
======================================================================

Model: google/gemma-3n-E2B-it
Chunk duration: 3.0s
Wake word: 'Hello Gemma', 'Hey Gemma', or 'Hi Gemma'

======================================================================

[Gemma] Voice assistant activated. Say Hello Gemma to get started.
[Gemma] Starting continuous listening...

[Listening] Recording...
[Heard] "hello gemma"
[Gemma] Wake word detected: 'hello gemma'

======================================================================
[Gemma] Speaking: "Yes?"
[Gemma] Capturing image...
[Gemma] Image captured
[Gemma] Connecting to MCP server...
[Gemma] Analyzing face...
[Gemma] Recognized: John Doe (85.2%)
[Gemma] Speaking: "Hello, John Doe!"
======================================================================

[Gemma] Ready for next command...
```

### Documentation

- **[GEMMA3N_QUICKSTART.md](GEMMA3N_QUICKSTART.md)** - 3-minute setup guide
- **[GEMMA3N_HUGGINGFACE_AUTH.md](GEMMA3N_HUGGINGFACE_AUTH.md)** - Authentication guide
- **[GEMMA3N_NATIVE_AUDIO_GUIDE.md](GEMMA3N_NATIVE_AUDIO_GUIDE.md)** - Complete documentation
- **[GEMMA3N_TIMM_DEPENDENCY_FIX.md](GEMMA3N_TIMM_DEPENDENCY_FIX.md)** - Dependency troubleshooting

### Troubleshooting

**"GatedRepoError: 401 Client Error"**
```bash
# Not authenticated - run authentication check
python test_hf_auth.py

# Login if needed
huggingface-cli login
```

**"TimmWrapperModel requires the timm library"**
```bash
pip install timm>=0.9.0
```

**"load_audio_librosa requires the librosa library"**
```bash
pip install librosa>=0.11.0
```

**"Audio too quiet (RMS: 0.0001)"**
- Check microphone permissions
- Increase microphone volume
- Speak louder or closer to mic
- Try different microphone

**Slow transcription on CPU**
- Use E2B model instead of E4B
- Reduce chunk duration: `--duration 2.0`
- Consider GPU acceleration (100x faster)

## Project Status

✅ **Production-Ready System**

### Core Features
- ✅ **MCP Server**: 8 production-grade tools for facial recognition
- ✅ **OAuth 2.1**: Secure authentication with JWT tokens
- ✅ **ChromaDB**: Scalable vector database with HNSW indexing
- ✅ **Health Monitoring**: Component health checks with degraded mode
- ✅ **Audit Logging**: Comprehensive security logs (32 audit points)
- ✅ **Batch Enrollment**: Automated user registration from directories
- ✅ **Interactive Testing**: Webcam capture tool with multiple modes
- ✅ **Voice Assistant**: Gemma 3n native audio with continuous listening

### Quality & Reliability
- ✅ Automated test suites (OAuth, MCP, Health)
- ✅ Production-grade error handling
- ✅ Security compliance ready (audit logs, PII redaction)
- ✅ Scalable architecture (handles 1000+ users)
- ✅ Local-first privacy (no external API calls)

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
