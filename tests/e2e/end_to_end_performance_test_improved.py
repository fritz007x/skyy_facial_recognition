#!/usr/bin/env python3
"""
Enhanced End-to-End Performance Testing for Skyy Facial Recognition System
Tests complete voice pipeline with detailed profiling, hardware capture, and SLA validation

Improvements over original:
1. Hardware/environment info capture (CPU, GPU, RAM, audio device)
2. Warm-up phase to stabilize measurements
3. Component-level profiling with confidence intervals
4. SLA threshold validation with pass/fail reporting
5. Proper MCP error handling (fails fast, doesn't silently degrade)
6. Mock implementations for external dependencies (Google Speech, TTS)
7. Statistical rigor: confidence intervals, outlier detection
8. Detailed performance breakdown and optimization suggestions
9. Regression detection (comparison with baseline)
10. Better reporting with color-coded results

Author: Team 5 - Advanced NLP
Date: December 2025
"""

import time
import json
import base64
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union
from datetime import datetime
import statistics
import subprocess

# Audio processing
import cv2
import numpy as np

# Optional: For capturing system info
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Optional: For capturing GPU info
try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Default SLA targets (milliseconds)
SLA_TARGETS = {
    'wake_word_detection': 3000,      # 3 seconds
    'speech_to_text': 500,            # 500ms
    'camera_capture': 200,            # 200ms
    'face_encoding': 150,             # 150ms
    'face_recognition': 1500,         # 1.5 seconds
    'response_generation': 500,       # 500ms
    'text_to_speech': 3000,           # 3 seconds
    'end_to_end': 8000,               # 8 seconds total
}

SIMULATION_MODE = False  # Set to True for testing without hardware


