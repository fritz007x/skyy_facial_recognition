"""
OAuth 2.1 Middleware for MCP Server

Provides token validation for MCP tool calls.
"""

from functools import wraps
from typing import Optional, Callable, Any
import json

try:
    from .oauth_config import oauth_config
except ImportError:
    from oauth_config import oauth_config


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require OAuth token authentication for MCP tools.

    The token should be passed in the tool's input as 'access_token' field.

    Usage:
        @mcp.tool()
        @require_auth
        async def my_tool(input: MyInput) -> str:
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract token from kwargs or args
        token = None

        # Check if first argument has access_token attribute
        if args and hasattr(args[0], 'access_token'):
            token = args[0].access_token
        # Check all keyword arguments for access_token attribute
        elif kwargs:
            for key, value in kwargs.items():
                if hasattr(value, 'access_token'):
                    token = value.access_token
                    break
        # Check if access_token is directly in kwargs
        if not token and 'access_token' in kwargs:
            token = kwargs['access_token']

        if not token:
            raise AuthenticationError(
                "Authentication required. Please provide an 'access_token' in the request."
            )

        # Verify token
        payload = oauth_config.verify_token(token)
        if not payload:
            raise AuthenticationError(
                "Invalid or expired access token. Please obtain a new token."
            )

        # Add client_id to kwargs for the tool to use if needed
        kwargs['_client_id'] = payload['sub']

        # Call the original function
        return await func(*args, **kwargs)

    return wrapper


def get_client_id_from_context(**kwargs) -> Optional[str]:
    """
    Extract the authenticated client ID from the function context.

    This should be called from within an @require_auth decorated function.

    Returns:
        Client ID if authentication was successful, None otherwise
    """
    return kwargs.get('_client_id')


def create_auth_error_response(error_msg: str, response_format: str = "markdown") -> str:
    """
    Create a standardized error response for authentication failures.

    Args:
        error_msg: Error message to include
        response_format: 'markdown' or 'json'

    Returns:
        Formatted error message
    """
    error_data = {
        "status": "error",
        "error_type": "authentication_error",
        "message": error_msg,
        "hint": "Use the OAuth token generation script to obtain an access token"
    }

    if response_format == "json":
        return json.dumps(error_data, indent=2)
    else:
        return f"""# 🔒 Authentication Error

**{error_msg}**

## How to authenticate:

1. Generate client credentials:
   ```bash
   python src/oauth_admin.py create-client --name "My Client"
   ```

2. Obtain an access token:
   ```bash
   python src/oauth_admin.py get-token --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```

3. Include the token in your MCP requests in the `access_token` field

For more information, see the OAuth documentation in README.md
"""
