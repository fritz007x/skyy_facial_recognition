#!/usr/bin/env python3
"""
End-to-End Performance Testing for Skyy Facial Recognition System
Tests complete voice pipeline from "Hello Gemma" to personalized greeting

This script measures:
1. Wake word detection latency
2. Speech-to-text processing time
3. Camera capture time
4. Face recognition latency
5. Response generation time
6. Text-to-speech latency
7. Total end-to-end time

Author: Team 5 - Advanced NLP
Date: December 2025
"""

import time
import json
import base64
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import statistics

# Audio processing
import speech_recognition as sr
import pyttsx3

# Camera
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

# Optional: For simulated testing without actual audio/camera
SIMULATION_MODE = False  # Set to True for testing without hardware


class PerformanceTimer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
        print(f"  [{self.name}] {self.elapsed:.1f}ms")
    
    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed if self.elapsed else 0.0


class PerformanceMetrics:
    """Container for all performance metrics."""
    
    def __init__(self):
        self.wake_word_detection: List[float] = []
        self.speech_to_text: List[float] = []
        self.camera_capture: List[float] = []
        self.face_encoding: List[float] = []
        self.mcp_call: List[float] = []
        self.face_recognition: List[float] = []
        self.response_generation: List[float] = []
        self.text_to_speech: List[float] = []
        self.end_to_end: List[float] = []
        
        # Detailed breakdown
        self.insightface_detection: List[float] = []
        self.insightface_embedding: List[float] = []
        self.chromadb_query: List[float] = []
    
    def add_measurement(self, metric_name: str, value: float):
        """Add a measurement to the specified metric."""
        if hasattr(self, metric_name):
            getattr(self, metric_name).append(value)
    
    def get_summary(self) -> Dict:
        """Get statistical summary of all metrics."""
        summary = {}
        
        for attr_name in dir(self):
            if not attr_name.startswith('_') and isinstance(getattr(self, attr_name), list):
                values = getattr(self, attr_name)
                if values:
                    summary[attr_name] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
                        'count': len(values)
                    }
        
        return summary
    
    def save_to_file(self, filepath: Path):
        """Save metrics to JSON file."""
        summary = self.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)


