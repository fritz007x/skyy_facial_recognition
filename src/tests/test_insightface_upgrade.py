#!/usr/bin/env python3
"""
Quick test script to verify InsightFace 0.7.3 upgrade is working correctly
with the Skyy Facial Recognition MCP Server.
"""

import sys
import os

import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_insightface_import():
    """Test InsightFace can be imported and version is correct."""
    print("=" * 60)
    print("TEST 1: InsightFace Import and Version")
    print("=" * 60)
    try:
        import insightface
        print(f"[OK] InsightFace imported successfully")
        print(f"[OK] Version: {insightface.__version__}")

        if insightface.__version__ >= "0.7.3":
            print(f"[OK] Version is 0.7.3 or higher - PASS")
            return True
        else:
            print(f"[X] Version is {insightface.__version__}, expected 0.7.3+")
            return False
    except Exception as e:
        print(f"[X] Failed to import InsightFace: {e}")
        traceback.print_exc()
        return False

def test_face_analysis_model():
    """Test that FaceAnalysis can initialize with buffalo_l model."""
    print("\n" + "=" * 60)
    print("TEST 2: FaceAnalysis Model Initialization")
    print("=" * 60)
    try:
        from insightface.app import FaceAnalysis
        print("[OK] FaceAnalysis imported")

        # Initialize the model (this will download if not present)
        print("[...] Initializing buffalo_l model...")
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        print("[OK] FaceAnalysis initialized")

        # Prepare the model
        app.prepare(ctx_id=0, det_size=(640, 640))
        print("[OK] Model prepared successfully - PASS")
        return True
    except Exception as e:
        print(f"[X] Failed to initialize FaceAnalysis: {e}")
        traceback.print_exc()
        return False

def test_mcp_server_import():
    """Test that the MCP server can be imported."""
    print("\n" + "=" * 60)
    print("TEST 3: MCP Server Import")
    print("=" * 60)
    try:
        import skyy_facial_recognition_mcp
        print("[OK] MCP server module imported successfully")

        # Check for key components
        has_mcp = hasattr(skyy_facial_recognition_mcp, 'mcp')
        print(f"[{'OK' if has_mcp else 'X'}] MCP instance found: {has_mcp}")

        return has_mcp
    except Exception as e:
        print(f"[X] Failed to import MCP server: {e}")
        traceback.print_exc()
        return False

def test_database_operations():
    """Test basic database operations."""
    print("\n" + "=" * 60)
    print("TEST 4: Database Operations")
    print("=" * 60)
    try:
        import json
        from pathlib import Path

        db_path = Path("./skyy_face_data")
        print(f"[OK] Database path: {db_path.absolute()}")

        if db_path.exists():
            print(f"[OK] Database directory exists")

            index_file = db_path / "index.json"
            if index_file.exists():
                with open(index_file, 'r') as f:
                    data = json.load(f)
                user_count = len(data.get('users', {}))
                print(f"[OK] Database has {user_count} registered users")
            else:
                print(f"[INFO] No index.json file yet (database is empty)")
        else:
            print(f"[INFO] Database directory will be created on first use")

        return True
    except Exception as e:
        print(f"[X] Database check failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("INSIGHTFACE 0.7.3 UPGRADE VERIFICATION TEST")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")

    results = []

    # Run tests
    results.append(("InsightFace Import", test_insightface_import()))
    results.append(("Face Analysis Model", test_face_analysis_model()))
    results.append(("MCP Server Import", test_mcp_server_import()))
    results.append(("Database Operations", test_database_operations()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! InsightFace 0.7.3 is working correctly.")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
