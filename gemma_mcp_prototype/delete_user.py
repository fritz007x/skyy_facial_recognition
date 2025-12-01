"""
Delete User Script - Delete a registered user by name.

Usage:
    # Windows
    C:\\path\\to\\facial_mcp_py311\\Scripts\\python.exe delete_user.py "Full Name"
    C:\\path\\to\\facial_mcp_py311\\Scripts\\python.exe delete_user.py --list
    
    # Linux/Mac
    /path/to/facial_mcp_py311/bin/python delete_user.py "Full Name"
    /path/to/facial_mcp_py311/bin/python delete_user.py --list

This script:
1. Connects to the Skyy Facial Recognition MCP server
2. Searches for users matching the provided name (case-insensitive)
3. Prompts for confirmation before deleting
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Direct import of only what we need - avoid importing modules package
from oauth_config import oauth_config

# Import MCP facade directly to avoid triggering speech/vision imports
sys.path.insert(0, str(Path(__file__).parent))
from modules.mcp_sync_facade import SyncMCPFacade
from config import MCP_PYTHON_PATH, MCP_SERVER_SCRIPT

def setup_oauth() -> str:
    """Setup OAuth and get access token."""
    client_id = "gemma_admin_client"
    
    # Check if client already exists, if not create it
    clients = oauth_config.load_clients()
    if client_id not in clients:
        print(f"[OAuth] Creating admin client: {client_id}")
        oauth_config.create_client(
            client_id=client_id,
            client_name="Gemma Admin Client"
        )
    
    return oauth_config.create_access_token(client_id)

def find_users_by_name(users: List[Dict[str, Any]], name_query: str) -> List[Dict[str, Any]]:
    """Find users matching the name query (case-insensitive)."""
    query = name_query.lower().strip()
    matches = []
    
    for user in users:
        user_name = user.get("name", "").lower()
        if query in user_name:
            matches.append(user)
            
    return matches

def main():
    parser = argparse.ArgumentParser(description="Delete a user from the facial recognition database.")
    parser.add_argument("name", nargs='?', help="Full name of the user to delete")
    parser.add_argument("--list", action="store_true", help="List all users to 'users_list.txt'")
    args = parser.parse_args()
    
    if not args.name and not args.list:
        parser.print_help()
        return 1
    
    target_name = args.name
    
    print("=" * 60)
    if args.list:
        print("  LIST ALL USERS")
    else:
        print(f"  DELETE USER: '{target_name}'")
    print("=" * 60)
    
    # 1. Setup OAuth
    try:
        token = setup_oauth()
        print("[Init] OAuth token generated.")
    except Exception as e:
        print(f"[Error] OAuth setup failed: {e}")
        return 1
        
    # 2. Connect to MCP
    print("[Init] Connecting to MCP server...")
    with SyncMCPFacade(MCP_PYTHON_PATH, MCP_SERVER_SCRIPT) as mcp:
        if not mcp._connected:
            print("[Error] Failed to connect to MCP server.")
            return 1
            
        # 3. List all users (with pagination)
        print("[Action] Fetching user list...")
        users = []
        offset = 0
        limit = 100
        
        while True:
            result = mcp.list_users(token, limit=limit, offset=offset)
            
            if "users" not in result:
                print(f"[Error] Failed to list users: {result}")
                return 1
                
            batch = result["users"]
            users.extend(batch)
            
            if len(batch) < limit:
                break
                
            offset += limit
            
        print(f"[Info] Found {len(users)} total registered users.")
        
        # 4. Handle --list
        if args.list:
            output_file = "users_list.txt"
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"Registered Users ({len(users)})\n")
                    f.write("=" * 40 + "\n\n")
                    for user in users:
                        name = user.get("name", "Unknown")
                        uid = user.get("user_id", "Unknown")
                        reg = user.get("registration_timestamp", "Unknown")
                        f.write(f"Name: {name}\nID:   {uid}\nReg:  {reg}\n{'-'*20}\n")
                print(f"[Success] User list written to '{output_file}'")
            except Exception as e:
                print(f"[Error] Failed to write to file: {e}")
                return 1
            
            # If no name provided, we are done
            if not target_name:
                return 0

        # 5. Find matches (if name provided)
        matches = find_users_by_name(users, target_name)
        
        if not matches:
            print(f"\n[Result] No users found matching '{target_name}'.")
            return 0
            
        # 6. Handle matches
        selected_user = None
        
        if len(matches) == 1:
            user = matches[0]
            print(f"\n[Match] Found 1 user:")
            print(f"  - Name: {user.get('name')}")
            print(f"  - ID:   {user.get('user_id')}")
            print(f"  - Reg:  {user.get('registration_timestamp')}")
            
            confirm = input("\nAre you sure you want to DELETE this user? (y/N): ").lower()
            if confirm == 'y':
                selected_user = user
            else:
                print("Operation cancelled.")
                return 0
                
        else:
            print(f"\n[Match] Found {len(matches)} users matching '{target_name}':")
            for i, user in enumerate(matches):
                print(f"  {i+1}. {user.get('name')} (ID: {user.get('user_id')})")
                
            selection = input("\nEnter the number of the user to delete (or 0 to cancel): ")
            try:
                idx = int(selection)
                if 1 <= idx <= len(matches):
                    selected_user = matches[idx-1]
                    
                    confirm = input(f"Confirm deletion of '{selected_user.get('name')}'? (y/N): ").lower()
                    if confirm != 'y':
                        print("Operation cancelled.")
                        return 0
                elif idx == 0:
                    print("Operation cancelled.")
                    return 0
                else:
                    print("Invalid selection.")
                    return 1
            except ValueError:
                print("Invalid input.")
                return 1
        
        # 7. Perform deletion
        if selected_user:
            user_id = selected_user.get('user_id')
            print(f"\n[Action] Deleting user ID: {user_id}...")
            
            delete_result = mcp.delete_user(token, user_id)
            
            if delete_result.get("status") == "success":
                print(f"[Success] User '{selected_user.get('name')}' has been deleted.")
            else:
                print(f"[Error] Deletion failed: {delete_result}")
                return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
