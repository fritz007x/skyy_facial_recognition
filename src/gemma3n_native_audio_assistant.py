"""
Gemma 3n Voice Assistant - Native Audio Processing

Uses Gemma 3n's native multimodal audio capabilities via Hugging Face Transformers.
This version processes audio directly through Gemma 3n's Universal Speech Model (USM)
without requiring external speech recognition libraries.

Features:
- Native audio understanding (no Whisper needed)
- Wake word detection using Gemma 3n
- Webcam facial recognition via MCP
- Text-to-speech greeting

Requirements:
- transformers>=4.53.0
- torch>=2.0.0
- torchaudio>=2.0.0
- timm>=0.9.0 (PyTorch Image Models - CRITICAL for Gemma 3n multimodal)
- pyttsx3 (TTS)
- opencv-python (webcam)
- huggingface-hub>=0.20.0

Setup:
    pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub
"""

import asyncio
import sys
import json
import base64
import cv2
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Comprehensive dependency checking with educational error messages
def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Check all required dependencies for Gemma 3n.

    Returns:
        Tuple of (all_ok: bool, missing_packages: List[str])
    """
    missing = []

    # Check torch first (required by other packages)
    try:
        import torch
    except ImportError:
        missing.append("torch>=2.0.0")

    # Check transformers
    try:
        import transformers
        # Verify version
        from packaging import version
        if version.parse(transformers.__version__) < version.parse("4.53.0"):
            missing.append(f"transformers>=4.53.0 (found {transformers.__version__})")
    except ImportError:
        missing.append("transformers>=4.53.0")

    # Check huggingface-hub
    try:
        import huggingface_hub
    except ImportError:
        missing.append("huggingface-hub>=0.20.0")

    # Check torchaudio
    try:
        import torchaudio
    except ImportError:
        missing.append("torchaudio>=2.0.0")

    # Check timm - CRITICAL for Gemma 3n multimodal
    try:
        import timm
    except ImportError:
        missing.append("timm>=0.9.0")

    # Check pyttsx3
    try:
        import pyttsx3
    except ImportError:
        missing.append("pyttsx3>=2.90")

    return len(missing) == 0, missing


def print_dependency_error(missing_packages: List[str]):
    """Print educational error message about missing dependencies."""
    print("\n" + "=" * 70)
    print("MISSING DEPENDENCIES FOR GEMMA 3N")
    print("=" * 70)
    print("\nThe following required packages are missing or outdated:")
    print()
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print()
    print("=" * 70)
    print("WHY THESE PACKAGES ARE NEEDED:")
    print("=" * 70)
    print()

    for pkg in missing_packages:
        if pkg.startswith("timm"):
            print("  timm (PyTorch Image Models):")
            print("    - CRITICAL for Gemma 3n's multimodal capabilities")
            print("    - Required even for audio-only use (Gemma 3n is unified multimodal)")
            print("    - Provides TimmWrapperModel for vision processing")
            print("    - Without this, you'll get: 'TimmWrapperModel requires the timm library'")
            print()
        elif pkg.startswith("transformers"):
            print("  transformers:")
            print("    - Provides the Gemma 3n model architecture")
            print("    - Version 4.53.0+ required for native audio support")
            print("    - Includes AutoProcessor and AutoModelForImageTextToText")
            print()
        elif pkg.startswith("torch"):
            print("  torch (PyTorch):")
            print("    - Core deep learning framework")
            print("    - Required for running neural network models")
            print()
        elif pkg.startswith("torchaudio"):
            print("  torchaudio:")
            print("    - Audio loading and preprocessing")
            print("    - Resamples audio to 16kHz for Gemma 3n")
            print()
        elif pkg.startswith("huggingface-hub"):
            print("  huggingface-hub:")
            print("    - Authentication for gated models")
            print("    - Model downloading and caching")
            print()
        elif pkg.startswith("pyttsx3"):
            print("  pyttsx3:")
            print("    - Text-to-speech for voice responses")
            print()

    print("=" * 70)
    print("HOW TO FIX:")
    print("=" * 70)
    print()
    print("1. Activate your virtual environment:")
    print("   facial_mcp_py311\\Scripts\\activate")
    print()
    print("2. Install all missing packages:")
    print("   pip install " + " ".join(missing_packages))
    print()
    print("   OR install all Gemma 3n dependencies at once:")
    print("   pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub pyttsx3")
    print()
    print("3. Verify installation:")
    print("   python -c \"import timm; print('timm version:', timm.__version__)\"")
    print()
    print("=" * 70)
    print("For complete setup instructions, see: GEMMA3N_QUICKSTART.md")
    print("=" * 70 + "\n")


# Check dependencies before importing
all_ok, missing = check_dependencies()
if not all_ok:
    print_dependency_error(missing)
    sys.exit(1)

# Now safe to import after verification
import torch

try:
    from transformers import AutoProcessor, AutoModelForImageTextToText
    from huggingface_hub import login, whoami, HfFolder
    from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError
except ImportError as e:
    print(f"\n[ERROR] Failed to import transformers or huggingface_hub: {e}")
    print("This should not happen after dependency check. Please reinstall:")
    print("  pip install --force-reinstall transformers>=4.53.0 huggingface-hub")
    sys.exit(1)

try:
    import torchaudio
except ImportError:
    print("\n[ERROR] torchaudio import failed after dependency check")
    print("Please reinstall: pip install --force-reinstall torchaudio")
    sys.exit(1)

try:
    import timm
    print(f"[System] timm library loaded successfully (version: {timm.__version__})")
except ImportError:
    print("\n[ERROR] timm import failed after dependency check")
    print("This is CRITICAL for Gemma 3n multimodal capabilities")
    print("Please install: pip install timm>=0.9.0")
    sys.exit(1)

try:
    import pyttsx3
except ImportError:
    print("\n[ERROR] pyttsx3 import failed")
    print("Please install: pip install pyttsx3")
    sys.exit(1)

# MCP client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))
from oauth_config import OAuthConfig


class Gemma3nNativeAudioAssistant:
    """
    Voice-activated facial recognition using Gemma 3n's native audio capabilities.

    Uses Gemma 3n E2B/E4B model with built-in audio understanding.
    """

    def __init__(self, model_id: str = "google/gemma-3n-E2B-it"):
        """
        Initialize assistant with Gemma 3n native audio model.

        Args:
            model_id: Hugging Face model ID (E2B-it for 2B, E4B-it for 4B)
        """
        self.model_id = model_id
        self.tts_engine = pyttsx3.init()
        self.access_token = None
        self.running = False

        # Audio parameters (Gemma 3n requirements)
        self.sample_rate = 16000  # 16kHz required by Gemma 3n
        self.channels = 1  # Mono
        self.wake_word_duration = 3  # Listen for 3 seconds

        # Configure TTS
        self._configure_tts()

        # Check and setup Hugging Face authentication
        print(f"\n[System] Preparing to load Gemma 3n model: {model_id}")
        self._check_huggingface_auth()

        # Load Gemma 3n model
        print("[System] Loading model (this may take several minutes on first run)...")
        self._load_model()

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

    def _check_huggingface_auth(self):
        """
        Check Hugging Face authentication and provide helpful guidance.

        Tries to authenticate using:
        1. HF_TOKEN environment variable
        2. Existing token from huggingface-cli login
        """
        print("\n" + "=" * 70)
        print("HUGGING FACE AUTHENTICATION CHECK")
        print("=" * 70)

        # Check if already authenticated
        try:
            user_info = whoami()
            print(f"[OK] Authenticated as: {user_info['name']}")
            print(f"[OK] Token found and valid")
            return True
        except Exception:
            pass  # Not authenticated, continue to try other methods

        # Try environment variable
        hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')

        if hf_token:
            print("[System] Found HF_TOKEN environment variable")
            print("[System] Authenticating with token...")
            try:
                login(token=hf_token, add_to_git_credential=False)
                user_info = whoami()
                print(f"[OK] Successfully authenticated as: {user_info['name']}")
                return True
            except Exception as e:
                print(f"[WARNING] Token from environment variable is invalid: {e}")

        # Check if token exists from CLI login
        token_path = Path.home() / ".huggingface" / "token"
        if token_path.exists():
            print(f"[OK] Found existing token at: {token_path}")
            try:
                user_info = whoami()
                print(f"[OK] Authenticated as: {user_info['name']}")
                return True
            except Exception as e:
                print(f"[WARNING] Existing token is invalid: {e}")

        # No valid authentication found
        print("\n" + "=" * 70)
        print("[ERROR] NOT AUTHENTICATED WITH HUGGING FACE")
        print("=" * 70)
        print("\nGemma 3n models are GATED and require authentication.")
        print("\nTo access these models, you need to:")
        print("\n1. CREATE A HUGGING FACE ACCOUNT:")
        print("   Visit: https://huggingface.co/join")
        print("\n2. REQUEST ACCESS TO THE MODEL:")
        print(f"   Visit: https://huggingface.co/{self.model_id}")
        print("   Click 'Request Access' and accept the terms")
        print("   (Access is usually granted instantly)")
        print("\n3. GET YOUR API TOKEN:")
        print("   a. Go to: https://huggingface.co/settings/tokens")
        print("   b. Click 'New token'")
        print("   c. Name: 'gemma3n-local-dev'")
        print("   d. Type: 'Read'")
        print("   e. Click 'Generate token'")
        print("   f. Copy the token (starts with 'hf_')")
        print("\n4. AUTHENTICATE (choose ONE method):")
        print("\n   METHOD A - Environment Variable (Quick for testing):")
        print("   Windows CMD:")
        print("      set HF_TOKEN=hf_your_token_here")
        print("   Windows PowerShell:")
        print("      $env:HF_TOKEN = 'hf_your_token_here'")
        print("   Linux/Mac:")
        print("      export HF_TOKEN=hf_your_token_here")
        print("\n   METHOD B - CLI Login (Recommended for permanent setup):")
        print("      pip install huggingface-hub")
        print("      huggingface-cli login")
        print("      (Then paste your token when prompted)")
        print("\n" + "=" * 70)
        print("\nFor detailed instructions, see: GEMMA3N_HUGGINGFACE_AUTH.md")
        print("=" * 70 + "\n")

        sys.exit(1)

    def _load_model(self):
        """Load Gemma 3n model and processor."""
        try:
            # Load processor
            print("[System] Loading processor...")
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            # Load model
            print("[System] Loading model weights...")
            # Use bfloat16 for efficiency, CPU for compatibility
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                low_cpu_mem_usage=True
            )

            device = next(self.model.parameters()).device
            print(f"[System] Model loaded successfully on device: {device}")

            # Check if GPU is available
            if torch.cuda.is_available():
                print(f"[System] GPU: {torch.cuda.get_device_name(0)}")
                print(f"[System] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            else:
                print("[System] Running on CPU (slower but works)")

        except GatedRepoError as e:
            print(f"\n[ERROR] Access Denied to Gated Model: {self.model_id}")
            print("\n" + "=" * 70)
            print("This model requires authentication and access approval.")
            print("=" * 70)
            print("\nQuick fix:")
            print("1. Request access: https://huggingface.co/" + self.model_id)
            print("2. Login: huggingface-cli login")
            print("\nFor detailed instructions, see: GEMMA3N_HUGGINGFACE_AUTH.md")
            print("=" * 70 + "\n")
            sys.exit(1)

        except RepositoryNotFoundError as e:
            print(f"\n[ERROR] Model not found: {self.model_id}")
            print("\nPossible issues:")
            print("  - Model ID is incorrect")
            print("  - Model has been moved or deleted")
            print("  - You don't have access to this private model")
            print("\nAvailable Gemma 3n models:")
            print("  - google/gemma-3n-E2B-it (2B parameters)")
            print("  - google/gemma-3n-E4B-it (4B parameters)")
            sys.exit(1)

        except Exception as e:
            print(f"\n[ERROR] Failed to load Gemma 3n model: {e}")
            print("\nPossible issues:")
            print("  - Model not downloaded (downloading now...)")
            print("  - Insufficient RAM (need ~4GB for E2B, ~6GB for E4B)")
            print("  - transformers version too old (need >=4.53.0)")
            print("  - Network connection issues")
            print("\nFor authentication issues, see: GEMMA3N_HUGGINGFACE_AUTH.md")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def speak(self, text: str):
        """Speak text using TTS."""
        print(f"[Gemma] Speaking: \"{text}\"")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def setup_oauth(self):
        """Setup OAuth and get access token."""
        oauth_config = OAuthConfig()
        client_id = "gemma3n_native_assistant"
        clients = oauth_config.load_clients()

        if client_id not in clients:
            print(f"[OAuth] Creating client: {client_id}")
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma 3n Native Audio Assistant"
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

    def load_and_prepare_audio(self, audio_path: str) -> torch.Tensor:
        """
        Load audio file and prepare for Gemma 3n.

        Args:
            audio_path: Path to audio file

        Returns:
            Audio tensor in Gemma 3n format (16kHz, mono, float32)
        """
        # Load audio file
        waveform, sample_rate = torchaudio.load(audio_path)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Resample to 16kHz if needed
        if sample_rate != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
            waveform = resampler(waveform)

        # Convert to float32 and ensure range [-1, 1]
        waveform = waveform.float()
        max_val = torch.abs(waveform).max()
        if max_val > 1.0:
            waveform = waveform / max_val

        return waveform

    def transcribe_with_gemma3n(self, audio_path: str) -> str:
        """
        Transcribe audio using Gemma 3n's native audio understanding.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        print(f"[Gemma 3n] Processing audio with native audio model...")

        try:
            # Prepare chat message with audio
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "audio", "audio": str(audio_path)},
                        {"type": "text", "text": "Transcribe this audio."}
                    ]
                }
            ]

            # Process through Gemma 3n
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )

            # Move to same device as model
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # Generate transcription
            print("[Gemma 3n] Generating transcription...")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=64,
                    do_sample=False  # Deterministic for consistency
                )

            # Decode output
            transcription = self.processor.batch_decode(
                outputs,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]

            # Extract just the transcription (remove prompt)
            # The output includes the prompt, extract the response part
            if "model" in transcription:
                transcription = transcription.split("model")[-1].strip()

            print(f"[Gemma 3n] Transcribed: \"{transcription}\"")

            return transcription.lower()

        except Exception as e:
            print(f"[ERROR] Gemma 3n transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return ""

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

    def detect_wake_word_from_audio(self, audio_path: str) -> bool:
        """
        Detect wake word using Gemma 3n native audio processing.

        Args:
            audio_path: Path to audio file

        Returns:
            True if wake word detected
        """
        print("[Gemma] Listening for 'Hello Gemma'...", flush=True)

        # Transcribe using Gemma 3n's native audio understanding
        transcription = self.transcribe_with_gemma3n(audio_path)

        # Check for wake word
        if transcription:
            wake_words = ["hello gemma", "hey gemma", "hi gemma"]
            for wake_word in wake_words:
                if wake_word in transcription:
                    print(f"[Gemma] Wake word detected: '{wake_word}'")
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


async def test_with_prerecorded_audio(audio_file: str):
    """
    Test assistant with pre-recorded audio file.

    Args:
        audio_file: Path to audio file
    """
    audio_path = Path(audio_file)

    if not audio_path.exists():
        print(f"[ERROR] Audio file not found: {audio_path}")
        return 1

    print("\n" + "=" * 70)
    print("      GEMMA 3N NATIVE AUDIO ASSISTANT - INTEGRATION TEST")
    print("=" * 70)
    print(f"\nModel: Using Gemma 3n with native audio processing")
    print(f"Audio File: {audio_path}")
    print("Workflow: Native Audio → Wake Word → Face Recognition → TTS")
    print("\n" + "=" * 70)

    try:
        # Create assistant (use E2B for faster testing, E4B for better accuracy)
        assistant = Gemma3nNativeAudioAssistant(model_id="google/gemma-3n-E2B-it")

        # Setup OAuth
        assistant.setup_oauth()

        # Test wake word detection with Gemma 3n native audio
        if assistant.detect_wake_word_from_audio(str(audio_path)):
            print("\n[SUCCESS] Wake word detected with Gemma 3n native audio!")

            # Handle the wake word
            await assistant.handle_wake_word()

            print("\n" + "=" * 70)
            print("[SUCCESS] Full integration test completed!")
            print("=" * 70)
            return 0
        else:
            print("\n[FAIL] Wake word not detected")
            return 1

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Gemma 3n Voice Assistant with Native Audio Processing"
    )
    parser.add_argument(
        'audio_file',
        type=str,
        help='Path to pre-recorded wake word audio file'
    )
    parser.add_argument(
        '--model',
        type=str,
        default="google/gemma-3n-E2B-it",
        choices=["google/gemma-3n-E2B-it", "google/gemma-3n-E4B-it"],
        help='Gemma 3n model variant (E2B=2B params, E4B=4B params)'
    )

    args = parser.parse_args()

    # Run test
    exit_code = asyncio.run(test_with_prerecorded_audio(args.audio_file))
    sys.exit(exit_code)
