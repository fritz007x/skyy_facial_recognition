"""
Gemma - Voice-Activated Facial Recognition Assistant

A voice-controlled assistant that responds to "Hello Gemma" by:
1. Capturing an image from webcam
2. Recognizing the face using MCP server
3. Greeting the user by name using text-to-speech

Requirements:
- Microphone for wake word detection
- Webcam for facial recognition
- Speakers for audio response
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

# Speech recognition
try:
    import speech_recognition as sr
except ImportError:
    print("ERROR: speech_recognition not installed")
    print("Install with: pip install SpeechRecognition pyaudio")
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

# Add src directory to path for OAuth imports
sys.path.insert(0, str(Path(__file__).parent))
from oauth_config import OAuthConfig


class GemmaVoiceAssistant:
    """
    Voice-activated facial recognition assistant.

    Wake word: "Hello Gemma"
    Action: Capture face, recognize, and greet user
    """

    def __init__(self):
        """Initialize Gemma voice assistant."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.access_token = None
        self.running = False

        # Configure TTS
        self._configure_tts()

        # Calibrate microphone for ambient noise
        self._calibrate_microphone()

    def _configure_tts(self):
        """Configure text-to-speech engine."""
        # Set voice properties
        voices = self.tts_engine.getProperty('voices')

        # Try to use a female voice (Gemma sounds better with female voice)
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        # Set speech rate (default is 200)
        self.tts_engine.setProperty('rate', 175)

        # Set volume (0.0 to 1.0)
        self.tts_engine.setProperty('volume', 0.9)

    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise."""
        print("\n[Gemma] Calibrating microphone for ambient noise...")
        print("[Gemma] Please wait (3 seconds)...", flush=True)

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=3)

        print("[Gemma] Microphone calibrated!\n")

    def speak(self, text: str):
        """
        Speak text using TTS.

        Args:
            text: Text to speak
        """
        print(f"[Gemma] Speaking: \"{text}\"")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def setup_oauth(self):
        """Setup OAuth and get access token."""
        oauth_config = OAuthConfig()

        client_id = "gemma_assistant"
        clients = oauth_config.load_clients()

        if client_id not in clients:
            print(f"[OAuth] Creating client: {client_id}")
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma Voice Assistant"
            )

        self.access_token = oauth_config.create_access_token(client_id)
        print(f"[OAuth] Access token generated\n")

    def get_mcp_session(self):
        """Create and return MCP session context manager."""
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir.parent

        python_path = project_root / "facial_mcp_py311" / "Scripts" / "python.exe"
        server_script = project_root / "src" / "skyy_facial_recognition_mcp.py"

        if not python_path.exists():
            raise FileNotFoundError(f"Python interpreter not found: {python_path}")
        if not server_script.exists():
            raise FileNotFoundError(f"MCP server not found: {server_script}")

        server_params = StdioServerParameters(
            command=str(python_path),
            args=[str(server_script)],
            env=None
        )

        return stdio_client(server_params)

    def capture_face_image(self) -> Optional[str]:
        """
        Capture an image from webcam and return as base64.

        Returns:
            Base64-encoded image or None if capture failed
        """
        print("[Gemma] Opening camera...")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Could not open webcam")
            return None

        # Give camera time to warm up
        time.sleep(0.5)

        # Capture frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("[ERROR] Failed to capture image")
            return None

        print("[Gemma] Image captured!")

        # Encode image to JPEG
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
        Listen for the wake word "Hello Gemma".

        Returns:
            True if wake word detected, False otherwise
        """
        with self.microphone as source:
            print("[Gemma] Listening for 'Hello Gemma'...", flush=True)

            try:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

                # Recognize speech
                text = self.recognizer.recognize_google(audio).lower()
                print(f"[Heard] \"{text}\"")

                # Check for wake word
                if "hello gemma" in text or "hey gemma" in text:
                    return True

            except sr.WaitTimeoutError:
                # Timeout - just continue listening
                pass
            except sr.UnknownValueError:
                # Could not understand audio
                pass
            except sr.RequestError as e:
                print(f"[ERROR] Speech recognition error: {e}")
                time.sleep(1)

            return False

    async def handle_wake_word(self):
        """Handle wake word detection - capture and recognize face."""
        # Acknowledge wake word
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
                # Face detected but not recognized
                print("[Gemma] Face not recognized")
                self.speak("Hello! I don't recognize you. Would you like to register?")

            elif status == 'low_confidence':
                # Low confidence match
                user = result.get('user', {})
                user_name = user.get('name', 'there')
                print(f"[Gemma] Low confidence match: {user_name}")
                self.speak(f"Hello! Are you {user_name}?")

            else:
                # Error
                message = result.get('message', 'Unknown error')
                print(f"[ERROR] {message}")

                if 'no face' in message.lower() or 'no faces found' in message.lower():
                    self.speak("I don't see anyone. Please position yourself in front of the camera.")
                else:
                    self.speak("I'm having trouble recognizing faces right now. Please try again.")

        except Exception as e:
            print(f"[ERROR] Recognition failed: {e}")
            self.speak("I'm having trouble with the facial recognition system.")

    async def run(self):
        """Run the Gemma voice assistant main loop."""
        print("\n" + "=" * 70)
        print("                    GEMMA VOICE ASSISTANT")
        print("                  Voice-Activated Face Recognition")
        print("=" * 70)
        print("\nWake word: 'Hello Gemma'")
        print("Action: Recognize face and greet user by name")
        print("\nPress Ctrl+C to exit\n")
        print("=" * 70)

        # Setup OAuth
        self.setup_oauth()

        # Welcome message
        self.speak("Gemma voice assistant activated. Say Hello Gemma to get started.")

        self.running = True

        try:
            while self.running:
                # Listen for wake word
                if self.listen_for_wake_word():
                    print("[Gemma] Wake word detected!\n")

                    # Handle the request
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
        assistant = GemmaVoiceAssistant()
        await assistant.run()

    except Exception as e:
        print(f"\n[ERROR] Failed to start Gemma: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check requirements
    print("\n[System] Checking requirements...")

    # Check microphone
    try:
        sr.Microphone.list_microphone_names()
        print("[OK] Microphone available")
    except:
        print("[ERROR] No microphone detected")
        print("Please connect a microphone and try again")
        sys.exit(1)

    # Check webcam
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("[OK] Webcam available")
        cap.release()
    else:
        print("[ERROR] No webcam detected")
        print("Please connect a webcam and try again")
        sys.exit(1)

    # Run assistant
    asyncio.run(main())