class EndToEndPerformanceTester:
    """Complete end-to-end performance testing for voice-activated facial recognition."""
    
    def __init__(self, mcp_access_token: str = "test_token_123", simulation: bool = False):
        self.access_token = mcp_access_token
        self.simulation = simulation
        self.metrics = PerformanceMetrics()
        
        # Initialize components
        if not self.simulation:
            self._init_speech_components()
            self._init_camera()
    
    def _init_speech_components(self):
        """Initialize speech recognition and TTS."""
        print("Initializing speech components...")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Speed
        self.tts_engine.setProperty('volume', 0.9)  # Volume
        
        # Calibrate microphone
        print("Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        
        print("✓ Speech components ready")
    
    def _init_camera(self):
        """Initialize camera."""
        print("Initializing camera...")
        self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            print("⚠ Warning: Could not open camera. Using simulation mode.")
            self.simulation = True
        else:
            # Warm up camera
            for _ in range(5):
                self.camera.read()
            print("✓ Camera ready")
    
    def measure_wake_word_detection(self) -> float:
        """
        Measure time to detect wake word.
        
        Returns:
            Time in milliseconds
        """
        print("\n[1/8] Testing Wake Word Detection")
        
        if self.simulation:
            print("  [SIMULATION] Simulating wake word detection...")
            time.sleep(0.1)  # Simulate processing
            elapsed = 2000.0  # Typical 2 seconds
            print(f"  [SIMULATION] {elapsed:.1f}ms")
            return elapsed
        
        print("  Say 'Hello Gemma' when ready...")
        
        with PerformanceTimer("Wake Word Detection") as timer:
            with self.microphone as source:
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                    transcription = self.recognizer.recognize_google(audio).lower()
                    
                    if 'hello' in transcription or 'gemma' in transcription:
                        print(f"  Detected: '{transcription}'")
                    else:
                        print(f"  Warning: Unexpected phrase '{transcription}'")
                
                except sr.WaitTimeoutError:
                    print("  Timeout waiting for speech")
                except sr.UnknownValueError:
                    print("  Could not understand audio")
        
        return timer.get_elapsed_ms()
    
    def measure_speech_to_text(self, prompt: str = "yes") -> float:
        """
        Measure speech-to-text processing time.
        
        Returns:
            Time in milliseconds
        """
        print(f"\n[2/8] Testing Speech-to-Text")
        
        if self.simulation:
            print(f"  [SIMULATION] Simulating STT for '{prompt}'...")
            time.sleep(0.05)
            elapsed = 250.0  # Typical 250ms
            print(f"  [SIMULATION] {elapsed:.1f}ms")
            return elapsed
        
        print(f"  Say '{prompt}' when ready...")
        
        with PerformanceTimer("Speech-to-Text") as timer:
            with self.microphone as source:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    transcription = self.recognizer.recognize_google(audio)
                    print(f"  Transcribed: '{transcription}'")
                
                except sr.WaitTimeoutError:
                    print("  Timeout waiting for speech")
                except sr.UnknownValueError:
                    print("  Could not understand audio")
        
        return timer.get_elapsed_ms()
    
    def measure_camera_capture(self) -> Tuple[float, Optional[str]]:
        """
        Measure camera capture time.
        
        Returns:
            Tuple of (time in ms, base64 encoded image)
        """
        print("\n[3/8] Testing Camera Capture")
        
        if self.simulation:
            print("  [SIMULATION] Simulating camera capture...")
            time.sleep(0.01)
            # Create dummy image
            dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', dummy_img)
            image_b64 = base64.b64encode(buffer).decode('utf-8')
            elapsed = 75.0
            print(f"  [SIMULATION] {elapsed:.1f}ms")
            return elapsed, image_b64
        
        image_b64 = None
        
        with PerformanceTimer("Camera Capture") as timer:
            ret, frame = self.camera.read()
            
            if ret:
                print(f"  Captured frame: {frame.shape}")
            else:
                print("  Failed to capture frame")
                return timer.get_elapsed_ms(), None
        
        return timer.get_elapsed_ms(), frame
    
    def measure_face_encoding(self, frame) -> Tuple[float, Optional[str]]:
        """
        Measure time to encode image to base64.
        
        Returns:
            Tuple of (time in ms, base64 string)
        """
        print("\n[4/8] Testing Face Encoding")
        
        image_b64 = None
        
        with PerformanceTimer("Face Encoding") as timer:
            if isinstance(frame, str):
                # Already base64
                image_b64 = frame
            else:
                # Encode to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                image_b64 = base64.b64encode(buffer).decode('utf-8')
                print(f"  Encoded to base64 ({len(image_b64)} chars)")
        
        return timer.get_elapsed_ms(), image_b64
    
    def measure_mcp_recognition(self, image_b64: str) -> Tuple[float, Dict]:
        """
        Measure MCP tool call and face recognition.
        
        Returns:
            Tuple of (total time in ms, recognition result)
        """
        print("\n[5/8] Testing MCP Face Recognition")
        
        # Import MCP functions
        try:
            from skyy_facial_recognition_mcp import recognize_face, RecognizeFaceInput, ResponseFormat
        except ImportError:
            print("  ⚠ Cannot import MCP server. Simulating...")
            time.sleep(0.3)
            return 300.0, {
                "status": "recognized",
                "user": {"name": "Test User"},
                "distance": 0.18
            }
        
        result = None
        
        with PerformanceTimer("MCP Recognition (Total)") as total_timer:
            # Create parameters
            params = RecognizeFaceInput(
                image_data=image_b64,
                access_token=self.access_token,
                confidence_threshold=0.25,
                response_format=ResponseFormat.JSON
            )
            
            # Call recognition
            result_str = asyncio.run(recognize_face(params))
            result = json.loads(result_str)
            
            status = result.get("status", "unknown")
            distance = result.get("distance", 1.0)
            user_name = result.get("user", {}).get("name", "Unknown")
            
            print(f"  Status: {status}")
            print(f"  Distance: {distance:.4f}")
            if status == "recognized":
                print(f"  User: {user_name}")
        
        return total_timer.get_elapsed_ms(), result
    
    def measure_response_generation(self, recognition_result: Dict) -> Tuple[float, str]:
        """
        Measure response generation time (Gemma 3 simulation).
        
        Returns:
            Tuple of (time in ms, response text)
        """
        print("\n[6/8] Testing Response Generation")
        
        response = ""
        
        with PerformanceTimer("Response Generation") as timer:
            # Simulate Gemma 3 processing
            status = recognition_result.get("status")
            
            if status == "recognized":
                user_name = recognition_result.get("user", {}).get("name", "there")
                response = f"Hello {user_name}! Welcome back!"
            else:
                response = "Hello! I don't recognize you. Would you like me to remember you?"
            
            # Simulate LLM inference time (100-500ms typical)
            if not self.simulation:
                time.sleep(0.2)  # Simulated processing
            
            print(f"  Generated: '{response}'")
        
        return timer.get_elapsed_ms(), response
    
    def measure_text_to_speech(self, text: str) -> float:
        """
        Measure text-to-speech time.
        
        Returns:
            Time in milliseconds
        """
        print("\n[7/8] Testing Text-to-Speech")
        
        if self.simulation:
            print(f"  [SIMULATION] Simulating TTS for '{text}'...")
            # Estimate based on text length (typical: 150 words per minute)
            words = len(text.split())
            estimated_ms = (words / 150) * 60 * 1000
            time.sleep(estimated_ms / 1000)
            print(f"  [SIMULATION] {estimated_ms:.1f}ms")
            return estimated_ms
        
        with PerformanceTimer("Text-to-Speech") as timer:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        
        return timer.get_elapsed_ms()
    
    def run_single_test(self, test_num: int) -> Dict[str, float]:
        """
        Run a complete end-to-end test.
        
        Returns:
            Dictionary of timing measurements
        """
        print(f"\n{'='*70}")
        print(f"END-TO-END TEST #{test_num}")
        print(f"{'='*70}")
        
        timings = {}
        
        # Start total timer
        e2e_start = time.perf_counter()
        
        # 1. Wake word detection
        timings['wake_word'] = self.measure_wake_word_detection()
        
        # 2. Speech-to-text (confirmation)
        timings['stt'] = self.measure_speech_to_text()
        
        # 3. Camera capture
        timings['camera'], frame = self.measure_camera_capture()
        
        if frame is None:
            print("\n⚠ Test aborted: Camera capture failed")
            return timings
        
        # 4. Face encoding
        timings['encoding'], image_b64 = self.measure_face_encoding(frame)
        
        # 5. MCP recognition
        timings['recognition'], result = self.measure_mcp_recognition(image_b64)
        
        # 6. Response generation
        timings['response_gen'], response = self.measure_response_generation(result)
        
        # 7. Text-to-speech
        timings['tts'] = self.measure_text_to_speech(response)
        
        # Calculate total
        e2e_elapsed = (time.perf_counter() - e2e_start) * 1000
        timings['total'] = e2e_elapsed
        
        print(f"\n{'='*70}")
        print(f"[8/8] END-TO-END TOTAL: {e2e_elapsed:.1f}ms ({e2e_elapsed/1000:.2f}s)")
        print(f"{'='*70}")
        
        return timings
    
    def run_performance_test(self, num_tests: int = 5) -> PerformanceMetrics:
        """
        Run multiple end-to-end tests and collect statistics.
        
        Args:
            num_tests: Number of complete tests to run
            
        Returns:
            PerformanceMetrics object with all measurements
        """
        print(f"\n{'#'*70}")
        print(f"STARTING PERFORMANCE TEST SUITE ({num_tests} iterations)")
        print(f"{'#'*70}\n")
        
        for test_num in range(1, num_tests + 1):
            timings = self.run_single_test(test_num)
            
            # Record metrics
            if 'wake_word' in timings:
                self.metrics.add_measurement('wake_word_detection', timings['wake_word'])
            if 'stt' in timings:
                self.metrics.add_measurement('speech_to_text', timings['stt'])
            if 'camera' in timings:
                self.metrics.add_measurement('camera_capture', timings['camera'])
            if 'encoding' in timings:
                self.metrics.add_measurement('face_encoding', timings['encoding'])
            if 'recognition' in timings:
                self.metrics.add_measurement('face_recognition', timings['recognition'])
            if 'response_gen' in timings:
                self.metrics.add_measurement('response_generation', timings['response_gen'])
            if 'tts' in timings:
                self.metrics.add_measurement('text_to_speech', timings['tts'])
            if 'total' in timings:
                self.metrics.add_measurement('end_to_end', timings['total'])
            
            # Pause between tests
            if test_num < num_tests:
                print(f"\n⏸  Waiting 3 seconds before next test...\n")
                time.sleep(3)
        
        return self.metrics
    
    def generate_report(self) -> str:
        """
        Generate a formatted performance report.
        
        Returns:
            Formatted report string
        """
        summary = self.metrics.get_summary()
        
        report = "\n" + "="*70 + "\n"
        report += "PERFORMANCE TEST RESULTS - SUMMARY\n"
        report += "="*70 + "\n\n"
        
        # Table header
        report += f"{'Component':<25} {'Mean':<10} {'Median':<10} {'Min':<10} {'Max':<10} {'StdDev':<10}\n"
        report += "-"*70 + "\n"
        
        # Component order for display
        component_order = [
            ('wake_word_detection', 'Wake Word Detection'),
            ('speech_to_text', 'Speech-to-Text'),
            ('camera_capture', 'Camera Capture'),
            ('face_encoding', 'Face Encoding'),
            ('face_recognition', 'Face Recognition'),
            ('response_generation', 'Response Generation'),
            ('text_to_speech', 'Text-to-Speech'),
            ('end_to_end', 'END-TO-END TOTAL'),
        ]
        
        for key, label in component_order:
            if key in summary:
                stats = summary[key]
                report += f"{label:<25} "
                report += f"{stats['mean']:>8.1f}ms "
                report += f"{stats['median']:>8.1f}ms "
                report += f"{stats['min']:>8.1f}ms "
                report += f"{stats['max']:>8.1f}ms "
                report += f"{stats['stdev']:>8.1f}ms\n"
        
        report += "\n" + "="*70 + "\n"
        
        # Key insights
        if 'end_to_end' in summary:
            e2e_mean = summary['end_to_end']['mean']
            report += "\nKEY INSIGHTS:\n"
            report += f"  • Average end-to-end latency: {e2e_mean:.1f}ms ({e2e_mean/1000:.2f}s)\n"
            
            # Breakdown
            if 'wake_word_detection' in summary:
                ww_pct = (summary['wake_word_detection']['mean'] / e2e_mean) * 100
                report += f"  • Wake word detection: {ww_pct:.1f}% of total time\n"
            
            if 'face_recognition' in summary:
                fr_pct = (summary['face_recognition']['mean'] / e2e_mean) * 100
                report += f"  • Face recognition: {fr_pct:.1f}% of total time\n"
            
            if 'text_to_speech' in summary:
                tts_pct = (summary['text_to_speech']['mean'] / e2e_mean) * 100
                report += f"  • Text-to-speech: {tts_pct:.1f}% of total time\n"
        
        report += "\n" + "="*70 + "\n"
        
        return report
    
    def cleanup(self):
        """Release resources."""
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()


def main():
    """Main entry point for performance testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='End-to-end performance testing for Skyy Facial Recognition')
    parser.add_argument('--num-tests', type=int, default=5, help='Number of test iterations (default: 5)')
    parser.add_argument('--simulation', action='store_true', help='Run in simulation mode (no hardware required)')
    parser.add_argument('--output', type=str, default='performance_results.json', help='Output file for results')
    parser.add_argument('--access-token', type=str, default='test_token_123', help='MCP access token')
    
    args = parser.parse_args()
    
    # Create tester
    tester = EndToEndPerformanceTester(
        mcp_access_token=args.access_token,
        simulation=args.simulation or SIMULATION_MODE
    )
    
    try:
        # Run tests
        metrics = tester.run_performance_test(num_tests=args.num_tests)
        
        # Generate and print report
        report = tester.generate_report()
        print(report)
        
        # Save results
        output_path = Path(args.output)
        metrics.save_to_file(output_path)
        print(f"\n✓ Detailed results saved to: {output_path}")
        
        # Save report
        report_path = output_path.parent / f"{output_path.stem}_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"✓ Report saved to: {report_path}")
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
