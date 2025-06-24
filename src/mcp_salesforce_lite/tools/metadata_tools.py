"""Metadata tools for Salesforce MCP server."""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime

import mcp.types as types

logger = logging.getLogger(__name__)


def get_metadata_tools() -> List[types.Tool]:
    """Get metadata-related tools."""
    return [
        types.Tool(
            name="describe_object_definition",
            description="Get metadata and field information for a Salesforce object with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The Salesforce object type to describe",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of fields to return",
                        "default": 100,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of fields to skip for pagination",
                        "default": 0,
                    },
                },
                "required": ["object_type"],
            },
        ),
        types.Tool(
            name="list_avail_objects",
            description="List available Salesforce objects with limit and pagination (10-20 objects max)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of objects to return (max: 20)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of objects to skip for pagination",
                        "default": 0,
                        "minimum": 0,
                    },
                    "custom_only": {
                        "type": "boolean",
                        "description": "If true, return only custom objects",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
    ]


async def handle_metadata_tools(name: str, arguments: Dict[str, Any], client) -> List[types.TextContent]:
    """Handle metadata tool calls."""
    try:
        if name == "describe_object_definition":
            object_type = arguments.get("object_type")
            limit = arguments.get("limit", 100)
            offset = arguments.get("offset", 0)
            if not object_type:
                raise ValueError("Missing 'object_type' argument")

            result = client.describe_object(object_type)

            if result["success"]:
                # Apply pagination to fields
                fields = result["fields"]
                total_fields = len(fields)
                paginated_fields = fields[offset:offset + limit]

                response = {
                    "success": True,
                    "object_type": object_type,
                    "name": result["name"],
                    "label": result["label"],
                    "labelPlural": result["labelPlural"],
                    "createable": result["createable"],
                    "updateable": result["updateable"],
                    "deletable": result["deletable"],
                    "queryable": result["queryable"],
                    "fields": paginated_fields,
                    "pagination": {
                        "total_fields": total_fields,
                        "limit": limit,
                        "offset": offset,
                        "returned_count": len(paginated_fields),
                        "has_more": offset + limit < total_fields
                    },
                    "described_at": datetime.now().isoformat()
                }
            else:
                response = {
                    "success": False,
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown"),
                    "object_type": object_type
                }

            return [types.TextContent(
                type="text",
                text=f"Object Description:\n{json.dumps(response, indent=2)}"
            )]

        elif name == "list_avail_objects":
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)
            custom_only = arguments.get("custom_only", False)

            # Enforce maximum limit
            if limit > 20:
                limit = 20
            elif limit < 1:
                limit = 1

            result = client.list_objects()

            if result["success"]:
                objects = result["objects"]

                # Filter custom objects if requested
                if custom_only:
                    objects = [obj for obj in objects if obj.get("custom", False)]

                # Apply pagination
                total_objects = len(objects)
                paginated_objects = objects[offset:offset + limit]

                response = {
                    "success": True,
                    "objects": paginated_objects,
                    "pagination": {
                        "total_objects": total_objects,
                        "limit": limit,
                        "offset": offset,
                        "returned_count": len(paginated_objects),
                        "has_more": offset + limit < total_objects,
                        "custom_only": custom_only
                    },
                    "listed_at": datetime.now().isoformat()
                }
            else:
                response = {
                    "success": False,
                    "error": result["error"],
                    "error_type": result.get("error_type", "Unknown")
                }

            return [types.TextContent(
                type="text",
                text=f"Available Objects:\n{json.dumps(response, indent=2)}"
            )]

        else:
            raise ValueError(f"Unknown metadata tool: {name}")

    except Exception as e:
        logger.error(f"Error in metadata tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]