# Delete User Utility - Quick Reference

## Usage

### Delete a User
```bash
python delete_user.py <user_id>
```

Example:
```bash
python delete_user.py user_676a6dfed8a1
```

The script will:
1. Connect to MCP server
2. Search through all users (with pagination if needed)
3. Display user details
4. Prompt for confirmation
5. Delete the user if confirmed

### List All Users
```bash
python delete_user.py --list
```

Shows up to 100 users with their details:
- User ID
- Name
- Registration timestamp
- Recognition count
- Last recognized date

## Interactive Example

```
============================================================
  USER DELETION UTILITY
============================================================

[Setup] Configuring OAuth...
[OAuth] Using existing client: delete_user_utility
[OAuth] Access token generated

[Setup] Connecting to MCP server...
[OK] Connected to MCP server

============================================================
  DELETING USER: user_676a6dfed8a1
============================================================

[1/3] Verifying user exists...
[1/3] Searching through all 375 users...
[OK] Found user:
    Name: Test User
    Enrolled: 2025-11-19T02:27:08.343408

[2/3] Confirming deletion...
Are you sure you want to delete user 'user_676a6dfed8a1'? (yes/no): yes

[3/3] Deleting user...
[OK] Successfully deleted user 'user_676a6dfed8a1'
  Message: User deleted successfully

[Cleanup] Disconnecting from MCP server...
[OK] Done.
```

## Common Scenarios

### User Not Found
```
[X] Error: User 'invalid_user' not found in database.

Searched 375 users. To see all users, run:
    python delete_user.py --list
```

### Canceling Deletion
```
[2/3] Confirming deletion...
Are you sure you want to delete user 'user_676a6dfed8a1'? (yes/no): no
[X] Deletion cancelled.
```

### Large Database
If you have many users (>100), the script automatically paginates through all of them to find the target user. Progress is shown:

```
[1/3] Searching through all 375 users...
[MCP] Calling tool: skyy_list_users
[MCP] Calling tool: skyy_list_users
[MCP] Calling tool: skyy_list_users
...
[OK] Found user:
    Name: Test User
```

## Error Handling

The script includes robust error handling for:
- MCP connection failures
- OAuth setup issues
- User not found
- Network/timeout issues
- Invalid responses

All errors are clearly reported with `[X]` prefix.

## Requirements

- Python 3.11.9
- Active virtual environment: `facial_mcp_py311`
- MCP server accessible
- Valid OAuth client configuration

## Activation

Before running, ensure virtual environment is activated:

### Windows
```bash
facial_mcp_py311\Scripts\activate
```

### Unix/Mac
```bash
source facial_mcp_py311/bin/activate
```

Or run directly with full Python path:
```bash
facial_mcp_py311/Scripts/python.exe delete_user.py <user_id>
```
