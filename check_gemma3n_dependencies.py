#!/usr/bin/env python3
"""
Gemma 3n Dependency Checker

Comprehensive dependency verification for Gemma 3n models.
Run this before attempting to use Gemma 3n to ensure all requirements are met.

Usage:
    python check_gemma3n_dependencies.py
"""

import sys
from typing import List, Tuple, Dict, Any


def check_python_version() -> Tuple[bool, str]:
    """Check Python version (3.8+)."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"{version.major}.{version.minor}.{version.micro}"
    return True, f"{version.major}.{version.minor}.{version.micro}"


def check_package_version(package_name: str, min_version: str = None) -> Tuple[bool, str, str]:
    """
    Check if a package is installed and optionally verify version.

    Returns:
        (installed: bool, version: str, error_message: str)
    """
    try:
        module = __import__(package_name)
        version = getattr(module, '__version__', 'unknown')

        if min_version:
            try:
                from packaging import version as pkg_version
                if pkg_version.parse(version) < pkg_version.parse(min_version):
                    return False, version, f"Version {version} < required {min_version}"
            except ImportError:
                # packaging not available, skip version check
                pass

        return True, version, ""

    except ImportError:
        return False, "not installed", "Package not found"


def check_all_dependencies() -> Dict[str, Any]:
    """
    Check all Gemma 3n dependencies.

    Returns:
        Dictionary with check results
    """
    results = {
        'python': {'required': '3.8+', 'status': False, 'version': '', 'critical': True},
        'torch': {'required': '2.0.0+', 'status': False, 'version': '', 'critical': True},
        'transformers': {'required': '4.53.0+', 'status': False, 'version': '', 'critical': True},
        'torchaudio': {'required': '2.0.0+', 'status': False, 'version': '', 'critical': True},
        'timm': {'required': '0.9.0+', 'status': False, 'version': '', 'critical': True},
        'huggingface_hub': {'required': '0.20.0+', 'status': False, 'version': '', 'critical': True},
        'pyttsx3': {'required': '2.90+', 'status': False, 'version': '', 'critical': False},
        'opencv-python (cv2)': {'required': 'any', 'status': False, 'version': '', 'critical': False},
    }

    # Check Python version
    python_ok, python_version = check_python_version()
    results['python']['status'] = python_ok
    results['python']['version'] = python_version

    # Check packages
    packages_to_check = {
        'torch': '2.0.0',
        'transformers': '4.53.0',
        'torchaudio': '2.0.0',
        'timm': '0.9.0',
        'huggingface_hub': '0.20.0',
        'pyttsx3': None,  # No minimum version
    }

    for package, min_ver in packages_to_check.items():
        ok, version, error = check_package_version(package, min_ver)
        results[package]['status'] = ok
        results[package]['version'] = version
        if error:
            results[package]['error'] = error

    # Special check for cv2 (opencv-python)
    try:
        import cv2
        results['opencv-python (cv2)']['status'] = True
        results['opencv-python (cv2)']['version'] = cv2.__version__
    except ImportError:
        results['opencv-python (cv2)']['version'] = 'not installed'

    return results


def print_results(results: Dict[str, Any]):
    """Print formatted dependency check results."""
    print("\n" + "=" * 80)
    print("GEMMA 3N DEPENDENCY CHECKER")
    print("=" * 80)

    critical_missing = []
    optional_missing = []

    # Print each dependency
    for name, info in results.items():
        status = "[OK]" if info['status'] else "[MISSING]"
        critical = " (CRITICAL)" if info.get('critical', False) else " (Optional)"
        version_info = info['version'] if info['version'] else 'unknown'

        print(f"\n{status} {name}{critical if not info['status'] else ''}")
        print(f"    Required: {info['required']}")
        print(f"    Found:    {version_info}")

        if not info['status']:
            if info.get('critical', False):
                critical_missing.append(name)
            else:
                optional_missing.append(name)

        if 'error' in info:
            print(f"    Error:    {info['error']}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if not critical_missing and not optional_missing:
        print("\n[SUCCESS] All dependencies are installed and ready!")
        print("\nYou can now run:")
        print("  python src\\gemma3n_native_audio_assistant.py test_audio\\hello_gemma.wav")
        return True

    if critical_missing:
        print("\n[ERROR] Critical dependencies are missing!")
        print("\nMissing critical packages:")
        for pkg in critical_missing:
            print(f"  - {pkg}")

    if optional_missing:
        print("\n[WARNING] Optional dependencies are missing:")
        for pkg in optional_missing:
            print(f"  - {pkg}")

    # Installation instructions
    print("\n" + "=" * 80)
    print("INSTALLATION INSTRUCTIONS")
    print("=" * 80)

    print("\n1. Activate your virtual environment:")
    print("   facial_mcp_py311\\Scripts\\activate")

    if critical_missing or optional_missing:
        print("\n2. Install missing packages:")

        # Build install command
        packages_to_install = []
        if 'torch' in critical_missing:
            packages_to_install.append("torch>=2.0.0")
        if 'transformers' in critical_missing:
            packages_to_install.append("transformers>=4.53.0")
        if 'torchaudio' in critical_missing:
            packages_to_install.append("torchaudio>=2.0.0")
        if 'timm' in critical_missing:
            packages_to_install.append("timm>=0.9.0")
        if 'huggingface_hub' in critical_missing:
            packages_to_install.append("huggingface-hub>=0.20.0")
        if 'pyttsx3' in critical_missing or 'pyttsx3' in optional_missing:
            packages_to_install.append("pyttsx3")
        if 'opencv-python (cv2)' in critical_missing or 'opencv-python (cv2)' in optional_missing:
            packages_to_install.append("opencv-python")

        if packages_to_install:
            print(f"   pip install {' '.join(packages_to_install)}")

        print("\n   OR install all Gemma 3n dependencies at once:")
        print("   pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub pyttsx3 opencv-python")

    print("\n3. Re-run this checker to verify:")
    print("   python check_gemma3n_dependencies.py")

    # Special note about timm
    if 'timm' in critical_missing:
        print("\n" + "=" * 80)
        print("IMPORTANT: WHY TIMM IS REQUIRED")
        print("=" * 80)
        print("\nThe 'timm' (PyTorch Image Models) library is CRITICAL for Gemma 3n:")
        print("  - Gemma 3n is a unified multimodal model (audio + vision + text)")
        print("  - Even for audio-only use, the model architecture requires vision components")
        print("  - The TimmWrapperModel is part of Gemma 3n's internal architecture")
        print("  - Without timm, model loading will fail with:")
        print("    'TimmWrapperModel requires the timm library'")
        print("\nInstall with: pip install timm>=0.9.0")

    print("\n" + "=" * 80)

    return False


def main():
    """Main entry point."""
    print("\nChecking Gemma 3n dependencies...")

    results = check_all_dependencies()
    success = print_results(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
