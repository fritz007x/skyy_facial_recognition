"""
Speech module for voice recognition and text-to-speech.

Inspired by the skyy_compliment speech architecture, this module provides:
- Wake word detection for voice-activated interactions
- Speech recognition for user responses
- Text-to-speech for spoken output

Uses:
- speech_recognition library for voice input
- pyttsx3 for local text-to-speech
"""

import speech_recognition as sr
import pyttsx3
import time
from typing import Optional, Tuple, List


class SpeechManager:
    """
    Handles voice recognition and speech synthesis.
    
    Features:
    - Configurable wake word detection
    - Ambient noise calibration
    - Multiple speech recognition backends
    - Local text-to-speech (no cloud required)
    """
    
    def __init__(self, rate: int = 150, volume: float = 1.0):
        """
        Initialize speech manager.
        
        Args:
            rate: Speech rate in words per minute (default 150)
            volume: Speech volume from 0.0 to 1.0 (default 1.0)
        """
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Calibrate microphone for ambient noise
        self._calibrate_microphone()
    
    def _calibrate_microphone(self, duration: float = 1.0) -> None:
        """
        Calibrate microphone for ambient noise levels.
        
        Args:
            duration: Seconds to listen for ambient noise calibration
        """
        print("[Speech] Calibrating microphone for ambient noise...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            print("[Speech] Microphone calibrated successfully.")
        except Exception as e:
            print(f"[Speech] Warning: Microphone calibration failed: {e}")
    
    def listen_for_wake_word(
        self, 
        wake_words: List[str],
        timeout: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Listen continuously for wake word activation.
        
        Args:
            wake_words: List of acceptable wake phrases (e.g., ["hello gemma", "hey gemma"])
            timeout: Optional timeout in seconds. None = listen indefinitely
            
        Returns:
            Tuple of (detected: bool, transcription: str)
            
        Example:
            detected, text = speech.listen_for_wake_word(["hello gemma"])
            if detected:
                # Handle wake word activation
        """
        # Normalize wake words to lowercase
        wake_words = [w.lower().strip() for w in wake_words]
        
        with self.microphone as source:
            try:
                print(f"[Speech] Listening for wake words: {wake_words}")
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=5  # Max phrase length
                )
                
                # Transcribe using Google Speech Recognition (free tier)
                # This requires internet but is very accurate
                transcription = self.recognizer.recognize_google(audio).lower()
                print(f"[Speech] Heard: '{transcription}'")
                
                # Check if any wake word is present in the transcription
                for wake_word in wake_words:
                    if wake_word in transcription:
                        return True, transcription
                
                return False, transcription
                
            except sr.WaitTimeoutError:
                # Timeout reached without detecting speech
                return False, ""
            except sr.UnknownValueError:
                # Speech detected but not understood
                return False, "[unintelligible]"
            except sr.RequestError as e:
                # API error (network issue, etc.)
                print(f"[Speech] Recognition service error: {e}")
                return False, ""
    
    def listen_for_response(self, timeout: float = 5.0) -> str:
        """
        Listen for a user response (e.g., name, confirmation).
        
        Args:
            timeout: How long to wait for response in seconds
            
        Returns:
            Transcribed text or empty string if nothing understood
        """
        print("[Speech] Listening for response...")
        
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=10  # Allow longer phrases for names
                )
                
                transcription = self.recognizer.recognize_google(audio)
                print(f"[Speech] Response: '{transcription}'")
                return transcription
                
            except sr.WaitTimeoutError:
                print("[Speech] No response detected (timeout)")
                return ""
            except sr.UnknownValueError:
                print("[Speech] Could not understand response")
                return "[unintelligible]"
            except sr.RequestError as e:
                print(f"[Speech] Recognition error: {e}")
                return ""
    
    def speak(self, text: str, pre_delay: float = 0.3) -> None:
        """
        Speak the given text using text-to-speech.

        Args:
            text: Text to speak aloud
            pre_delay: Delay before speaking (allows audio device to switch from recording to playback)
        """
        if not text:
            return

        # Small delay to allow microphone to fully release before TTS
        # This prevents audio device conflicts on Windows
        if pre_delay > 0:
            time.sleep(pre_delay)

        print(f"[Speech] Speaking: '{text}'")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def ask_permission(self, prompt: str) -> bool:
        """
        Ask user for permission via voice and listen for response.

        Args:
            prompt: Question to ask user (e.g., "Can I take your photo?")

        Returns:
            True if user gives affirmative response, False otherwise
        """
        self.speak(prompt)

        # Add delay to ensure TTS completes before opening microphone
        # Opening mic too quickly can interrupt TTS on Windows
        time.sleep(0.5)

        response = self.listen_for_response(timeout=5.0)
        
        # List of affirmative responses
        affirmative_words = [
            "yes", "yeah", "sure", "okay", "ok", "yep", 
            "go ahead", "please", "alright", "fine", "do it"
        ]
        
        response_lower = response.lower()
        return any(word in response_lower for word in affirmative_words)
    
    def set_voice(self, voice_id: Optional[str] = None) -> None:
        """
        Set the TTS voice.
        
        Args:
            voice_id: Voice ID to use. If None, lists available voices.
        """
        voices = self.engine.getProperty('voices')
        
        if voice_id is None:
            print("[Speech] Available voices:")
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})")
            return
        
        for voice in voices:
            if voice_id in voice.id:
                self.engine.setProperty('voice', voice.id)
                print(f"[Speech] Voice set to: {voice.name}")
                return
        
        print(f"[Speech] Voice not found: {voice_id}")
    
    def set_rate(self, rate: int) -> None:
        """
        Set speech rate.
        
        Args:
            rate: Words per minute (typical range: 100-200)
        """
        self.engine.setProperty('rate', rate)
        print(f"[Speech] Rate set to: {rate} WPM")
    
    def set_volume(self, volume: float) -> None:
        """
        Set speech volume.
        
        Args:
            volume: Volume level from 0.0 to 1.0
        """
        volume = max(0.0, min(1.0, volume))
        self.engine.setProperty('volume', volume)
        print(f"[Speech] Volume set to: {volume}")
