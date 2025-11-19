"""
Test client for Skyy Facial Recognition MCP Server

This script tests all the tools provided by the MCP server:
- OAuth authentication
- Database statistics
- User registration
- Face recognition
- User management (list, get, update, delete)
"""

import asyncio
import json
import base64
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import OAuth config
try:
    from oauth_config import oauth_config
except ImportError:
    from src.oauth_config import oauth_config

# Import from same directory
try:
    from webcam_capture import capture_from_webcam
except ImportError:
    # If running from project root
    from src.webcam_capture import capture_from_webcam

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}[X] {text}{Colors.RESET}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}[i] {text}{Colors.RESET}")

def print_result(result):
    """Print tool result."""
    print(f"{Colors.YELLOW}{result}{Colors.RESET}")

def load_test_image():
    """Load a test image or capture from webcam."""
    # First, check if there's a captured image file
    if Path('captured_image.txt').exists():
        print_info("Found captured_image.txt, using it...")
        with open('captured_image.txt', 'r') as f:
            return f.read().strip()

    # Try to find any test images
    test_images = list(Path('.').glob('*.jpg')) + list(Path('.').glob('*.png'))
    if test_images:
        print_info(f"Found test image: {test_images[0]}")
        with open(test_images[0], 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            return image_data

    # Capture from webcam
    print_info("No test images found. Attempting to capture from webcam...")
    print_info("Press SPACE to capture, ESC to cancel")
    image_data = capture_from_webcam()
    if image_data:
        # Save for future use
        with open('captured_image.txt', 'w') as f:
            f.write(image_data)
        print_success("Image captured and saved to captured_image.txt")
        return image_data

    return None

def setup_oauth():
    """Setup OAuth client and generate access token."""
    print_header("OAuth 2.1 Setup")

    # Create a test client
    client_id = "test_mcp_client"

    # Check if client already exists, if not create it
    clients = oauth_config.load_clients()
    if client_id not in clients:
        print_info("Creating OAuth test client...")
        credentials = oauth_config.create_client(
            client_id=client_id,
            client_name="MCP Test Client"
        )
        client_secret = credentials['client_secret']
        print_success(f"OAuth client created: {client_id}")
    else:
        # Get existing client secret
        client_secret = clients[client_id]['client_secret']
        print_info(f"Using existing OAuth client: {client_id}")

    # Generate access token
    print_info("Generating access token...")
    access_token = oauth_config.create_access_token(client_id)
    print_success(f"Access token generated (expires in {oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes)")
    print_info(f"Token: {access_token[:50]}...")

    return access_token

async def test_mcp_server():
    """Test all MCP server tools."""

    print_header("Skyy Facial Recognition MCP Server Test")

    # Setup OAuth and get access token
    access_token = setup_oauth()

    # Server parameters
    python_path = Path("facial_mcp_py311/Scripts/python.exe").absolute()
    server_script = Path("src/skyy_facial_recognition_mcp.py").absolute()

    server_params = StdioServerParameters(
        command=str(python_path),
        args=[str(server_script)],
        env=None
    )

    print_info(f"Starting MCP server: {python_path}")
    print_info(f"Server script: {server_script}")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:

                # Initialize the connection
                await session.initialize()
                print_success("Connected to MCP server")

                # List available tools
                tools_response = await session.list_tools()
                print_success(f"Found {len(tools_response.tools)} tools")
                for tool in tools_response.tools:
                    print(f"  • {tool.name}: {tool.description[:80]}...")

                # Test 1: Get Database Statistics
                print_header("Test 1: Get Database Statistics")
                try:
                    result = await session.call_tool("skyy_get_database_stats",
                        arguments={
                            "access_token": access_token,
                            "response_format": "markdown"
                        }
                    )
                    print_result(result.content[0].text)
                    print_success("Database stats retrieved")
                except Exception as e:
                    print_error(f"Failed: {e}")

                # Test 2: List Users
                print_header("Test 2: List Registered Users")
                try:
                    result = await session.call_tool("skyy_list_users",
                        arguments={
                            "access_token": access_token,
                            "limit": 20,
                            "offset": 0,
                            "response_format": "markdown"
                        }
                    )
                    print_result(result.content[0].text)
                    print_success("User list retrieved")
                except Exception as e:
                    print_error(f"Failed: {e}")

                # Test 3: Register New User
                print_header("Test 3: Register New User")

                # Get image data
                print_info("Loading test image...")
                image_data = load_test_image()

                if not image_data:
                    print_error("No image available. Skipping registration test.")
                    return

                print_success(f"Image loaded ({len(image_data)} bytes)")

                try:
                    result = await session.call_tool("skyy_register_user",
                        arguments={
                            "access_token": access_token,
                            "name": "Test User",
                            "image_data": image_data,
                            "metadata": {
                                "department": "Testing",
                                "role": "MCP Test Subject",
                                "test_timestamp": "2025-11-05"
                            },
                            "response_format": "markdown"
                        }
                    )
                    print_result(result.content[0].text)
                    print_success("User registered successfully")

                    # Parse the result to get user_id (if in JSON format)
                    # For now, we'll try to extract it from markdown
                    result_text = result.content[0].text
                    user_id = None
                    for line in result_text.split('\n'):
                        if '**User ID:**' in line:
                            user_id = line.split('**User ID:**')[1].strip()
                            break

                    if user_id:
                        print_info(f"Registered user ID: {user_id}")

                except Exception as e:
                    print_error(f"Failed: {e}")
                    return

                # Test 4: Recognize Face
                print_header("Test 4: Recognize Face")
                try:
                    result = await session.call_tool("skyy_recognize_face",
                        arguments={
                            "access_token": access_token,
                            "image_data": image_data,
                            "confidence_threshold": 0.25,
                            "response_format": "markdown"
                        }
                    )
                    print_result(result.content[0].text)
                    print_success("Face recognition completed")
                except Exception as e:
                    print_error(f"Failed: {e}")

                # Test 5: Get User Profile (if we have a user_id)
                if user_id:
                    print_header("Test 5: Get User Profile")
                    try:
                        result = await session.call_tool("skyy_get_user_profile",
                            arguments={
                                "access_token": access_token,
                                "user_id": user_id,
                                "response_format": "markdown"
                            }
                        )
                        print_result(result.content[0].text)
                        print_success("User profile retrieved")
                    except Exception as e:
                        print_error(f"Failed: {e}")

                    # Test 6: Update User
                    print_header("Test 6: Update User Information")
                    try:
                        result = await session.call_tool("skyy_update_user",
                            arguments={
                                "access_token": access_token,
                                "user_id": user_id,
                                "name": "Updated Test User",
                                "metadata": {
                                    "department": "Testing - Updated",
                                    "role": "Senior MCP Test Subject",
                                    "updated": "true"
                                },
                                "response_format": "markdown"
                            }
                        )
                        print_result(result.content[0].text)
                        print_success("User information updated")
                    except Exception as e:
                        print_error(f"Failed: {e}")

                    # Test 7: Delete User (optional - ask user first)
                    print_header("Test 7: Delete User (Optional)")
                    user_input = input(f"{Colors.YELLOW}Delete test user '{user_id}'? (y/n): {Colors.RESET}").strip().lower()
                    if user_input == 'y':
                        try:
                            result = await session.call_tool("skyy_delete_user",
                                arguments={
                                    "access_token": access_token,
                                    "user_id": user_id,
                                    "response_format": "markdown"
                                }
                            )
                            print_result(result.content[0].text)
                            print_success("User deleted")
                        except Exception as e:
                            print_error(f"Failed: {e}")
                    else:
                        print_info("Skipping user deletion")

                # Final stats
                print_header("Final Database Statistics")
                try:
                    result = await session.call_tool("skyy_get_database_stats",
                        arguments={
                            "access_token": access_token,
                            "response_format": "markdown"
                        }
                    )
                    print_result(result.content[0].text)
                except Exception as e:
                    print_error(f"Failed: {e}")

                print_header("All Tests Completed!")

    except Exception as e:
        print_error(f"Server connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"{Colors.BOLD}Starting MCP Server Test Client{Colors.RESET}")
    print(f"{Colors.BOLD}Make sure your virtual environment is activated!{Colors.RESET}\n")

    try:
        asyncio.run(test_mcp_server())
    except KeyboardInterrupt:
        print_info("\nTest interrupted by user")
    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
