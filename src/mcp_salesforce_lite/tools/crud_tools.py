"""CRUD tools for Salesforce MCP server."""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime

import mcp.types as types

logger = logging.getLogger(__name__)


def get_crud_tools() -> List[types.Tool]:
    """Get CRUD-related tools."""
    return [
        types.Tool(
            name="create_record",
            description="Create a new Salesforce record",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The Salesforce object type (e.g., 'Account', 'Contact')",
                    },
                    "record_data": {
                        "type": "object",
                        "description": "Dictionary containing the field values for the new record",
                        "additionalProperties": True,
                    },
                },
                "required": ["object_type", "record_data"],
            },
        ),
        types.Tool(
            name="update_record",
            description="Update an existing Salesforce record",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The Salesforce object type (e.g., 'Account', 'Contact')",
                    },
                    "record_id": {
                        "type": "string",
                        "description": "The ID of the record to update",
                    },
                    "update_data": {
                        "type": "object",
                        "description": "Dictionary containing the field values to update",
                        "additionalProperties": True,
                    },
                },
                "required": ["object_type", "record_id", "update_data"],
            },
        ),
        types.Tool(
            name="delete_record",
            description="Delete a Salesforce record",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The Salesforce object type (e.g., 'Account', 'Contact')",
                    },
                    "record_id": {
                        "type": "string",
                        "description": "The ID of the record to delete",
                    },
                },
                "required": ["object_type", "record_id"],
            },
        ),
    ]


async def handle_crud_tools(name: str, arguments: Dict[str, Any], client) -> List[types.TextContent]:
    """Handle CRUD tool calls."""
    try:
        if name == "create_record":
            object_type = arguments.get("object_type")
            record_data = arguments.get("record_data")
            if not object_type or not record_data:
                raise ValueError("Missing 'object_type' or 'record_data' argument")

            result = client.create_record(object_type, record_data)

            if result["success"]:
                response = {
                    "success": True,
                    "id": result["id"],
                    "created": result["created"],
                    "object_type": object_type,
                    "created_data": record_data,
                    "created_at": datetime.now().isoformat()
                }
            else:
                response = {
                    "success": False,
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown"),
                    "object_type": object_type,
                    "attempted_data": record_data
                }

            return [types.TextContent(
                type="text",
                text=f"Record Creation Result:\n{json.dumps(response, indent=2)}"
            )]

        elif name == "update_record":
            object_type = arguments.get("object_type")
            record_id = arguments.get("record_id")
            update_data = arguments.get("update_data")
            if not object_type or not record_id or not update_data:
                raise ValueError("Missing 'object_type', 'record_id', or 'update_data' argument")

            result = client.update_record(object_type, record_id, update_data)

            if result["success"]:
                response = {
                    "success": True,
                    "id": record_id,
                    "updated": result["updated"],
                    "object_type": object_type,
                    "updated_data": update_data,
                    "updated_at": datetime.now().isoformat()
                }
            else:
                response = {
                    "success": False,
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown"),
                    "object_type": object_type,
                    "record_id": record_id,
                    "attempted_data": update_data
                }

            return [types.TextContent(
                type="text",
                text=f"Record Update Result:\n{json.dumps(response, indent=2)}"
            )]

        elif name == "delete_record":
            object_type = arguments.get("object_type")
            record_id = arguments.get("record_id")
            if not object_type or not record_id:
                raise ValueError("Missing 'object_type' or 'record_id' argument")

            result = client.delete_record(object_type, record_id)

            if result["success"]:
                response = {
                    "success": True,
                    "id": record_id,
                    "deleted": result["deleted"],
                    "object_type": object_type,
                    "deleted_at": datetime.now().isoformat()
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
                text=f"Record Deletion Result:\n{json.dumps(response, indent=2)}"
            )]

        else:
            raise ValueError(f"Unknown CRUD tool: {name}")

    except Exception as e:
        logger.error(f"Error in CRUD tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]