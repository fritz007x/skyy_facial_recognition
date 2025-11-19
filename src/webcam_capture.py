"""
Enhanced Webcam Capture with Facial Recognition

This script provides multiple modes:
1. Capture and Register User - Capture image and register new user
2. Recognize Face - Capture image and recognize who it is
3. Live Recognition - Continuous face recognition from webcam feed
"""

import cv2
import base64
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import OAuth config
try:
    from oauth_config import oauth_config
except ImportError:
    from src.oauth_config import oauth_config

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def setup_oauth():
    """Setup OAuth client and generate access token."""
    # Create a webcam client
    client_id = "webcam_tool_client"

    # Check if client already exists, if not create it
    clients = oauth_config.load_clients()
    if client_id not in clients:
        print(f"{Colors.BLUE}[i] Creating OAuth client for webcam tool...{Colors.RESET}")
        credentials = oauth_config.create_client(
            client_id=client_id,
            client_name="Webcam Tool Client"
        )
        print(f"{Colors.GREEN}[OK] OAuth client created{Colors.RESET}")

    # Generate access token
    access_token = oauth_config.create_access_token(client_id)
    print(f"{Colors.GREEN}[OK] Access token generated (expires in {oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes){Colors.RESET}")

    return access_token

def capture_from_webcam():
    """Capture a single frame from webcam and return as base64."""
    cap = cv2.VideoCapture(0)  # 0 is usually the default webcam

    if not cap.isOpened():
        print(f"{Colors.RED}Error: Could not open webcam{Colors.RESET}")
        return None

    print(f"{Colors.CYAN}Press SPACE to capture, ESC to cancel{Colors.RESET}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"{Colors.RED}Failed to grab frame{Colors.RESET}")
            break

        # Display the frame
        cv2.imshow('Webcam - Press SPACE to capture', frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC
            print(f"{Colors.YELLOW}Cancelled{Colors.RESET}")
            break
        elif key == 32:  # SPACE
            # Convert to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            print(f"{Colors.GREEN}Image captured!{Colors.RESET}")
            cap.release()
            cv2.destroyAllWindows()
            return image_base64

    cap.release()
    cv2.destroyAllWindows()
    return None


async def get_mcp_session():
    """Create and return an MCP session."""
    python_path = Path("facial_mcp_py311/Scripts/python.exe").absolute()
    server_script = Path("src/skyy_facial_recognition_mcp.py").absolute()

    server_params = StdioServerParameters(
        command=str(python_path),
        args=[str(server_script)],
        env=None
    )

    return stdio_client(server_params)


async def capture_and_register_mode(access_token):
    """Capture image and optionally register a new user."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== CAPTURE & REGISTER ==={Colors.RESET}\n")

    # Capture image
    print(f"{Colors.CYAN}Position yourself in front of the camera...{Colors.RESET}")
    image_data = capture_from_webcam()

    if not image_data:
        print(f"{Colors.RED}No image captured{Colors.RESET}")
        return

    # Save to file
    print(f"{Colors.GREEN}Base64 length: {len(image_data)}{Colors.RESET}")
    with open('captured_image.txt', 'w') as f:
        f.write(image_data)
    print(f"{Colors.GREEN}Saved to captured_image.txt{Colors.RESET}")

    # Ask if user wants to register
    print(f"\n{Colors.CYAN}Would you like to register this person? (y/n): {Colors.RESET}", end='')
    register_choice = input().strip().lower()

    if register_choice != 'y':
        print(f"{Colors.YELLOW}Image saved without registration{Colors.RESET}")
        return

    # Get user name
    name = input(f"{Colors.CYAN}Enter user's full name: {Colors.RESET}").strip()
    if not name:
        print(f"{Colors.RED}Name cannot be empty{Colors.RESET}")
        return

    # Get optional metadata
    department = input(f"{Colors.CYAN}Department (optional): {Colors.RESET}").strip()
    role = input(f"{Colors.CYAN}Role (optional): {Colors.RESET}").strip()

    metadata = {}
    if department:
        metadata['department'] = department
    if role:
        metadata['role'] = role

    # Register with MCP server
    print(f"\n{Colors.CYAN}Registering user with facial recognition system...{Colors.RESET}")

    try:
        async with await get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool("skyy_register_user",
                    arguments={
                        "params": {
                            "access_token": access_token,
                            "name": name,
                            "image_data": image_data,
                            "metadata": metadata,
                            "response_format": "markdown"
                        }
                    }
                )

                print(f"\n{Colors.GREEN}{result.content[0].text}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def recognize_face_mode(access_token):
    """Capture image and recognize the person."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== RECOGNIZE FACE ==={Colors.RESET}\n")

    # Get threshold
    threshold_input = input(f"{Colors.CYAN}Confidence threshold (0.0-1.0, default 0.25): {Colors.RESET}").strip()
    threshold = 0.25
    if threshold_input:
        try:
            threshold = float(threshold_input)
            if threshold < 0.0 or threshold > 1.0:
                print(f"{Colors.YELLOW}Invalid threshold, using default 0.25{Colors.RESET}")
                threshold = 0.25
        except ValueError:
            print(f"{Colors.YELLOW}Invalid threshold, using default 0.25{Colors.RESET}")

    # Capture image
    print(f"\n{Colors.CYAN}Position yourself in front of the camera...{Colors.RESET}")
    image_data = capture_from_webcam()

    if not image_data:
        print(f"{Colors.RED}No image captured{Colors.RESET}")
        return

    # Recognize with MCP server
    print(f"{Colors.CYAN}Analyzing face...{Colors.RESET}")

    try:
        async with await get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool("skyy_recognize_face",
                    arguments={
                        "params": {
                            "access_token": access_token,
                            "image_data": image_data,
                            "confidence_threshold": threshold,
                            "response_format": "markdown"
                        }
                    }
                )

                print(f"\n{Colors.GREEN}{result.content[0].text}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def live_recognition_mode(access_token):
    """Continuous face recognition from webcam feed."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== LIVE RECOGNITION MODE ==={Colors.RESET}\n")
    print(f"{Colors.YELLOW}Press 'r' to recognize current frame, 'q' to quit{Colors.RESET}\n")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(f"{Colors.RED}Error: Could not open webcam{Colors.RESET}")
        return

    # Get session ready
    async with await get_mcp_session() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            last_recognition = "No recognition yet"

            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"{Colors.RED}Failed to grab frame{Colors.RESET}")
                    break

                # Add text overlay with last recognition result
                cv2.putText(frame, last_recognition, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'r' to recognize | 'q' to quit", (10, frame.shape[0] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                # Display the frame
                cv2.imshow('Live Recognition Mode', frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):  # Quit
                    print(f"{Colors.YELLOW}Exiting live mode{Colors.RESET}")
                    break

                elif key == ord('r'):  # Recognize
                    # Capture current frame
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')

                    try:
                        # Recognize face
                        result = await session.call_tool("skyy_recognize_face",
                            arguments={
                                "params": {
                                    "access_token": access_token,
                                    "image_data": image_base64,
                                    "confidence_threshold": 0.25,
                                    "response_format": "json"
                                }
                            }
                        )

                        # Parse JSON result
                        result_json = json.loads(result.content[0].text)

                        if result_json['status'] == 'recognized':
                            user_name = result_json['user']['name']
                            distance = result_json['distance']
                            last_recognition = f"Recognized: {user_name} (distance: {distance:.4f})"
                            print(f"{Colors.GREEN}Recognized: {user_name} (distance: {distance:.4f}){Colors.RESET}")
                        elif result_json['status'] == 'not_recognized':
                            last_recognition = "Unknown person"
                            print(f"{Colors.YELLOW}Unknown person{Colors.RESET}")
                        else:
                            last_recognition = "Recognition failed"
                            print(f"{Colors.RED}Recognition failed{Colors.RESET}")

                    except Exception as e:
                        last_recognition = f"Error: {str(e)[:30]}"
                        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

    cap.release()
    cv2.destroyAllWindows()


async def list_users_mode(access_token):
    """List all registered users."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== REGISTERED USERS ==={Colors.RESET}\n")

    try:
        async with await get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool("skyy_list_users",
                    arguments={
                        "params": {
                            "access_token": access_token,
                            "limit": 50,
                            "offset": 0,
                            "response_format": "markdown"
                        }
                    }
                )

                print(f"{Colors.GREEN}{result.content[0].text}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def database_stats_mode(access_token):
    """Show database statistics."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== DATABASE STATISTICS ==={Colors.RESET}\n")

    try:
        async with await get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool("skyy_get_database_stats",
                    arguments={
                        "params": {
                            "access_token": access_token,
                            "response_format": "markdown"
                        }
                    }
                )

                print(f"{Colors.GREEN}{result.content[0].text}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")




def show_menu():
    """Display the main menu."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Skyy Facial Recognition - Webcam Tool'.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    print(f"{Colors.BOLD}Choose a mode:{Colors.RESET}")
    print(f"  {Colors.GREEN}1{Colors.RESET} - Capture & Register User")
    print(f"  {Colors.GREEN}2{Colors.RESET} - Recognize Face (single capture)")
    print(f"  {Colors.GREEN}3{Colors.RESET} - Live Recognition (continuous)")
    print(f"  {Colors.GREEN}4{Colors.RESET} - List Registered Users")
    print(f"  {Colors.GREEN}5{Colors.RESET} - Database Statistics")
    print(f"  {Colors.GREEN}0{Colors.RESET} - Exit")
    print()


async def main():
    """Main application loop."""
    # Setup OAuth and get access token
    print(f"\n{Colors.BOLD}{Colors.CYAN}Setting up OAuth authentication...{Colors.RESET}\n")
    access_token = setup_oauth()
    print()

    while True:
        show_menu()
        choice = input(f"{Colors.CYAN}Enter your choice: {Colors.RESET}").strip()

        if choice == '0':
            print(f"{Colors.YELLOW}Goodbye!{Colors.RESET}")
            break
        elif choice == '1':
            await capture_and_register_mode(access_token)
        elif choice == '2':
            await recognize_face_mode(access_token)
        elif choice == '3':
            await live_recognition_mode(access_token)
        elif choice == '4':
            await list_users_mode(access_token)
        elif choice == '5':
            await database_stats_mode(access_token)
        else:
            print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")

        # Pause before showing menu again
        if choice != '0':
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


if __name__ == "__main__":
    print(f"{Colors.BOLD}Skyy Facial Recognition - Webcam Tool{Colors.RESET}")
    print(f"{Colors.BOLD}Make sure your MCP server is available!{Colors.RESET}\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
