# User Deletion Utility Guide

Quick reference for the `delete_user.py` utility script.

## Purpose

Delete users from the facial recognition database using their user_id.

## Usage

### List All Users

First, list all users to find the correct user_id:

```bash
python delete_user.py --list
```

**Output:**
```
============================================================
  LISTING ALL USERS
============================================================

Found 3 user(s):

  User ID: john_smith_1
  Name: John Smith
  Enrolled: 2025-11-29T16:45:23.123456
  Metadata: {'registered_via': 'gemma_voice'}
------------------------------------------------------------
  User ID: jane_doe_1
  Name: Jane Doe
  Enrolled: 2025-11-29T16:50:15.654321
  Metadata: {'registered_via': 'gemma_voice'}
------------------------------------------------------------
```

### Delete a User

Delete a user by their user_id:

```bash
python delete_user.py john_smith_1
```

**Interactive Confirmation:**
```
============================================================
  DELETING USER: john_smith_1
============================================================

[1/3] Verifying user exists...
✓ Found user:
    Name: John Smith
    Enrolled: 2025-11-29T16:45:23.123456

[2/3] Confirming deletion...
Are you sure you want to delete user 'john_smith_1'? (yes/no): yes

[3/3] Deleting user...
✓ Successfully deleted user 'john_smith_1'
  Message: User deleted successfully
```

### Skip Confirmation (Advanced)

For automated scripts, skip the confirmation prompt:

```bash
python delete_user.py john_smith_1 --no-confirm
```

**⚠️ Warning:** Use with caution - deletion is permanent!

## Features

✅ **Verification**: Confirms user exists before deletion
✅ **User Details**: Shows user information before deleting
✅ **Confirmation**: Interactive prompt to prevent accidental deletions
✅ **Error Handling**: Clear error messages if user doesn't exist
✅ **OAuth Integration**: Automatic authentication with MCP server

## Error Handling

### User Not Found

```
❌ Error: User 'invalid_user' not found in database.

Available users:
  - john_smith_1 (John Smith)
  - jane_doe_1 (Jane Doe)
```

### Connection Failed

```
❌ MCP connection failed
```

**Solution**: Ensure the MCP server is configured correctly in `config.py`

## Technical Details

**Dependencies:**
- `SyncMCPFacade` - Synchronous MCP client
- `oauth_config` - OAuth authentication
- `config` - Server configuration

**Authentication:**
- Creates OAuth client: `delete_user_utility`
- Generates temporary access token
- Token auto-expires after 60 minutes

**Safety Features:**
1. User existence verification before deletion
2. Interactive confirmation prompt
3. Detailed logging of all operations
4. Graceful error handling
5. Automatic cleanup on exit

## Examples

### Example 1: List and Delete

```bash
# Step 1: List all users
python delete_user.py --list

# Step 2: Delete a specific user
python delete_user.py john_smith_1
```

### Example 2: Quick Deletion (No Confirmation)

```bash
python delete_user.py old_user_123 --no-confirm
```

### Example 3: Batch Deletion Script

Create a batch script `delete_multiple.sh`:

```bash
#!/bin/bash
users=("user1_1" "user2_1" "user3_1")

for user in "${users[@]}"; do
    python delete_user.py "$user" --no-confirm
done
```

## Notes

- **User IDs** follow the format: `{name_lowercase}_{count}`
  - Example: `john_smith_1`, `jane_doe_2`

- **Deletion is permanent** - users cannot be recovered once deleted

- **Embeddings and metadata** are removed along with the user

- **Database consistency** is maintained - all references are cleaned up

## Troubleshooting

### Issue: Script hangs during connection

**Solution**: Kill any running MCP server processes and try again

### Issue: Permission denied

**Solution**: Ensure you have write access to the database directory

### Issue: OAuth error

**Solution**: Check that `src/oauth_config.py` is configured correctly

## Related Tools

- `delete_user.py` - Delete users (this script)
- `gemma_mcp_prototype/main_sync_refactored.py` - Main voice assistant
- `src/skyy_facial_recognition_mcp.py` - MCP server

## Support

For issues or questions, refer to:
- `CLAUDE.md` - Project documentation
- `VOSK_MIGRATION.md` - Speech recognition details
- `VOSK_GRAMMAR_FIX.md` - Grammar format fixes
