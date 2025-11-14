# Skyy Facial Recognition Integration via MCP

## Overview

This project enhances the Skyy AI platform by developing a facial recognition capability that integrates with Skyy's existing orchestration system through the Model Context Protocol (MCP). The solution enables Skyy to recognize and greet users automatically, creating a personalized interaction experience while maintaining local processing and data privacy.

## Vision

*"MCP-integrated facial recognition for personalized Skyy interactions"*

## Key Features

- **User Enrollment**: Trigger-based registration with "Skyy, remember me" command
- **Automatic Recognition**: Real-time facial recognition during user interactions
- **Local-First Architecture**: All data processing and storage happens locally
- **MCP Integration**: Seamless integration with Skyy's orchestration system

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

## Use Cases

### Primary: User Recognition
1. User approaches Skyy-enabled device
2. Skyy captures image via camera
3. System checks image against local database
4. Match found → Skyy greets user by name
5. No match → Standard greeting proceeds

### Secondary: New User Registration
1. User says "Skyy, remember me"
2. Skyy activates registration mode
3. Skyy prompts for user information
4. Skyy captures facial image
5. System stores data in local database
6. Skyy confirms successful registration

## Setup Instructions

### Prerequisites
- Python 3.11.9
- Webcam or compatible camera device
- Windows/Linux/macOS
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fritz007x/skyy_facial_recognition.git
   cd FACIAL_RECOGNITION_MCP
   ```

2. **Create and activate virtual environment**

   Windows:
   ```bash
   python -m venv facial_mcp_py311
   facial_mcp_py311\Scripts\activate
   ```

   Linux/macOS:
   ```bash
   python3.11 -m venv facial_mcp_py311
   source facial_mcp_py311/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python src/test_insightface_upgrade.py
   ```

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
FACIAL_RECOGNITION_MCP/
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
- Labeled Faces in the Wild (LFW) dataset

---
