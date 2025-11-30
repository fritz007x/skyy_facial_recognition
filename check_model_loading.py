"""
Check if Gemma 3n model loading is progressing or stuck.

This script monitors the HuggingFace cache directory to see if files are being written.
"""

import os
import time
from pathlib import Path

def get_cache_dir():
    """Get HuggingFace cache directory."""
    cache_home = os.environ.get("HF_HOME", os.path.join(os.path.expanduser("~"), ".cache", "huggingface"))
    return Path(cache_home) / "hub"

def find_model_cache(model_name: str = "gemma-3n-E4B"):
    """Find the model cache directory."""
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        print(f"[ERROR] Cache directory not found: {cache_dir}")
        return None

    # Find matching model directory
    for item in cache_dir.iterdir():
        if item.is_dir() and model_name.lower() in item.name.lower():
            return item

    print(f"[INFO] No cache directory found for {model_name}")
    print(f"[INFO] Model hasn't started downloading yet")
    return None

def monitor_progress(model_dir: Path, duration: int = 30):
    """Monitor if files are being written to model directory."""
    print(f"\n[Monitoring] Watching: {model_dir}")
    print(f"[Monitoring] Duration: {duration} seconds\n")

    # Get initial state
    initial_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
    initial_time = time.time()

    print(f"[Status] Initial cache size: {initial_size / 1024 / 1024:.1f} MB")
    print(f"[Status] Monitoring for {duration} seconds...\n")

    # Monitor for changes
    time.sleep(duration)

    # Get final state
    final_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
    final_time = time.time()

    size_change = final_size - initial_size
    time_elapsed = final_time - initial_time

    print(f"[Status] Final cache size: {final_size / 1024 / 1024:.1f} MB")
    print(f"[Status] Size change: {size_change / 1024 / 1024:.1f} MB in {time_elapsed:.1f}s")

    if size_change > 0:
        speed = size_change / time_elapsed / 1024 / 1024
        print(f"[Result] ✓ PROGRESSING - Download speed: {speed:.2f} MB/s")

        # Estimate remaining time (rough)
        # E4B model is ~8GB total
        remaining = (8 * 1024) - (final_size / 1024 / 1024)
        if remaining > 0 and speed > 0:
            eta_minutes = (remaining / speed) / 60
            print(f"[Estimate] ~{eta_minutes:.0f} minutes remaining at current speed")
    else:
        print(f"[Result] ✗ STUCK - No file changes detected")
        print(f"[Advice] The model loading may be stuck. Consider:")
        print(f"  1. Press Ctrl+C to stop")
        print(f"  2. Use E2B model instead (designed for CPU)")
        print(f"  3. Check Task Manager for memory usage")

def main():
    print("=" * 70)
    print("Gemma 3n Model Loading Monitor")
    print("=" * 70)

    # Check E4B first
    model_dir = find_model_cache("gemma-3n-E4B")

    if model_dir:
        monitor_progress(model_dir, duration=30)
    else:
        # Try E2B
        model_dir = find_model_cache("gemma-3n-E2B")
        if model_dir:
            monitor_progress(model_dir, duration=30)
        else:
            print("\n[INFO] No Gemma 3n model cache found")
            print("[INFO] Model may not have started loading yet")
            print("\n[Advice] Check if the voice assistant script is still running")

if __name__ == "__main__":
    main()
