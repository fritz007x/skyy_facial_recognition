#!/usr/bin/env python3
"""
Basic Face Recognition Example

This example demonstrates how to use the Skyy Facial Recognition MCP client
for basic face registration and recognition tasks.

Usage:
    python examples/basic_recognition.py

Requirements:
    - Running MCP server: python src/skyy_facial_recognition_mcp.py
    - Valid OAuth token (see docs/developer/oauth-implementation.md)
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Demonstrate basic face recognition operations."""

    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["src/skyy_facial_recognition_mcp.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")

            # Example: Get system health status
            result = await session.call_tool("skyy_get_health_status", {})
            print(f"\nHealth Status: {result.content}")

            # Example: List registered users
            result = await session.call_tool("skyy_list_users", {})
            print(f"\nRegistered Users: {result.content}")


if __name__ == "__main__":
    asyncio.run(main())
