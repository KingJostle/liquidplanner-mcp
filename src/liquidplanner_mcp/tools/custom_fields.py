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
            item_type: Type of item ('task', 'project', '
