"""
Test script to verify audit logging fixes.

This script tests that all audit logging method calls match their signatures.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audit_logger import AuditLogger, AuditOutcome

def test_audit_logging():
    """Test all audit logging methods with the parameters used in the MCP server."""
    print("Testing audit logging method signatures...")

    # Create temporary audit logger
    logger = AuditLogger(log_dir="./test_audit_logs", redact_pii=False)

    # Test log_registration (as called in MCP server)
    print("1. Testing log_registration...")
    try:
        logger.log_registration(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            user_name="Test User",
            user_id="user_123",
            biometric_data={
                "detection_score": 0.95,
                "landmark_quality": 0.88,
                "face_size_ratio": 0.35,
                "num_faces_detected": 1
            }
        )
        print("   [OK] log_registration works correctly")
    except Exception as e:
        print(f"   [FAIL] log_registration failed: {e}")
        return False

    # Test log_recognition (as called in MCP server)
    print("2. Testing log_recognition...")
    try:
        logger.log_recognition(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            user_id="user_123",
            user_name="Test User",
            confidence_score=0.92,
            threshold=0.25,
            biometric_data={
                "distance": 0.18,
                "detection_score": 0.95,
                "landmark_quality": 0.88
            }
        )
        print("   [OK] log_recognition works correctly")
    except Exception as e:
        print(f"   [FAIL] log_recognition failed: {e}")
        return False

    # Test log_deletion (as called in MCP server)
    print("3. Testing log_deletion...")
    try:
        logger.log_deletion(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            user_id="user_123",
            user_name="Test User"
        )
        print("   [OK] log_deletion works correctly")
    except Exception as e:
        print(f"   [FAIL] log_deletion failed: {e}")
        return False

    # Test log_profile_access (as called in MCP server)
    print("4. Testing log_profile_access...")
    try:
        logger.log_profile_access(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            user_id="user_123",
            user_name="Test User"
        )
        print("   [OK] log_profile_access works correctly")
    except Exception as e:
        print(f"   [FAIL] log_profile_access failed: {e}")
        return False

    # Test log_profile_access with additional_info (list_users call)
    print("5. Testing log_profile_access with additional_info...")
    try:
        logger.log_profile_access(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            additional_info={
                "total_users": 10,
                "returned_count": 5,
                "offset": 0,
                "limit": 20
            }
        )
        print("   [OK] log_profile_access with additional_info works correctly")
    except Exception as e:
        print(f"   [FAIL] log_profile_access with additional_info failed: {e}")
        return False

    # Test log_user_update (as called in MCP server)
    print("6. Testing log_user_update...")
    try:
        logger.log_user_update(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            user_id="user_123",
            user_name="Test User",
            changes={"name": "New Name", "metadata": {"department": "Engineering"}}
        )
        print("   [OK] log_user_update works correctly")
    except Exception as e:
        print(f"   [FAIL] log_user_update failed: {e}")
        return False

    # Test log_database_operation (as called in MCP server)
    print("7. Testing log_database_operation...")
    try:
        logger.log_database_operation(
            client_id="test_client",
            outcome=AuditOutcome.SUCCESS,
            operation_type="get_stats",
            additional_info={
                "total_users": 10,
                "total_recognitions": 50
            }
        )
        print("   [OK] log_database_operation works correctly")
    except Exception as e:
        print(f"   [FAIL] log_database_operation failed: {e}")
        return False

    # Test log_health_event (as called in MCP server)
    print("8. Testing log_health_event...")
    try:
        from audit_logger import AuditEventType
        logger.log_health_event(
            event_type=AuditEventType.HEALTH_CHECK,
            component="system",
            status="healthy",
            message="Health status query executed",
            client_id="test_client",
            details={
                "components_healthy": 3,
                "degraded_mode": False
            }
        )
        print("   [OK] log_health_event works correctly")
    except Exception as e:
        print(f"   [FAIL] log_health_event failed: {e}")
        return False

    print("\n[OK] All audit logging tests passed!")
    return True

if __name__ == "__main__":
    success = test_audit_logging()

    # Clean up test logs
    import shutil
    test_log_dir = Path("./test_audit_logs")
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)
        print("\nCleaned up test audit logs")

    sys.exit(0 if success else 1)
