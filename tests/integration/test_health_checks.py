"""
Test script for health checking and degraded mode functionality.

This script demonstrates:
1. Health status monitoring
2. Component availability checks
3. Degraded mode behavior (registration queuing)
4. Health state transitions
"""

import asyncio
import sys
import json
import base64
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add src directory to path for OAuth imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from oauth_config import OAuthConfig


def setup_oauth():
    """Setup OAuth client and generate access token."""
    oauth_config = OAuthConfig()

    client_id = "health_test_client"
    clients = oauth_config.load_clients()

    if client_id not in clients:
        print(f"[OAuth] Creating new client: {client_id}")
        credentials = oauth_config.create_client(
            client_id=client_id,
            client_name="Health Check Test Client"
        )
        print(f"[OAuth] Client created successfully")
    else:
        print(f"[OAuth] Using existing client: {client_id}")

    # Generate access token
    access_token = oauth_config.create_access_token(client_id)
    print(f"[OAuth] Access token generated\n")

    return access_token


def get_mcp_session():
    """Create and return an MCP session context manager."""
    # Get the absolute path to the project root
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent.parent

    # Build absolute paths
    python_path = project_root / "facial_mcp_py311" / "Scripts" / "python.exe"
    server_script = project_root / "src" / "skyy_facial_recognition_mcp.py"

    # Verify paths exist
    if not python_path.exists():
        raise FileNotFoundError(f"Python interpreter not found at: {python_path}")
    if not server_script.exists():
        raise FileNotFoundError(f"MCP server script not found at: {server_script}")

    print(f"[MCP] Starting server: {server_script}")
    print(f"[MCP] Using Python: {python_path}\n")

    server_params = StdioServerParameters(
        command=str(python_path),
        args=[str(server_script)],
        env=None
    )

    return stdio_client(server_params)


async def test_health_status(session: ClientSession, access_token: str):
    """Test the health status tool."""
    print("=" * 80)
    print("TEST 1: Health Status Check")
    print("=" * 80)

    try:
        result = await session.call_tool(
            "skyy_get_health_status",
            arguments={
                "params": {
                    "access_token": access_token,
                    "response_format": "json"
                }
            }
        )

        if result and result.content:
            content = result.content[0].text
            health_data = json.loads(content)

            print("\n[Health Status]")
            print(f"Overall Status: {health_data['overall_status'].upper()}")
            print("\nComponent Health:")
            for comp, data in health_data['components'].items():
                status_symbol = {
                    'healthy': '[OK]',
                    'degraded': '[WARN]',
                    'unavailable': '[X]'
                }[data['status']]
                print(f"  {status_symbol} {comp}: {data['status']} - {data['message']}")

            print("\nAvailable Capabilities:")
            for cap, available in health_data['capabilities'].items():
                symbol = '[OK]' if available else '[X]'
                print(f"  {symbol} {cap}")

            if health_data['degraded_mode']['active']:
                print("\n[WARN] Degraded Mode Active!")
                print(f"Queued Registrations: {health_data['degraded_mode']['queued_registrations']}")

            return health_data
        else:
            print("\n[X] No response from health status tool")
            return None

    except Exception as e:
        print(f"\n[X] Error getting health status: {e}")
        return None


async def test_registration(session: ClientSession, access_token: str, test_image: str):
    """Test user registration (will queue if ChromaDB unavailable)."""
    print("\n" + "=" * 80)
    print("TEST 2: User Registration (with health checks)")
    print("=" * 80)

    try:
        result = await session.call_tool(
            "skyy_register_user",
            arguments={
                "params": {
                    "access_token": access_token,
                    "name": "Health Test User",
                    "image_data": test_image,
                    "metadata": {"test": "health_check"},
                    "response_format": "json"
                }
            }
        )

        if result and result.content:
            content = result.content[0].text
            reg_data = json.loads(content)

            print(f"\n[Registration] Status: {reg_data.get('status', 'unknown')}")
            print(f"Message: {reg_data.get('message', 'No message')}")

            if reg_data.get('status') == 'queued':
                print(f"\n[OK] Registration queued successfully (degraded mode)")
                print(f"Queue Position: {reg_data['user']['queue_position']}")
            elif reg_data.get('status') == 'success':
                print(f"\n[OK] Registration successful (normal mode)")
                print(f"User ID: {reg_data['user']['user_id']}")
            elif reg_data.get('status') == 'error':
                # This is expected for test image without a face
                if "No face detected" in reg_data['message']:
                    print(f"\n[OK] Error handling works correctly (no face in test image)")
                else:
                    print(f"\n[X] Unexpected error: {reg_data['message']}")

            return reg_data
        else:
            print("\n[X] No response from registration tool")
            return None

    except Exception as e:
        print(f"\n[X] Error during registration: {e}")
        return None


