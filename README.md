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


### Running the MCP Server (optional)

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

### Testing with Webcam Capture Tool (optional)

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

# Gemma 3 Facial Recognition Prototype

Voice-activated facial recognition using Gemma 3 as the orchestrating LLM, integrated with the Skyy Facial Recognition MCP server.

## Overview

This prototype demonstrates how to build a voice-activated AI assistant that:

1. **Listens** for the wake word "Hello Gemma"
2. **Requests permission** to capture a photo
3. **Captures** an image from the webcam
4. **Calls** the MCP `skyy_recognize_face` tool
5. **Generates** a personalized greeting using Gemma 3
6. **Offers** to register unknown users

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GEMMA 3 ORCHESTRATOR                            │
│                        (Local via Ollama)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Speech     │ │   Webcam     │ │  MCP Client  │
            │  Recognition │ │   Capture    │ │  (OAuth 2.1) │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    │               │               ▼
                    │               │   ┌─────────────────────┐
                    │               │   │  skyy_facial_       │
                    │               │   │  recognition_mcp.py │
                    │               │   │                     │
                    │               │   │ Tools:              │
                    │               │   │ - recognize_face    │
                    │               │   │ - register_user     │
                    │               │   │ - get_health_status │
                    │               │   └─────────────────────┘
                    │               │               │
                    ▼               ▼               ▼
            ┌─────────────────────────────────────────────────┐
            │              User Interaction                    │
            │         (Voice + Visual Feedback)               │
            └─────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Skyy Facial Recognition Server

This prototype requires the existing MCP server to be available. Ensure you have:

- Completed the [main project setup](../README.md)
- Virtual environment `facial_mcp_py311` with all dependencies
- InsightFace model downloaded (~200MB on first run)

### 2. Ollama with Gemma 3

Install Ollama and pull the Gemma 3 model:

```bash
# Install Ollama from https://ollama.com/

# Pull Gemma 3 model
ollama pull gemma3:4b

# Verify it's working
ollama run gemma3:4b "Say hello"
```
## Configuration (optional)

Edit `config.py` to match your environment:

```python
# Paths - adjust if your virtual environment is elsewhere
MCP_PYTHON_PATH = PROJECT_ROOT / "facial_mcp_py311" / "Scripts" / "python.exe"
MCP_SERVER_SCRIPT = PROJECT_ROOT / "src" / "skyy_facial_recognition_mcp.py"

# Ollama model
OLLAMA_MODEL = "gemma3:4b"  # or "gemma3:12b" for better reasoning

# Wake words
WAKE_WORD = "skyy recognize me"
WAKE_WORD_ALTERNATIVES = ["sky recognize me", "sky recognise me", "skyy recognise me"]

# Recognition threshold (lower = stricter)
SIMILARITY_THRESHOLD = 0.25
```

## Usage

### Running the Prototype

1. **Start Ollama** (if not running as a service):
   ```bash
   ollama serve
   ```

2. **Activate virtual environment**:
   ```bash
   facial_mcp_py311\Scripts\activate  # Windows
   ```

3. **Run the prototype**:
   ```bash
   cd gemma_mcp_prototype
   python main.py
   ```

4. **Interact**:
   - Say a voice command
   - Grant permission when asked
   - Look at the camera
   - Receive personalized greeting (or register if unknown)

### Example Interaction

```
[Init] All systems initialized!

============================================================
  Listening for: ['skyy recognize me', 'sky recognize me', 'sky recognise me', 'skyy recognise me']
  Press Ctrl+C to exit
============================================================

[Speech] Speaking: 'Hello! I'm Skyy. Say 'Skyy, recognize me' when you're ready.'

[Speech] Heard: 'skyy recognize me'
[Wake] Detected wake word in: 'skyy recognize me'

[Speech] Speaking: 'I'd like to take your photo to see if I recognize you. Is that okay?'
[Speech] Response: 'yes'
[Permission] camera_capture: GRANTED

[Speech] Speaking: 'Great! Look at the camera.'
[Vision] Captured image: 45632 bytes (base64)

[Speech] Speaking: 'Let me take a look...'
[MCP] Calling tool: skyy_recognize_face
[Recognition] Result: {'status': 'recognized', 'user': {'name': 'Andy', ...}}

[Speech] Speaking: 'Hey Andy! Great to see you again. How's the NLP project going?'
```

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
