"""
Security Audit Logger for Facial Recognition MCP Server

Provides comprehensive audit logging for all biometric operations to meet
security and compliance requirements. Uses loguru for structured logging
with automatic rotation and retention policies.

Compliance Features:
- Tamper-evident logging (append-only)
- Structured data format (JSON)
- Automatic log rotation and retention
- PII handling with configurable redaction
- Security event tracking
- Performance monitoring
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from loguru import logger
import sys


class AuditEventType(str, Enum):
    """Types of auditable events in the system."""
    # Biometric Operations
    REGISTRATION = "registration"
    RECOGNITION = "recognition"
    DELETION = "deletion"
    PROFILE_ACCESS = "profile_access"
    USER_UPDATE = "user_update"
    BATCH_ENROLLMENT = "batch_enrollment"

    # Database Operations
    DATABASE_QUERY = "database_query"
    DATABASE_STATS = "database_stats"

    # Security Events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    # System Events
    HEALTH_CHECK = "health_check"
    HEALTH_STATE_CHANGE = "health_state_change"
    DEGRADED_MODE_ENTER = "degraded_mode_enter"
    DEGRADED_MODE_EXIT = "degraded_mode_exit"

    # Administrative Events
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"
    CONFIG_CHANGE = "config_change"


class AuditOutcome(str, Enum):
    """Outcome of an auditable operation."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    QUEUED = "queued"
    DENIED = "denied"
    ERROR = "error"


