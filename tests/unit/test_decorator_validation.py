"""
Test OAuth decorator with MCP tool call
"""

import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.oauth_config import oauth_config

async def test_decorator():
    """Test OAuth decorator validation."""

    print("=" * 60)
    print("OAUTH DECORATOR VALIDATION TEST")
    print("=" * 60)

    # Setup OAuth
    client_id = "decorator_test_client"
    clients = oauth_config.load_clients()
    if client_id not in clients:
        print(f"\n[+] Creating OAuth client: {client_id}")
        oauth_config.create_client(client_id=client_id, client_name="Decorator Test Client")

    # Generate valid token
    print("[+] Generating valid access token...")
    valid_token = oauth_config.create_access_token(client_id)
    print(f"[+] Valid token: {valid_token[:50]}...")

    # Setup MCP server connection
    python_path = Path("facial_mcp_py311/Scripts/python.exe").absolute()
    server_script = Path("src/skyy_facial_recognition_mcp.py").absolute()

    server_params = StdioServerParameters(
        command=str(python_path),
        args=[str(server_script)],
        env=None
    )

    print(f"\n[+] Connecting to MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[+] Connected successfully")

            # Test 1: Valid token
            print("\n" + "=" * 60)
            print("TEST 1: Valid Token (Should Succeed)")
            print("=" * 60)

            try:
                result = await session.call_tool(
                    "skyy_get_database_stats",
                    arguments={
                        "params": {
                            "access_token": valid_token,
                            "response_format": "json"
                        }
                    }
                )
                print("[+] SUCCESS - Valid token accepted")
                print(f"    Result length: {len(result.content[0].text)} chars")
            except Exception as e:
                print(f"[-] FAILED - Valid token rejected: {e}")

            # Test 2: Invalid token (completely bogus)
            print("\n" + "=" * 60)
            print("TEST 2: Invalid Token (Should Fail)")
            print("=" * 60)

            try:
                result = await session.call_tool(
                    "skyy_get_database_stats",
                    arguments={
                        "params": {
                            "access_token": "completely_invalid_token_xyz123",
                            "response_format": "json"
                        }
                    }
                )
                # If we get here, the token was NOT rejected
                response_text = result.content[0].text
                print(f"[-] FAILED - Invalid token was accepted!")
                print(f"    Response: {response_text[:200]}")

                # Check if it's an error response
                if "error" in response_text.lower() or "authentication" in response_text.lower():
                    print("    (Note: Response contains error message, but call didn't raise exception)")
            except Exception as e:
                print(f"[+] SUCCESS - Invalid token rejected with error:")
                print(f"    {str(e)[:200]}")

            # Test 3: Missing token
            print("\n" + "=" * 60)
            print("TEST 3: Missing Token (Should Fail)")
            print("=" * 60)

            try:
                result = await session.call_tool(
                    "skyy_get_database_stats",
                    arguments={
                        "params": {
                            # No access_token provided
                            "response_format": "json"
                        }
                    }
                )
                print(f"[-] FAILED - Missing token was accepted!")
                print(f"    Response: {result.content[0].text[:200]}")
            except Exception as e:
                print(f"[+] SUCCESS - Missing token rejected with error:")
                print(f"    {str(e)[:200]}")

            # Test 4: Expired token
            print("\n" + "=" * 60)
            print("TEST 4: Expired Token (Should Fail)")
            print("=" * 60)

            import jwt
            from datetime import datetime, timedelta

            expired_payload = {
                "sub": client_id,
                "iat": datetime.utcnow() - timedelta(hours=2),
                "exp": datetime.utcnow() - timedelta(hours=1),
                "type": "access_token",
                "iss": "skyy_facial_recognition_mcp"
            }
            expired_token = jwt.encode(expired_payload, oauth_config.private_key, algorithm=oauth_config.ALGORITHM)

            try:
                result = await session.call_tool(
                    "skyy_get_database_stats",
                    arguments={
                        "params": {
                            "access_token": expired_token,
                            "response_format": "json"
                        }
                    }
                )
                print(f"[-] FAILED - Expired token was accepted!")
                print(f"    Response: {result.content[0].text[:200]}")
            except Exception as e:
                print(f"[+] SUCCESS - Expired token rejected with error:")
                print(f"    {str(e)[:200]}")

    print("\n" + "=" * 60)
    print("DECORATOR VALIDATION TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_decorator())
