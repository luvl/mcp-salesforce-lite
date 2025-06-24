#!/usr/bin/env python3
"""Simple Salesforce MCP Server."""

import asyncio
import logging
import sys
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Handle both direct execution and module imports
try:
    from .client import SalesforceClient
    from .tools import (
        get_query_tools, handle_query_tools,
        get_crud_tools, handle_crud_tools,
        get_metadata_tools, handle_metadata_tools
    )
except ImportError:
    # Add the src directory to the path for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.mcp_salesforce_lite.client import SalesforceClient
    from src.mcp_salesforce_lite.tools import (
        get_query_tools, handle_query_tools,
        get_crud_tools, handle_crud_tools,
        get_metadata_tools, handle_metadata_tools
    )

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("salesforce-lite")

# Global client instance
sf_client: Optional[SalesforceClient] = None


def get_client() -> SalesforceClient:
    """Get or create Salesforce client instance."""
    global sf_client
    if sf_client is None:
        sf_client = SalesforceClient()
    return sf_client


# TOOLS - Functions that AI can call

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    tools = []
    tools.extend(get_query_tools())
    tools.extend(get_crud_tools())
    tools.extend(get_metadata_tools())
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls by routing to appropriate tool modules."""
    client = get_client()

    # Query tools
    if name in ["soql_query", "search_records", "get_record"]:
        return await handle_query_tools(name, arguments, client)

    # CRUD tools
    elif name in ["create_record", "update_record", "delete_record"]:
        return await handle_crud_tools(name, arguments, client)

    # Metadata tools
    elif name in ["describe_object_definition", "list_avail_objects"]:
        return await handle_metadata_tools(name, arguments, client)

    else:
        logger.error(f"Unknown tool: {name}")
        return [types.TextContent(
            type="text",
            text=f"Error: Unknown tool '{name}'"
        )]


async def run():
    """Main entry point for the MCP server."""
    logger.info("Starting Salesforce MCP Server...")

    # Test connection on startup
    try:
        client = get_client()
        logger.info("Salesforce connection established successfully")
    except Exception as e:
        logger.error(f"Failed to establish Salesforce connection: {e}")
        logger.error("Please check your environment variables and Salesforce configuration")
        return

    # Run the MCP server
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="salesforce-lite",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    """Main entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
