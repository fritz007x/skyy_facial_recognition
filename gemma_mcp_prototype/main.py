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
from modules.registration_orchestrator import RegistrationOrchestrator
from modules.deletion_orchestrator import DeletionOrchestrator
from modules.update_orchestrator import UpdateOrchestrator
from config import (
    WAKE_WORD,
    WAKE_WORD_ALTERNATIVES,
    REGISTRATION_WAKE_WORD,
    REGISTRATION_WAKE_WORD_ALTERNATIVES,
    DELETION_WAKE_WORD,
    DELETION_WAKE_WORD_ALTERNATIVES,
    UPDATE_WAKE_WORD,
    UPDATE_WAKE_WORD_ALTERNATIVES,
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
    ENERGY_THRESHOLD,
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    ENABLE_LLM_CONFIRMATION,
    LLM_CONFIRMATION_MODEL,
    LLM_CONFIRMATION_TIMEOUT,
    LLM_CONFIRMATION_TEMPERATURE,
    LLM_CONFIRMATION_MAX_TOKENS
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
        self.registration: Optional[RegistrationOrchestrator] = None
        self.deletion: Optional[DeletionOrchestrator] = None
        self.update: Optional[UpdateOrchestrator] = None
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

        # 5. Initialize permission manager with LLM confirmation parsing
        print("\n[Init] Setting up permission manager with Gemma 3 LLM...", flush=True)
        self.permission = PermissionManager(
            self.speech,
            whisper_model=WHISPER_MODEL,
            whisper_device=WHISPER_DEVICE,
            whisper_compute_type=WHISPER_COMPUTE_TYPE,
            enable_llm_confirmation=ENABLE_LLM_CONFIRMATION,
            llm_model=LLM_CONFIRMATION_MODEL,
            llm_timeout=LLM_CONFIRMATION_TIMEOUT,
            llm_temperature=LLM_CONFIRMATION_TEMPERATURE,
            llm_max_tokens=LLM_CONFIRMATION_MAX_TOKENS
        )

        # 6. Initialize voice registration orchestrator
        print("\n[Init] Setting up voice registration orchestrator...", flush=True)
        self.registration = RegistrationOrchestrator(
            tts_speak_func=self.speech.speak,
            whisper_model=WHISPER_MODEL,
            whisper_device=WHISPER_DEVICE,
            whisper_compute_type=WHISPER_COMPUTE_TYPE,
            max_retries=3
        )
        print("[Init] Registration orchestrator ready (Whisper will load on first use).", flush=True)

        # 7. Initialize deletion orchestrator
        print("\n[Init] Setting up deletion orchestrator...", flush=True)
        self.deletion = DeletionOrchestrator(
            tts_speak_func=self.speech.speak,
            whisper_model=WHISPER_MODEL,
            whisper_device=WHISPER_DEVICE,
            whisper_compute_type=WHISPER_COMPUTE_TYPE
        )
        print("[Init] Deletion orchestrator ready (Whisper shared with registration).", flush=True)

        # 8. Initialize update orchestrator
        print("\n[Init] Setting up update orchestrator...", flush=True)
        self.update = UpdateOrchestrator(
            tts_speak_func=self.speech.speak,
            whisper_model=WHISPER_MODEL,
            whisper_device=WHISPER_DEVICE,
            whisper_compute_type=WHISPER_COMPUTE_TYPE,
            max_retries=3,
            enable_llm_confirmation=ENABLE_LLM_CONFIRMATION,
            llm_model=LLM_CONFIRMATION_MODEL,
            llm_timeout=LLM_CONFIRMATION_TIMEOUT,
            llm_temperature=LLM_CONFIRMATION_TEMPERATURE,
            llm_max_tokens=LLM_CONFIRMATION_MAX_TOKENS
        )
        print("[Init] Update orchestrator ready (Whisper shared with other orchestrators).", flush=True)

        # 9. Check server health status (NEW: Synchronous call)
        print("\n[Init] Checking server health...", flush=True)
        health = self.mcp.get_health_status(self.access_token)  # NO await!
        if health:
            overall = health.get('overall_status', 'unknown')
            print(f"[Init] Server status: {overall.upper()}", flush=True)

            if health.get('degraded_mode', {}).get('active'):
                print("[Init] WARNING: Server is in degraded mode", flush=True)

        # 9. Verify Ollama/Gemma is available
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

    def initialize_camera_with_retry(self, max_retries: int = 3) -> bool:
        """
        Initialize camera with retry logic and proper cleanup.

        Handles common camera initialization failures after multiple cycles:
        - Ensures previous camera instance is fully released
        - Adds delay between release and re-initialization
        - Retries on failure with exponential backoff

        Args:
            max_retries: Maximum number of initialization attempts (default 3)

        Returns:
            True if camera initialized successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Check if camera is already initialized
                if hasattr(self.camera, 'cap') and self.camera.cap is not None:
                    # Camera already initialized, verify it's working
                    if self.camera.cap.isOpened():
                        return True
                    else:
                        # Camera handle exists but is closed, need to clean up
                        print(f"[Camera] Camera handle closed, releasing before retry...", flush=True)
                        try:
                            self.camera.release()
                        except Exception as release_error:
                            print(f"[Camera] Error during release: {release_error}", flush=True)
                        time.sleep(0.5)  # Give OS time to release device

                # Log initialization attempt
                if attempt > 0:
                    print(f"[Camera] Initialization attempt {attempt + 1}/{max_retries}...", flush=True)
                else:
                    print(f"[Camera] Initializing camera...", flush=True)

                # Ensure any previous instance is fully released
                if hasattr(self.camera, 'cap'):
                    try:
                        self.camera.release()
                    except:
                        pass
                    time.sleep(0.5)  # Give OS time to release device

                # Attempt initialization
                if self.camera.initialize():
                    print(f"[Camera] Initialization successful", flush=True)
                    return True
                else:
                    print(f"[Camera] Initialization attempt {attempt + 1} failed", flush=True)
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        delay = 2 ** attempt
                        print(f"[Camera] Waiting {delay}s before retry...", flush=True)
                        time.sleep(delay)
            except Exception as e:
                print(f"[Camera] Error on attempt {attempt + 1}: {e}", flush=True)
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    print(f"[Camera] Waiting {delay}s before retry...", flush=True)
                    time.sleep(delay)

        # All retries exhausted
        print(f"[Camera] Failed to initialize after {max_retries} attempts", flush=True)
        return False

    def handle_recognition(self) -> None:
        """
        Handle the full recognition flow after wake word detection - SYNCHRONOUS.
        """
        # 1. Request camera permission
        if not self.permission.request_camera_permission():
            return

        # 2. Initialize camera with retry logic (handles multiple init/release cycles)
        if not self.initialize_camera_with_retry(max_retries=3):
            self.speech.speak("Sorry, I couldn't access the camera after multiple attempts. Please check your camera and try again.")
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

        # Ensure camera is initialized with retry logic
        if not self.initialize_camera_with_retry(max_retries=3):
            self.speech.speak("Sorry, I couldn't access the camera after multiple attempts. Please try again.")
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

    def handle_voice_registration(self) -> None:
        """
        Handle voice-based user registration flow.

        Uses RegistrationOrchestrator to:
        1. Capture name via VAD + Whisper
        2. Confirm name with user
        3. Request camera permission
        4. Capture photo
        5. Complete registration via MCP
        """
        print("\n[VoiceRegistration] Starting voice registration flow...", flush=True)

        # Run the complete registration flow
        success, name = self.registration.run_registration_flow(
            permission_manager=self.permission,
            camera_manager=self.camera,
            mcp_facade=self.mcp,
            access_token=self.access_token
        )

        if success:
            print(f"[VoiceRegistration] Registration completed successfully for: {name}", flush=True)
        else:
            print("[VoiceRegistration] Registration failed or cancelled", flush=True)

        # Reset orchestrator state
        self.registration.reset()

    def handle_deletion(self) -> None:
        """
        Handle voice-activated user deletion flow.

        Uses DeletionOrchestrator to:
        1. Request camera permission
        2. Recognize user via face
        3. Confirm identity via voice
        4. Explain deletion consequences
        5. Get final confirmation
        6. Execute deletion via MCP
        """
        print("\n[Deletion] Starting deletion flow...", flush=True)

        # Run the complete deletion flow
        success, user_id = self.deletion.run_deletion_flow(
            permission_manager=self.permission,
            camera_manager=self.camera,
            mcp_facade=self.mcp,
            access_token=self.access_token,
            confidence_threshold=SIMILARITY_THRESHOLD
        )

        if success:
            print(f"[Deletion] Deletion completed successfully for user: {user_id}", flush=True)
        else:
            print("[Deletion] Deletion failed or cancelled", flush=True)

        # Reset orchestrator state
        self.deletion.reset()

    def handle_update(self) -> None:
        """
        Handle voice-activated user profile update flow.

        Uses UpdateOrchestrator to:
        1. Request camera permission
        2. Recognize user via face
        3. Confirm identity via voice
        4. Fetch and present current profile
        5. Select fields to update
        6. Capture new information (name, metadata)
        7. Preview changes
        8. Get final confirmation
        9. Execute update via MCP
        """
        print("\n[Update] Starting user update flow...", flush=True)

        # Run the complete update flow
        success, user_id = self.update.run_update_flow(
            permission_manager=self.permission,
            camera_manager=self.camera,
            mcp_facade=self.mcp,
            access_token=self.access_token,
            confidence_threshold=SIMILARITY_THRESHOLD
        )

        if success:
            print(f"[Update] Update completed successfully for user: {user_id}", flush=True)
        else:
            print("[Update] Update failed or cancelled", flush=True)

        # Reset orchestrator state
        self.update.reset()

    def validate_token(self) -> bool:
        """
        Validate that current token is still valid by testing it with a quick MCP call.

        This protects against:
        - System clock changes
        - Process suspension/resume
        - Token revocation
        - Server restarts

        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token:
            return False

        try:
            # Quick health check also validates token
            # This is a lightweight operation that doesn't require face processing
            health = self.mcp.get_health_status(self.access_token)
            is_valid = health is not None and 'overall_status' in health

            if not is_valid:
                print("[OAuth] Token validation failed: invalid health response", flush=True)

            return is_valid
        except Exception as e:
            print(f"[OAuth] Token validation failed: {e}", flush=True)
            return False

    def refresh_token_if_needed(self) -> None:
        """
        Check and refresh OAuth token if needed.

        Implements two-tier validation:
        1. Time-based: Proactively refresh 5 minutes before expiry
        2. Functional: Validate token actually works after idle periods
        """
        elapsed_minutes = (time.time() - self.token_created_time) / 60
        token_expire_minutes = oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES

        # Tier 1: Proactive refresh 5 minutes before expiry
        needs_refresh = elapsed_minutes > (token_expire_minutes - 5)

        # Tier 2: Functional validation for tokens older than 5 minutes
        # Skip validation for fresh tokens to avoid unnecessary MCP calls
        if not needs_refresh and elapsed_minutes > 5:
            if not self.validate_token():
                print("[OAuth] Token validation failed, forcing refresh", flush=True)
                needs_refresh = True

        if needs_refresh:
            try:
                print("[OAuth] Refreshing access token...", flush=True)
                self.access_token = self.setup_oauth()
                self.token_created_time = time.time()
                print(f"[OAuth] Token refreshed (valid for {token_expire_minutes} minutes)", flush=True)
            except Exception as e:
                print(f"[OAuth] ERROR: Token refresh failed: {e}", flush=True)
                print("[OAuth] Will retry on next cycle", flush=True)

    def run(self) -> None:
        """
        Main run loop - SYNCHRONOUS (matches skyy_compliment).

        Listens for three types of wake words:
        1. Recognition wake words: "Skyy, recognize me" -> facial recognition
        2. Registration wake words: "Skyy, remember me" -> voice registration
        3. Deletion wake words: "Skyy, forget me" -> user deletion
        """
        # Combine all wake words
        recognition_wake_words = [WAKE_WORD] + WAKE_WORD_ALTERNATIVES
        registration_wake_words = [REGISTRATION_WAKE_WORD] + REGISTRATION_WAKE_WORD_ALTERNATIVES
        deletion_wake_words = [DELETION_WAKE_WORD] + DELETION_WAKE_WORD_ALTERNATIVES
        update_wake_words = [UPDATE_WAKE_WORD] + UPDATE_WAKE_WORD_ALTERNATIVES
        all_wake_words = recognition_wake_words + registration_wake_words + deletion_wake_words + update_wake_words

        print("\n" + "=" * 60, flush=True)
        print(f"  Recognition wake words: {recognition_wake_words}", flush=True)
        print(f"  Registration wake words: {registration_wake_words}", flush=True)
        print(f"  Update wake words: {update_wake_words}", flush=True)
        print(f"  Deletion wake words: {deletion_wake_words}", flush=True)
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
                    all_wake_words,
                    timeout=None,  # Listen indefinitely
                    energy_threshold=ENERGY_THRESHOLD
                )

                if detected:
                    print(f"\n[Wake] Detected wake word in: '{transcription}'", flush=True)

                    # Determine which type of wake word was detected
                    transcription_lower = transcription.lower()

                    # Check if it's a deletion wake word (highest priority for safety)
                    is_deletion = any(
                        del_word.lower() in transcription_lower
                        for del_word in deletion_wake_words
                    )

                    # Check if it's a registration wake word
                    is_registration = any(
                        reg_word.lower() in transcription_lower
                        for reg_word in registration_wake_words
                    )

                    # Check if it's an update wake word
                    is_update = any(
                        upd_word.lower() in transcription_lower
                        for upd_word in update_wake_words
                    )

                    if is_deletion:
                        # Handle deletion flow (highest priority for safety)
                        print("[Main] Routing to user deletion...", flush=True)
                        self.handle_deletion()
                    elif is_update:
                        # Handle update flow (requires authentication)
                        print("[Main] Routing to user update...", flush=True)
                        self.handle_update()
                    elif is_registration:
                        # Handle voice registration flow
                        print("[Main] Routing to voice registration...", flush=True)
                        self.handle_voice_registration()
                    else:
                        # Handle recognition flow (default)
                        print("[Main] Routing to facial recognition...", flush=True)
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
