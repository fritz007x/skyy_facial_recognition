# Gemma 3 Facial Recognition Prototype

Voice-activated facial recognition system integrated with the Skyy Facial Recognition MCP server, enhanced with Gemma 3 for natural language understanding.

## Overview

This prototype demonstrates how to build a voice-activated AI assistant that:

1. **Listens** for wake words ("Skyy, recognize me", "Skyy, remember me", "Skyy, forget me")
2. **Recognizes** users via facial recognition
3. **Registers** new users with voice-captured names
4. **Deletes** user profiles with multi-step confirmation
5. **Understands** natural language confirmations (yes/no responses in natural ways)
6. **Manages** user privacy with camera permission requests

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      VOICE ORCHESTRATION SYSTEM                         │
│              (Speech Recognition, Vision, MCP Integration)              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Speech     │ │   Webcam     │ │  MCP Client  │
            │  Recognition │ │   Capture    │ │  (OAuth 2.1) │
            │   + Whisper  │ │  + InsightFace│ │ Recognition, │
            │              │ │              │ │ Registration,│
            │              │ │              │ │   Deletion   │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    ├───────────────┴───────────────┤
                    │                               │
                    ▼                               ▼
            ┌──────────────────┐         ┌──────────────────┐
            │ Orchestrators    │         │  Gemma 3 (LLM)   │
            │ - Registration   │         │   via Ollama      │
            │ - Deletion       │         │ - Confirmations   │
            │ - Recognition    │         │ - Greetings      │
            └──────────────────┘         └──────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
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
pip install -r src/gemma_voice_assistant/requirements.txt

# Or install individually:
pip install ollama vosk pyttsx3 sounddevice soundfile webrtcvad-wheels faster-whisper noisereduce
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
src/gemma_voice_assistant/
├── main.py                           # Main orchestration script
├── config.py                         # Configuration constants
├── requirements.txt                  # Additional dependencies
├── README.md                         # This file
└── modules/
    ├── __init__.py
    ├── speech_orchestrator.py        # Voice recognition & TTS orchestrator
    ├── vision.py                     # Webcam capture
    ├── mcp_client.py                 # Async MCP client (OAuth-aware)
    ├── mcp_sync_facade.py            # Synchronous MCP facade
    ├── permission.py                 # User consent handling
    ├── voice_activity_detector.py    # VAD-based speech recording
    ├── whisper_transcription_engine.py  # Whisper AI transcription
    ├── registration_orchestrator.py  # Voice registration flow
    └── deletion_orchestrator.py      # User deletion flow
```

## Configuration

Edit `config.py` to match your environment:

```python
# Paths - adjust if your virtual environment is elsewhere
MCP_PYTHON_PATH = PROJECT_ROOT / "facial_mcp_py311" / "Scripts" / "python.exe"
MCP_SERVER_SCRIPT = PROJECT_ROOT / "src" / "skyy_facial_recognition_mcp.py"

# Ollama model
OLLAMA_MODEL = "gemma3:4b"  # or "gemma3:12b" for better reasoning

# Wake words for recognition
WAKE_WORD = "skyy recognize me"
WAKE_WORD_ALTERNATIVES = ["sky recognize me", "sky recognise me", "skyy recognise me"]

# Wake words for registration
REGISTRATION_WAKE_WORD = "skyy remember me"
REGISTRATION_WAKE_WORD_ALTERNATIVES = ["sky remember me", "skyy remember me"]

# Wake words for deletion
DELETION_WAKE_WORD = "skyy forget me"
DELETION_WAKE_WORD_ALTERNATIVES = ["sky forget me", "skyy delete me", "sky delete me"]

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
   cd src/gemma_voice_assistant
   python main.py
   ```

4. **Interact**:
   - Say **"Skyy, recognize me"** for facial recognition
   - Say **"Skyy, remember me"** to register a new profile
   - Say **"Skyy, forget me"** to delete your profile
   - Grant permission when asked
   - Look at the camera
   - Follow the voice prompts

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

## Features

### 1. Facial Recognition ("Skyy, recognize me")

Recognizes registered users and generates personalized greetings:
- Face detection and recognition using InsightFace
- OAuth 2.1 authentication with MCP server
- Personalized greetings generated by Gemma 3
- Offers registration for unknown users

### 2. Voice Registration ("Skyy, remember me")

Register new users with voice-captured names:
- Voice Activity Detection (VAD) for automatic speech capture
- Whisper AI for accurate name transcription
- **Natural language confirmation** using Gemma 3 LLM
- Multi-step confirmation to verify correct name
- Face photo capture and storage
- Prevents duplicate registrations

**Example Flow:**
```
USER: "Skyy, remember me"
SYSTEM: "Please say your full name after the beep."
USER: "My name is John Smith"
SYSTEM: "I heard John Smith. Is that correct? Say yes or no."
USER: "Yes"
SYSTEM: "Please look at the camera."
SYSTEM: "Registration complete. Welcome, John Smith!"
```

### 3. User Deletion ("Skyy, forget me")

Delete user profiles with multi-step safety confirmation:
- Face recognition to verify identity
- **Natural language confirmation** using Gemma 3 LLM
- Voice confirmation of recognized name
- Clear explanation of deletion consequences
- Final confirmation required
- Permanent deletion of all user data

**Safety Features:**
- Multi-step confirmation prevents accidental deletion
- Face authentication required (must be physically present)
- Identity verification via voice
- **Smart confirmation parsing** - understands natural responses like "Sure thing", "Not really", "Go ahead"
- Explicit consent at each step
- Default to cancel on unclear responses
- Automatic fallback to keyword matching if LLM unavailable

**Example Flow (with Natural Language Understanding):**
```
USER: "Skyy, forget me"
SYSTEM: "I need to verify your identity before deleting your profile."
SYSTEM: "Please look at the camera so I can confirm your identity."
SYSTEM: "I recognized you as John Smith. Is that correct? Say yes or no."
USER: "Sure, that's me"  ← Natural language response!
SYSTEM: "John Smith, this will permanently delete all your data from the system,
         including your face profile and all associated information.
         This action cannot be undone.
         Say yes to proceed with deletion, or no to cancel."
USER: "Go ahead"  ← Natural language response!
SYSTEM: "Deleting your profile now. Please wait."
SYSTEM: "Your profile has been successfully deleted, John Smith. Goodbye."
```

**Accepted Confirmation Phrases:**
- Affirmative: "Yes", "Yeah", "Sure", "Absolutely", "Go ahead", "Correct", "That's right"
- Negative: "No", "Nope", "Not really", "I don't think so", "Wrong", "Try again"
- Unclear: "Maybe", "I'm not sure" → Safely cancels the operation

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
users = mcp_facade.list_users(access_token)

# Get database statistics
stats = mcp_facade.get_database_stats(access_token)

# Check system health
health = mcp_facade.get_health_status(access_token)

# Delete a user (requires user_id)
result = mcp_facade.delete_user(access_token, user_id)
```

## License

MIT License - see the main project LICENSE file.

## Acknowledgments

- Skyy Facial Recognition MCP Server (Team 5)
- Ollama Team for local LLM inference
- Google for Speech Recognition API
- InsightFace for facial recognition models
