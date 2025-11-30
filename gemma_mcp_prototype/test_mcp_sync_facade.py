"""
Test suite for SyncMCPFacade.

Tests the synchronous facade over the async MCP client.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import asyncio

from modules.mcp_sync_facade import SyncMCPFacade


class TestSyncMCPFacade(unittest.TestCase):
    """Test SyncMCPFacade."""

    def setUp(self):
        """Set up test fixtures."""
        self.python_path = Path("/fake/python")
        self.server_script = Path("/fake/server.py")

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_initialization(self, mock_client_class):
        """Test facade initialization."""
        facade = SyncMCPFacade(self.python_path, self.server_script)

        self.assertEqual(facade.python_path, self.python_path)
        self.assertEqual(facade.server_script, self.server_script)
        self.assertFalse(facade._connected)
        self.assertIsNone(facade._event_loop)

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_connect_success(self, mock_client_class):
        """Test successful connection."""
        # Mock the async client
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        result = facade.connect()

        self.assertTrue(result)
        self.assertTrue(facade._connected)
        mock_client.connect.assert_called_once()

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_connect_failure(self, mock_client_class):
        """Test failed connection."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=False)
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        result = facade.connect()

        self.assertFalse(result)
        self.assertFalse(facade._connected)

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_disconnect(self, mock_client_class):
        """Test disconnection."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        facade.connect()
        facade.disconnect()

        self.assertFalse(facade._connected)
        mock_client.disconnect.assert_called_once()

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_context_manager(self, mock_client_class):
        """Test context manager protocol."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        with SyncMCPFacade(self.python_path, self.server_script) as facade:
            self.assertTrue(facade._connected)

        # After exiting context, should be disconnected
        self.assertFalse(facade._connected)

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_recognize_face(self, mock_client_class):
        """Test recognize_face method."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.recognize_face = AsyncMock(return_value={
            "status": "recognized",
            "user": {"name": "John Doe"}
        })
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        facade.connect()

        result = facade.recognize_face(
            access_token="test_token",
            image_data="base64data",
            confidence_threshold=0.25
        )

        self.assertEqual(result["status"], "recognized")
        self.assertEqual(result["user"]["name"], "John Doe")
        mock_client.recognize_face.assert_called_once()

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_register_user(self, mock_client_class):
        """Test register_user method."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.register_user = AsyncMock(return_value={
            "status": "success",
            "user": {"user_id": "12345"}
        })
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        facade.connect()

        result = facade.register_user(
            access_token="test_token",
            name="Jane Doe",
            image_data="base64data"
        )

        self.assertEqual(result["status"], "success")
        mock_client.register_user.assert_called_once()

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_ensure_connected_raises(self, mock_client_class):
        """Test that methods raise error when not connected."""
        facade = SyncMCPFacade(self.python_path, self.server_script)

        with self.assertRaises(RuntimeError) as context:
            facade.recognize_face("token", "data")

        self.assertIn("not connected", str(context.exception))

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_get_health_status(self, mock_client_class):
        """Test get_health_status method."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.get_health_status = AsyncMock(return_value={
            "overall_status": "healthy"
        })
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        facade.connect()

        result = facade.get_health_status("test_token")

        self.assertEqual(result["overall_status"], "healthy")
        mock_client.get_health_status.assert_called_once()

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_list_users(self, mock_client_class):
        """Test list_users method."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.list_users = AsyncMock(return_value={
            "users": [{"name": "User1"}, {"name": "User2"}],
            "total": 2
        })
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        facade.connect()

        result = facade.list_users("test_token", limit=10, offset=0)

        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["users"]), 2)

    @patch('modules.mcp_sync_facade.SkyyMCPClient')
    def test_double_connect(self, mock_client_class):
        """Test that double connect is handled gracefully."""
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        facade = SyncMCPFacade(self.python_path, self.server_script)
        result1 = facade.connect()
        result2 = facade.connect()

        self.assertTrue(result1)
        self.assertTrue(result2)
        # Should only call connect once
        self.assertEqual(mock_client.connect.call_count, 1)


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("SYNC MCP FACADE TESTS")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSyncMCPFacade)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
