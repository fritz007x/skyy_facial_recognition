"""
Utility script to update the CAMERA_INDEX value inside config.py.

This script re-implements minimal versions of:
- list_available_cameras()
- select_camera_interactive()
- change_camera_mode()

It does NOT import webcam_capture(enhanced).py and remains standalone.
"""

import cv2
import re
from pathlib import Path

# Path to config.py (adjust if needed)
CONFIG_PATH = Path(__file__).parent / "config.py"


# -------------------------------------------------------------------------
# 1) Minimal reimplementation: list_available_cameras()
# -------------------------------------------------------------------------
def list_available_cameras(max_index=10):
    cameras = []
    print("\n=== SCANNING FOR CAMERAS ===")

    for i in range(max_index):
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Use DirectShow to avoid Windows errors
            if cap is None or not cap.isOpened():
                continue

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            backend = cap.getBackendName()

            cameras.append({
                "index": i,
                "width": width,
                "height": height,
                "fps": fps,
                "backend": backend
            })

            print(f"  [{i}] {width}x{height} @ {fps}fps ({backend})")

        except Exception:
            pass

        finally:
            if 'cap' in locals():
                cap.release()

    return cameras



# -------------------------------------------------------------------------
# 2) Minimal reimplementation: select_camera_interactive()
# -------------------------------------------------------------------------
def select_camera_interactive():
    print("\n=== CAMERA SELECTION ===")

    cameras = list_available_cameras()
    if not cameras:
        raise RuntimeError("No cameras found.")

    while True:
        choice = input("\nSelect camera index (default 0): ").strip()

        if choice == "":
            return 0

        try:
            idx = int(choice)
            if any(cam["index"] == idx for cam in cameras):
                return idx
            print("Invalid camera index. Try again.")
        except ValueError:
            print("Please enter a valid number.")


# -------------------------------------------------------------------------
# 3) Minimal equivalent of change_camera_mode() — but updates config.py
# -------------------------------------------------------------------------
def update_config_camera_index(new_index):
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"config.py not found: {CONFIG_PATH}")

    text = CONFIG_PATH.read_text()

    # Replace the line CAMERA_INDEX = X
    new_text = re.sub(
        r"^CAMERA_INDEX\s*=\s*\d+",
        f"CAMERA_INDEX = {new_index}",
        text,
        flags=re.MULTILINE
    )

    CONFIG_PATH.write_text(new_text)
    print(f"\n✔ Updated CAMERA_INDEX = {new_index} in config.py")


# -------------------------------------------------------------------------
# Main utility function
# -------------------------------------------------------------------------
def main():
    print("\n=== CAMERA CONFIGURATION UPDATER ===")

    try:
        selected_index = select_camera_interactive()
        update_config_camera_index(selected_index)
        print("\nDone!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
