"""
Gemma 3n Voice Assistant - Using Native Speech Recognition

A voice-activated assistant using Gemma 3n's native multimodal capabilities:
1. Listens for "Hello Gemma" using Gemma 3n's audio understanding
2. Captures face image from webcam
3. Recognizes face using MCP server
4. Greets user by name using text-to-speech

Requires:
- Gemma 3n model (via Ollama)
- Microphone for audio input
- Webcam for facial recognition
- Speakers for TTS output
"""

import asyncio
import sys
import json
import base64
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import time
import sounddevice as sd
import soundfile as sf
import tempfile

# Ollama for Gemma 3n
try:
    import ollama
except ImportError:
    print("ERROR: ollama not installed")
    print("Install with: pip install ollama")
    print("Then run: ollama pull gemma3n")
    sys.exit(1)

# Text-to-speech
try:
    import pyttsx3
except ImportError:
    print("ERROR: pyttsx3 not installed")
    print("Install with: pip install pyttsx3")
    sys.exit(1)

# MCP client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))
from oauth_config import OAuthConfig


class Gemma3nVoiceAssistant:
    """
    Voice-activated facial recognition assistant using Gemma 3n.

    Uses Gemma 3n's native multimodal capabilities for speech recognition.
    """

    def __init__(self):
        """Initialize Gemma 3n voice assistant."""
        self.tts_engine = pyttsx3.init()
        self.access_token = None
        self.running = False

        # Audio recording parameters
        self.sample_rate = 16000  # 16kHz for speech
        self.channels = 1  # Mono
        self.wake_word_duration = 3  # Listen for 3 seconds at a time

        # Configure TTS
        self._configure_tts()

        # Verify Gemma 3n is available
        self._check_gemma3n()

    def _check_gemma3n(self):
        """Verify Gemma 3n model is available via Ollama."""
        print("\n[System] Checking Gemma 3n availability...")

        try:
            # List available models
            response = ollama.list()

            # Check if Ollama is running and returned models
            if not hasattr(response, 'models'):
                print("[ERROR] Unexpected response from Ollama")
                print("Please verify Ollama is running properly")
                sys.exit(1)

            # Extract model names from Model objects
            # Each model has a .model attribute (not ['name'])
            model_names = [model.model for model in response.models]

            if not model_names:
                print("[ERROR] No models found in Ollama")
                print("\nPlease install a Gemma model:")
                print("  ollama pull gemma3n:2b    # 2B parameter model")
                print("  or")
                print("  ollama pull gemma3n:4b    # 4B parameter model")
                sys.exit(1)

            # Check for gemma3n variants
            gemma_models = [m for m in model_names if 'gemma' in m.lower() and '3' in m]

            if not gemma_models:
                print("[ERROR] Gemma 3n not found in Ollama")
                print(f"\nFound models: {', '.join(model_names)}")
                print("\nPlease install Gemma 3n:")
                print("  ollama pull gemma3n:2b    # 2B parameter model")
                print("  or")
                print("  ollama pull gemma3n:4b    # 4B parameter model")
                sys.exit(1)

            # Use the first available Gemma 3n model
            self.gemma_model = gemma_models[0]
            print(f"[OK] Using model: {self.gemma_model}")

        except AttributeError as e:
            print(f"[ERROR] Failed to access Ollama model list: {e}")
            print("\nMake sure you're using the latest Ollama Python client:")
            print("  pip install --upgrade ollama")
            sys.exit(1)
        except ConnectionError as e:
            print(f"[ERROR] Cannot connect to Ollama service: {e}")
            print("\nMake sure Ollama is running:")
            print("  1. Install Ollama from https://ollama.ai")
            print("  2. Start Ollama service")
            print("  3. Pull Gemma 3n: ollama pull gemma3n")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to connect to Ollama: {e}")
            print(f"Error type: {type(e).__name__}")
            print("\nMake sure Ollama is running:")
            print("  1. Install Ollama from https://ollama.ai")
            print("  2. Start Ollama service")
            print("  3. Pull Gemma 3n: ollama pull gemma3n")
            sys.exit(1)

    def _configure_tts(self):
        """Configure text-to-speech engine."""
        voices = self.tts_engine.getProperty('voices')

        # Try to use a female voice
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        self.tts_engine.setProperty('rate', 175)
        self.tts_engine.setProperty('volume', 0.9)

    def speak(self, text: str):
        """Speak text using TTS."""
        print(f"[Gemma] Speaking: \"{text}\"")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def setup_oauth(self):
        """Setup OAuth and get access token."""
        oauth_config = OAuthConfig()
        client_id = "gemma3n_assistant"
        clients = oauth_config.load_clients()

        if client_id not in clients:
            print(f"[OAuth] Creating client: {client_id}")
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma 3n Voice Assistant"
            )

        self.access_token = oauth_config.create_access_token(client_id)
        print(f"[OAuth] Access token generated\n")

    def get_mcp_session(self):
        """Create MCP session context manager."""
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir.parent

        python_path = project_root / "facial_mcp_py311" / "Scripts" / "python.exe"
        server_script = project_root / "src" / "skyy_facial_recognition_mcp.py"

        if not python_path.exists():
            raise FileNotFoundError(f"Python not found: {python_path}")
        if not server_script.exists():
            raise FileNotFoundError(f"MCP server not found: {server_script}")

        server_params = StdioServerParameters(
            command=str(python_path),
            args=[str(server_script)],
            env=None
        )

        return stdio_client(server_params)

    def record_audio(self, duration: float) -> str:
        """
        Record audio from microphone and save to temporary file.

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to temporary audio file
        """
        print(f"[Gemma] Recording audio ({duration}s)...")

        # Record audio
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )
        sd.wait()  # Wait for recording to complete

        # Save to temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(temp_file.name, audio_data, self.sample_rate)

        return temp_file.name

    def transcribe_audio_with_gemma3n(self, audio_path: str) -> str:
        """
        Transcribe audio using Gemma 3n's native speech recognition.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        print("[Gemma 3n] Transcribing audio...")

        try:
            # Read audio file as bytes
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()

            # Use Gemma 3n for transcription
            # Gemma 3n accepts audio input natively
            response = ollama.generate(
                model=self.gemma_model,
                prompt="Transcribe the following audio to text:",
                images=[audio_bytes],  # Audio is passed as binary data
                stream=False
            )

            transcription = response['response'].strip()
            print(f"[Gemma 3n] Transcribed: \"{transcription}\"")

            return transcription.lower()

        except Exception as e:
            print(f"[ERROR] Gemma 3n transcription failed: {e}")
            return ""
        finally:
            # Clean up temporary file
            try:
                Path(audio_path).unlink()
            except:
                pass

    def capture_face_image(self) -> Optional[str]:
        """
        Capture image from webcam and return as base64.

        Returns:
            Base64-encoded image or None if failed
        """
        print("[Gemma] Opening camera...")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Could not open webcam")
            return None

        # Warm up camera
        time.sleep(0.5)

        # Capture frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("[ERROR] Failed to capture image")
            return None

        print("[Gemma] Image captured!")

        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()

        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        return image_base64

    async def recognize_face(self, image_data: str) -> Dict[str, Any]:
        """
        Recognize face using MCP server.

        Args:
            image_data: Base64-encoded image

        Returns:
            Recognition result dictionary
        """
        print("[Gemma] Connecting to MCP server...")

        async with self.get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                print("[Gemma] Analyzing face...")

                result = await session.call_tool(
                    "skyy_recognize_face",
                    arguments={
                        "params": {
                            "access_token": self.access_token,
                            "image_data": image_data,
                            "confidence_threshold": 0.25,
                            "response_format": "json"
                        }
                    }
                )

                if result and result.content:
                    content = result.content[0].text
                    return json.loads(content)

                return {"status": "error", "message": "No response from server"}

    def listen_for_wake_word(self) -> bool:
        """
        Listen for wake word using Gemma 3n's native speech recognition.

        Returns:
            True if wake word detected, False otherwise
        """
        print("[Gemma] Listening for 'Hello Gemma'...", flush=True)

        # Record audio
        audio_path = self.record_audio(self.wake_word_duration)

        # Transcribe using Gemma 3n
        transcription = self.transcribe_audio_with_gemma3n(audio_path)

        # Check for wake word
        if transcription:
            if "hello gemma" in transcription or "hey gemma" in transcription:
                return True

        return False

    async def handle_wake_word(self):
        """Handle wake word - capture and recognize face."""
        # Acknowledge
        self.speak("Yes?")

        # Capture image
        image_data = self.capture_face_image()

        if not image_data:
            self.speak("I couldn't see you. Please make sure the camera is working.")
            return

        # Recognize face
        try:
            result = await self.recognize_face(image_data)
            status = result.get('status', 'error')

            if status == 'recognized':
                # User recognized!
                user = result.get('user', {})
                user_name = user.get('name', 'friend')
                confidence = result.get('confidence', 0)

                print(f"[Gemma] Recognized: {user_name} (confidence: {confidence:.1%})")

                # Greet user by name
                greeting = f"Hello, {user_name}!"
                self.speak(greeting)

            elif status == 'not_recognized':
                print("[Gemma] Face not recognized")
                self.speak("Hello! I don't recognize you. Would you like to register?")

            elif status == 'low_confidence':
                user = result.get('user', {})
                user_name = user.get('name', 'there')
                print(f"[Gemma] Low confidence match: {user_name}")
                self.speak(f"Hello! Are you {user_name}?")

            else:
                message = result.get('message', 'Unknown error')
                print(f"[ERROR] {message}")

                if 'no face' in message.lower() or 'no faces found' in message.lower():
                    self.speak("I don't see anyone. Please position yourself in front of the camera.")
                else:
                    self.speak("I'm having trouble recognizing faces right now.")

        except Exception as e:
            print(f"[ERROR] Recognition failed: {e}")
            self.speak("I'm having trouble with the facial recognition system.")

    async def run(self):
        """Run the Gemma 3n voice assistant main loop."""
        print("\n" + "=" * 70)
        print("              GEMMA 3N VOICE ASSISTANT")
        print("        Native Multimodal Speech Recognition")
        print("=" * 70)
        print(f"\nModel: {self.gemma_model}")
        print("Wake word: 'Hello Gemma'")
        print("Action: Recognize face and greet user by name")
        print("\nPress Ctrl+C to exit\n")
        print("=" * 70)

        # Setup OAuth
        self.setup_oauth()

        # Welcome
        self.speak("Gemma 3n voice assistant activated. Say Hello Gemma to get started.")

        self.running = True

        try:
            while self.running:
                # Listen for wake word using Gemma 3n
                if self.listen_for_wake_word():
                    print("[Gemma] Wake word detected!\n")

                    # Handle request
                    await self.handle_wake_word()

                    print("\n" + "-" * 70)
                    print("[Gemma] Ready for next command...")
                    print("-" * 70 + "\n")

        except KeyboardInterrupt:
            print("\n\n[Gemma] Shutting down...")
            self.speak("Goodbye!")
            self.running = False


async def main():
    """Main entry point."""
    try:
        assistant = Gemma3nVoiceAssistant()
        await assistant.run()

    except Exception as e:
        print(f"\n[ERROR] Failed to start Gemma: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check requirements
    print("\n[System] Checking requirements...")

    # Check webcam
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("[OK] Webcam available")
        cap.release()
    else:
        print("[ERROR] No webcam detected")
        sys.exit(1)

    # Check audio devices
    try:
        devices = sd.query_devices()
        if devices:
            print("[OK] Audio devices available")
    except:
        print("[ERROR] No audio devices detected")
        sys.exit(1)

    # Run assistant
    asyncio.run(main())
