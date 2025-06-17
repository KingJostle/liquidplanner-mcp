"""
Exception classes for LiquidPlanner MCP Server
Comprehensive error handling with structured error information
"""

from typing import Any, Dict, Optional, List


class LiquidPlannerMCPError(Exception):
    """Base exception for all LiquidPlanner MCP errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        result = {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }
        
        if self.cause:
            result["cause"] = str(self.cause)
        
        return result
    
    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [f"{self.error_code}: {self.message}"]
        
        if self.details:
            parts.append(f"Details: {self.details}")
        
        if self.cause:
            parts.append(f"Caused by: {self.cause}")
        
        return " | ".join(parts)


class LiquidPlannerAPIError(LiquidPlannerMCPError):
    """Exception for LiquidPlanner API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.status_code = status_code
        self.response_data = response_data or {}
        self.request_data = request_data or {}
        
        details = kwargs.get("details", {})
        details.update({
            "status_code": status_code,
            "response_data": response_data,
            "request_data": request_data,
        })
        
        super().__init__(message, details=details, **kwargs)


class LiquidPlannerAuthError(LiquidPlannerAPIError):
    """Exception for authentication and authorization errors."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="LIQUIDPLANNER_AUTH_ERROR", **kwargs)


class LiquidPlannerRateLimitError(LiquidPlannerAPIError):
    """Exception for rate limiting errors."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        self.retry_after = retry_after
        
        details = kwargs.get("details", {})
        details["retry_after"] = retry_after
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_RATE_LIMIT_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerNotFoundError(LiquidPlannerAPIError):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        **kwargs
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        details = kwargs.get("details", {})
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_NOT_FOUND_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerValidationError(LiquidPlannerMCPError):
    """Exception for data validation errors."""
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, List[str]]] = None,
        validation_context: Optional[str] = None,
        **kwargs
    ):
        self.field_errors = field_errors or {}
        self.validation_context = validation_context
        
        details = kwargs.get("details", {})
        details.update({
            "field_errors": field_errors,
            "validation_context": validation_context,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_VALIDATION_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerConfigError(LiquidPlannerMCPError):
    """Exception for configuration errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None,
        **kwargs
    ):
        self.config_key = config_key
        self.config_value = config_value
        
        details = kwargs.get("details", {})
        details.update({
            "config_key": config_key,
            "config_value": config_value,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_CONFIG_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerTimeoutError(LiquidPlannerAPIError):
    """Exception for request timeout errors."""
    
    def __init__(
        self,
        message: str = "Request timed out",
        timeout_duration: Optional[float] = None,
        **kwargs
    ):
        self.timeout_duration = timeout_duration
        
        details = kwargs.get("details", {})
        details["timeout_duration"] = timeout_duration
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_TIMEOUT_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerConnectionError(LiquidPlannerAPIError):
    """Exception for connection errors."""
    
    def __init__(
        self,
        message: str = "Connection failed",
        endpoint: Optional[str] = None,
        **kwargs
    ):
        self.endpoint = endpoint
        
        details = kwargs.get("details", {})
        details["endpoint"] = endpoint
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_CONNECTION_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerCustomFieldError(LiquidPlannerMCPError):
    """Exception for custom field related errors."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_id: Optional[int] = None,
        field_type: Optional[str] = None,
        item_type: Optional[str] = None,
        **kwargs
    ):
        self.field_name = field_name
        self.field_id = field_id
        self.field_type = field_type
        self.item_type = item_type
        
        details = kwargs.get("details", {})
        details.update({
            "field_name": field_name,
            "field_id": field_id,
            "field_type": field_type,
            "item_type": item_type,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_CUSTOM_FIELD_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerTimeEntryError(LiquidPlannerMCPError):
    """Exception for time entry related errors."""
    
    def __init__(
        self,
        message: str,
        task_id: Optional[int] = None,
        person_id: Optional[int] = None,
        work_date: Optional[str] = None,
        **kwargs
    ):
        self.task_id = task_id
        self.person_id = person_id
        self.work_date = work_date
        
        details = kwargs.get("details", {})
        details.update({
            "task_id": task_id,
            "person_id": person_id,
            "work_date": work_date,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_TIME_ENTRY_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerBulkOperationError(LiquidPlannerMCPError):
    """Exception for bulk operation errors."""
    
    def __init__(
        self,
        message: str,
        operation_type: Optional[str] = None,
        failed_items: Optional[List[Dict[str, Any]]] = None,
        successful_items: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        self.operation_type = operation_type
        self.failed_items = failed_items or []
        self.successful_items = successful_items or []
        
        details = kwargs.get("details", {})
        details.update({
            "operation_type": operation_type,
            "failed_count": len(self.failed_items),
            "successful_count": len(self.successful_items),
            "failed_items": failed_items,
            "successful_items": successful_items,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_BULK_OPERATION_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerCacheError(LiquidPlannerMCPError):
    """Exception for cache-related errors."""
    
    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        cache_operation: Optional[str] = None,
        **kwargs
    ):
        self.cache_key = cache_key
        self.cache_operation = cache_operation
        
        details = kwargs.get("details", {})
        details.update({
            "cache_key": cache_key,
            "cache_operation": cache_operation,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_CACHE_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerCSVError(LiquidPlannerMCPError):
    """Exception for CSV processing errors."""
    
    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        column_name: Optional[str] = None,
        csv_data_sample: Optional[str] = None,
        **kwargs
    ):
        self.line_number = line_number
        self.column_name = column_name
        self.csv_data_sample = csv_data_sample
        
        details = kwargs.get("details", {})
        details.update({
            "line_number": line_number,
            "column_name": column_name,
            "csv_data_sample": csv_data_sample,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_CSV_ERROR",
            details=details,
            **kwargs
        )


class LiquidPlannerDeduplicationError(LiquidPlannerMCPError):
    """Exception for deduplication process errors."""
    
    def __init__(
        self,
        message: str,
        duplicate_entries: Optional[List[Dict[str, Any]]] = None,
        deduplication_rules: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.duplicate_entries = duplicate_entries or []
        self.deduplication_rules = deduplication_rules or {}
        
        details = kwargs.get("details", {})
        details.update({
            "duplicate_count": len(self.duplicate_entries),
            "duplicate_entries": duplicate_entries,
            "deduplication_rules": deduplication_rules,
        })
        
        super().__init__(
            message,
            error_code="LIQUIDPLANNER_DEDUPLICATION_ERROR",
            details=details,
            **kwargs
        )


def handle_api_exception(response_status: int, response_data: Dict[str, Any], **kwargs) -> LiquidPlannerAPIError:
    """
    Factory function to create appropriate API exception based on response status.
    
    Args:
        response_status: HTTP response status code
        response_data: Response data from API
        **kwargs: Additional arguments for exception
    
    Returns:
        Appropriate LiquidPlannerAPIError subclass
    """
    
    error_message = "API request failed"
    
    # Extract error message from response if available
    if isinstance(response_data, dict):
        if "errors" in response_data:
            if isinstance(response_data["errors"], list):
                error_message = "; ".join(response_data["errors"])
            else:
                error_message = str(response_data["errors"])
        elif "error" in response_data:
            error_message = str(response_data["error"])
        elif "message" in response_data:
            error_message = str(response_data["message"])
    
    # Create appropriate exception based on status code
    if response_status == 401:
        return LiquidPlannerAuthError(
            f"Authentication failed: {error_message}",
            status_code=response_status,
            response_data=response_data,
            **kwargs
        )
    elif response_status == 403:
        return LiquidPlannerAuthError(
            f"Access forbidden: {error_message}",
            status_code=response_status,
            response_data=response_data,
            **kwargs
        )
    elif response_status == 404:
        return LiquidPlannerNotFoundError(
            f"Resource not found: {error_message}",
            status_code=response_status,
            response_data=response_data,
            **kwargs
        )
    elif response_status == 429:
        retry_after = None
        if "retry_after" in response_data:
            retry_after = response_data["retry_after"]
        
        return LiquidPlannerRateLimitError(
            f"Rate limit exceeded: {error_message}",
            status_code=response_status,
            response_data=response_data,
            retry_after=retry_after,
            **kwargs
        )
    elif 400 <= response_status < 500:
        return LiquidPlannerValidationError(
            f"Client error: {error_message}",
            status_code=response_status,
            response_data=response_data,
            **kwargs
        )
    elif response_status >= 500:
        return LiquidPlannerAPIError(
            f"Server error: {error_message}",
            status_code=response_status,
            response_data=response_data,
            **kwargs
        )
    else:
        return LiquidPlannerAPIError(
            f"Unexpected response: {error_message}",
            status_code=response_status,
            response_data=response_data,
            **kwargs
        )
