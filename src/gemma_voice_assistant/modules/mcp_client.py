"""
MCP Client module for connecting Gemma 3 to the Skyy Facial Recognition MCP server.

This client is designed to work with the existing skyy_facial_recognition_mcp.py server
which uses:
- OAuth 2.1 authentication with JWT tokens
- Pydantic input models with nested 'params' structure
- JSON response format for programmatic parsing

The client handles the specific argument structure expected by the server's tools.
"""

import asyncio
import json
from typing import Optional, Any, Dict
from contextlib import AsyncExitStack
from pathlib import Path

# MCP SDK imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class SkyyMCPClient:
    """
    MCP Client wrapper for Skyy Facial Recognition tools.
    
    This client is specifically designed to work with the Skyy Facial Recognition
    MCP server's tool interface, which expects arguments in a specific format:
    
    {
        "params": {
            "access_token": "...",
            "name": "...",
            ...
            "response_format": "json"
        }
    }
    
    Tools available:
    - skyy_register_user: Register a new user with facial data
    - skyy_recognize_face: Recognize a registered user from an image
    - skyy_list_users: List all registered users
    - skyy_get_user_profile: Get detailed user profile
    - skyy_update_user: Update user information
    - skyy_delete_user: Delete a user from the database
    - skyy_get_database_stats: Get database statistics
    - skyy_get_health_status: Get system health status
    """
    
    def __init__(self, python_path: Path, server_script: Path):
        """
        Initialize MCP client.
        
        Args:
            python_path: Path to Python interpreter in virtual environment
            server_script: Path to MCP server script
        """
        self.python_path = Path(python_path)
        self.server_script = Path(server_script)
        self.session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Establish connection to MCP server.
        
        Returns:
            True if connection successful
        """
        # Verify paths exist
        if not self.python_path.exists():
            print(f"[MCP] ERROR: Python interpreter not found at: {self.python_path}")
            return False
        if not self.server_script.exists():
            print(f"[MCP] ERROR: Server script not found at: {self.server_script}")
            return False
        
        print(f"[MCP] Starting server: {self.server_script}")
        print(f"[MCP] Using Python: {self.python_path}")
        
        try:
            self._exit_stack = AsyncExitStack()
            await self._exit_stack.__aenter__()
            
            # Configure stdio transport
            server_params = StdioServerParameters(
                command=str(self.python_path),
                args=[str(self.server_script)],
                env=None
            )
            
            # Create stdio client connection
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            # Read and write streams from transport
            read_stream, write_stream = stdio_transport

            # Create session
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize the session
            await self.session.initialize()
            
            self._connected = True
            print("[MCP] Connected successfully!")
            
            # List available tools
            tools_response = await self.session.list_tools()
            tool_names = [t.name for t in tools_response.tools]
            print(f"[MCP] Available tools: {tool_names}")
            
            return True
            
        except Exception as e:
            print(f"[MCP] Connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def disconnect(self) -> None:
        """Close MCP connection."""
        if self._exit_stack:
            await self._exit_stack.__aexit__(None, None, None)
            self._connected = False
            print("[MCP] Disconnected.")
    
    async def call_tool(
        self, 
        tool_name: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool with given parameters.
        
        The server expects arguments in the format:
        {"params": {...}}
        
        Args:
            tool_name: Name of the tool to call
            params: Dictionary of tool parameters (will be wrapped in "params")
            
        Returns:
            Tool response as dictionary
        """
        if not self._connected or self.session is None:
            raise RuntimeError("MCP client not connected")
        
        print(f"[MCP] Calling tool: {tool_name}")
        
        try:
            # Wrap parameters in the expected format
            arguments = {"params": params}
            
            result = await self.session.call_tool(tool_name, arguments=arguments)
            
            # Parse the result content
            if result.content:
                for content_block in result.content:
                    if hasattr(content_block, 'text'):
                        try:
                            return json.loads(content_block.text)
                        except json.JSONDecodeError:
                            # If not JSON, return as-is in a dict
                            return {"raw_response": content_block.text}
            
            return {"error": "No content in response"}
            
        except Exception as e:
            print(f"[MCP] Tool call failed: {e}")
            return {"status": "error", "message": str(e)}
    
    # =========================================================================
    # Convenience methods for specific tools
    # =========================================================================
    
    async def recognize_face(
        self, 
        access_token: str,
        image_data: str,
        confidence_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """
        Call skyy_recognize_face tool.
        
        Args:
            access_token: OAuth 2.1 access token
            image_data: Base64-encoded image data
            confidence_threshold: Maximum distance for recognition (0.0-1.0)
            
        Returns:
            Recognition result with status and user info (if matched)
            
        Response format:
            {
                "status": "recognized" | "not_recognized" | "low_confidence" | "error",
                "distance": float,
                "threshold": float,
                "user": {
                    "user_id": str,
                    "name": str,
                    "metadata": dict,
                    "recognition_count": int
                }
            }
        """
        return await self.call_tool(
            "skyy_recognize_face",
            {
                "access_token": access_token,
                "image_data": image_data,
                "confidence_threshold": confidence_threshold,
                "response_format": "json"
            }
        )
    
    async def register_user(
        self,
        access_token: str,
        name: str,
        image_data: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call skyy_register_user tool.
        
        Args:
            access_token: OAuth 2.1 access token
            name: User's full name
            image_data: Base64-encoded face image
            metadata: Optional user metadata
            
        Returns:
            Registration result with user_id
            
        Response format:
            {
                "status": "success" | "queued" | "error",
                "message": str,
                "user": {
                    "user_id": str,
                    "name": str,
                    "registration_timestamp": str,
                    "face_quality": {...},
                    "metadata": dict
                }
            }
        """
        params = {
            "access_token": access_token,
            "name": name,
            "image_data": image_data,
            "response_format": "json"
        }
        if metadata:
            params["metadata"] = metadata
            
        return await self.call_tool("skyy_register_user", params)
    
    async def get_user_profile(
        self, 
        access_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Call skyy_get_user_profile tool.
        
        Args:
            access_token: OAuth 2.1 access token
            user_id: User's unique identifier
            
        Returns:
            User profile data
        """
        return await self.call_tool(
            "skyy_get_user_profile",
            {
                "access_token": access_token,
                "user_id": user_id,
                "response_format": "json"
            }
        )
    
    async def list_users(
        self, 
        access_token: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Call skyy_list_users tool.
        
        Args:
            access_token: OAuth 2.1 access token
            limit: Maximum users to return
            offset: Number of users to skip
            
        Returns:
            List of all registered users with pagination info
        """
        return await self.call_tool(
            "skyy_list_users",
            {
                "access_token": access_token,
                "limit": limit,
                "offset": offset,
                "response_format": "json"
            }
        )
    
    async def update_user(
        self,
        access_token: str,
        user_id: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call skyy_update_user tool.
        
        Args:
            access_token: OAuth 2.1 access token
            user_id: User's unique identifier
            name: Optional new name
            metadata: Optional new metadata
            
        Returns:
            Updated user data
        """
        params = {
            "access_token": access_token,
            "user_id": user_id,
            "response_format": "json"
        }
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = metadata
            
        return await self.call_tool("skyy_update_user", params)
    
    async def delete_user(
        self, 
        access_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Call skyy_delete_user tool.
        
        Args:
            access_token: OAuth 2.1 access token
            user_id: User's unique identifier
            
        Returns:
            Deletion confirmation
        """
        return await self.call_tool(
            "skyy_delete_user",
            {
                "access_token": access_token,
                "user_id": user_id,
                "response_format": "json"
            }
        )
    
    async def get_database_stats(self, access_token: str) -> Dict[str, Any]:
        """
        Call skyy_get_database_stats tool.
        
        Args:
            access_token: OAuth 2.1 access token
            
        Returns:
            Database statistics
        """
        return await self.call_tool(
            "skyy_get_database_stats",
            {
                "access_token": access_token,
                "response_format": "json"
            }
        )
    
    async def get_health_status(self, access_token: str) -> Dict[str, Any]:
        """
        Call skyy_get_health_status tool.
        
        Args:
            access_token: OAuth 2.1 access token
            
        Returns:
            Comprehensive health status including:
            - overall_status: "healthy" | "degraded"
            - components: Health of InsightFace, ChromaDB, OAuth
            - capabilities: Available tool operations
            - degraded_mode: Queue status if active
        """
        return await self.call_tool(
            "skyy_get_health_status",
            {
                "access_token": access_token,
                "response_format": "json"
            }
        )
