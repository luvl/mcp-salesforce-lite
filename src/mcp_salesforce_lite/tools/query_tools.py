"""Query tools for Salesforce MCP server."""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime

import mcp.types as types

logger = logging.getLogger(__name__)


def get_query_tools() -> List[types.Tool]:
    """Get query-related tools."""
    return [
        types.Tool(
            name="soql_query",
            description="Execute a SOQL query against Salesforce",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SOQL query string to execute",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="search_records",
            description="Search for records across multiple Salesforce objects",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "The term to search for",
                    },
                    "object_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of object types to search in",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results per object type",
                        "default": 10,
                    },
                },
                "required": ["search_term", "object_types"],
            },
        ),
        types.Tool(
            name="get_record",
            description="Retrieve a specific Salesforce record by ID with limit and pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The Salesforce object type (e.g., 'Account', 'Contact')",
                    },
                    "record_id": {
                        "type": "string",
                        "description": "The record ID to retrieve",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                        "default": 1,
                    },
                },
                "required": ["object_type", "record_id"],
            },
        ),
    ]


async def handle_query_tools(name: str, arguments: Dict[str, Any], client) -> List[types.TextContent]:
    """Handle query tool calls."""
    try:
        if name == "soql_query":
            query = arguments.get("query")
            if not query:
                raise ValueError("Missing 'query' argument")

            result = client.query(query)

            if result["success"]:
                response = {
                    "success": True,
                    "total_size": result["totalSize"],
                    "done": result["done"],
                    "records": result["records"],
                    "query": query,
                    "executed_at": datetime.now().isoformat()
                }
            else:
                response = {
                    "success": False,
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown"),
                    "query": query
                }

            return [types.TextContent(
                type="text",
                text=f"SOQL Query Results:\n{json.dumps(response, indent=2)}"
            )]

        elif name == "search_records":
            search_term = arguments.get("search_term")
            object_types = arguments.get("object_types")
            limit = arguments.get("limit", 10)
            if not search_term or not object_types:
                raise ValueError("Missing 'search_term' or 'object_types' argument")

            result = client.search_records(search_term, object_types, limit)

            response = {
                "success": result["success"],
                "search_term": result["search_term"],
                "object_types": object_types,
                "total_found": result["total_found"],
                "results": result["results"],
                "searched_at": datetime.now().isoformat()
            }

            return [types.TextContent(
                type="text",
                text=f"Search Results:\n{json.dumps(response, indent=2)}"
            )]

        elif name == "get_record":
            object_type = arguments.get("object_type")
            record_id = arguments.get("record_id")
            limit = arguments.get("limit", 1)
            if not object_type or not record_id:
                raise ValueError("Missing 'object_type' or 'record_id' argument")

            result = client.get_record(object_type, record_id)

            if result["success"]:
                response = {
                    "success": True,
                    "record": result["record"],
                    "object_type": object_type,
                    "record_id": record_id,
                    "limit": limit,
                    "retrieved_at": datetime.now().isoformat()
                }
            else:
                response = {
                    "success": False,
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown"),
                    "object_type": object_type,
                    "record_id": record_id
                }

            return [types.TextContent(
                type="text",
                text=f"Record Retrieved:\n{json.dumps(response, indent=2)}"
            )]

        else:
            raise ValueError(f"Unknown query tool: {name}")

    except Exception as e:
        logger.error(f"Error in query tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]