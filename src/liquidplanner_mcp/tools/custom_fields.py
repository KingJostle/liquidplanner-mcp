"""
Custom Fields Manager for LiquidPlanner MCP Server
Handles discovery, validation, and manipulation of custom fields
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
import structlog

from ..client import LiquidPlannerClient
from ..exceptions import (
    LiquidPlannerCustomFieldError,
    LiquidPlannerValidationError,
    LiquidPlannerNotFoundError,
)
from ..models import (
    LiquidPlannerCustomField,
    CustomFieldResponse,
    CustomFieldUpdateRequest,
)

logger = structlog.get_logger(__name__)


class CustomFieldsManager:
    """
    Manages LiquidPlanner custom fields operations.
    
    Features:
    - Custom field discovery and caching
    - Field name and ID resolution
    - Type validation and conversion
    - Bulk custom field updates
    - Picklist value validation
    """
    
    def __init__(self, client: LiquidPlannerClient):
        self.client = client
        self._field_cache: Dict[str, List[LiquidPlannerCustomField]] = {}
        self._field_mappings: Dict[str, Dict[Union[str, int], LiquidPlannerCustomField]] = {}
        
        logger.info("Custom Fields Manager initialized")
    
    async def list_custom_fields(self, item_type: str) -> List[Dict[str, Any]]:
        """
        List all available custom fields for a specific item type.
        
        Args:
            item_type: Type of item ('task', 'project', 'folder', 'package')
            
        Returns:
            List of custom field definitions
        """
        try:
            logger.info("Listing custom fields", item_type=item_type)
            
            # Validate item type
            self._validate_item_type(item_type)
            
            # Get custom fields from cache or API
            custom_fields = await self._get_custom_fields(item_type)
            
            # Convert to response format
            field_dicts = [field.dict() for field in custom_fields]
            
            logger.info("Listed custom fields successfully", 
                       item_type=item_type, 
                       count=len(field_dicts))
            
            return field_dicts
            
        except Exception as e:
            logger.error("Failed to list custom fields", 
                        item_type=item_type, 
                        error=str(e))
            raise LiquidPlannerCustomFieldError(
                f"Failed to list custom fields for {item_type}: {e}",
                item_type=item_type
            ) from e
    
    async def get_custom_field_values(self, item_id: int, item_type: str) -> Dict[str, Any]:
        """
        Get all custom field values for a specific item.
        
        Args:
            item_id: ID of the item
            item_type: Type of item
            
        Returns:
            Dictionary of custom field values (field name -> value)
        """
        try:
            logger.info("Getting custom field values", 
                       item_id=item_id, 
                       item_type=item_type)
            
            # Validate item type
            self._validate_item_type(item_type)
            
            # Get item custom field values from API
            custom_field_values = await self.client.get_item_custom_fields(item_type, item_id)
            
            # Get custom field definitions for name mapping
            custom_fields = await self._get_custom_fields(item_type)
            field_mapping = {field.id: field for field in custom_fields}
            
            # Convert field IDs to names where possible
            result = {}
            for field_id_str, value in custom_field_values.items():
                try:
                    field_id = int(field_id_str)
                    if field_id in field_mapping:
                        field_name = field_mapping[field_id].name
                        result[field_name] = value
                        # Also include by ID for backwards compatibility
                        result[f"custom_field_{field_id}"] = value
                    else:
                        # Unknown field, include by ID
                        result[f"custom_field_{field_id}"] = value
                except ValueError:
                    # Non-numeric field ID, include as-is
                    result[field_id_str] = value
            
            logger.info("Retrieved custom field values successfully", 
                       item_id=item_id, 
                       item_type=item_type, 
                       field_count=len(result))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get custom field values", 
                        item_id=item_id, 
                        item_type=item_type, 
                        error=str(e))
            raise LiquidPlannerCustomFieldError(
                f"Failed to get custom field values for {item_type} {item_id}: {e}",
                item_type=item_type
            ) from e
    
    async def update_custom_fields(
        self, 
        item_id: int, 
        item_type: str, 
        custom_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update custom field values for an item.
        Supports both field names and field IDs.
        
        Args:
            item_id: ID of the item to update
            item_type: Type of item
            custom_fields: Dictionary of field name/ID -> value
            
        Returns:
            Updated item with custom field values
        """
        try:
            logger.info("Updating custom fields", 
                       item_id=item_id, 
                       item_type=item_type, 
                       field_count=len(custom_fields))
            
            # Validate item type
            self._validate_item_type(item_type)
            
            # Get custom field definitions
            field_definitions = await self._get_custom_fields(item_type)
            
            # Build mapping for name/ID resolution
            await self._build_field_mappings(item_type)
            field_mapping = self._field_mappings[item_type]
            
            # Convert field names to IDs and validate values
            processed_fields = {}
            validation_errors = {}
            
            for field_identifier, value in custom_fields.items():
                try:
                    # Resolve field definition
                    field_def = await self._resolve_field_definition(
                        field_identifier, item_type, field_mapping
                    )
                    
                    if not field_def:
                        validation_errors[field_identifier] = f"Custom field not found: {field_identifier}"
                        continue
                    
                    # Validate and convert value
                    validated_value = await self._validate_and_convert_value(
                        value, field_def
                    )
                    
                    # Use field ID for API call
                    processed_fields[str(field_def.id)] = validated_value
                    
                except Exception as e:
                    validation_errors[field_identifier] = str(e)
            
            # Check for validation errors
            if validation_errors:
                raise LiquidPlannerValidationError(
                    "Custom field validation failed",
                    field_errors=validation_errors,
                    validation_context="custom_field_update"
                )
            
            # Update custom fields via API
            updated_item = await self.client.update_item_custom_fields(
                item_type, item_id, processed_fields
            )
            
            logger.info("Updated custom fields successfully", 
                       item_id=item_id, 
                       item_type=item_type, 
                       updated_fields=list(processed_fields.keys()))
            
            return updated_item
            
        except Exception as e:
            logger.error("Failed to update custom fields", 
                        item_id=item_id, 
                        item_type=item_type, 
                        error=str(e))
            raise LiquidPlannerCustomFieldError(
                f"Failed to update custom fields for {item_type} {item_id}: {e}",
                item_type=item_type
            ) from e
    
    async def bulk_update_custom_fields(
        self, 
        updates: List[CustomFieldUpdateRequest]
    ) -> Dict[str, Any]:
        """
        Perform bulk custom field updates.
        
        Args:
            updates: List of custom field update requests
            
        Returns:
            Bulk operation results
        """
        try:
            logger.info("Starting bulk custom field updates", update_count=len(updates))
            
            results = []
            errors = []
            
            # Process updates in batches to avoid overwhelming the API
            batch_size = 10
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                batch_tasks = []
                
                for update in batch:
                    task = self._process_single_update(update)
                    batch_tasks.append(task)
                
                # Execute batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for j, result in enumerate(batch_results):
                    update_request = batch[j]
                    if isinstance(result, Exception):
                        errors.append({
                            "item_id": update_request.item_id,
                            "item_type": update_request.item_type,
                            "error": str(result)
                        })
                    else:
                        results.append({
                            "item_id": update_request.item_id,
                            "item_type": update_request.item_type,
                            "result": result
                        })
            
            logger.info("Completed bulk custom field updates", 
                       total=len(updates), 
                       successful=len(results), 
                       failed=len(errors))
            
            return {
                "total_updates": len(updates),
                "successful_updates": len(results),
                "failed_updates": len(errors),
                "results": results,
                "errors": errors
            }
            
        except Exception as e:
            logger.error("Bulk custom field update failed", error=str(e))
            raise LiquidPlannerCustomFieldError(
                f"Bulk custom field update failed: {e}"
            ) from e
    
    async def discover_custom_fields(self, item_type: str) -> Dict[str, Any]:
        """
        Discover and analyze custom fields for an item type.
        
        Args:
            item_type: Type of item to analyze
            
        Returns:
            Detailed custom field analysis
        """
        try:
            logger.info("Discovering custom fields", item_type=item_type)
            
            # Get custom fields
            custom_fields = await self._get_custom_fields(item_type)
            
            # Analyze field types and usage
            analysis = {
                "item_type": item_type,
                "total_fields": len(custom_fields),
                "field_types": {},
                "required_fields": [],
                "picklist_fields": [],
                "fields": []
            }
            
            for field in custom_fields:
                # Count field types
                field_type = field.field_type
                analysis["field_types"][field_type] = analysis["field_types"].get(field_type, 0) + 1
                
                # Track required fields
                if field.is_required:
                    analysis["required_fields"].append({
                        "id": field.id,
                        "name": field.name,
                        "type": field.field_type
                    })
                
                # Track picklist fields
                if field.field_type == "picklist" and field.picklist_values:
                    analysis["picklist_fields"].append({
                        "id": field.id,
                        "name": field.name,
                        "values": field.picklist_values
                    })
                
                # Add to detailed fields list
                analysis["fields"].append({
                    "id": field.id,
                    "name": field.name,
                    "type": field.field_type,
                    "required": field.is_required,
                    "enabled": field.is_enabled,
                    "default_value": field.default_value,
                    "picklist_values": field.picklist_values
                })
            
            logger.info("Custom field discovery completed", 
                       item_type=item_type, 
                       total_fields=analysis["total_fields"])
            
            return analysis
            
        except Exception as e:
            logger.error("Custom field discovery failed", 
                        item_type=item_type, 
                        error=str(e))
            raise LiquidPlannerCustomFieldError(
                f"Custom field discovery failed for {item_type}: {e}",
                item_type=item_type
            ) from e
    
    # Private helper methods
    
    def _validate_item_type(self, item_type: str) -> None:
        """Validate that item_type is supported."""
        valid_types = ["task", "project", "folder", "package"]
        if item_type not in valid_types:
            raise LiquidPlannerValidationError(
                f"Invalid item type: {item_type}. Must be one of: {valid_types}",
                validation_context="item_type"
            )
    
    async def _get_custom_fields(self, item_type: str) -> List[LiquidPlannerCustomField]:
        """Get custom fields from cache or API."""
        # Check cache first
        if item_type in self._field_cache:
            logger.debug("Using cached custom fields", item_type=item_type)
            return self._field_cache[item_type]
        
        # Fetch from API
        logger.debug("Fetching custom fields from API", item_type=item_type)
        field_data = await self.client.get_custom_fields(item_type)
        
        # Convert to Pydantic models
        custom_fields = []
        for field_dict in field_data:
            try:
                # Ensure required fields are present
                field_dict.setdefault("item_type", item_type)
                field_dict.setdefault("is_required", False)
                field_dict.setdefault("is_enabled", True)
                
                field = LiquidPlannerCustomField(**field_dict)
                custom_fields.append(field)
            except Exception as e:
                logger.warning("Failed to parse custom field", 
                             field_data=field_dict, 
                             error=str(e))
        
        # Cache the results
        self._field_cache[item_type] = custom_fields
        
        return custom_fields
    
    async def _build_field_mappings(self, item_type: str) -> None:
        """Build field name and ID mappings."""
        if item_type in self._field_mappings:
            return
        
        custom_fields = await self._get_custom_fields(item_type)
        
        mapping = {}
        for field in custom_fields:
            # Map by name (case-insensitive)
            mapping[field.name.lower()] = field
            mapping[field.name] = field
            
            # Map by ID
            mapping[field.id] = field
            mapping[str(field.id)] = field
            
            # Map by formatted ID
            mapping[f"custom_field_{field.id}"] = field
        
        self._field_mappings[item_type] = mapping
    
    async def _resolve_field_definition(
        self, 
        field_identifier: Union[str, int], 
        item_type: str,
        field_mapping: Dict[Union[str, int], LiquidPlannerCustomField]
    ) -> Optional[LiquidPlannerCustomField]:
        """Resolve field definition from name or ID."""
        
        # Try direct lookup
        if field_identifier in field_mapping:
            return field_mapping[field_identifier]
        
        # Try case-insensitive name lookup
        if isinstance(field_identifier, str):
            lower_identifier = field_identifier.lower()
            if lower_identifier in field_mapping:
                return field_mapping[lower_identifier]
        
        # Try numeric ID lookup
        if isinstance(field_identifier, str) and field_identifier.isdigit():
            field_id = int(field_identifier)
            if field_id in field_mapping:
                return field_mapping[field_id]
        
        return None
    
    async def _validate_and_convert_value(
        self, 
        value: Any, 
        field_def: LiquidPlannerCustomField
    ) -> Any:
        """Validate and convert value according to field type."""
        
        if value is None:
            if field_def.is_required:
                raise LiquidPlannerValidationError(
                    f"Required field '{field_def.name}' cannot be null"
                )
            return None
        
        field_type = field_def.field_type.lower()
        
        try:
            if field_type == "text":
                return str(value)
            
            elif field_type == "number":
                if isinstance(value, (int, float)):
                    return value
                return float(value)
            
            elif field_type == "date":
                if isinstance(value, str):
                    # Try to parse date string
                    from datetime import datetime
                    try:
                        # Try ISO format first
                        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        return parsed.date().isoformat()
                    except ValueError:
                        # Try common date formats
                        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                            try:
                                parsed = datetime.strptime(value, fmt)
                                return parsed.date().isoformat()
                            except ValueError:
                                continue
                        raise ValueError(f"Invalid date format: {value}")
                return str(value)
            
            elif field_type == "checkbox":
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("true", "yes", "1", "on")
                return bool(value)
            
            elif field_type == "picklist":
                str_value = str(value)
                if field_def.picklist_values and str_value not in field_def.picklist_values:
                    raise LiquidPlannerValidationError(
                        f"Invalid picklist value '{str_value}' for field '{field_def.name}'. "
                        f"Valid values: {field_def.picklist_values}"
                    )
                return str_value
            
            else:
                # Unknown field type, return as string
                logger.warning("Unknown field type, converting to string", 
                             field_type=field_type, 
                             field_name=field_def.name)
                return str(value)
                
        except Exception as e:
            raise LiquidPlannerValidationError(
                f"Invalid value '{value}' for {field_type} field '{field_def.name}': {e}"
            ) from e
    
    async def _process_single_update(self, update: CustomFieldUpdateRequest) -> Dict[str, Any]:
        """Process a single custom field update."""
        return await self.update_custom_fields(
            update.item_id,
            update.item_type,
            update.custom_fields
        )
    
    def clear_cache(self, item_type: Optional[str] = None) -> None:
        """Clear custom field cache."""
        if item_type:
            self._field_cache.pop(item_type, None)
            self._field_mappings.pop(item_type, None)
            logger.info("Cleared custom field cache", item_type=item_type)
        else:
            self._field_cache.clear()
            self._field_mappings.clear()
            logger.info("Cleared all custom field caches")
