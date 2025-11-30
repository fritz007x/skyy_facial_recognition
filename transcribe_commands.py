"""
Gemma 3n Voice Command Transcription

This script uses the Gemma 3n E2B model to transcribe voice commands.
It supports both live microphone input and pre-recorded audio files.

Requirements:
    pip install -r requirements.txt
    (Ensure transformers>=4.53.0, torch, torchaudio, timm, librosa, sounddevice are installed)
"""

import argparse
import sys
import os
import time
import tempfile
import threading
import queue
from pathlib import Path
from typing import Optional

import torch
import torchaudio
import sounddevice as sd
import soundfile as sf
import numpy as np
from transformers import AutoProcessor, AutoModelForImageTextToText
from huggingface_hub import login, whoami
from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError

class Gemma3nTranscriber:
    def __init__(self, model_id: str = "google/gemma-3n-E2B-it"):
        self.model_id = model_id
        self.sample_rate = 16000  # Required by Gemma 3n
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"[System] Initializing Gemma 3n Transcriber with model: {model_id}")
        self._check_auth()
        self._load_model()

    def _check_auth(self):
        """Check Hugging Face authentication."""
        try:
            whoami()
            print("[System] Authenticated with Hugging Face.")
        except Exception:
            token = os.environ.get("HF_TOKEN")
            if token:
                print("[System] Authenticating with HF_TOKEN...")
                login(token=token)
            else:
                print("[WARNING] Not authenticated. Model download may fail if not cached.")

    def _load_model(self):
        """Load the model and processor."""
        print(f"[System] Loading model on {self.device}...")
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else "cpu",
                low_cpu_mem_usage=True
            )
            print("[System] Model loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            sys.exit(1)

    def record_audio(self, duration: float = 5.0) -> str:
        """
        Record audio from microphone for a fixed duration.
        Returns path to temporary WAV file.
        """
        print(f"\n[Recording] Listening for {duration} seconds...")
        
        # Record
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        print("[Recording] Finished.")

        # Check for silence
        rms = np.sqrt(np.mean(recording**2))
        print(f"[Debug] Audio RMS amplitude: {rms:.4f}")
        if rms < 0.001:
            print("[WARNING] Audio is very quiet. Check your microphone.")

        # Convert to 16-bit PCM
        recording_int16 = (recording * 32767).astype(np.int16)

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(temp_file.name, recording_int16, self.sample_rate, subtype='PCM_16')
        return temp_file.name

    def record_audio_manual(self) -> str:
        """
        Record audio until Enter is pressed.
        Returns path to temporary WAV file.
        """
        print("\n[Recording] Press Enter to start recording...")
        input()
        
        print("[Recording] Recording... Press Enter to stop.")
        
        q = queue.Queue()
        
        def callback(indata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())

        # Start stream
        with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=callback):
            input()  # Wait for Enter to stop
            
        print("[Recording] Finished.")

        # Collect data
        data = []
        while not q.empty():
            data.append(q.get())
        
        if not data:
            print("[Warning] No audio recorded.")
            return None
            
        recording = np.concatenate(data, axis=0)

        # Check for silence
        rms = np.sqrt(np.mean(recording**2))
        print(f"[Debug] Audio RMS amplitude: {rms:.4f}")
        if rms < 0.001:
            print("[WARNING] Audio is very quiet. Check your microphone.")

        # Convert to 16-bit PCM
        recording_int16 = (recording * 32767).astype(np.int16)

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(temp_file.name, recording_int16, self.sample_rate, subtype='PCM_16')
        return temp_file.name

    def transcribe(self, audio_path: str) -> str:
        """Transcribe the audio file."""
        if not os.path.exists(audio_path):
            print(f"[ERROR] File not found: {audio_path}")
            return ""

        print(f"[Gemma 3n] Transcribing {audio_path}...")
        
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
            
            # Debug: Print input shapes
            for k, v in inputs.items():
                print(f"[Debug] Input {k} shape: {v.shape}")

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

            # Clean up
            if "model" in transcription:
                transcription = transcription.split("model")[-1].strip()
            
            return transcription

        except Exception as e:
            print(f"[ERROR] Transcription failed: {e}")
            return ""

def main():
    parser = argparse.ArgumentParser(description="Gemma 3n Voice Transcription")
    parser.add_argument("--file", type=str, help="Path to pre-recorded audio file")
    parser.add_argument("--duration", type=float, default=5.0, help="Duration for fixed recording (seconds)")
    parser.add_argument("--manual", action="store_true", help="Use manual start/stop for recording")
    parser.add_argument("--loop", action="store_true", help="Run in a loop (for microphone)")
    
    args = parser.parse_args()

    transcriber = Gemma3nTranscriber()

    if args.file:
        # Transcribe file
        text = transcriber.transcribe(args.file)
        print(f"\n[Transcription] {text}")
    else:
        # Microphone loop or single run
        while True:
            if args.manual:
                audio_file = transcriber.record_audio_manual()
            else:
                print(f"\n[Instruction] Recording for {args.duration} seconds...")
                audio_file = transcriber.record_audio(duration=args.duration)
            
            if audio_file:
                text = transcriber.transcribe(audio_file)
                print(f"\n[Transcription] {text}")
                
                # Cleanup temp file
                try:
                    os.unlink(audio_file)
                except:
                    pass
            
            if not args.loop:
                break
            
            print("\n[Loop] Press Ctrl+C to exit, or wait for next cycle...")
            time.sleep(1)

if __name__ == "__main__":
    main()