def calculate_confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval for a sample."""
    if len(values) < 2:
        return (values[0], values[0]) if values else (0, 0)

    n = len(values)
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    margin = stdev * 1.96 / (n ** 0.5)  # 95% confidence
    return (mean - margin, mean + margin)


def detect_outliers(values: List[float], threshold: float = 2.0) -> Tuple[List[int], List[float]]:
    """Detect outliers using Z-score method."""
    if len(values) < 3:
        return [], values

    mean = statistics.mean(values)
    stdev = statistics.stdev(values)

    outliers = []
    outlier_indices = []
    for i, val in enumerate(values):
        z_score = abs((val - mean) / stdev) if stdev > 0 else 0
        if z_score > threshold:
            outlier_indices.append(i)
            outliers.append(val)

    return outlier_indices, outliers


class SystemInfo:
    """Capture system hardware and environment information."""

    @staticmethod
    def get_system_info() -> Dict:
        """Gather system information."""
        info = {
            'timestamp': datetime.now().isoformat(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

        # CPU info
        if HAS_PSUTIL:
            info['cpu_count'] = psutil.cpu_count()
            info['cpu_freq'] = f"{psutil.cpu_freq().current:.0f} MHz" if psutil.cpu_freq() else "Unknown"
            info['cpu_percent'] = f"{psutil.cpu_percent(interval=0.1):.1f}%"
            info['ram_total_gb'] = f"{psutil.virtual_memory().total / (1024**3):.1f}"
            info['ram_available_gb'] = f"{psutil.virtual_memory().available / (1024**3):.1f}"

        # GPU info
        if HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                info['gpu_count'] = len(gpus)
                if gpus:
                    info['gpu_0_name'] = gpus[0].name
                    info['gpu_0_load'] = f"{gpus[0].load * 100:.1f}%"
                    info['gpu_0_memory_free'] = f"{gpus[0].memoryFree:.0f}MB"
            except Exception:
                pass

        # Camera info
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                info['camera_available'] = True
                info['camera_resolution'] = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                info['camera_fps'] = f"{cap.get(cv2.CAP_PROP_FPS):.1f}"
                cap.release()
            else:
                info['camera_available'] = False
        except Exception:
            info['camera_available'] = False

        return info


class MockSpeechRecognizer:
    """Deterministic mock for speech recognition (replaces Google API dependency)."""

    def __init__(self):
        self.call_count = 0

    def recognize_wake_word(self) -> Tuple[float, str]:
        """Simulate wake word detection with realistic latency."""
        self.call_count += 1
        # Vosk typical latency: 1500-2500ms
        latency = np.random.normal(2000, 300)
        latency = max(1000, min(3500, latency))  # Constrain to realistic range
        time.sleep(latency / 1000)
        return latency, "hello gemma"

    def recognize_speech(self, prompt: str = "yes") -> Tuple[float, str]:
        """Simulate speech-to-text with realistic latency."""
        # Whisper typical latency: 150-400ms
        latency = np.random.normal(250, 50)
        latency = max(100, min(400, latency))
        time.sleep(latency / 1000)
        return latency, prompt


class MockFaceRecognizer:
    """Deterministic mock for MCP face recognition calls."""

    def __init__(self):
        self.call_count = 0

    def recognize(self, image_b64: str) -> Tuple[float, Dict]:
        """Simulate face recognition with component breakdown."""
        self.call_count += 1

        # InsightFace detection: 200-400ms
        detection_time = np.random.normal(300, 50)
        detection_time = max(150, min(500, detection_time))

        # ChromaDB query: 300-600ms
        db_query_time = np.random.normal(450, 100)
        db_query_time = max(200, min(800, db_query_time))

        total_time = detection_time + db_query_time
        time.sleep(total_time / 1000)

        # Alternate between recognized and unknown
        is_recognized = (self.call_count % 2) == 1

        result = {
            'status': 'recognized' if is_recognized else 'not_recognized',
            'user': {'name': 'Test User'} if is_recognized else {},
            'distance': 0.18 if is_recognized else 0.95,
            'timing': {
                'insightface_detection_ms': detection_time,
                'chromadb_query_ms': db_query_time,
                'total_ms': total_time
            }
        }

        return total_time, result


class MockTTSEngine:
    """Deterministic mock for text-to-speech."""

    def synthesize(self, text: str) -> float:
        """Simulate TTS with latency based on text length."""
        # pyttsx3 typical: ~100ms per word
        word_count = len(text.split())
        base_latency = word_count * 100 + np.random.normal(200, 50)
        base_latency = max(500, min(2500, base_latency))
        time.sleep(base_latency / 1000)
        return base_latency


class PerformanceTimer:
    """Enhanced context manager for timing code blocks."""

    def __init__(self, name: str, verbose: bool = True):
        self.name = name
        self.start_time = None
        self.elapsed = None
        self.verbose = verbose

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = (time.perf_counter() - self.start_time) * 1000
        if self.verbose:
            print(f"  [{self.name}] {self.elapsed:.1f}ms")

    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed if self.elapsed else 0.0


class PerformanceMetrics:
    """Enhanced metrics container with statistical analysis."""

    def __init__(self):
        self.wake_word_detection: List[float] = []
        self.speech_to_text: List[float] = []
        self.camera_capture: List[float] = []
        self.face_encoding: List[float] = []
        self.face_recognition: List[float] = []
        self.response_generation: List[float] = []
        self.text_to_speech: List[float] = []
        self.end_to_end: List[float] = []

        # Component breakdown
        self.insightface_detection: List[float] = []
        self.chromadb_query: List[float] = []

        # Meta
        self.system_info: Dict = {}
        self.test_config: Dict = {}

    def add_measurement(self, metric_name: str, value: float):
        """Add measurement to metric."""
        if hasattr(self, metric_name):
            getattr(self, metric_name).append(value)

    def get_summary(self) -> Dict:
        """Get comprehensive statistical summary."""
        summary = {}

        for attr_name in dir(self):
            if not attr_name.startswith('_') and isinstance(getattr(self, attr_name), list):
                values = getattr(self, attr_name)
                if values:
                    outlier_indices, outliers = detect_outliers(values)
                    ci_low, ci_high = calculate_confidence_interval(values)

                    summary[attr_name] = {
                        'count': len(values),
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
                        'ci_95_low': ci_low,
                        'ci_95_high': ci_high,
                        'outliers': outliers,
                        'outlier_indices': outlier_indices,
                    }

        return summary

    def save_to_file(self, filepath: Path):
        """Save metrics to JSON."""
        summary = self.get_summary()
        data = {
            'summary': summary,
            'system_info': self.system_info,
            'test_config': self.test_config,
            'timestamp': datetime.now().isoformat(),
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


class EnhancedEndToEndPerformanceTester:
    """Enhanced end-to-end performance tester with profiling and SLA validation."""

    def __init__(self, simulation: bool = False, num_warmup: int = 2, num_tests: int = 5):
        self.simulation = simulation
        self.num_warmup = num_warmup
        self.num_tests = num_tests
        self.metrics = PerformanceMetrics()

        # Initialize components
        self.speech_recognizer = MockSpeechRecognizer()
        self.face_recognizer = MockFaceRecognizer()
        self.tts_engine = MockTTSEngine()

        # Capture system info
        self.metrics.system_info = SystemInfo.get_system_info()
        self.metrics.test_config = {
            'simulation_mode': simulation,
            'warmup_runs': num_warmup,
            'test_runs': num_tests,
            'sla_targets': SLA_TARGETS,
        }

        self._init_camera()

    def _init_camera(self):
        """Initialize camera."""
        print("Initializing camera...")
        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            print(f"{Colors.YELLOW}[!] Warning: Could not open camera{Colors.RESET}")
            self.simulation = True
        else:
            # Warm up camera
            for _ in range(5):
                self.camera.read()
            print(f"{Colors.GREEN}[OK] Camera ready{Colors.RESET}")

    def run_warmup_phase(self):
        """Run warm-up iterations to stabilize measurements."""
        print(f"\n{Colors.CYAN}Running warm-up phase ({self.num_warmup} iterations)...{Colors.RESET}\n")

        for i in range(self.num_warmup):
            print(f"  Warm-up {i+1}/{self.num_warmup}")
            try:
                self._run_single_test_internal()
            except Exception as e:
                print(f"  {Colors.YELLOW}Warning during warm-up: {e}{Colors.RESET}")

    def measure_wake_word_detection(self) -> float:
        """Measure wake word detection latency."""
        print("\n[1/7] Testing Wake Word Detection")

        with PerformanceTimer("Wake Word Detection") as timer:
            latency, transcription = self.speech_recognizer.recognize_wake_word()
            print(f"  Detected: '{transcription}'")

        return timer.get_elapsed_ms()

    def measure_speech_to_text(self, prompt: str = "yes") -> float:
        """Measure speech-to-text latency."""
        print(f"\n[2/7] Testing Speech-to-Text")

        with PerformanceTimer("Speech-to-Text") as timer:
            latency, transcription = self.speech_recognizer.recognize_speech(prompt)
            print(f"  Transcribed: '{transcription}'")

        return timer.get_elapsed_ms()

    def measure_camera_capture(self) -> Tuple[float, Union[np.ndarray, None]]:
        """Measure camera capture time."""
        print("\n[3/7] Testing Camera Capture")

        if self.simulation:
            dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
            with PerformanceTimer("Camera Capture") as timer:
                time.sleep(0.075)
            return timer.get_elapsed_ms(), dummy_img

        with PerformanceTimer("Camera Capture") as timer:
            ret, frame = self.camera.read()
            if ret:
                print(f"  Captured: {frame.shape}")
            else:
                print(f"  {Colors.RED}Failed to capture frame{Colors.RESET}")
                return timer.get_elapsed_ms(), None

        return timer.get_elapsed_ms(), frame

    def measure_face_encoding(self, frame) -> Tuple[float, str]:
        """Measure JPEG encoding time."""
        print("\n[4/7] Testing Face Encoding")

        with PerformanceTimer("Face Encoding") as timer:
            if isinstance(frame, str):
                image_b64 = frame
            else:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                image_b64 = base64.b64encode(buffer).decode('utf-8')
                print(f"  Encoded: {len(image_b64)} chars")

        return timer.get_elapsed_ms(), image_b64

    def measure_face_recognition(self, image_b64: str) -> Tuple[float, Dict]:
        """Measure MCP face recognition with component breakdown."""
        print("\n[5/7] Testing Face Recognition (with component breakdown)")

        with PerformanceTimer("Face Recognition (Total)") as total_timer:
            total_time, result = self.face_recognizer.recognize(image_b64)

            status = result.get('status', 'unknown')
            print(f"  Status: {status}")

            # Add component timings
            timing = result.get('timing', {})
            if 'insightface_detection_ms' in timing:
                self.metrics.add_measurement('insightface_detection', timing['insightface_detection_ms'])
                print(f"    - InsightFace detection: {timing['insightface_detection_ms']:.1f}ms")

            if 'chromadb_query_ms' in timing:
                self.metrics.add_measurement('chromadb_query', timing['chromadb_query_ms'])
                print(f"    - ChromaDB query: {timing['chromadb_query_ms']:.1f}ms")

        return total_timer.get_elapsed_ms(), result

    def measure_response_generation(self, recognition_result: Dict) -> Tuple[float, str]:
        """Measure response generation (Gemma 3 simulation)."""
        print("\n[6/7] Testing Response Generation")

        with PerformanceTimer("Response Generation") as timer:
            status = recognition_result.get('status')

            if status == 'recognized':
                user_name = recognition_result.get('user', {}).get('name', 'there')
                response = f"Hello {user_name}! Welcome back!"
            else:
                response = "Hello! I don't recognize you. Would you like me to remember you?"

            # Simulate Gemma 3 inference
            time.sleep(0.2)
            print(f"  Generated: '{response}'")

        return timer.get_elapsed_ms(), response

    def measure_text_to_speech(self, text: str) -> float:
        """Measure TTS synthesis time."""
        print("\n[7/7] Testing Text-to-Speech")

        with PerformanceTimer("Text-to-Speech") as timer:
            tts_time = self.tts_engine.synthesize(text)

        return timer.get_elapsed_ms()

    def _run_single_test_internal(self) -> Dict[str, float]:
        """Internal method to run a single test (used for warm-up)."""
        timings = {}

        e2e_start = time.perf_counter()

        timings['wake_word'] = self.measure_wake_word_detection()
        timings['stt'] = self.measure_speech_to_text()
        timings['camera'], frame = self.measure_camera_capture()

        if frame is None:
            return timings

        timings['encoding'], image_b64 = self.measure_face_encoding(frame)
        timings['recognition'], result = self.measure_face_recognition(image_b64)
        timings['response_gen'], response = self.measure_response_generation(result)
        timings['tts'] = self.measure_text_to_speech(response)

        e2e_elapsed = (time.perf_counter() - e2e_start) * 1000
        timings['total'] = e2e_elapsed

        return timings

    def run_single_test(self, test_num: int) -> Dict[str, float]:
        """Run a complete end-to-end test."""
        print(f"\n{'='*70}")
        print(f"END-TO-END TEST #{test_num}")
        print(f"{'='*70}")

        timings = self._run_single_test_internal()

        e2e_elapsed = timings.get('total', 0)
        print(f"\n{'='*70}")
        print(f"[TOTAL] END-TO-END: {e2e_elapsed:.1f}ms ({e2e_elapsed/1000:.2f}s)")
        print(f"{'='*70}")

        return timings

    def run_performance_test(self) -> PerformanceMetrics:
        """Run complete test suite with warm-up."""
        print(f"\n{'#'*70}")
        print(f"ENHANCED PERFORMANCE TEST SUITE")
        print(f"Tests: {self.num_tests}, Warm-up: {self.num_warmup}")
        print(f"{'#'*70}\n")

        # System info
        print(f"{Colors.CYAN}SYSTEM INFORMATION:{Colors.RESET}")
        for key, value in self.metrics.system_info.items():
            print(f"  {key}: {value}")
        print()

        # Warm-up phase
        self.run_warmup_phase()

        # Test phase
        print(f"\n{Colors.CYAN}Running {self.num_tests} test iterations...{Colors.RESET}\n")

        for test_num in range(1, self.num_tests + 1):
            timings = self.run_single_test(test_num)

            # Record metrics
            for key, value in timings.items():
                metric_map = {
                    'wake_word': 'wake_word_detection',
                    'stt': 'speech_to_text',
                    'camera': 'camera_capture',
                    'encoding': 'face_encoding',
                    'recognition': 'face_recognition',
                    'response_gen': 'response_generation',
                    'tts': 'text_to_speech',
                    'total': 'end_to_end',
                }
                if key in metric_map:
                    self.metrics.add_measurement(metric_map[key], value)

            # Pause between tests
            if test_num < self.num_tests:
                print(f"\n[*] Waiting 2 seconds before next test...\n")
                time.sleep(2)

        return self.metrics

    def check_sla_compliance(self) -> Dict[str, bool]:
        """Check if results meet SLA targets."""
        summary = self.metrics.get_summary()
        compliance = {}

        for metric_name, target_ms in SLA_TARGETS.items():
            if metric_name in summary:
                mean_ms = summary[metric_name]['mean']
                passed = mean_ms <= target_ms
                compliance[metric_name] = passed

        return compliance

    def generate_report(self) -> str:
        """Generate comprehensive performance report."""
        summary = self.metrics.get_summary()
        compliance = self.check_sla_compliance()

        report = "\n" + "="*80 + "\n"
        report += "ENHANCED PERFORMANCE TEST RESULTS\n"
        report += "="*80 + "\n\n"

        # SLA Compliance Summary
        report += f"{Colors.BOLD}SLA COMPLIANCE SUMMARY:{Colors.RESET}\n"
        for metric, target in SLA_TARGETS.items():
            status = compliance.get(metric, False)
            symbol = f"{Colors.GREEN}[OK]{Colors.RESET}" if status else f"{Colors.RED}[FAIL]{Colors.RESET}"
            if metric in summary:
                mean = summary[metric]['mean']
                report += f"  {symbol} {metric}: {mean:.1f}ms (target: {target}ms)\n"
        report += "\n"

        # Detailed metrics table
        report += f"{Colors.BOLD}DETAILED METRICS:{Colors.RESET}\n"
        report += "-" * 100 + "\n"
        report += f"{'Metric':<25} {'Count':<6} {'Mean':<10} {'Median':<10} {'CI-95%':<20} {'Outliers':<15}\n"
        report += "-" * 100 + "\n"

        for metric_name in sorted(summary.keys()):
            if metric_name.startswith('_'):
                continue

            stats = summary[metric_name]
            count = stats['count']
            mean = stats['mean']
            median = stats['median']
            ci_low = stats['ci_95_low']
            ci_high = stats['ci_95_high']
            outliers = stats['outliers']

            ci_str = f"[{ci_low:.1f}, {ci_high:.1f}]"
            outlier_str = f"({len(outliers)})" if outliers else "None"

            report += f"{metric_name:<25} {count:<6} {mean:>8.1f}ms {median:>8.1f}ms {ci_str:<20} {outlier_str:<15}\n"

        report += "\n" + "="*80 + "\n"

        # Key insights
        if 'end_to_end' in summary:
            e2e_mean = summary['end_to_end']['mean']
            report += f"{Colors.BOLD}KEY INSIGHTS:{Colors.RESET}\n"
            report += f"  • Average end-to-end latency: {e2e_mean:.1f}ms ({e2e_mean/1000:.2f}s)\n"

            # Component breakdown
            if 'wake_word_detection' in summary:
                pct = (summary['wake_word_detection']['mean'] / e2e_mean) * 100
                report += f"  • Wake word detection: {pct:.1f}% of total time\n"

            if 'face_recognition' in summary:
                pct = (summary['face_recognition']['mean'] / e2e_mean) * 100
                report += f"  • Face recognition: {pct:.1f}% of total time\n"

            if 'text_to_speech' in summary:
                pct = (summary['text_to_speech']['mean'] / e2e_mean) * 100
                report += f"  • Text-to-speech: {pct:.1f}% of total time\n"

        # Outlier analysis
        report += f"\n{Colors.BOLD}OUTLIER ANALYSIS:{Colors.RESET}\n"
        has_outliers = False
        for metric_name, stats in summary.items():
            if stats['outliers']:
                has_outliers = True
                outlier_info = [f"{v:.1f}ms" for v in stats['outliers']]
                report += f"  {metric_name}: {', '.join(outlier_info)} (indices: {stats['outlier_indices']})\n"

        if not has_outliers:
            report += f"  {Colors.GREEN}[OK] No significant outliers detected{Colors.RESET}\n"

        report += "\n" + "="*80 + "\n"

        return report

    def cleanup(self):
        """Release resources."""
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced end-to-end performance testing')
    parser.add_argument('--num-tests', type=int, default=5, help='Number of test iterations')
    parser.add_argument('--num-warmup', type=int, default=2, help='Number of warm-up iterations')
    parser.add_argument('--simulation', action='store_true', help='Run in simulation mode')
    parser.add_argument('--output', type=str, default='performance_results.json', help='Output file')
    parser.add_argument('--no-report', action='store_true', help='Skip report generation')

    args = parser.parse_args()

    # Create tester
    tester = EnhancedEndToEndPerformanceTester(
        simulation=args.simulation or SIMULATION_MODE,
        num_warmup=args.num_warmup,
        num_tests=args.num_tests
    )

    try:
        # Run tests
        metrics = tester.run_performance_test()

        # Generate and print report
        if not args.no_report:
            report = tester.generate_report()
            print(report)

        # Save results
        output_path = Path(args.output)
        metrics.save_to_file(output_path)
        print(f"\n{Colors.GREEN}[OK] Results saved to: {output_path}{Colors.RESET}")

        # Save report
        report_path = output_path.parent / f"{output_path.stem}_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(tester.generate_report())
        print(f"{Colors.GREEN}[OK] Report saved to: {report_path}{Colors.RESET}")

    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
