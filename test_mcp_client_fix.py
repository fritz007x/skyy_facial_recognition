"""
Test script to verify the MCP client fix in main_sync.py.

This script tests that the persistent event loop properly handles
multiple async MCP calls without the "different task" error.
"""

import sys
from pathlib import Path

# Add gemma_mcp_prototype to path
sys.path.insert(0, str(Path(__file__).parent / "gemma_mcp_prototype"))

# Add src directory for oauth_config
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gemma_mcp_prototype.main_sync import GemmaFacialRecognition


def test_mcp_client_multiple_calls():
    """
    Test that MCP client can make multiple async calls without errors.

    This tests the fix for:
    RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
    """
    print("=" * 80)
    print("Testing MCP Client Fix - Multiple Async Calls")
    print("=" * 80)

    app = GemmaFacialRecognition()

    try:
        # Test 1: Initialize (connects to MCP)
        print("\n[Test] Initializing application (includes MCP connect)...")
        if not app.initialize():
            print("[Test] FAILED: Initialization failed")
            return False

        print("[Test] PASSED: Initialization successful")

        # Test 2: Make a second MCP call (this would fail with the old code)
        print("\n[Test] Making second MCP call (get_health_status)...")
        try:
            health = app._run_async(app.mcp_client.get_health_status(app.access_token))
            if health:
                print(f"[Test] PASSED: Second MCP call successful - Status: {health.get('overall_status', 'unknown')}")
            else:
                print("[Test] WARNING: Health check returned None")
        except RuntimeError as e:
            if "different task" in str(e):
                print(f"[Test] FAILED: Got the 'different task' error: {e}")
                return False
            raise

        # Test 3: Make a third MCP call (get_database_stats)
        print("\n[Test] Making third MCP call (get_database_stats)...")
        try:
            stats = app._run_async(app.mcp_client.get_database_stats(app.access_token))
            if stats:
                print(f"[Test] PASSED: Third MCP call successful - Users: {stats.get('total_users', 0)}")
            else:
                print("[Test] WARNING: Database stats returned None")
        except RuntimeError as e:
            if "different task" in str(e):
                print(f"[Test] FAILED: Got the 'different task' error: {e}")
                return False
            raise

        # Test 4: Make a fourth MCP call (list_users)
        print("\n[Test] Making fourth MCP call (list_users)...")
        try:
            users = app._run_async(app.mcp_client.list_users(app.access_token))
            if users:
                user_count = len(users.get('users', []))
                print(f"[Test] PASSED: Fourth MCP call successful - Listed {user_count} users")
            else:
                print("[Test] WARNING: List users returned None")
        except RuntimeError as e:
            if "different task" in str(e):
                print(f"[Test] FAILED: Got the 'different task' error: {e}")
                return False
            raise

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED!")
        print("The MCP client can now make multiple async calls without errors.")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[Test] FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        app.cleanup()


if __name__ == "__main__":
    success = test_mcp_client_multiple_calls()
    sys.exit(0 if success else 1)
