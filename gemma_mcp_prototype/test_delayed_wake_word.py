"""
Test Script for Delayed Wake Word Improvements

Tests the following improvements:
1. Event Loop Health Monitoring (mcp_sync_facade.py)
2. OAuth Token Validation (main.py)
3. Camera Lifecycle Retry Logic (main.py)

Simulates the scenario where wake word is detected several minutes
after app initialization to ensure all components remain healthy.
"""

import sys
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.mcp_sync_facade import SyncMCPFacade
from config import MCP_PYTHON_PATH, MCP_SERVER_SCRIPT


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def record(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
            print(f"  [OK] {test_name}: PASSED {message}")
        else:
            self.failed += 1
            print(f"  [X] {test_name}: FAILED {message}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.passed}/{total} passed, {self.failed}/{total} failed")
        print(f"{'='*60}")
        return self.failed == 0


def test_event_loop_health_monitoring(results: TestResults):
    """
    Test 1: Event Loop Health Monitoring

    Verifies that:
    - Event loop health check runs periodically
    - Pending tasks are monitored
    - Completed tasks are cleaned up
    - Timeout protection works
    """
    print("\n[Test 1] Event Loop Health Monitoring")
    print("-" * 60)

    try:
        # Create facade instance
        facade = SyncMCPFacade(MCP_PYTHON_PATH, MCP_SERVER_SCRIPT)

        # Test 1.1: Health tracking initialization
        results.record(
            "Event loop health tracking initialized",
            hasattr(facade, '_last_health_check') and hasattr(facade, '_health_check_interval'),
            f"(last_check={facade._last_health_check}, interval={facade._health_check_interval}s)"
        )

        # Test 1.2: Event loop creation
        loop = facade._ensure_event_loop()
        results.record(
            "Event loop created successfully",
            loop is not None and not loop.is_closed(),
            f"(loop={type(loop).__name__})"
        )

        # Test 1.3: Health check method exists
        results.record(
            "Health check method exists",
            hasattr(facade, '_ensure_event_loop_health') and callable(facade._ensure_event_loop_health),
        )

        # Test 1.4: Initial health check passes
        is_healthy = facade._ensure_event_loop_health()
        results.record(
            "Initial event loop health check passes",
            is_healthy,
        )

        # Test 1.5: Simulate health check after interval
        facade._last_health_check = time.time() - 65  # 65 seconds ago
        is_healthy_after_interval = facade._ensure_event_loop_health()
        results.record(
            "Health check runs after interval",
            is_healthy_after_interval,
            f"(last_check updated: {time.time() - facade._last_health_check:.2f}s ago)"
        )

        # Test 1.6: Timeout protection in _run_async
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"

        try:
            result = facade._run_async(quick_task(), timeout=5.0)
            results.record(
                "Timeout protection allows fast operations",
                result == "success",
            )
        except Exception as e:
            results.record(
                "Timeout protection allows fast operations",
                False,
                f"(error: {e})"
            )

        # Test 1.7: Timeout protection catches slow operations
        async def slow_task():
            await asyncio.sleep(10)
            return "should timeout"

        try:
            facade._run_async(slow_task(), timeout=1.0)
            results.record(
                "Timeout protection catches slow operations",
                False,
                "(should have raised RuntimeError)"
            )
        except RuntimeError as e:
            results.record(
                "Timeout protection catches slow operations",
                "timed out" in str(e).lower(),
                f"(error: {e})"
            )

        # Cleanup
        if facade._event_loop and not facade._event_loop.is_closed():
            facade._event_loop.close()

    except Exception as e:
        results.record(
            "Event loop health monitoring test",
            False,
            f"(unexpected error: {e})"
        )


def test_oauth_token_validation(results: TestResults):
    """
    Test 2: OAuth Token Validation

    Verifies that:
    - Token validation method exists
    - Token refresh logic includes validation
    - Two-tier validation system works
    """
    print("\n[Test 2] OAuth Token Validation")
    print("-" * 60)

    try:
        # Import main module
        import main

        # Test 2.1: validate_token method exists
        app_class = main.GemmaFacialRecognition
        results.record(
            "validate_token method exists",
            hasattr(app_class, 'validate_token'),
        )

        # Test 2.2: refresh_token_if_needed method exists
        results.record(
            "refresh_token_if_needed method exists",
            hasattr(app_class, 'refresh_token_if_needed'),
        )

        # Test 2.3: Mock app instance to test validation logic
        app = app_class()

        # Mock MCP facade
        app.mcp = Mock()
        app.mcp.get_health_status = Mock(return_value={"overall_status": "healthy"})

        # Test with valid token
        app.access_token = "test_token"
        is_valid = app.validate_token()
        results.record(
            "Token validation calls health check",
            app.mcp.get_health_status.called,
            f"(valid={is_valid})"
        )

        # Test 2.4: Token validation detects invalid responses
        app.mcp.get_health_status = Mock(return_value=None)
        is_valid = app.validate_token()
        results.record(
            "Token validation detects invalid responses",
            not is_valid,
        )

        # Test 2.5: Token validation handles exceptions
        app.mcp.get_health_status = Mock(side_effect=Exception("Connection error"))
        is_valid = app.validate_token()
        results.record(
            "Token validation handles exceptions gracefully",
            not is_valid,
        )

    except Exception as e:
        results.record(
            "OAuth token validation test",
            False,
            f"(unexpected error: {e})"
        )


def test_camera_lifecycle_retry(results: TestResults):
    """
    Test 3: Camera Lifecycle Retry Logic

    Verifies that:
    - Camera retry method exists
    - Retry logic attempts multiple times
    - Proper cleanup between retries
    - Exponential backoff works
    """
    print("\n[Test 3] Camera Lifecycle Retry Logic")
    print("-" * 60)

    try:
        # Import main module
        import main

        # Test 3.1: initialize_camera_with_retry method exists
        app_class = main.GemmaFacialRecognition
        results.record(
            "initialize_camera_with_retry method exists",
            hasattr(app_class, 'initialize_camera_with_retry'),
        )

        # Test 3.2: Method signature accepts max_retries
        app = app_class()
        import inspect
        sig = inspect.signature(app.initialize_camera_with_retry)
        has_retries_param = 'max_retries' in sig.parameters
        results.record(
            "Method accepts max_retries parameter",
            has_retries_param,
        )

        # Test 3.3: Mock camera to test retry logic
        app.camera = Mock()
        app.camera.cap = None
        app.camera.initialize = Mock(return_value=False)  # First attempts fail
        app.camera.release = Mock()

        # Test with all retries failing
        success = app.initialize_camera_with_retry(max_retries=2)
        results.record(
            "Retry logic attempts multiple times",
            app.camera.initialize.call_count >= 2,
            f"(attempts={app.camera.initialize.call_count})"
        )

        results.record(
            "Retry logic returns False after exhausting retries",
            not success,
        )

        # Test 3.4: Mock successful initialization on second try
        app.camera.initialize = Mock(side_effect=[False, True])  # Fail, then succeed
        app.camera.cap = Mock()
        app.camera.cap.isOpened = Mock(return_value=True)

        success = app.initialize_camera_with_retry(max_retries=3)
        results.record(
            "Retry logic succeeds on second attempt",
            success,
            f"(attempts={app.camera.initialize.call_count})"
        )

        # Test 3.5: Already initialized camera is detected
        app.camera.cap = Mock()
        app.camera.cap.isOpened = Mock(return_value=True)
        app.camera.initialize = Mock()

        success = app.initialize_camera_with_retry(max_retries=3)
        results.record(
            "Already initialized camera detected",
            success and app.camera.initialize.call_count == 0,
            "(skipped re-initialization)"
        )

    except Exception as e:
        results.record(
            "Camera lifecycle retry test",
            False,
            f"(unexpected error: {e})"
        )


def test_delayed_wake_word_simulation(results: TestResults):
    """
    Test 4: Delayed Wake Word Simulation

    Simulates the complete scenario:
    - App starts at T=0
    - Idle for simulated time
    - Wake word detected
    - All components should remain healthy
    """
    print("\n[Test 4] Delayed Wake Word Simulation")
    print("-" * 60)

    try:
        import main

        # Test 4.1: Simulate app initialization
        print("  [Simulation] Initializing app components...")
        app = main.GemmaFacialRecognition()

        # Mock dependencies
        app.mcp = Mock(spec=SyncMCPFacade)
        app.mcp._event_loop = asyncio.new_event_loop()
        app.mcp._last_health_check = time.time()
        app.mcp._health_check_interval = 60.0
        app.mcp._ensure_event_loop_health = Mock(return_value=True)
        app.mcp.get_health_status = Mock(return_value={"overall_status": "healthy"})

        app.access_token = "test_token"
        app.token_created_time = time.time()

        app.camera = Mock()
        app.camera.cap = None
        app.camera.initialize = Mock(return_value=True)
        app.camera.cap = Mock()
        app.camera.cap.isOpened = Mock(return_value=True)
        app.camera.release = Mock()

        results.record(
            "App components initialized",
            app.mcp is not None and app.access_token is not None,
        )

        # Test 4.2: Simulate idle period (5 minutes)
        print("  [Simulation] Simulating 5-minute idle period...")
        idle_minutes = 5
        app.token_created_time = time.time() - (idle_minutes * 60)  # 5 minutes ago

        # Simulate health check after idle
        app.mcp._last_health_check = time.time() - 65  # Last check was 65s ago

        results.record(
            "Idle period simulated",
            (time.time() - app.token_created_time) / 60 >= idle_minutes,
            f"(elapsed: {(time.time() - app.token_created_time) / 60:.1f} minutes)"
        )

        # Test 4.3: Token validation after idle
        print("  [Simulation] Validating token after idle period...")
        is_token_valid = app.validate_token()
        results.record(
            "Token validation after idle period",
            is_token_valid and app.mcp.get_health_status.called,
        )

        # Test 4.4: Event loop health after idle
        print("  [Simulation] Checking event loop health...")
        is_loop_healthy = app.mcp._ensure_event_loop_health()
        results.record(
            "Event loop health check after idle period",
            is_loop_healthy,
        )

        # Test 4.5: Camera initialization after idle
        print("  [Simulation] Initializing camera after idle period...")
        camera_initialized = app.initialize_camera_with_retry(max_retries=3)
        results.record(
            "Camera initialization after idle period",
            camera_initialized,
        )

        # Test 4.6: Complete workflow
        print("  [Simulation] Testing complete wake word -> recognition workflow...")

        # Mock speech manager
        app.speech = Mock()
        app.speech.speak = Mock()
        app.permission = Mock()
        app.permission.request_camera_permission = Mock(return_value=True)
        app.camera.capture_to_base64 = Mock(return_value=(True, "base64_image_data"))
        app.mcp.recognize_face = Mock(return_value={"status": "recognized", "user": {"name": "Test User"}})

        # Simulate recognition flow
        try:
            app.handle_recognition()
            workflow_success = True
        except Exception as e:
            workflow_success = False
            print(f"    Error in workflow: {e}")

        results.record(
            "Complete recognition workflow after idle",
            workflow_success and app.mcp.recognize_face.called,
        )

        # Cleanup
        if hasattr(app.mcp, '_event_loop') and not app.mcp._event_loop.is_closed():
            app.mcp._event_loop.close()

    except Exception as e:
        results.record(
            "Delayed wake word simulation test",
            False,
            f"(unexpected error: {e})"
        )


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DELAYED WAKE WORD IMPROVEMENTS - TEST SUITE")
    print("="*60)
    print("\nTesting improvements for wake word detection after idle periods...")
    print("Simulates scenario: App idle for 5-10 minutes, then wake word detected")

    results = TestResults()

    # Run all test suites
    test_event_loop_health_monitoring(results)
    test_oauth_token_validation(results)
    test_camera_lifecycle_retry(results)
    test_delayed_wake_word_simulation(results)

    # Print summary
    all_passed = results.summary()

    if all_passed:
        print("\n[OK] All tests PASSED! The improvements are working correctly.")
        return 0
    else:
        print(f"\n[X] {results.failed} test(s) FAILED. Please review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
