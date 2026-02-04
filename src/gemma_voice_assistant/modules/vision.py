"""
Vision module for webcam capture.

Based on the webcam_capture.py patterns from the Skyy Facial Recognition project.
Provides utilities for capturing images from webcam and encoding them for the MCP server.

The MCP server expects base64-encoded JPEG images, which this module provides.
"""

import cv2
import base64
import numpy as np
from typing import Optional, Tuple
from pathlib import Path
import tempfile


class WebcamManager:
    """
    Handles webcam capture operations.
    
    Provides methods for:
    - Initializing webcam with warmup
    - Capturing single frames
    - Encoding frames as base64 for MCP server
    - Saving frames to disk
    - Showing preview window
    """
    
    def __init__(
        self, 
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        warmup_frames: int = 30
    ):
        """
        Initialize webcam manager.
        
        Args:
            camera_index: Camera device index (0 is usually default webcam)
            width: Capture width in pixels
            height: Capture height in pixels
            warmup_frames: Number of frames to skip for camera warmup
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.warmup_frames = warmup_frames
        self.cap: Optional[cv2.VideoCapture] = None
    
    def initialize(self) -> bool:
        """
        Initialize the webcam.

        Opens the camera device, sets resolution, and performs warmup
        by reading and discarding initial frames.

        Returns:
            True if successful, False otherwise
        """
        import time
        import platform

        print(f"[Vision] Initializing camera {self.camera_index}...")

        # On Windows, try DirectShow backend first (more reliable than MSMF)
        if platform.system() == "Windows":
            print("[Vision] Using DirectShow backend (Windows)...")
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            print("[Vision] ERROR: Could not open camera")
            print("[Vision] Make sure no other application is using the webcam")
            return False

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Give camera time to initialize hardware
        time.sleep(0.5)

        # Read actual resolution (may differ from requested)
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[Vision] Camera resolution: {actual_width}x{actual_height}")

        # Warm up camera (skip initial frames for auto-exposure to settle)
        print(f"[Vision] Warming up camera ({self.warmup_frames} frames)...")
        failed_frames = 0
        for i in range(self.warmup_frames):
            ret, _ = self.cap.read()
            if not ret:
                failed_frames += 1
                # Brief pause on failure to give camera time
                time.sleep(0.1)
            # Small delay between frames to avoid overwhelming the camera
            time.sleep(0.05)

        if failed_frames > 0:
            print(f"[Vision] Warmup: {failed_frames}/{self.warmup_frames} frames failed")

        # Verify camera is working by capturing a test frame
        ret, test_frame = self.cap.read()
        if not ret or test_frame is None:
            print("[Vision] ERROR: Camera not responding after warmup")
            self.cap.release()
            self.cap = None
            return False

        print("[Vision] Camera ready.")
        return True
    
    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a single frame from the webcam.
        
        Returns:
            Tuple of (success: bool, frame: numpy array or None)
        """
        if self.cap is None or not self.cap.isOpened():
            print("[Vision] ERROR: Camera not initialized")
            return False, None
        
        ret, frame = self.cap.read()
        
        if not ret or frame is None:
            print("[Vision] ERROR: Failed to capture frame")
            return False, None
        
        return True, frame
    
    def capture_to_base64(self, format: str = ".jpg", quality: int = 95) -> Tuple[bool, str]:
        """
        Capture frame and encode as base64 string.
        
        This is the format expected by the MCP server's image_data parameter.
        
        Args:
            format: Image format (.jpg recommended for smaller size)
            quality: JPEG quality 0-100 (default 95)
            
        Returns:
            Tuple of (success: bool, base64_string: str)
        """
        success, frame = self.capture_frame()
        
        if not success or frame is None:
            return False, ""
        
        # Encode frame to bytes
        if format.lower() in ['.jpg', '.jpeg']:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        else:
            encode_params = []
        
        _, buffer = cv2.imencode(format, frame, encode_params)
        
        # Convert to base64
        base64_string = base64.b64encode(buffer).decode('utf-8')
        
        print(f"[Vision] Captured image: {len(base64_string)} bytes (base64)")
        return True, base64_string
    
    def capture_to_file(self, filepath: Optional[str] = None) -> Tuple[bool, str]:
        """
        Capture frame and save to file.
        
        Args:
            filepath: Optional path. If None, creates temp file.
            
        Returns:
            Tuple of (success: bool, filepath: str)
        """
        success, frame = self.capture_frame()
        
        if not success or frame is None:
            return False, ""
        
        if filepath is None:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            filepath = str(Path(temp_dir) / "gemma_capture.jpg")
        
        cv2.imwrite(filepath, frame)
        print(f"[Vision] Saved capture to: {filepath}")
        
        return True, filepath
    
    def show_preview(self, duration_ms: int = 3000, window_name: str = "Camera Preview") -> None:
        """
        Show a preview window of the camera feed.
        
        Args:
            duration_ms: How long to show preview in milliseconds
            window_name: Name of the preview window
        """
        print(f"[Vision] Showing preview for {duration_ms}ms...")
        print("[Vision] Press 'q' to close early")
        
        start_time = cv2.getTickCount()
        
        while True:
            success, frame = self.capture_frame()
            
            if success and frame is not None:
                # Add instruction text
                cv2.putText(
                    frame, 
                    "Press 'q' to close", 
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (255, 255, 255), 
                    2
                )
                cv2.imshow(window_name, frame)
            
            # Check for 'q' key or timeout
            elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency() * 1000
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or elapsed >= duration_ms:
                break
        
        cv2.destroyAllWindows()
    
    def capture_with_preview(self, window_name: str = "Capture - Press SPACE") -> Tuple[bool, str]:
        """
        Show preview and capture when user presses SPACE.
        
        Similar to the webcam_capture.py interactive mode.
        
        Args:
            window_name: Name of the preview window
            
        Returns:
            Tuple of (success: bool, base64_string: str)
        """
        print("[Vision] Press SPACE to capture, ESC to cancel")
        
        while True:
            success, frame = self.capture_frame()
            
            if not success or frame is None:
                print("[Vision] Failed to grab frame")
                break
            
            # Add instruction text
            cv2.putText(
                frame,
                "SPACE: Capture | ESC: Cancel",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("[Vision] Capture cancelled")
                cv2.destroyAllWindows()
                return False, ""
            
            elif key == 32:  # SPACE
                # Encode current frame
                _, buffer = cv2.imencode('.jpg', frame)
                base64_string = base64.b64encode(buffer).decode('utf-8')
                print(f"[Vision] Image captured! ({len(base64_string)} bytes)")
                cv2.destroyAllWindows()
                return True, base64_string
        
        cv2.destroyAllWindows()
        return False, ""
    
    def release(self) -> None:
        """Release the webcam resource."""
        if self.cap is not None:
            self.cap.release()
            cv2.destroyAllWindows()
            print("[Vision] Camera released.")
    
    def is_open(self) -> bool:
        """Check if camera is currently open."""
        return self.cap is not None and self.cap.isOpened()
