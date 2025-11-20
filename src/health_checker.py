"""
Health Check System for Skyy Facial Recognition MCP Server

Monitors health of critical components and manages degraded mode operations.
Enables dynamic capability advertisement based on actual system health.
"""

from enum import Enum
from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status for system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ComponentType(str, Enum):
    """Types of monitored components."""
    INSIGHTFACE = "insightface"
    CHROMADB = "chromadb"
    OAUTH = "oauth"


@dataclass
class ComponentHealth:
    """Health information for a component."""
    component: ComponentType
    status: HealthStatus
    message: str
    last_checked: datetime = field(default_factory=datetime.now)
    error: Optional[Exception] = None


@dataclass
class QueuedRegistration:
    """Queued user registration for degraded mode."""
    name: str
    image_data: str
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class HealthChecker:
    """
    Monitors health of critical MCP server components.

    Tracks health state of:
    - InsightFace model (required for face recognition)
    - ChromaDB (required for database operations, supports degraded mode)
    - OAuth system (required for authentication)

    Features:
    - Health state monitoring and transitions
    - Degraded mode support (queue registrations when ChromaDB unavailable)
    - Callback system for health state changes
    - Capability-based tool availability
    """

    def __init__(self):
        """Initialize health checker with all components unavailable."""
        self.health_states: Dict[ComponentType, ComponentHealth] = {
            ComponentType.INSIGHTFACE: ComponentHealth(
                component=ComponentType.INSIGHTFACE,
                status=HealthStatus.UNAVAILABLE,
                message="Not initialized"
            ),
            ComponentType.CHROMADB: ComponentHealth(
                component=ComponentType.CHROMADB,
                status=HealthStatus.UNAVAILABLE,
                message="Not initialized"
            ),
            ComponentType.OAUTH: ComponentHealth(
                component=ComponentType.OAUTH,
                status=HealthStatus.UNAVAILABLE,
                message="Not initialized"
            )
        }

        # Degraded mode: queue for pending registrations when ChromaDB unavailable
        self.registration_queue: List[QueuedRegistration] = []

        # Callbacks for health state changes
        self.state_change_callbacks: List[Callable[[ComponentType, HealthStatus, HealthStatus], None]] = []

    def register_state_change_callback(self, callback: Callable[[ComponentType, HealthStatus, HealthStatus], None]):
        """
        Register a callback to be called when component health changes.

        Callback signature: (component, old_status, new_status) -> None
        """
        self.state_change_callbacks.append(callback)

    def _notify_state_change(self, component: ComponentType, old_status: HealthStatus, new_status: HealthStatus):
        """Notify all registered callbacks of a health state change."""
        if old_status != new_status:
            logger.info(f"Health state change: {component.value} {old_status.value} -> {new_status.value}")
            for callback in self.state_change_callbacks:
                try:
                    callback(component, old_status, new_status)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")

    def update_health(self, component: ComponentType, status: HealthStatus, message: str, error: Optional[Exception] = None):
        """Update health status for a component."""
        old_status = self.health_states[component].status

        self.health_states[component] = ComponentHealth(
            component=component,
            status=status,
            message=message,
            error=error
        )

        self._notify_state_change(component, old_status, status)

    def get_health(self, component: ComponentType) -> ComponentHealth:
        """Get current health status for a component."""
        return self.health_states[component]

    def is_healthy(self, component: ComponentType) -> bool:
        """Check if a component is healthy."""
        return self.health_states[component].status == HealthStatus.HEALTHY

    def is_available(self, component: ComponentType) -> bool:
        """Check if a component is available (healthy or degraded)."""
        return self.health_states[component].status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    async def check_insightface(self, face_app_initializer: Callable) -> bool:
        """
        Check InsightFace model health.

        Args:
            face_app_initializer: Function to initialize face app

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Attempt to initialize InsightFace
            face_app = face_app_initializer()

            if face_app is None:
                self.update_health(
                    ComponentType.INSIGHTFACE,
                    HealthStatus.UNAVAILABLE,
                    "Failed to initialize InsightFace model"
                )
                return False

            # Model loaded successfully
            self.update_health(
                ComponentType.INSIGHTFACE,
                HealthStatus.HEALTHY,
                "InsightFace model loaded successfully"
            )
            return True

        except Exception as e:
            self.update_health(
                ComponentType.INSIGHTFACE,
                HealthStatus.UNAVAILABLE,
                f"InsightFace initialization failed: {str(e)}",
                error=e
            )
            logger.error(f"InsightFace health check failed: {e}")
            return False

    async def check_chromadb(self, chroma_initializer: Callable) -> bool:
        """
        Check ChromaDB health.

        Args:
            chroma_initializer: Function to initialize ChromaDB

        Returns:
            True if healthy or degraded, False if unavailable
        """
        try:
            # Attempt to initialize ChromaDB
            collection = chroma_initializer()

            if collection is None:
                # Enter degraded mode
                self.update_health(
                    ComponentType.CHROMADB,
                    HealthStatus.DEGRADED,
                    "ChromaDB unavailable - operating in degraded mode (queuing registrations)"
                )
                return False

            # Test basic operations
            collection.count()

            # Check if we have queued registrations to process
            if self.registration_queue:
                # Recovery from degraded mode
                queue_size = len(self.registration_queue)
                self.update_health(
                    ComponentType.CHROMADB,
                    HealthStatus.HEALTHY,
                    f"ChromaDB recovered - {queue_size} queued registrations ready to process"
                )
            else:
                self.update_health(
                    ComponentType.CHROMADB,
                    HealthStatus.HEALTHY,
                    "ChromaDB operational"
                )
            return True

        except Exception as e:
            # Enter degraded mode
            self.update_health(
                ComponentType.CHROMADB,
                HealthStatus.DEGRADED,
                f"ChromaDB error - operating in degraded mode: {str(e)}",
                error=e
            )
            logger.warning(f"ChromaDB health check failed, entering degraded mode: {e}")
            return False

    async def check_oauth(self, oauth_config) -> bool:
        """
        Check OAuth system health.

        Args:
            oauth_config: OAuth configuration object

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Verify OAuth data directory and keys exist
            oauth_data_dir = Path("oauth_data")
            private_key_path = oauth_data_dir / "private_key.pem"
            public_key_path = oauth_data_dir / "public_key.pem"

            if not oauth_data_dir.exists():
                self.update_health(
                    ComponentType.OAUTH,
                    HealthStatus.UNAVAILABLE,
                    "OAuth data directory not found"
                )
                return False

            if not private_key_path.exists() or not public_key_path.exists():
                self.update_health(
                    ComponentType.OAUTH,
                    HealthStatus.UNAVAILABLE,
                    "OAuth keys not found"
                )
                return False

            # Verify oauth_config is accessible
            if oauth_config is None:
                self.update_health(
                    ComponentType.OAUTH,
                    HealthStatus.UNAVAILABLE,
                    "OAuth config not initialized"
                )
                return False

            self.update_health(
                ComponentType.OAUTH,
                HealthStatus.HEALTHY,
                "OAuth system operational"
            )
            return True

        except Exception as e:
            self.update_health(
                ComponentType.OAUTH,
                HealthStatus.UNAVAILABLE,
                f"OAuth health check failed: {str(e)}",
                error=e
            )
            logger.error(f"OAuth health check failed: {e}")
            return False

    def queue_registration(self, name: str, image_data: str, metadata: Dict[str, Any]):
        """Queue a user registration when ChromaDB is unavailable."""
        queued = QueuedRegistration(
            name=name,
            image_data=image_data,
            metadata=metadata
        )
        self.registration_queue.append(queued)
        logger.info(f"Queued registration for {name} (queue size: {len(self.registration_queue)})")

    def get_queued_registrations(self) -> List[QueuedRegistration]:
        """Get all queued registrations."""
        return self.registration_queue.copy()

    def clear_registration_queue(self):
        """Clear the registration queue after processing."""
        count = len(self.registration_queue)
        self.registration_queue.clear()
        logger.info(f"Cleared {count} registrations from queue")

    def get_available_capabilities(self) -> Dict[str, bool]:
        """
        Get dictionary of available capabilities based on health state.

        Returns:
            Dictionary mapping capability names to availability
        """
        insightface_healthy = self.is_healthy(ComponentType.INSIGHTFACE)
        chromadb_available = self.is_available(ComponentType.CHROMADB)
        chromadb_healthy = self.is_healthy(ComponentType.CHROMADB)

        return {
            "register_user": insightface_healthy and chromadb_available,
            "recognize_face": insightface_healthy and chromadb_healthy,
            "get_user_profile": chromadb_healthy,
            "list_users": chromadb_healthy,
            "delete_user": chromadb_healthy,
            "get_database_stats": chromadb_healthy,
            "search_similar_faces": insightface_healthy and chromadb_healthy,
            # Degraded mode: can queue registrations even if ChromaDB degraded
            "queue_registration": insightface_healthy and not chromadb_healthy
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        capabilities = self.get_available_capabilities()

        return {
            "overall_status": self._calculate_overall_status(),
            "components": {
                comp.value: {
                    "status": health.status.value,
                    "message": health.message,
                    "last_checked": health.last_checked.isoformat(),
                    "error": str(health.error) if health.error else None
                }
                for comp, health in self.health_states.items()
            },
            "capabilities": capabilities,
            "degraded_mode": {
                "active": not self.is_healthy(ComponentType.CHROMADB),
                "queued_registrations": len(self.registration_queue)
            }
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall system health status."""
        statuses = [health.status for health in self.health_states.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return "healthy"
        elif any(s == HealthStatus.UNAVAILABLE for s in statuses):
            # Critical component unavailable
            return "degraded"
        else:
            return "degraded"


# Global health checker instance
health_checker = HealthChecker()
