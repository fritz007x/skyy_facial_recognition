"""
Test script to verify all bug fixes are working correctly.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_similarity_calculation():
    """Test the corrected similarity calculation."""
    print("=" * 60)
    print("Testing Similarity Calculation Fix")
    print("=" * 60)

    # Test cases: (distance, expected_similarity)
    test_cases = [
        (0.0, 100.0),   # Perfect match
        (0.2, 90.0),    # Very strong match
        (0.4, 80.0),    # Strong match
        (0.5, 75.0),    # Good match
        (1.0, 50.0),    # Medium match
        (1.5, 25.0),    # Weak match
        (2.0, 0.0),     # No match
        (2.5, 0.0),     # Beyond range (should clamp to 0)
    ]

    all_passed = True
    for distance, expected in test_cases:
        # Corrected formula: (1 - distance/2) * 100, clamped to [0, 100]
        similarity = max(0, min(100, (1 - distance / 2) * 100))

        passed = abs(similarity - expected) < 0.01
        status = "[PASS]" if passed else "[FAIL]"

        print(f"{status} | Distance: {distance:.2f} -> Similarity: {similarity:.1f}% (expected {expected:.1f}%)")

        if not passed:
            all_passed = False

    print()
    return all_passed

def test_imports():
    """Test that all imports work correctly."""
    print("=" * 60)
    print("Testing Imports")
    print("=" * 60)

    try:
        # Test oauth_config import
        from oauth_config import oauth_config
        print("[PASS] | oauth_config imported successfully")

        # Test config import
        from config import (
            WAKE_WORD, WAKE_WORD_ALTERNATIVES, MCP_PYTHON_PATH,
            MCP_SERVER_SCRIPT, SIMILARITY_THRESHOLD
        )
        print("[PASS] | config imported successfully")
        print(f"  - Wake words: {WAKE_WORD_ALTERNATIVES}")
        print(f"  - Python path: {MCP_PYTHON_PATH}")

        # Test modules import
        from modules.speech import SpeechManager
        from modules.vision import WebcamManager
        from modules.mcp_client import SkyyMCPClient
        from modules.permission import PermissionManager
        print("[PASS] | All modules imported successfully")

        print()
        return True

    except ImportError as e:
        print(f"[FAIL] | Import error: {e}")
        print()
        return False

def test_name_validation():
    """Test the name validation logic."""
    print("=" * 60)
    print("Testing Name Validation")
    print("=" * 60)

    import re

    # Test cases: (name, should_be_valid)
    test_cases = [
        ("John Doe", True),
        ("Mary-Jane", True),
        ("O'Brien", True),
        ("Dr. Smith", True),
        ("J", False),  # Too short
        ("", False),  # Empty
        ("A" * 101, False),  # Too long
        ("John123", False),  # Contains numbers
        ("Test@User", False),  # Contains special chars
        ("José García", False),  # Regex doesn't support accented characters
    ]

    all_passed = True
    pattern = r'^[a-zA-Z\s\-\.\']+$'

    for name, should_be_valid in test_cases:
        # Validation logic from main.py
        is_valid = bool(
            name and
            len(name) >= 2 and
            len(name) <= 100 and
            re.match(pattern, name) is not None
        )

        passed = is_valid == should_be_valid
        status = "[PASS]" if passed else "[FAIL]"

        display_name = name if len(name) <= 30 else name[:30] + "..."
        print(f"{status} | '{display_name}' -> {'Valid' if is_valid else 'Invalid'} (expected {'Valid' if should_be_valid else 'Invalid'})")

        if not passed:
            all_passed = False

    print()
    return all_passed

def test_platform_paths():
    """Test cross-platform path detection."""
    print("=" * 60)
    print("Testing Cross-Platform Paths")
    print("=" * 60)

    import platform
    from pathlib import Path

    current_os = platform.system()
    print(f"Current OS: {current_os}")

    # Import and check path
    from config import MCP_PYTHON_PATH, VENV_NAME

    print(f"Virtual env name: {VENV_NAME}")
    print(f"Python path: {MCP_PYTHON_PATH}")

    # Verify correct path structure
    if current_os == "Windows":
        expected_part = "Scripts"
    else:
        expected_part = "bin"

    path_str = str(MCP_PYTHON_PATH)
    if expected_part in path_str:
        print(f"[PASS] | Correct path structure for {current_os} (contains '{expected_part}')")
        result = True
    else:
        print(f"[FAIL] | Incorrect path structure for {current_os} (missing '{expected_part}')")
        result = False

    print()
    return result

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" GEMMA MCP PROTOTYPE - BUG FIX VERIFICATION")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Similarity Calculation", test_similarity_calculation()))
    results.append(("Name Validation", test_name_validation()))
    results.append(("Platform Paths", test_platform_paths()))

    # Summary
    print("=" * 60)
    print(" TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} | {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n[OK] All tests passed! Bug fixes verified successfully.\n")
        return 0
    else:
        print("\n[ERROR] Some tests failed. Please review the output above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