class AuditLogger:
    """
    Security audit logger for biometric operations.

    Features:
    - Structured JSON logging
    - Automatic log rotation (daily, 30-day retention)
    - Separate audit and debug logs
    - PII redaction options
    - Tamper-evident design (append-only)
    """

    def __init__(self, log_dir: str = "./audit_logs", redact_pii: bool = False):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
            redact_pii: If True, hash user identifiers and redact sensitive data
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.redact_pii = redact_pii

        # Configure loguru
        self._configure_loguru()

    def _configure_loguru(self):
        """Configure loguru with separate audit and debug logs."""
        # Remove default handler
        logger.remove()

        # Console output (INFO and above, colored)
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )

        # Audit log (JSON format, daily rotation, 30-day retention)
        audit_log_path = self.log_dir / "audit_{time:YYYY-MM-DD}.log"
        logger.add(
            str(audit_log_path),
            format="{message}",  # Raw JSON
            level="INFO",
            rotation="00:00",  # Rotate daily at midnight
            retention="30 days",  # Keep 30 days of logs
            compression="zip",  # Compress rotated logs
            serialize=True,  # Output as JSON
            enqueue=True,  # Thread-safe
            filter=lambda record: record["extra"].get("audit") is True
        )

        # Debug log (detailed, hourly rotation, 7-day retention)
        debug_log_path = self.log_dir / "debug_{time:YYYY-MM-DD}.log"
        logger.add(
            str(debug_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 hour",
            retention="7 days",
            compression="zip",
            enqueue=True,
            filter=lambda record: record["extra"].get("audit") is not True
        )

    def _hash_identifier(self, identifier: str) -> str:
        """Hash an identifier for PII protection."""
        if not self.redact_pii:
            return identifier
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _redact_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive fields from metadata."""
        if not self.redact_pii or not metadata:
            return metadata

        # Fields to redact
        sensitive_fields = ['email', 'phone', 'ssn', 'employee_id', 'address']

        redacted = metadata.copy()
        for field in sensitive_fields:
            if field in redacted:
                redacted[field] = "[REDACTED]"

        return redacted

    def log_audit_event(
        self,
        event_type: AuditEventType,
        outcome: AuditOutcome,
        details: Dict[str, Any],
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Log a security audit event.

        Args:
            event_type: Type of event being logged
            outcome: Outcome of the operation
            details: Additional event-specific details
            client_id: OAuth client that initiated the operation
            user_id: User identifier involved in the operation
            error_message: Error message if outcome is failure/error
        """
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "outcome": outcome.value,
            "client_id": self._hash_identifier(client_id) if client_id else None,
            "user_id": self._hash_identifier(user_id) if user_id else None,
            "details": self._redact_metadata(details),
            "error": error_message
        }

        # Log with audit flag
        logger.bind(audit=True).info(json.dumps(audit_record))

    def log_registration(
        self,
        user_id: str,
        name: str,
        client_id: str,
        outcome: AuditOutcome,
        detection_score: Optional[float] = None,
        face_quality: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Log a user registration event."""
        details = {
            "operation": "register_user",
            "name": name if not self.redact_pii else "[REDACTED]",
            "detection_score": detection_score,
            "face_quality": face_quality,
            "metadata": metadata
        }

        self.log_audit_event(
            event_type=AuditEventType.REGISTRATION,
            outcome=outcome,
            details=details,
            client_id=client_id,
            user_id=user_id,
            error_message=error
        )

    def log_recognition(
        self,
        client_id: str,
        outcome: AuditOutcome,
        recognized_user_id: Optional[str] = None,
        confidence: Optional[float] = None,
        distance: Optional[float] = None,
        threshold: Optional[float] = None,
        num_faces_detected: int = 1,
        error: Optional[str] = None
    ):
        """Log a face recognition attempt."""
        details = {
            "operation": "recognize_face",
            "confidence": confidence,
            "distance": distance,
            "threshold": threshold,
            "num_faces_detected": num_faces_detected,
            "recognition_status": "recognized" if recognized_user_id else "not_recognized"
        }

        self.log_audit_event(
            event_type=AuditEventType.RECOGNITION,
            outcome=outcome,
            details=details,
            client_id=client_id,
            user_id=recognized_user_id,
            error_message=error
        )

    def log_deletion(
        self,
        user_id: str,
        client_id: str,
        outcome: AuditOutcome,
        name: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log a user deletion event."""
        details = {
            "operation": "delete_user",
            "name": name if not self.redact_pii else "[REDACTED]"
        }

        self.log_audit_event(
            event_type=AuditEventType.DELETION,
            outcome=outcome,
            details=details,
            client_id=client_id,
            user_id=user_id,
            error_message=error
        )

    def log_profile_access(
        self,
        user_id: str,
        client_id: str,
        outcome: AuditOutcome,
        operation: str = "get_profile",
        error: Optional[str] = None
    ):
        """Log a user profile access event."""
        details = {
            "operation": operation
        }

        self.log_audit_event(
            event_type=AuditEventType.PROFILE_ACCESS,
            outcome=outcome,
            details=details,
            client_id=client_id,
            user_id=user_id,
            error_message=error
        )

    def log_user_update(
        self,
        user_id: str,
        client_id: str,
        outcome: AuditOutcome,
        updated_fields: list,
        error: Optional[str] = None
    ):
        """Log a user profile update event."""
        details = {
            "operation": "update_user",
            "updated_fields": updated_fields
        }

        self.log_audit_event(
            event_type=AuditEventType.USER_UPDATE,
            outcome=outcome,
            details=details,
            client_id=client_id,
            user_id=user_id,
            error_message=error
        )

    def log_database_operation(
        self,
        operation: str,
        client_id: str,
        outcome: AuditOutcome,
        record_count: Optional[int] = None,
        query_params: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Log a database operation."""
        details = {
            "operation": operation,
            "record_count": record_count,
            "query_params": query_params
        }

        self.log_audit_event(
            event_type=AuditEventType.DATABASE_QUERY,
            outcome=outcome,
            details=details,
            client_id=client_id,
            error_message=error
        )

    def log_auth_event(
        self,
        client_id: str,
        outcome: AuditOutcome,
        operation: str,
        reason: Optional[str] = None
    ):
        """Log an authentication event."""
        event_type = AuditEventType.AUTH_SUCCESS if outcome == AuditOutcome.SUCCESS else AuditEventType.AUTH_FAILURE

        details = {
            "operation": operation,
            "reason": reason
        }

        self.log_audit_event(
            event_type=event_type,
            outcome=outcome,
            details=details,
            client_id=client_id,
            error_message=reason if outcome != AuditOutcome.SUCCESS else None
        )

    def log_health_event(
        self,
        event_type: AuditEventType,
        component: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a health check or state change event."""
        event_details = {
            "component": component,
            "status": status,
            "message": message
        }

        if details:
            event_details.update(details)

        outcome = AuditOutcome.SUCCESS if status == "healthy" else AuditOutcome.FAILURE

        self.log_audit_event(
            event_type=event_type,
            outcome=outcome,
            details=event_details
        )

    def log_batch_enrollment(
        self,
        client_id: str,
        total_images: int,
        success_count: int,
        fail_count: int,
        skip_count: int,
        queued_count: int,
        duration_seconds: float
    ):
        """Log a batch enrollment operation."""
        details = {
            "operation": "batch_enrollment",
            "total_images": total_images,
            "success_count": success_count,
            "fail_count": fail_count,
            "skip_count": skip_count,
            "queued_count": queued_count,
            "duration_seconds": duration_seconds,
            "images_per_second": total_images / duration_seconds if duration_seconds > 0 else 0
        }

        outcome = AuditOutcome.SUCCESS if fail_count == 0 else AuditOutcome.PARTIAL

        self.log_audit_event(
            event_type=AuditEventType.BATCH_ENROLLMENT,
            outcome=outcome,
            details=details,
            client_id=client_id
        )

    def log_server_start(self, health_status: Dict[str, Any]):
        """Log server startup event."""
        details = {
            "operation": "server_start",
            "health_status": health_status
        }

        self.log_audit_event(
            event_type=AuditEventType.SERVER_START,
            outcome=AuditOutcome.SUCCESS,
            details=details
        )

    def debug(self, message: str, **kwargs):
        """Log a debug message (not included in audit logs)."""
        logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message (not included in audit logs)."""
        logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message (not included in audit logs)."""
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message (not included in audit logs)."""
        logger.error(message, **kwargs)


# Global audit logger instance
audit_logger = AuditLogger(redact_pii=False)  # Set to True for production PII redaction


def configure_audit_logging(log_dir: str = "./audit_logs", redact_pii: bool = False):
    """
    Configure the global audit logger.

    Args:
        log_dir: Directory for audit log files
        redact_pii: If True, enable PII redaction
    """
    global audit_logger
    audit_logger = AuditLogger(log_dir=log_dir, redact_pii=redact_pii)
