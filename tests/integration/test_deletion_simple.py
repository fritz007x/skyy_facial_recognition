"""
Simple test script for deletion feature - no dependencies.
Validates code syntax and structure only.

Usage:
    python test_deletion_simple.py
"""

import ast
from pathlib import Path


def test_file_syntax(filepath, description):
    """Test that a Python file has valid syntax."""
    print(f"Testing: {description}")
    print(f"  File: {filepath}")

    if not filepath.exists():
        print(f"  ✗ File not found: {filepath}")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"  [OK] Valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"  [X] Syntax error: {e}")
        return False


def test_file_contains(filepath, search_strings, description):
    """Test that a file contains specific strings."""
    print(f"Testing: {description}")

    if not filepath.exists():
        print(f"  [X] File not found: {filepath}")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        for search_str in search_strings:
            if search_str in content:
                print(f"  [OK] Found: {search_str}")
            else:
                print(f"  [X] Missing: {search_str}")
                return False
        return True
    except Exception as e:
        print(f"  [X] Error reading file: {e}")
        return False


def main():
    print("=" * 60)
    print("  DELETION FEATURE - SIMPLE VALIDATION TESTS")
    print("=" * 60 + "\n")

    project_root = Path(__file__).parent.parent.parent
    gemma_root = project_root / "src" / "gemma_voice_assistant"

    tests_passed = 0
    tests_total = 0

    # Test 1: deletion_orchestrator.py syntax
    tests_total += 1
    if test_file_syntax(
        gemma_root / "modules" / "deletion_orchestrator.py",
        "DeletionOrchestrator syntax"
    ):
        tests_passed += 1
    print()

    # Test 2: deletion_orchestrator.py contains required classes
    tests_total += 1
    if test_file_contains(
        gemma_root / "modules" / "deletion_orchestrator.py",
        [
            "class DeletionState(Enum)",
            "class DeletionOrchestrator",
            "def recognize_user",
            "def confirm_identity",
            "def explain_and_confirm_deletion",
            "def execute_deletion",
            "def run_deletion_flow",
            "def _extract_confirmation"
        ],
        "DeletionOrchestrator required methods"
    ):
        tests_passed += 1
    print()

    # Test 3: config.py updated with deletion wake words
    tests_total += 1
    if test_file_contains(
        gemma_root / "config.py",
        [
            "DELETION_WAKE_WORD",
            "DELETION_WAKE_WORD_ALTERNATIVES",
            "skyy forget me"
        ],
        "Config deletion wake words"
    ):
        tests_passed += 1
    print()

    # Test 4: main.py syntax
    tests_total += 1
    if test_file_syntax(
        gemma_root / "main.py",
        "main.py syntax"
    ):
        tests_passed += 1
    print()

    # Test 5: main.py imports and uses DeletionOrchestrator
    tests_total += 1
    if test_file_contains(
        gemma_root / "main.py",
        [
            "from modules.deletion_orchestrator import DeletionOrchestrator",
            "DELETION_WAKE_WORD",
            "DELETION_WAKE_WORD_ALTERNATIVES",
            "self.deletion",
            "def handle_deletion",
            "self.deletion.run_deletion_flow"
        ],
        "main.py DeletionOrchestrator integration"
    ):
        tests_passed += 1
    print()

    # Test 6: main.py routes deletion wake words
    tests_total += 1
    if test_file_contains(
        gemma_root / "main.py",
        [
            "deletion_wake_words",
            "is_deletion",
            "self.handle_deletion()"
        ],
        "main.py wake word routing"
    ):
        tests_passed += 1
    print()

    # Test 7: Check documentation exists
    tests_total += 1
    docs_exist = all([
        (project_root / "DELETION_ARCHITECTURE.md").exists(),
        (project_root / "DELETION_QUICK_START.md").exists(),
        (project_root / "DELETION_SUMMARY.md").exists(),
        (project_root / "TEST_DELETION_FEATURE.md").exists()
    ])
    if docs_exist:
        print("Testing: Documentation files")
        print("  [OK] DELETION_ARCHITECTURE.md")
        print("  [OK] DELETION_QUICK_START.md")
        print("  [OK] DELETION_SUMMARY.md")
        print("  [OK] TEST_DELETION_FEATURE.md")
        tests_passed += 1
    else:
        print("Testing: Documentation files")
        print("  [X] Some documentation files missing")
    print()

    # Summary
    print("=" * 60)
    if tests_passed == tests_total:
        print(f"  ALL TESTS PASSED [OK] ({tests_passed}/{tests_total})")
        print("=" * 60)
        print("\nImplementation validated successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment: facial_mcp_py311\\Scripts\\activate")
        print("2. Run application: python src/gemma_voice_assistant/main.py")
        print("3. Test with voice: Say 'Skyy, forget me'")
        print("\nSee TEST_DELETION_FEATURE.md for comprehensive test procedures")
        return 0
    else:
        print(f"  TESTS FAILED [X] ({tests_passed}/{tests_total} passed)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
