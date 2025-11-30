"""
Gemma 3n Voice Assistant - Full Integration Test

Tests the complete voice assistant workflow using pre-recorded audio:
1. Load pre-recorded "Hello Gemma" wake word audio
2. Transcribe with Whisper speech recognition
3. Detect wake word
4. Capture face image from webcam
5. Recognize face via MCP server
6. Greet user by name using TTS

This is an end-to-end test without requiring live microphone input.

Usage:
    python test_gemma3n_full_integration.py <path_to_audio_file>

Example:
    python test_gemma3n_full_integration.py "Voice Recording.m4a"
"""

import asyncio
import sys
import json
import base64
import cv2
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Whisper for audio transcription
try:
    import whisper
except ImportError:
    print("ERROR: whisper not installed")
    print("Install with: pip install openai-whisper")
    sys.exit(1)

# Text-to-speech
try:
    import pyttsx3
except ImportError:
    print("ERROR: pyttsx3 not installed")
    print("Install with: pip install pyttsx3")
    sys.exit(1)

# MCP client
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("ERROR: mcp not installed")
    print("Install with: pip install mcp")
    sys.exit(1)

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from oauth_config import OAuthConfig


class Gemma3nIntegrationTest:
    """Full integration test for Gemma 3n voice assistant."""

    def __init__(self, audio_file: Path):
        """
        Initialize integration test.

        Args:
            audio_file: Path to pre-recorded wake word audio
        """
        self.audio_file = audio_file
        self.tts_engine = pyttsx3.init()
        self.access_token = None

        # Configure TTS
        self._configure_tts()

        # Load Whisper model
        print("\n[System] Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("[System] Whisper model loaded")

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
        print("\n[Test] Setting up OAuth...")
        oauth_config = OAuthConfig()
        client_id = "gemma3n_integration_test"
        clients = oauth_config.load_clients()

        if client_id not in clients:
            print(f"[OAuth] Creating client: {client_id}")
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma 3n Integration Test"
            )

        self.access_token = oauth_config.create_access_token(client_id)
        print(f"[OAuth] Access token generated")

    def get_mcp_session(self):
        """Create MCP session context manager."""
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir

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

    def transcribe_wake_word(self) -> Optional[str]:
        """
        Transcribe pre-recorded wake word audio.

        Returns:
            Transcribed text or None if failed
        """
        print(f"\n[Test] Transcribing audio: {self.audio_file.name}")

        try:
            result = self.whisper_model.transcribe(str(self.audio_file))
            transcription = result['text'].strip().lower()
            print(f"[Whisper] Transcribed: \"{transcription}\"")
            return transcription

        except Exception as e:
            print(f"[ERROR] Whisper transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def detect_wake_word(self, transcription: str) -> bool:
        """
        Check if transcription contains wake word.

        Args:
            transcription: Transcribed text (lowercase)

        Returns:
            True if wake word detected
        """
        wake_words = ["hello gemma", "hey gemma", "hi gemma"]

        for wake_word in wake_words:
            if wake_word in transcription:
                print(f"[Test] Wake word detected: \"{wake_word}\"")
                return True

        print(f"[Test] No wake word detected in: \"{transcription}\"")
        return False

    def capture_face_image(self) -> Optional[str]:
        """
        Capture image from webcam and return as base64.

        Returns:
            Base64-encoded image or None if failed
        """
        print("\n[Test] Opening camera...")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Could not open webcam")
            return None

        # Warm up camera
        import time
        time.sleep(0.5)

        # Capture frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("[ERROR] Failed to capture image")
            return None

        print("[Test] Image captured!")

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
        print("\n[Test] Connecting to MCP server...")

        async with self.get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                print("[Test] Analyzing face...")

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

    async def run_full_test(self) -> bool:
        """
        Run complete integration test.

        Returns:
            True if test passed, False otherwise
        """
        print("\n" + "=" * 70)
        print("GEMMA 3N VOICE ASSISTANT - FULL INTEGRATION TEST")
        print("=" * 70)
        print(f"\nAudio File: {self.audio_file}")
        print("Test Flow: Wake Word → Camera → Face Recognition → TTS Greeting")
        print("\n" + "=" * 70)

        # Setup OAuth
        self.setup_oauth()

        # Step 1: Transcribe wake word
        print("\n### STEP 1: WAKE WORD TRANSCRIPTION ###")
        transcription = self.transcribe_wake_word()

        if not transcription:
            print("[FAIL] Failed to transcribe audio")
            return False

        # Step 2: Detect wake word
        print("\n### STEP 2: WAKE WORD DETECTION ###")
        wake_word_detected = self.detect_wake_word(transcription)

        if not wake_word_detected:
            print("[FAIL] Wake word not detected")
            return False

        # Acknowledge wake word
        print("\n[Test] Wake word detected! Activating assistant...")
        self.speak("Yes?")

        # Step 3: Capture face
        print("\n### STEP 3: FACE CAPTURE ###")
        image_data = self.capture_face_image()

        if not image_data:
            self.speak("I couldn't see you. Please make sure the camera is working.")
            return False

        # Step 4: Recognize face via MCP
        print("\n### STEP 4: FACE RECOGNITION (MCP SERVER) ###")
        try:
            result = await self.recognize_face(image_data)
            status = result.get('status', 'error')

            print(f"[Test] MCP Response Status: {status}")

            if status == 'recognized':
                # User recognized!
                user = result.get('user', {})
                user_name = user.get('name', 'friend')
                confidence = result.get('confidence', 0)

                print(f"[SUCCESS] Recognized: {user_name}")
                print(f"[SUCCESS] Confidence: {confidence:.1%}")

                # Step 5: TTS Greeting
                print("\n### STEP 5: TTS GREETING ###")
                greeting = f"Hello, {user_name}!"
                self.speak(greeting)

                return True

            elif status == 'not_recognized':
                print("[PARTIAL] Face detected but not recognized")
                self.speak("Hello! I don't recognize you. Would you like to register?")
                return False

            elif status == 'low_confidence':
                user = result.get('user', {})
                user_name = user.get('name', 'there')
                print(f"[PARTIAL] Low confidence match: {user_name}")
                self.speak(f"Hello! Are you {user_name}?")
                return False

            else:
                message = result.get('message', 'Unknown error')
                print(f"[ERROR] {message}")

                if 'no face' in message.lower() or 'no faces found' in message.lower():
                    self.speak("I don't see anyone. Please position yourself in front of the camera.")
                else:
                    self.speak("I'm having trouble recognizing faces right now.")

                return False

        except Exception as e:
            print(f"[ERROR] Recognition failed: {e}")
            import traceback
            traceback.print_exc()
            self.speak("I'm having trouble with the facial recognition system.")
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Full integration test for Gemma 3n voice assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'audio_file',
        type=str,
        help='Path to pre-recorded "Hello Gemma" audio file'
    )

    args = parser.parse_args()

    audio_file = Path(args.audio_file)

    if not audio_file.exists():
        print(f"\n[ERROR] Audio file not found: {audio_file}")
        return 1

    try:
        # Create and run test
        test = Gemma3nIntegrationTest(audio_file)
        success = await test.run_full_test()

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        if success:
            print("\n[SUCCESS] Full integration test PASSED!")
            print("All components working correctly:")
            print("  ✓ Whisper speech recognition")
            print("  ✓ Wake word detection")
            print("  ✓ Webcam capture")
            print("  ✓ MCP server communication")
            print("  ✓ Face recognition")
            print("  ✓ TTS greeting")
        else:
            print("\n[FAILURE] Integration test FAILED!")
            print("Check the errors above for details.")

        print("\n" + "=" * 70)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


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
        print("Please connect a webcam and try again")
        sys.exit(1)

    # Run test
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
