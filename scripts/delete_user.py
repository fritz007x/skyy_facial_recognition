"""
Utility script to delete a user from the facial recognition database.

Usage:
    python delete_user.py <user_id>
    python delete_user.py --list  # List all users first

Example:
    python delete_user.py john_smith_1
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "gemma_voice_assistant"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.mcp_sync_facade import SyncMCPFacade
from config import MCP_SERVER_SCRIPT, MCP_PYTHON_PATH
from oauth_config import oauth_config


def setup_oauth():
    """Setup OAuth client and generate access token."""
    client_id = "delete_user_utility"

    # Check if client already exists, if not create it
    clients = oauth_config.load_clients()
    if client_id not in clients:
        print(f"[OAuth] Creating new client: {client_id}")
        oauth_config.create_client(
            client_id=client_id,
            client_name="Delete User Utility"
        )
    else:
        print(f"[OAuth] Using existing client: {client_id}")

    # Generate access token
    access_token = oauth_config.create_access_token(client_id)
    print(f"[OAuth] Access token generated")

    return access_token


def list_users(mcp, access_token):
    """List all users in the database."""
    print("\n" + "=" * 60)
    print("  LISTING ALL USERS")
    print("=" * 60 + "\n")

    try:
        result = mcp.list_users(access_token=access_token, limit=100)
    except Exception as e:
        print(f"[X] Error listing users: {type(e).__name__}: {e}")
        return

    # Check if error response
    if isinstance(result.get("status"), str) and result.get("status") == "error":
        print(f"Error listing users: {result.get('message', 'Unknown error')}")
        return

    users = result.get("users", [])
    total = result.get("total", len(users))

    if not users:
        print("No users found in the database.")
        return

    print(f"Found {len(users)} user(s) (showing up to 100 of {total} total):\n")

    for user in users:
        user_id = user.get("user_id", "N/A")
        name = user.get("name", "N/A")
        registration_timestamp = user.get("registration_timestamp", "N/A")
        recognition_count = user.get("recognition_count", 0)
        last_recognized = user.get("last_recognized", "Never")

        print(f"  User ID: {user_id}")
        print(f"  Name: {name}")
        print(f"  Enrolled: {registration_timestamp}")
        print(f"  Recognition Count: {recognition_count}")
        print(f"  Last Recognized: {last_recognized}")
        print("-" * 60)

    if result.get("has_more", False):
        print(f"\n[!] Showing first {len(users)} of {total} total users")
        print(f"    Use pagination to see more users")


def delete_user(mcp, access_token, user_id):
    """Delete a user by user_id."""
    print("\n" + "=" * 60, flush=True)
    print(f"  DELETING USER: {user_id}", flush=True)
    print("=" * 60 + "\n", flush=True)

    # First, verify the user exists
    print(f"[1/3] Verifying user exists...", flush=True)
    try:
        list_result = mcp.list_users(access_token=access_token)
    except Exception as e:
        print(f"[X] Error calling list_users: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

    # Check if error response (has 'status' field with 'error')
    if isinstance(list_result.get("status"), str) and list_result.get("status") == "error":
        print(f"[X] Error verifying user: {list_result.get('message', 'Unknown error')}")
        return False

    # Normal response has 'users' array
    users = list_result.get("users", [])

    if not users:
        print(f"[X] No users found in database.")
        return False

    # Check if user exists (need to fetch ALL users with pagination)
    all_users = users.copy()
    total = list_result.get("total", len(users))
    offset = list_result.get("offset", 0)
    limit = list_result.get("limit", 20)

    # Fetch remaining pages if user not found in first page
    user_exists = any(u.get("user_id") == user_id for u in all_users)

    if not user_exists and list_result.get("has_more", False):
        # Need to fetch more pages
        print(f"[1/3] Searching through all {total} users...")
        current_offset = limit

        while current_offset < total and not user_exists:
            try:
                page_result = mcp.list_users(
                    access_token=access_token,
                    limit=limit,
                    offset=current_offset
                )
                page_users = page_result.get("users", [])
                all_users.extend(page_users)

                user_exists = any(u.get("user_id") == user_id for u in page_users)
                current_offset += limit
            except Exception as e:
                print(f"[X] Error fetching user page: {e}")
                break

    if not user_exists:
        print(f"[X] Error: User '{user_id}' not found in database.")
        print(f"\nSearched {len(all_users)} users. To see all users, run:")
        print(f"    python delete_user.py --list")
        return False

    # Show user details before deletion
    user_data = next((u for u in all_users if u.get("user_id") == user_id), None)
    if user_data:
        print(f"[OK] Found user:")
        print(f"    Name: {user_data.get('name')}")
        print(f"    Enrolled: {user_data.get('registration_timestamp', 'N/A')}")

    # Confirm deletion
    print(f"\n[2/3] Confirming deletion...")
    confirmation = input(f"Are you sure you want to delete user '{user_id}'? (yes/no): ")

    if confirmation.lower() not in ['yes', 'y']:
        print("[X] Deletion cancelled.")
        return False

    # Delete the user
    print(f"\n[3/3] Deleting user...")
    result = mcp.delete_user(
        access_token=access_token,
        user_id=user_id
    )

    status = result.get("status", "error")

    if status == "success":
        print(f"[OK] Successfully deleted user '{user_id}'")
        print(f"  Message: {result.get('message', 'User deleted')}")
        return True
    else:
        print(f"[X] Error deleting user: {result.get('message', 'Unknown error')}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Delete a user from the facial recognition database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python delete_user.py john_smith_1              # Delete user by ID
  python delete_user.py --list                     # List all users first
  python delete_user.py john_smith_1 --no-confirm # Skip confirmation
        """
    )

    parser.add_argument(
        'user_id',
        nargs='?',
        help='User ID to delete (e.g., john_smith_1)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all users in the database'
    )

    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.list and not args.user_id:
        parser.error("Please provide a user_id or use --list to show all users")
        return 1

    print("=" * 60)
    print("  USER DELETION UTILITY")
    print("=" * 60)

    # Setup OAuth
    print("\n[Setup] Configuring OAuth...")
    try:
        access_token = setup_oauth()
    except Exception as e:
        print(f"[X] OAuth setup failed: {e}")
        return 1

    # Connect to MCP server
    print("\n[Setup] Connecting to MCP server...")
    mcp = SyncMCPFacade(
        python_path=MCP_PYTHON_PATH,
        server_script=MCP_SERVER_SCRIPT
    )

    if not mcp.connect():
        print("[X] MCP connection failed")
        return 1

    print("[OK] Connected to MCP server")

    try:
        # List users if requested
        if args.list:
            list_users(mcp, access_token)
            return 0

        # Delete user
        success = delete_user(mcp, access_token, args.user_id)

        return 0 if success else 1

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        print("\n[Cleanup] Disconnecting from MCP server...")
        mcp.disconnect()
        print("[OK] Done.")


if __name__ == "__main__":
    sys.exit(main())
