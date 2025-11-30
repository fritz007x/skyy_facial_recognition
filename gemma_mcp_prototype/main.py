"""
Gemma 3 Facial Recognition Prototype - REFACTORED VERSION
Main orchestration script using clean architecture.

IMPROVEMENTS APPLIED:
1. SyncMCPFacade - Clean synchronous interface over async MCP client
2. SpeechOrchestrator - Component-based speech architecture
3. AudioDeviceManager - Explicit resource lifecycle management

Voice-activated facial recognition using:
- Gemma 3 (via Ollama) as the orchestrating LLM
- MCP client connecting to Skyy Facial Recognition server
- Speech recognition for wake word detection
- Webcam capture for face images

FULLY SYNCHRONOUS - Clean architecture with no async leaks.
"""

import re
import sys
import time
from pathlib import Path
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add src directory for oauth_config (located in parent/src/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Local modules - NEW REFACTORED ARCHITECTURE
from modules.speech_orchestrator import SpeechOrchestrator as SpeechManager
from modules.mcp_sync_facade import SyncMCPFacade
from modules.vision import WebcamManager
from modules.permission import PermissionManager
from config import (
    WAKE_WORD,
    WAKE_WORD_ALTERNATIVES,
    MCP_SERVER_SCRIPT,
    MCP_PYTHON_PATH,
    CAMERA_INDEX,
    CAPTURE_WIDTH,
    CAPTURE_HEIGHT,
    WARMUP_FRAMES,
    SPEECH_RATE,
    SPEECH_VOLUME,
    SIMILARITY_THRESHOLD,
    OLLAMA_MODEL,
    ENERGY_THRESHOLD
)

# OAuth configuration - uses the same oauth_config as MCP server
from oauth_config import oauth_config

# Ollama for Gemma 3
try:
    import ollama
except ImportError:
    print("ERROR: ollama package not installed. Run: pip install ollama", flush=True)
    sys.exit(1)


class GemmaFacialRecognition:
    """
    Main application class orchestrating voice-activated facial recognition.

    REFACTORED ARCHITECTURE:
    - Uses SyncMCPFacade instead of _run_async() hack
    - Uses SpeechOrchestrator with component-based design
    - Maintains clean separation of concerns
    - 100% synchronous - no async leaks

    FULLY SYNCHRONOUS - matches skyy_compliment architecture.
    """

    def __init__(self):
        self.speech: Optional[SpeechManager] = None
        self.camera: Optional[WebcamManager] = None
        self.mcp: Optional[SyncMCPFacade] = None  # NEW: Clean synchronous facade
        self.permission: Optional[PermissionManager] = None
        self.access_token: Optional[str] = None
        self.token_created_time: float = 0

    def setup_oauth(self) -> str:
        """
        Setup OAuth client and generate access token.

        Returns:
            Access token string
        """
        client_id = "gemma_facial_client"

        # Check if client already exists, if not create it
        clients = oauth_config.load_clients()
        if client_id not in clients:
            print(f"[OAuth] Creating new client: {client_id}", flush=True)
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma Facial Recognition Client"
            )
        else:
            print(f"[OAuth] Using existing client: {client_id}", flush=True)

        # Generate access token
        access_token = oauth_config.create_access_token(client_id)
        print(f"[OAuth] Access token generated (expires in {oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes)", flush=True)

        return access_token

    def initialize(self) -> bool:
        """
        Initialize all components - SYNCHRONOUS with clean architecture.

        Returns:
            True if all components initialized successfully
        """
        print("=" * 60, flush=True)
        print("  GEMMA FACIAL RECOGNITION PROTOTYPE (REFACTORED)", flush=True)
        print("=" * 60, flush=True)

        # 1. Setup OAuth authentication
        print("\n[Init] Setting up OAuth authentication...", flush=True)
        try:
            self.access_token = self.setup_oauth()
            self.token_created_time = time.time()
        except Exception as e:
            print(f"[Init] ERROR: OAuth setup failed: {e}", flush=True)
            return False

        # 2. Initialize speech (NEW: Component-based architecture)
        print("\n[Init] Setting up speech recognition (component-based)...", flush=True)
        self.speech = SpeechManager(rate=SPEECH_RATE, volume=SPEECH_VOLUME)

        # 3. Create camera manager (but don't initialize yet - wait for permission)
        print("\n[Init] Creating webcam manager...", flush=True)
        self.camera = WebcamManager(
            camera_index=CAMERA_INDEX,
            width=CAPTURE_WIDTH,
            height=CAPTURE_HEIGHT,
            warmup_frames=WARMUP_FRAMES
        )
        print("[Init] Camera will be initialized after permission is granted.", flush=True)

        # 4. Initialize MCP client (NEW: Clean synchronous facade)
        print("\n[Init] Connecting to MCP server (using SyncMCPFacade)...", flush=True)
        self.mcp = SyncMCPFacade(
            python_path=MCP_PYTHON_PATH,
            server_script=MCP_SERVER_SCRIPT
        )
        if not self.mcp.connect():  # NO await! Clean synchronous call
            print("[Init] ERROR: MCP connection failed", flush=True)
            return False

        # 5. Initialize permission manager
        self.permission = PermissionManager(self.speech)

        # 6. Check server health status (NEW: Synchronous call)
        print("\n[Init] Checking server health...", flush=True)
        health = self.mcp.get_health_status(self.access_token)  # NO await!
        if health:
            overall = health.get('overall_status', 'unknown')
            print(f"[Init] Server status: {overall.upper()}", flush=True)

            if health.get('degraded_mode', {}).get('active'):
                print("[Init] WARNING: Server is in degraded mode", flush=True)

        # 7. Verify Ollama/Gemma is available
        print(f"\n[Init] Checking Ollama model ({OLLAMA_MODEL})...", flush=True)
        try:
            ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": "Say 'ready'"}],
                options={"num_predict": 10}
            )
            print(f"[Init] Gemma 3 ({OLLAMA_MODEL}) is ready.", flush=True)
        except Exception as e:
            print(f"[Init] WARNING: Ollama check failed: {e}", flush=True)
            print("[Init] Make sure Ollama is running and model is pulled.", flush=True)

        print("\n[Init] All systems initialized!", flush=True)
        print("[Init] Architecture: Component-based with SyncMCPFacade", flush=True)
        return True

    def cleanup(self) -> None:
        """Release all resources - SYNCHRONOUS with clean architecture."""
        print("\n[Cleanup] Shutting down...", flush=True)

        # Release speech resources (NEW: Component cleanup)
        if self.speech:
            self.speech.cleanup()

        if self.camera and hasattr(self.camera, 'cap') and self.camera.cap is not None:
            self.camera.release()

        # NEW: Clean synchronous disconnect (no _run_async needed!)
        if self.mcp:
            self.mcp.disconnect()  # NO await! Clean synchronous call

        print("[Cleanup] Done.", flush=True)

    def generate_greeting(self, recognition_result: dict) -> str:
        """
        Use Gemma 3 to generate a personalized greeting.

        Args:
            recognition_result: Result from skyy_recognize_face

        Returns:
            Generated greeting text
        """
        status = recognition_result.get("status", "error")

        if status == "recognized":
            user = recognition_result.get("user", {})
            name = user.get("name", "friend")
            distance = recognition_result.get("distance", 0)
            similarity = max(0, min(100, (1 - distance / 2) * 100))
            metadata = user.get("metadata", {})

            prompt = f"""You are Gemma, a friendly AI assistant at Miami Dade College.
Generate a warm, personalized greeting for {name} who you just recognized.

Recognition confidence: {similarity:.0f}%
User metadata: {metadata}

Keep the greeting brief (1-2 sentences), natural, and friendly.
Don't mention technical details like confidence scores or distances.
If there's relevant metadata (like department or role), you can mention it naturally."""

        elif status == "low_confidence":
            user = recognition_result.get("user", {})
            possible_name = user.get("name", "")

            prompt = f"""You are Gemma, a friendly AI assistant. Generate a polite greeting
for someone you're not quite sure about. You think they might be {possible_name}, but you're not certain.

Keep it brief (1-2 sentences), friendly, and gently ask if you got their name right.
Don't be technical or mention confidence scores."""

        else:  # not_recognized or error
            prompt = """You are Gemma, a friendly AI assistant at Miami Dade College.
Generate a polite greeting for someone you don't recognize yet.

Keep it brief (1-2 sentences), welcoming, and offer to help them register
so you can remember them next time. Don't be robotic."""

        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": 100, "temperature": 0.7}
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"[Gemma] Error generating greeting: {e}", flush=True)
            # Fallback greeting
            if status == "recognized":
                return f"Hello, {recognition_result.get('user', {}).get('name', 'there')}! Nice to see you."
            return "Hello! I don't think we've met. Would you like me to remember you?"

    def handle_recognition(self) -> None:
        """
        Handle the full recognition flow after wake word detection - SYNCHRONOUS.
        """
        # 1. Request camera permission
        if not self.permission.request_camera_permission():
            return

        # 2. Initialize camera if not already initialized (first time permission granted)
        if not hasattr(self.camera, 'cap') or self.camera.cap is None:
            print("[Recognition] Initializing camera (first time permission granted)...", flush=True)
            if not self.camera.initialize():
                self.speech.speak("Sorry, I couldn't access the camera. Please try again.")
                return

        # 3. Capture image
        time.sleep(1)  # Give user time to position
        success, image_base64 = self.camera.capture_to_base64()

        if not success:
            self.speech.speak("Sorry, I couldn't capture an image. Please try again.")
            # Release camera on error
            if hasattr(self.camera, 'cap') and self.camera.cap is not None:
                self.camera.release()
            return

        # 4. Call MCP tool for recognition (NEW: Clean synchronous call)
        self.speech.speak("Let me take a look...")
        result = self.mcp.recognize_face(  # NO await! Clean synchronous call
            access_token=self.access_token,
            image_data=image_base64,
            confidence_threshold=SIMILARITY_THRESHOLD
        )

        print(f"[Recognition] Result: {result}", flush=True)

        # 5. Generate and speak greeting
        greeting = self.generate_greeting(result)
        self.speech.speak(greeting)

        # 6. Release camera after recognition (privacy & resource management)
        if hasattr(self.camera, 'cap') and self.camera.cap is not None:
            print("[Recognition] Releasing camera...", flush=True)
            self.camera.release()
            print("[Recognition] Camera released.", flush=True)

        # 7. If not recognized, offer registration
        if result.get("status") == "not_recognized":
            self.handle_registration_offer()

    def handle_registration_offer(self) -> None:
        """
        Handle the registration flow for unrecognized users - SYNCHRONOUS.
        """
        self.speech.speak("What's your name?")
        name = self.speech.listen_for_response(timeout=10.0)

        if not name or name == "[unintelligible]":
            self.speech.speak("I didn't catch that. You can say 'Hello Gemma' anytime to try again.")
            return

        # Clean up name (capitalize, remove filler words)
        name = name.strip().title()

        # Validate name
        if not name or len(name) < 2:
            self.speech.speak("I didn't catch a valid name. Please try again later.")
            return

        if len(name) > 100:
            self.speech.speak("That name is too long. Please use a shorter name.")
            return

        # Check for valid characters
        if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
            self.speech.speak("Please use only letters and common punctuation in your name.")
            return

        # Confirm registration
        if not self.permission.request_registration_permission(name):
            return

        # Ensure camera is initialized (should already be from previous permission)
        if not hasattr(self.camera, 'cap') or self.camera.cap is None:
            print("[Registration] Camera not initialized. Initializing now...", flush=True)
            if not self.camera.initialize():
                self.speech.speak("Sorry, I couldn't access the camera. Please try again.")
                return

        # Capture image for registration
        self.speech.speak("Great! Look at the camera one more time.")
        time.sleep(1)
        success, image_base64 = self.camera.capture_to_base64()

        if not success:
            self.speech.speak("Sorry, the camera isn't working. Please try again later.")
            # Release camera on error
            if hasattr(self.camera, 'cap') and self.camera.cap is not None:
                self.camera.release()
            return

        # Register via MCP (NEW: Clean synchronous call)
        result = self.mcp.register_user(  # NO await! Clean synchronous call
            access_token=self.access_token,
            name=name,
            image_data=image_base64,
            metadata={"registered_via": "gemma_voice"}
        )

        status = result.get("status", "error")

        if status == "success":
            self.speech.speak(f"Perfect! I'll remember you now, {name}. Nice to meet you!")
        elif status == "queued":
            self.speech.speak(f"I've saved your information, {name}. The system is a bit busy, but I'll remember you soon!")
        else:
            error_msg = result.get("message", "Unknown error")
            if "No face detected" in error_msg:
                self.speech.speak("I couldn't see your face clearly. Please make sure you're well-lit and facing the camera.")
            else:
                self.speech.speak(f"Sorry, something went wrong. Please try again later.")

        # Release camera after registration (privacy & resource management)
        if hasattr(self.camera, 'cap') and self.camera.cap is not None:
            print("[Registration] Releasing camera...", flush=True)
            self.camera.release()
            print("[Registration] Camera released.", flush=True)

    def refresh_token_if_needed(self) -> None:
        """Check and refresh OAuth token if needed."""
        elapsed_minutes = (time.time() - self.token_created_time) / 60
        token_expire_minutes = oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES

        if elapsed_minutes > (token_expire_minutes - 5):
            print("[OAuth] Refreshing access token...", flush=True)
            self.access_token = self.setup_oauth()
            self.token_created_time = time.time()
            print(f"[OAuth] Token refreshed (valid for {token_expire_minutes} minutes)", flush=True)

    def run(self) -> None:
        """
        Main run loop - SYNCHRONOUS (matches skyy_compliment).
        """
        wake_words = [WAKE_WORD] + WAKE_WORD_ALTERNATIVES

        print("\n" + "=" * 60, flush=True)
        print(f"  Listening for: {wake_words}", flush=True)
        print("  Press Ctrl+C to exit", flush=True)
        print("=" * 60 + "\n", flush=True)

        # Start listening immediately - no initial greeting
        print("[Main] Ready. Listening for wake word...\n", flush=True)

        while True:
            try:
                # Check if OAuth token needs refresh
                self.refresh_token_if_needed()

                # Listen for wake word (using component-based speech)
                detected, transcription = self.speech.listen_for_wake_word(
                    wake_words,
                    timeout=None,  # Listen indefinitely
                    energy_threshold=ENERGY_THRESHOLD
                )

                if detected:
                    print(f"\n[Wake] Detected wake word in: '{transcription}'", flush=True)

                    # Handle recognition flow
                    self.handle_recognition()
                    print("\n[Main] Returning to listening mode...\n", flush=True)

            except KeyboardInterrupt:
                print("\n[Main] Interrupt received, shutting down...", flush=True)
                break
            except Exception as e:
                print(f"[Main] Error: {e}", flush=True)
                time.sleep(1)  # Brief pause before retry


def main():
    """Entry point - SYNCHRONOUS with clean architecture."""
    app = GemmaFacialRecognition()

    try:
        if app.initialize():
            app.run()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
