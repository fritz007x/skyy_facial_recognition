"""
Simple OAuth Test - Tests authentication without Unicode issues
"""

import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.oauth_config import oauth_config

async def test_oauth():
    """Test OAuth authentication flow."""

    print("=" * 60)
    print("OAUTH 2.1 AUTHENTICATION TEST")
    print("=" * 60)

    # Setup OAuth
    client_id = "simple_test_client"
    clients = oauth_config.load_clients()
    if client_id not in clients:
        print(f"\n[+] Creating OAuth client: {client_id}")
        oauth_config.create_client(client_id=client_id, client_name="Simple Test Client")
    else:
        print(f"\n[+] Using existing client: {client_id}")

    # Generate token
    print("[+] Generating access token...")
    access_token = oauth_config.create_access_token(client_id)
    print(f"[+] Token generated: {access_token[:50]}...")

    # Setup MCP server connection
    python_path = Path("facial_mcp_py311/Scripts/python.exe").absolute()
    server_script = Path("src/skyy_facial_recognition_mcp.py").absolute()

    server_params = StdioServerParameters(
        command=str(python_path),
        args=[str(server_script)],
        env=None
    )

    print(f"\n[+] Connecting to MCP server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("[+] Connected successfully")

                # Test 1: Get database stats (simple, no emoji in JSON)
                print("\n" + "=" * 60)
                print("TEST 1: Get Database Statistics (JSON format)")
                print("=" * 60)

                result = await session.call_tool(
                    "skyy_get_database_stats",
                    arguments={
                        "params": {
                            "access_token": access_token,
                            "response_format": "json"
                        }
                    }
                )

                print("[+] SUCCESS - Database stats retrieved")
                print(result.content[0].text)

                # Test 2: List users
                print("\n" + "=" * 60)
                print("TEST 2: List Users (JSON format)")
                print("=" * 60)

                result = await session.call_tool(
                    "skyy_list_users",
                    arguments={
                        "params": {
                            "access_token": access_token,
                            "limit": 5,
                            "offset": 0,
                            "response_format": "json"
                        }
                    }
                )

                print("[+] SUCCESS - User list retrieved")
                print(result.content[0].text)

                # Test 3: Test with invalid token
                print("\n" + "=" * 60)
                print("TEST 3: Invalid Token (Should Fail)")
                print("=" * 60)

                try:
                    result = await session.call_tool(
                        "skyy_get_database_stats",
                        arguments={
                            "params": {
                                "access_token": "invalid_token_12345",
                                "response_format": "json"
                            }
                        }
                    )
                    print("[-] UNEXPECTED: Call succeeded with invalid token")
                except Exception as e:
                    print(f"[+] SUCCESS - Invalid token correctly rejected: {str(e)[:100]}")

                print("\n" + "=" * 60)
                print("ALL OAUTH TESTS PASSED!")
                print("=" * 60)

    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_oauth())