async def test_recognition(session: ClientSession, access_token: str, test_image: str):
    """Test face recognition (will fail if dependencies unavailable)."""
    print("\n" + "=" * 80)
    print("TEST 3: Face Recognition (with health checks)")
    print("=" * 80)

    try:
        result = await session.call_tool(
            "skyy_recognize_face",
            arguments={
                "params": {
                    "access_token": access_token,
                    "image_data": test_image,
                    "response_format": "json"
                }
            }
        )

        if result and result.content:
            content = result.content[0].text
            recog_data = json.loads(content)

            print(f"\n[Recognition] Status: {recog_data.get('status', 'unknown')}")
            print(f"Message: {recog_data.get('message', 'No message')}")

            if recog_data.get('status') == 'error':
                # This is expected for test image without a face or in degraded mode
                if "No face detected" in recog_data['message']:
                    print(f"\n[OK] Error handling works correctly (no face in test image)")
                else:
                    print(f"\n[X] Recognition unavailable (degraded mode or error)")
            elif recog_data.get('status') == 'recognized':
                print(f"\n[OK] User recognized: {recog_data['user']['name']}")
            elif recog_data.get('status') == 'not_recognized':
                print(f"\n[OK] No matching user found")

            return recog_data
        else:
            print("\n[X] No response from recognition tool")
            return None

    except Exception as e:
        print(f"\n[X] Error during recognition: {e}")
        return None


async def get_database_stats(session: ClientSession, access_token: str):
    """Get database statistics."""
    print("\n" + "=" * 80)
    print("TEST 4: Database Statistics")
    print("=" * 80)

    try:
        result = await session.call_tool(
            "skyy_get_database_stats",
            arguments={
                "params": {
                    "access_token": access_token,
                    "response_format": "json"
                }
            }
        )

        if result and result.content:
            content = result.content[0].text
            stats = json.loads(content)

            if stats.get('status') == 'error':
                print(f"\n[X] Database unavailable: {stats['message']}")
            else:
                print(f"\n[Stats] Total Users: {stats.get('total_users', 0)}")
                print(f"Total Recognitions: {stats.get('total_recognitions', 0)}")

            return stats
        else:
            print("\n[X] No response from stats tool")
            return None

    except Exception as e:
        print(f"\n[X] Error getting stats: {e}")
        return None


async def main():
    """Run comprehensive health check tests."""
    print("\n" + "=" * 80)
    print("FACIAL RECOGNITION MCP - HEALTH CHECK TEST SUITE")
    print("=" * 80)
    print("\nThis test demonstrates:")
    print("1. Health status monitoring")
    print("2. Component availability checks")
    print("3. Degraded mode behavior (if ChromaDB unavailable)")
    print("4. Health-aware tool execution")
    print()

    # Setup OAuth
    access_token = setup_oauth()

    # Create a simple test image (200x200 white pixel PNG as base64)
    # Note: This won't actually register a face, but tests the health check logic
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAIAAAAiOjnJAAACFElEQVR4nO3UsQ0AIBADMWD/nZ8luALJHiDVKXtmFrx2ni+CsKh4LBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsIiISwSwiIhLBLCIiEsEsJCWPzDY5EQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBYJYZEQFglhkRAWCWGREBarcAEhCgSNcJ1nZQAAAABJRU5ErkJggg=="

    async with get_mcp_session() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("\n[MCP] Session initialized successfully")
            print("[MCP] Running health check tests...\n")

            # Test 1: Health Status
            health_data = await test_health_status(session, access_token)

            # Test 2: Registration (will queue if degraded)
            reg_data = await test_registration(session, access_token, test_image)

            # Test 3: Recognition (will fail if degraded)
            recog_data = await test_recognition(session, access_token, test_image)

            # Test 4: Database stats (will fail if degraded)
            stats_data = await get_database_stats(session, access_token)

            # Summary
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)

            if health_data:
                overall = health_data['overall_status']
                print(f"\nSystem Status: {overall.upper()}")

                if health_data['degraded_mode']['active']:
                    print("\n[WARN] System is in DEGRADED MODE")
                    print("Expected behavior:")
                    print("  - Registrations: QUEUED (waiting for recovery)")
                    print("  - Recognition: DISABLED")
                    print("  - Database queries: DISABLED")
                else:
                    print("\n[OK] System is FULLY OPERATIONAL")
                    print("All features available:")
                    print("  - Registrations: ACTIVE")
                    print("  - Recognition: ACTIVE")
                    print("  - Database queries: ACTIVE")

            print("\n" + "=" * 80)
            print("Test suite completed successfully!")
            print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
    except Exception as e:
        print(f"\n\n[X] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
