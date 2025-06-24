"""Salesforce client wrapper for MCP server."""

import os
import logging
from typing import Dict, List, Any, Optional
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceError


logger = logging.getLogger(__name__)


class SalesforceClient:
    """Salesforce client wrapper with authentication and API methods."""

    def __init__(self):
        self.sf: Optional[Salesforce] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Salesforce."""
        try:
            # Try token-based authentication first
            access_token = os.getenv('SALESFORCE_ACCESS_TOKEN')
            instance_url = os.getenv('SALESFORCE_INSTANCE_URL')

            if access_token and instance_url:
                self.sf = Salesforce(
                    instance_url=instance_url,
                    session_id=access_token
                )
                logger.info("Connected to Salesforce using access token")
                return

            # Fallback to username/password authentication
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'login')

            if username and password and security_token:
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    security_token=security_token,
                    domain=domain
                )
                logger.info("Connected to Salesforce using username/password")
                return

            raise ValueError("No valid Salesforce credentials found in environment variables")

        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            raise

    def query(self, soql: str) -> Dict[str, Any]:
        """Execute SOQL query."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            result = self.sf.query(soql)
            return {
                "success": True,
                "totalSize": result.get('totalSize', 0),
                "done": result.get('done', True),
                "records": result.get('records', [])
            }
        except SalesforceError as e:
            logger.error(f"SOQL query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def get_record(self, object_type: str, record_id: str) -> Dict[str, Any]:
        """Get a specific record by ID."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            sf_object = getattr(self.sf, object_type)
            record = sf_object.get(record_id)
            return {
                "success": True,
                "record": record
            }
        except SalesforceError as e:
            logger.error(f"Failed to get record {record_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def create_record(self, object_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            sf_object = getattr(self.sf, object_type)
            result = sf_object.create(data)
            return {
                "success": True,
                "id": result.get('id'),
                "created": result.get('success', True)
            }
        except SalesforceError as e:
            logger.error(f"Failed to create record: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def update_record(self, object_type: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            sf_object = getattr(self.sf, object_type)
            result = sf_object.update(record_id, data)
            return {
                "success": True,
                "updated": result == 204  # Salesforce returns 204 for successful updates
            }
        except SalesforceError as e:
            logger.error(f"Failed to update record {record_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def delete_record(self, object_type: str, record_id: str) -> Dict[str, Any]:
        """Delete a record."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            sf_object = getattr(self.sf, object_type)
            result = sf_object.delete(record_id)
            return {
                "success": True,
                "deleted": result == 204  # Salesforce returns 204 for successful deletes
            }
        except SalesforceError as e:
            logger.error(f"Failed to delete record {record_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def describe_object(self, object_type: str) -> Dict[str, Any]:
        """Get object metadata."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            sf_object = getattr(self.sf, object_type)
            description = sf_object.describe()

            # Extract key field information
            fields = []
            for field in description.get('fields', []):
                fields.append({
                    'name': field.get('name'),
                    'label': field.get('label'),
                    'type': field.get('type'),
                    'length': field.get('length'),
                    'required': not field.get('nillable', True),
                    'updateable': field.get('updateable', False),
                    'createable': field.get('createable', False),
                    'custom': field.get('custom', False)
                })

            return {
                "success": True,
                "name": description.get('name'),
                "label": description.get('label'),
                "labelPlural": description.get('labelPlural'),
                "createable": description.get('createable', False),
                "updateable": description.get('updateable', False),
                "deletable": description.get('deletable', False),
                "queryable": description.get('queryable', False),
                "fields": fields
            }
        except SalesforceError as e:
            logger.error(f"Failed to describe object {object_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def list_objects(self) -> Dict[str, Any]:
        """List all available Salesforce objects."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            global_describe = self.sf.describe()
            objects = []

            for obj in global_describe.get('sobjects', []):
                objects.append({
                    'name': obj.get('name'),
                    'label': obj.get('label'),
                    'labelPlural': obj.get('labelPlural'),
                    'custom': obj.get('custom', False),
                    'createable': obj.get('createable', False),
                    'updateable': obj.get('updateable', False),
                    'deletable': obj.get('deletable', False),
                    'queryable': obj.get('queryable', False)
                })

            return {
                "success": True,
                "totalSize": len(objects),
                "objects": objects
            }
        except SalesforceError as e:
            logger.error(f"Failed to list objects: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "SalesforceError"
            }

    def search_records(self, search_term: str, object_types: List[str], limit: int = 10) -> Dict[str, Any]:
        """Search for records across multiple objects."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        results = {}
        total_found = 0

        for obj_type in object_types:
            try:
                # Use SOQL with LIKE for simple search
                soql = f"SELECT Id, Name FROM {obj_type} WHERE Name LIKE '%{search_term}%' LIMIT {limit}"
                query_result = self.sf.query(soql)
                records = query_result.get('records', [])

                results[obj_type] = {
                    "records": records,
                    "count": len(records)
                }
                total_found += len(records)

            except Exception as e:
                logger.warning(f"Error searching in {obj_type}: {e}")
                results[obj_type] = {
                    "records": [],
                    "count": 0,
                    "error": str(e)
                }

        return {
            "success": True,
            "search_term": search_term,
            "total_found": total_found,
            "results": results
        }

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        if not self.sf:
            raise RuntimeError("Salesforce connection not established")

        try:
            # Query current user
            user_query = "SELECT Id, Name, Email, Username FROM User WHERE Id = UserInfo.getUserId() LIMIT 1"
            result = self.sf.query(user_query)

            if result.get('totalSize', 0) > 0:
                user_data = result['records'][0]
                return {
                    "success": True,
                    "user": user_data
                }
            else:
                return {
                    "success": False,
                    "error": "Could not retrieve user information"
                }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "RetrievalError"
            }
