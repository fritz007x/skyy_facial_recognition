"""
Gemma 3n Live Voice Assistant - Voice-Activated Facial Recognition

Voice-activated facial recognition using Gemma 3n native audio with MCP server integration.
Refactored based on transcribe_commands.py for improved audio handling and reliability.

Workflow:
1. Continuously listen to microphone
2. Process audio with Gemma 3n native audio understanding
3. Detect "Hello Gemma" wake word
4. Capture face from webcam
5. Recognize via MCP server
6. Greet user by name with TTS

Requirements:
    pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 librosa>=0.11.0
    pip install sounddevice soundfile pyttsx3 opencv-python mcp
"""

import argparse
import sys
import os
import json
import base64
import time
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import torch
import sounddevice as sd
import soundfile as sf
import numpy as np
import cv2
import pyttsx3

from transformers import AutoProcessor, AutoModelForImageTextToText
from huggingface_hub import login, whoami
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))
from oauth_config import OAuthConfig


class Gemma3nVoiceAssistant:
    """Voice assistant using Gemma 3n native audio with MCP facial recognition."""

    def __init__(self, model_id: str = "google/gemma-3n-E2B-it"):
        """
        Initialize voice assistant.

        Args:
            model_id: Hugging Face model ID (E2B-it or E4B-it)
        """
        self.model_id = model_id
        self.sample_rate = 16000  # Required by Gemma 3n
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.running = False
        self.access_token = None

        # Wake word phrases
        self.wake_words = ["hello gemma", "hey gemma", "hi gemma"]

        print(f"[System] Initializing Gemma 3n Voice Assistant")
        print(f"[System] Model: {model_id}")
        print(f"[System] Device: {self.device}")

        # Initialize components
        self._check_auth()
        self._load_model()
        self._setup_tts()
        self._setup_oauth()

    def _check_auth(self):
        """Check Hugging Face authentication."""
        try:
            whoami()
            print("[System] Authenticated with Hugging Face")
        except Exception:
            token = os.environ.get("HF_TOKEN")
            if token:
                print("[System] Authenticating with HF_TOKEN...")
                login(token=token)
            else:
                print("[WARNING] Not authenticated. Model may fail to load.")
                print("[WARNING] Set HF_TOKEN or run: huggingface-cli login")

    def _load_model(self):
        """Load Gemma 3n model and processor."""
        # Warn about E4B on CPU
        if "E4B" in self.model_id and self.device == "cpu":
            print("\n" + "=" * 70)
            print("[WARNING] E4B model on CPU requires ~16GB RAM and loads VERY slowly")
            print("[WARNING] Recommended: Use E2B model for CPU systems")
            print("[WARNING] Loading may take 20-40 minutes with memory swapping...")
            print("=" * 70 + "\n")

        print(f"[System] Loading model...")
        print("[System] This may take several minutes. Please be patient...")

        try:
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            # Add progress callback for model loading
            print("[System] Loading model weights (this is the slow part)...")
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else "cpu",
                low_cpu_mem_usage=True
            )
            print("[System] Model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            sys.exit(1)

    def _setup_tts(self):
        """Setup text-to-speech engine."""
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')

        # Try to use female voice
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        self.tts_engine.setProperty('rate', 175)
        self.tts_engine.setProperty('volume', 0.9)

    def _setup_oauth(self):
        """Setup OAuth and get access token."""
        oauth_config = OAuthConfig()
        client_id = "gemma3n_live_assistant"
        clients = oauth_config.load_clients()

        if client_id not in clients:
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma 3n Live Voice Assistant"
            )

        self.access_token = oauth_config.create_access_token(client_id)
        print("[System] OAuth configured\n")

    def speak(self, text: str):
        """Speak text using TTS."""
        print(f"[Gemma] Speaking: \"{text}\"")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def record_audio(self, duration: float = 3.0) -> Optional[str]:
        """
        Record audio from microphone for fixed duration.

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to temporary WAV file or None if failed
        """
        try:
            # Record
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()

            # Check for silence
            rms = np.sqrt(np.mean(recording**2))
            if rms < 0.001:
                print(f"[Debug] Audio too quiet (RMS: {rms:.4f})")
                return None

            # Convert to 16-bit PCM (better compatibility)
            recording_int16 = (recording * 32767).astype(np.int16)

            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(temp_file.name, recording_int16, self.sample_rate, subtype='PCM_16')

            return temp_file.name

        except Exception as e:
            print(f"[ERROR] Recording failed: {e}")
            return None

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio using Gemma 3n native audio.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text (lowercase)
        """
        if not os.path.exists(audio_path):
            print(f"[ERROR] File not found: {audio_path}")
            return ""

        try:
            # Prepare inputs
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "audio", "audio": audio_path},
                        {"type": "text", "text": "Transcribe this audio."}
                    ]
                }
            ]

            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )

            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=64,
                    do_sample=False,
                    top_p=None,
                    top_k=None
                )

            # Decode
            transcription = self.processor.batch_decode(
                outputs,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]

            # Clean up prompt from output
            if "model" in transcription:
                transcription = transcription.split("model")[-1].strip()

            return transcription.lower()

        except Exception as e:
            print(f"[ERROR] Transcription failed: {e}")
            return ""

    def detect_wake_word(self, transcription: str) -> bool:
        """
        Check if transcription contains wake word.

        Args:
            transcription: Transcribed text (lowercase)

        Returns:
            True if wake word detected
        """
        for wake_word in self.wake_words:
            if wake_word in transcription:
                print(f"[Gemma] Wake word detected: '{wake_word}'")
                return True
        return False

    def capture_face_image(self) -> Optional[str]:
        """
        Capture image from webcam.

        Returns:
            Base64-encoded image or None if failed
        """
        print("[Gemma] Capturing image...")

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

        print("[Gemma] Image captured")

        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()

        # Convert to base64
        return base64.b64encode(image_bytes).decode('utf-8')

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

    async def handle_wake_word(self):
        """Handle wake word detection - capture and recognize face."""
        # Acknowledge
        self.speak("Yes?")

        # Capture image
        image_data = self.capture_face_image()

        if not image_data:
            self.speak("I couldn't see you.")
            return

        # Recognize face
        try:
            result = await self.recognize_face(image_data)
            status = result.get('status', 'error')

            if status == 'recognized':
                user = result.get('user', {})
                user_name = user.get('name', 'friend')
                confidence = result.get('confidence', 0)

                print(f"[Gemma] Recognized: {user_name} ({confidence:.1%})")
                self.speak(f"Hello, {user_name}!")

            elif status == 'not_recognized':
                print("[Gemma] Face not recognized")
                self.speak("Hello! I don't recognize you.")

            elif status == 'low_confidence':
                user = result.get('user', {})
                user_name = user.get('name', 'there')
                print(f"[Gemma] Low confidence: {user_name}")
                self.speak(f"Hello! Are you {user_name}?")

            else:
                message = result.get('message', 'Unknown error')
                print(f"[ERROR] {message}")

                if 'no face' in message.lower():
                    self.speak("I don't see anyone.")
                else:
                    self.speak("I'm having trouble right now.")

        except Exception as e:
            print(f"[ERROR] Recognition failed: {e}")
            self.speak("I'm having trouble with facial recognition.")

    async def listen_loop(self, duration: float = 3.0):
        """
        Main listening loop.

        Args:
            duration: Audio chunk duration in seconds
        """
        print("\n[Gemma] Starting continuous listening...")
        print(f"[Gemma] Recording in {duration}s chunks")
        print("[Gemma] Say 'Hello Gemma' to activate")
        print("[Gemma] Press Ctrl+C to exit\n")

        self.speak("Voice assistant activated. Say Hello Gemma to get started.")

        self.running = True

        try:
            while self.running:
                print("[Listening] Recording...", end='\r', flush=True)

                # Record audio chunk
                audio_path = self.record_audio(duration=duration)

                if not audio_path:
                    time.sleep(0.1)
                    continue

                # Transcribe
                print("[Processing] Transcribing...                    ", end='\r', flush=True)
                transcription = self.transcribe(audio_path)

                # Cleanup temp file
                try:
                    os.unlink(audio_path)
                except:
                    pass

                if transcription:
                    print(f"[Heard] \"{transcription}\"                              ")

                    # Check for wake word
                    if self.detect_wake_word(transcription):
                        print("\n" + "=" * 70)

                        # Handle wake word
                        await self.handle_wake_word()

                        print("=" * 70)
                        print("[Gemma] Ready for next command...\n")

        except KeyboardInterrupt:
            print("\n\n[Gemma] Shutting down...")
            self.speak("Goodbye!")
            self.running = False


def check_requirements():
    """Check if all requirements are met."""
    print("[System] Checking requirements...")

    # Check microphone
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if input_devices:
            print(f"[OK] Microphone available ({len(input_devices)} input devices)")
        else:
            print("[ERROR] No microphone detected")
            return False
    except Exception as e:
        print(f"[ERROR] Audio check failed: {e}")
        return False

    # Check webcam
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("[OK] Webcam available")
        cap.release()
    else:
        print("[ERROR] No webcam detected")
        return False

    return True


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Gemma 3n Live Voice Assistant with Facial Recognition"
    )
    parser.add_argument(
        '--model',
        type=str,
        default="google/gemma-3n-E2B-it",
        choices=["google/gemma-3n-E2B-it", "google/gemma-3n-E4B-it"],
        help='Gemma 3n model variant (E2B=faster, E4B=more accurate)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=3.0,
        help='Audio chunk duration in seconds (default: 3.0)'
    )

    args = parser.parse_args()

    # Check requirements
    if not check_requirements():
        print("\n[ERROR] Requirements check failed")
        return 1

    print("\n" + "=" * 70)
    print("         GEMMA 3N LIVE VOICE ASSISTANT")
    print("         Voice-Activated Facial Recognition")
    print("=" * 70)
    print(f"\nModel: {args.model}")
    print(f"Chunk duration: {args.duration}s")
    print("Wake word: 'Hello Gemma', 'Hey Gemma', or 'Hi Gemma'")
    print("\n" + "=" * 70 + "\n")

    try:
        # Initialize assistant
        assistant = Gemma3nVoiceAssistant(model_id=args.model)

        # Run listening loop
        await assistant.listen_loop(duration=args.duration)

        return 0

    except Exception as e:
        print(f"\n[ERROR] Failed to start assistant: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
