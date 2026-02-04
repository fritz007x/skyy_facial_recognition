"""
Synchronous MCP Facade - Clean synchronous interface over async MCP client.

Provides a synchronous wrapper around the async SkyyMCPClient, eliminating
the need for _run_async() hacks in application code.

Follows the Facade and Adapter patterns from Clean Architecture.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Any, Dict

from .mcp_client import SkyyMCPClient


class SyncMCPFacade:
    """
    Synchronous facade over the async SkyyMCPClient.

    This class provides a clean synchronous interface for applications that
    don't want to deal with async/await complexity. It manages a persistent
    event loop internally to maintain the MCP client's AsyncExitStack context.

    Design Decisions:
    - Persistent Event Loop: Single event loop maintained throughout lifecycle
    - Context Manager Protocol: Supports with-statement for resource management
    - Zero Breaking Changes: Drop-in replacement for current _run_async() pattern
    - Thread Safety: Single event loop per instance (not thread-safe across threads)

    Usage:
        # As context manager (recommended)
        with SyncMCPFacade(python_path, server_script) as mcp:
            result = mcp.recognize_face(token, image_data)

        # Manual lifecycle
        mcp = SyncMCPFacade(python_path, server_script)
        mcp.connect()
        result = mcp.recognize_face(token, image_data)
        mcp.disconnect()
    """

    def __init__(self, python_path: Path, server_script: Path):
        """
        Initialize synchronous MCP facade.

        Args:
            python_path: Path to Python interpreter in virtual environment
            server_script: Path to MCP server script
        """
        self.python_path = Path(python_path)
        self.server_script = Path(server_script)

        # Async client (will be initialized in connect())
        self._client: Optional[SkyyMCPClient] = None

        # Persistent event loop for async operations
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # Connection state
        self._connected = False

        # Event loop health tracking
        self._last_health_check = 0.0
        self._health_check_interval = 60.0  # Check every 60 seconds

    def _ensure_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Ensure a persistent event loop exists.

        Returns:
            The event loop instance
        """
        if self._event_loop is None or self._event_loop.is_closed():
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def _ensure_event_loop_health(self) -> bool:
        """
        Verify event loop is healthy and responsive.

        Checks for:
        - Event loop exists and is not closed
        - Excessive pending tasks (potential memory leak)
        - Cleans up completed tasks

        Returns:
            True if event loop is healthy, False otherwise
        """
        if self._event_loop is None or self._event_loop.is_closed():
            print("[SyncMCPFacade] Event loop is closed or missing", flush=True)
            return False

        current_time = time.time()
        if current_time - self._last_health_check > self._health_check_interval:
            # Check for excessive pending tasks
            try:
                pending = asyncio.all_tasks(self._event_loop)
                pending_count = len(pending)

                if pending_count > 10:  # Threshold for unhealthy state
                    print(f"[SyncMCPFacade] WARNING: {pending_count} pending tasks in event loop", flush=True)

                # Clean up completed tasks to prevent accumulation
                completed_count = 0
                for task in pending:
                    if task.done():
                        try:
                            task.result()  # Retrieve exception if any
                            completed_count += 1
                        except Exception as e:
                            print(f"[SyncMCPFacade] Cleaned up task error: {e}", flush=True)

                if completed_count > 0:
                    print(f"[SyncMCPFacade] Cleaned up {completed_count} completed tasks", flush=True)

                self._last_health_check = current_time

            except Exception as e:
                print(f"[SyncMCPFacade] Event loop health check failed: {e}", flush=True)
                return False

        return True

    def _run_async(self, coro, timeout: float = 30.0):
        """
        Execute an async coroutine synchronously with timeout protection.

        This is the only place where async/await complexity is handled.
        Includes health checking and timeout protection to prevent indefinite blocks.

        Args:
            coro: Async coroutine to execute
            timeout: Maximum time in seconds to wait (default 30.0)

        Returns:
            Result of the coroutine

        Raises:
            RuntimeError: If event loop is unhealthy or operation times out
        """
        loop = self._ensure_event_loop()

        # Health check before execution
        if not self._ensure_event_loop_health():
            raise RuntimeError("Event loop in unhealthy state")

        # Add timeout protection
        try:
            async def run_with_timeout():
                return await asyncio.wait_for(coro, timeout=timeout)

            return loop.run_until_complete(run_with_timeout())
        except asyncio.TimeoutError:
            print(f"[SyncMCPFacade] Operation timed out after {timeout}s", flush=True)
            raise RuntimeError(f"MCP operation timed out after {timeout}s")

    def connect(self) -> bool:
        """
        Establish connection to MCP server.

        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            print("[SyncMCPFacade] Already connected.", flush=True)
            return True

        print("[SyncMCPFacade] Connecting to MCP server...", flush=True)

        # Create async client
        self._client = SkyyMCPClient(
            python_path=self.python_path,
            server_script=self.server_script
        )

        # Connect using persistent event loop
        success = self._run_async(self._client.connect())

        if success:
            self._connected = True
            print("[SyncMCPFacade] Connected successfully.", flush=True)
        else:
            print("[SyncMCPFacade] Connection failed.", flush=True)

        return success

    def disconnect(self) -> None:
        """
        Close MCP connection and cleanup resources.
        """
        if not self._connected:
            return

        print("[SyncMCPFacade] Disconnecting...", flush=True)

        try:
            if self._client:
                self._run_async(self._client.disconnect())
        except RuntimeError as e:
            # Suppress "different task" errors during cleanup
            if "different task" not in str(e):
                raise
            print(f"[SyncMCPFacade] Disconnect warning: {e}", flush=True)

        # Close event loop
        if self._event_loop is not None and not self._event_loop.is_closed():
            try:
                # Cancel any pending tasks
                pending = asyncio.all_tasks(self._event_loop)
                for task in pending:
                    task.cancel()

                # Stop and close the loop
                if self._event_loop.is_running():
                    self._event_loop.stop()

                self._event_loop.close()
                print("[SyncMCPFacade] Event loop closed.", flush=True)
            except Exception as e:
                print(f"[SyncMCPFacade] Error closing event loop: {e}", flush=True)
            finally:
                self._event_loop = None

        self._connected = False
        print("[SyncMCPFacade] Disconnected.", flush=True)

    # =========================================================================
    # Context Manager Protocol
    # =========================================================================

    def __enter__(self):
        """Context manager entry - connect to MCP server."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect from MCP server."""
        self.disconnect()
        return False  # Don't suppress exceptions

    # =========================================================================
    # MCP Tool Methods (Synchronous Interface)
    # =========================================================================

    def _ensure_connected(self) -> None:
        """Verify connection is established before calling tools."""
        if not self._connected or self._client is None:
            raise RuntimeError(
                "SyncMCPFacade not connected. Call connect() first or use context manager."
            )

    def recognize_face(
        self,
        access_token: str,
        image_data: str,
        confidence_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """
        Recognize a face from an image (synchronous).

        Args:
            access_token: OAuth 2.1 access token
            image_data: Base64-encoded image data
            confidence_threshold: Maximum distance for recognition (0.0-1.0)

        Returns:
            Recognition result dictionary
        """
        self._ensure_connected()
        return self._run_async(
            self._client.recognize_face(access_token, image_data, confidence_threshold)
        )

    def register_user(
        self,
        access_token: str,
        name: str,
        image_data: str,
        metadata: Optional[Dict[str, Any]] = None,
        allow_update: bool = False
    ) -> Dict[str, Any]:
        """
        Register a new user (synchronous).

        Args:
            access_token: OAuth 2.1 access token
            name: User's full name
            image_data: Base64-encoded face image
            metadata: Optional user metadata
            allow_update: If True, update existing user instead of returning duplicate error (demo mode)

        Returns:
            Registration result dictionary
        """
        self._ensure_connected()
        return self._run_async(
            self._client.register_user(access_token, name, image_data, metadata, allow_update)
        )

    def get_user_profile(
        self,
        access_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user profile (synchronous).

        Args:
            access_token: OAuth 2.1 access token
            user_id: User's unique identifier

        Returns:
            User profile dictionary
        """
        self._ensure_connected()
        return self._run_async(
            self._client.get_user_profile(access_token, user_id)
        )

    def list_users(
        self,
        access_token: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List registered users (synchronous).

        Args:
            access_token: OAuth 2.1 access token
            limit: Maximum users to return
            offset: Number of users to skip

        Returns:
            List of users with pagination info
        """
        self._ensure_connected()
        return self._run_async(
            self._client.list_users(access_token, limit, offset)
        )

    def update_user(
        self,
        access_token: str,
        user_id: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update user information (synchronous).

        Args:
            access_token: OAuth 2.1 access token
            user_id: User's unique identifier
            name: Optional new name
            metadata: Optional new metadata

        Returns:
            Updated user data
        """
        self._ensure_connected()
        return self._run_async(
            self._client.update_user(access_token, user_id, name, metadata)
        )

    def delete_user(
        self,
        access_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Delete a user (synchronous).

        Args:
            access_token: OAuth 2.1 access token
            user_id: User's unique identifier

        Returns:
            Deletion confirmation
        """
        self._ensure_connected()
        return self._run_async(
            self._client.delete_user(access_token, user_id)
        )

    def get_database_stats(self, access_token: str) -> Dict[str, Any]:
        """
        Get database statistics (synchronous).

        Args:
            access_token: OAuth 2.1 access token

        Returns:
            Database statistics
        """
        self._ensure_connected()
        return self._run_async(
            self._client.get_database_stats(access_token)
        )

    def get_health_status(self, access_token: str) -> Dict[str, Any]:
        """
        Get system health status (synchronous).

        Args:
            access_token: OAuth 2.1 access token

        Returns:
            Health status dictionary
        """
        self._ensure_connected()
        return self._run_async(
            self._client.get_health_status(access_token)
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "connected" if self._connected else "disconnected"
        return f"SyncMCPFacade(status={status}, server={self.server_script.name})"
