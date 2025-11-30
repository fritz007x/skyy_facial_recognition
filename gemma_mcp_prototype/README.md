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

### 3. Additional Dependencies

Install the speech dependencies in the existing virtual environment:

```bash
# Activate the virtual environment
facial_mcp_py311\Scripts\activate  # Windows
# or: source facial_mcp_py311/bin/activate  # Linux/macOS

# Install additional dependencies
pip install SpeechRecognition pyttsx3 pyaudio ollama
```

**Note for Windows users:** PyAudio may require additional steps:
```bash
# If pip install pyaudio fails, try:
pip install pipwin
pipwin install pyaudio
```

### 4. Hardware Requirements

- **Microphone**: For voice input
- **Speakers**: For voice output
- **Webcam**: For facial capture

## Project Structure

```
gemma_mcp_prototype/
├── main.py                 # Main orchestration script
├── config.py               # Configuration constants
├── requirements.txt        # Additional dependencies
├── README.md               # This file
└── modules/
    ├── __init__.py
    ├── speech.py           # Voice recognition & TTS
    ├── vision.py           # Webcam capture
    ├── mcp_client.py       # MCP client (OAuth-aware)
    └── permission.py       # User consent handling
```

## Configuration

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
   - Say "Hello Gemma" to wake the assistant
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

## MCP Integration Details

### Authentication

The prototype uses the same OAuth 2.1 system as the main project:

```python
from oauth_config import oauth_config

# Create/reuse client
client_id = "gemma_facial_client"
access_token = oauth_config.create_access_token(client_id)
```

### Tool Call Format

The MCP server expects arguments in a specific format:

```python
# Correct format (used by this client)
arguments = {
    "params": {
        "access_token": "...",
        "image_data": "base64...",
        "response_format": "json"
    }
}

# The client handles this wrapping automatically
result = await mcp_client.recognize_face(
    access_token=token,
    image_data=image_base64
)
```

### Response Handling

Recognition responses include status for different scenarios:

```python
# Recognized user
{
    "status": "recognized",
    "distance": 0.18,
    "user": {"name": "Andy", "user_id": "user_abc123", ...}
}

# Unknown user
{
    "status": "not_recognized",
    "message": "No matching user found"
}

# Degraded mode (ChromaDB unavailable)
{
    "status": "queued",
    "user": {"queue_position": 3, ...}
}
```

## Troubleshooting

### "Could not open camera"

- Ensure no other application is using the webcam
- Try a different camera index in `config.py`

### "Recognition service error"

- Check internet connection (Google Speech API requires internet)
- Consider switching to offline recognition (Sphinx)

### "Ollama check failed"

- Ensure Ollama is running: `ollama serve`
- Verify model is downloaded: `ollama list`
- Pull if missing: `ollama pull gemma3:4b`

### "MCP connection failed"

- Verify paths in `config.py` are correct
- Check that `skyy_facial_recognition_mcp.py` exists
- Ensure virtual environment has all dependencies

## Extending the Prototype

### Adding New Wake Words

Edit `config.py`:
```python
WAKE_WORD_ALTERNATIVES = ["sky recognize me", "sky recognise me", "skyy recognise me"]
```

### Custom Greeting Prompts

Modify `generate_greeting()` in `main.py` to customize Gemma's personality.

### Adding More Tools

The MCP client supports all server tools:
```python
# List all registered users
users = await mcp_client.list_users(access_token)

# Get database statistics
stats = await mcp_client.get_database_stats(access_token)

# Check system health
health = await mcp_client.get_health_status(access_token)
```

## License

MIT License - see the main project LICENSE file.

## Acknowledgments

- Skyy Facial Recognition MCP Server (Team 5)
- Ollama Team for local LLM inference
- Google for Speech Recognition API
- InsightFace for facial recognition models
