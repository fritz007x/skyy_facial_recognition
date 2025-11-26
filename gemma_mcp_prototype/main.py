"""
Gemma 3 Facial Recognition Prototype
Main orchestration script.

Voice-activated facial recognition using:
- Gemma 3 (via Ollama) as the orchestrating LLM
- MCP client connecting to Skyy Facial Recognition server
- Speech recognition for wake word detection
- Webcam capture for face images

This script is designed to work with the existing skyy_facial_recognition_mcp.py server
which uses OAuth 2.1 authentication and Pydantic input models.
"""

import asyncio
import re
import sys
import time
from pathlib import Path
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add src directory for oauth_config (located in parent/src/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Local modules
from modules.speech import SpeechManager
from modules.vision import WebcamManager
from modules.mcp_client import SkyyMCPClient
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
    OLLAMA_MODEL
)

# OAuth configuration - uses the same oauth_config as MCP server
from oauth_config import oauth_config

# Ollama for Gemma 3
try:
    import ollama
except ImportError:
    print("ERROR: ollama package not installed. Run: pip install ollama")
    sys.exit(1)


class GemmaFacialRecognition:
    """
    Main application class orchestrating voice-activated facial recognition.
    
    Integrates with the existing Skyy Facial Recognition MCP server using
    OAuth 2.1 authentication.
    """
    
    def __init__(self):
        self.speech: Optional[SpeechManager] = None
        self.camera: Optional[WebcamManager] = None
        self.mcp_client: Optional[SkyyMCPClient] = None
        self.permission: Optional[PermissionManager] = None
        self.access_token: Optional[str] = None
        self._running = False
    
    def setup_oauth(self) -> str:
        """
        Setup OAuth client and generate access token.
        
        Uses the same OAuth configuration as the MCP server to ensure
        compatibility with the authentication system.
        
        Returns:
            Access token string
        """
        client_id = "gemma_facial_client"
        
        # Check if client already exists, if not create it
        clients = oauth_config.load_clients()
        if client_id not in clients:
            print(f"[OAuth] Creating new client: {client_id}")
            oauth_config.create_client(
                client_id=client_id,
                client_name="Gemma Facial Recognition Client"
            )
        else:
            print(f"[OAuth] Using existing client: {client_id}")
        
        # Generate access token
        access_token = oauth_config.create_access_token(client_id)
        print(f"[OAuth] Access token generated (expires in {oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes)")
        
        return access_token
    
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if all components initialized successfully
        """
        print("=" * 60)
        print("  GEMMA FACIAL RECOGNITION PROTOTYPE")
        print("=" * 60)
        
        # 1. Setup OAuth authentication
        print("\n[Init] Setting up OAuth authentication...")
        try:
            self.access_token = self.setup_oauth()
        except Exception as e:
            print(f"[Init] ERROR: OAuth setup failed: {e}")
            return False
        
        # 2. Initialize speech
        print("\n[Init] Setting up speech recognition...")
        self.speech = SpeechManager(rate=SPEECH_RATE, volume=SPEECH_VOLUME)
        
        # 3. Initialize camera
        print("\n[Init] Setting up webcam...")
        self.camera = WebcamManager(
            camera_index=CAMERA_INDEX,
            width=CAPTURE_WIDTH,
            height=CAPTURE_HEIGHT,
            warmup_frames=WARMUP_FRAMES
        )
        if not self.camera.initialize():
            print("[Init] ERROR: Camera initialization failed")
            return False
        
        # 4. Initialize MCP client
        print("\n[Init] Connecting to MCP server...")
        self.mcp_client = SkyyMCPClient(
            python_path=MCP_PYTHON_PATH,
            server_script=MCP_SERVER_SCRIPT
        )
        if not await self.mcp_client.connect():
            print("[Init] ERROR: MCP connection failed")
            return False
        
        # 5. Initialize permission manager
        self.permission = PermissionManager(self.speech)
        
        # 6. Check server health status
        print("\n[Init] Checking server health...")
        health = await self.mcp_client.get_health_status(self.access_token)
        if health:
            overall = health.get('overall_status', 'unknown')
            print(f"[Init] Server status: {overall.upper()}")
            
            if health.get('degraded_mode', {}).get('active'):
                print("[Init] WARNING: Server is in degraded mode")
        
        # 7. Verify Ollama/Gemma is available
        print(f"\n[Init] Checking Ollama model ({OLLAMA_MODEL})...")
        try:
            ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": "Say 'ready'"}],
                options={"num_predict": 10}
            )
            print(f"[Init] Gemma 3 ({OLLAMA_MODEL}) is ready.")
        except Exception as e:
            print(f"[Init] WARNING: Ollama check failed: {e}")
            print("[Init] Make sure Ollama is running and model is pulled.")
        
        print("\n[Init] All systems initialized!")
        return True
    
    async def cleanup(self) -> None:
        """Release all resources."""
        print("\n[Cleanup] Shutting down...")
        
        if self.camera:
            self.camera.release()
        
        if self.mcp_client:
            await self.mcp_client.disconnect()
        
        print("[Cleanup] Done.")
    
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
            # Convert cosine distance to similarity percentage
            # Cosine distance range: [0, 2] where 0=identical, 2=opposite
            # Convert to 0-100% scale: 0 distance = 100%, 2 distance = 0%
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
            print(f"[Gemma] Error generating greeting: {e}")
            # Fallback greeting
            if status == "recognized":
                return f"Hello, {recognition_result.get('user', {}).get('name', 'there')}! Nice to see you."
            return "Hello! I don't think we've met. Would you like me to remember you?"
    
    async def handle_recognition(self) -> None:
        """
        Handle the full recognition flow after wake word detection.
        """
        # 1. Request camera permission
        if not self.permission.request_camera_permission():
            return
        
        # 2. Capture image
        await asyncio.sleep(1)  # Give user time to position
        success, image_base64 = self.camera.capture_to_base64()
        
        if not success:
            self.speech.speak("Sorry, I couldn't capture an image. Please try again.")
            return
        
        # 3. Call MCP tool for recognition
        self.speech.speak("Let me take a look...")
        result = await self.mcp_client.recognize_face(
            access_token=self.access_token,
            image_data=image_base64,
            confidence_threshold=SIMILARITY_THRESHOLD
        )
        
        print(f"[Recognition] Result: {result}")
        
        # 4. Generate and speak greeting
        greeting = self.generate_greeting(result)
        self.speech.speak(greeting)
        
        # 5. If not recognized, offer registration
        if result.get("status") == "not_recognized":
            await self.handle_registration_offer()
    
    async def handle_registration_offer(self) -> None:
        """
        Handle the registration flow for unrecognized users.
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

        # Check for valid characters (letters, spaces, hyphens, apostrophes, periods)
        if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
            self.speech.speak("Please use only letters and common punctuation in your name.")
            return
        
        # Confirm registration
        if not self.permission.request_registration_permission(name):
            return
        
        # Capture image for registration
        self.speech.speak("Great! Look at the camera one more time.")
        await asyncio.sleep(1)
        success, image_base64 = self.camera.capture_to_base64()
        
        if not success:
            self.speech.speak("Sorry, the camera isn't working. Please try again later.")
            return
        
        # Register via MCP
        result = await self.mcp_client.register_user(
            access_token=self.access_token,
            name=name,
            image_data=image_base64,
            metadata={"registered_via": "gemma_voice"}
        )
        
        status = result.get("status", "error")
        
        if status == "success":
            self.speech.speak(f"Perfect! I'll remember you now, {name}. Nice to meet you!")
        elif status == "queued":
            # Handle degraded mode
            queue_pos = result.get("user", {}).get("queue_position", "")
            self.speech.speak(f"I've saved your information, {name}. The system is a bit busy, but I'll remember you soon!")
        else:
            error_msg = result.get("message", "Unknown error")
            if "No face detected" in error_msg:
                self.speech.speak("I couldn't see your face clearly. Please make sure you're well-lit and facing the camera.")
            else:
                self.speech.speak(f"Sorry, something went wrong. Please try again later.")
    
    async def run(self) -> None:
        """
        Main run loop - listen for wake word and handle interactions.
        """
        self._running = True
        token_created_time = time.time()

        wake_words = [WAKE_WORD] + WAKE_WORD_ALTERNATIVES

        print("\n" + "=" * 60)
        print(f"  Listening for: {wake_words}")
        print("  Press Ctrl+C to exit")
        print("=" * 60 + "\n")

        self.speech.speak("Hello! I'm Gemma. Say 'Hello Gemma' when you're ready.")

        while self._running:
            try:
                # Check if OAuth token needs refresh (5 minutes before expiry)
                elapsed_minutes = (time.time() - token_created_time) / 60
                token_expire_minutes = oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES

                if elapsed_minutes > (token_expire_minutes - 5):
                    print("[OAuth] Refreshing access token...")
                    self.access_token = self.setup_oauth()
                    token_created_time = time.time()
                    print(f"[OAuth] Token refreshed (valid for {token_expire_minutes} minutes)")

                # Listen for wake word
                detected, transcription = self.speech.listen_for_wake_word(
                    wake_words,
                    timeout=None  # Listen indefinitely
                )

                if detected:
                    print(f"\n[Wake] Detected wake word in: '{transcription}'")
                    await self.handle_recognition()
                    print("\n[Main] Returning to listening mode...\n")

            except KeyboardInterrupt:
                print("\n[Main] Interrupt received, shutting down...")
                self._running = False
                break
            except Exception as e:
                print(f"[Main] Error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry


async def main():
    """Entry point."""
    app = GemmaFacialRecognition()
    
    try:
        if await app.initialize():
            await app.run()
    finally:
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
