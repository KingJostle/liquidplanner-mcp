"""
Data models for LiquidPlanner MCP Server
Pydantic models for API responses, requests, and internal data structures
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator


# Base Models
class BaseResponse(BaseModel):
    """Base response model."""
    success: bool
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseResponse):
    """Success response model."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = False
    error_code: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    status_code: int
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    headers: Optional[Dict[str, str]] = None
    cached: bool = False


class ToolCallResult(BaseModel):
    """Result of an MCP tool call."""
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


# LiquidPlanner Entity Models
class LiquidPlannerUser(BaseModel):
    """LiquidPlanner user/member model."""
    id: int
    user_name: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LiquidPlannerWorkspace(BaseModel):
    """LiquidPlanner workspace model."""
    id: int
    name: str
    company_name: Optional[str] = None
    timezone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LiquidPlannerCustomField(BaseModel):
    """LiquidPlanner custom field definition model."""
    id: int
    name: str
    field_type: str  # text, number, date, picklist, checkbox, etc.
    is_required: bool = False
    is_enabled: bool = True
    default_value: Optional[Any] = None
    picklist_values: Optional[List[str]] = None
    item_type: str  # task, project, folder, package
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LiquidPlannerTask(BaseModel):
    """LiquidPlanner task model."""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_type: Optional[str] = None  # project, folder, package
    is_done: bool = False
    done_on: Optional[date] = None
    priority: Optional[int] = None
    promise_to_start_on: Optional[date] = None
    promise_to_finish_on: Optional[date] = None
    earliest_start: Optional[date] = None
    earliest_finish: Optional[date] = None
    expected_start: Optional[date] = None
    expected_finish: Optional[date] = None
    low_effort_remaining: Optional[float] = None
    high_effort_remaining: Optional[float] = None
    work: Optional[float] = None
    assignments: Optional[List[Dict[str, Any]]] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


class LiquidPlannerProject(BaseModel):
    """LiquidPlanner project model."""
    id: int
    name: str
    description: Optional[str] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    is_done: bool = False
    done_on: Optional[date] = None
    parent_id: Optional[int] = None
    parent_type: Optional[str] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


class LiquidPlannerTimeEntry(BaseModel):
    """LiquidPlanner time entry model."""
    id: int
    task_id: int
    task_name: Optional[str] = None
    person_id: int
    person_name: Optional[str] = None
    work: float  # Hours
    work_date: date
    note: Optional[str] = None
    activity_id: Optional[int] = None
    activity_name: Optional[str] = None
    is_billable: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LiquidPlannerClient(BaseModel):
    """LiquidPlanner client model."""
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LiquidPlannerActivity(BaseModel):
    """LiquidPlanner activity model."""
    id: int
    name: str
    description: Optional[str] = None
    is_billable: bool = True
    is_active: bool = True


class LiquidPlannerFolder(BaseModel):
    """LiquidPlanner folder model."""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LiquidPlannerPackage(BaseModel):
    """LiquidPlanner package model."""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_done: bool = False
    done_on: Optional[date] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Request Models
class CreateTaskRequest(BaseModel):
    """Request model for creating tasks."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: int = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=10000)
    assignments: Optional[List[Dict[str, Any]]] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = None


class UpdateTaskRequest(BaseModel):
    """Request model for updating tasks."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    is_done: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    promise_to_start_on: Optional[date] = None
    promise_to_finish_on: Optional[date] = None
    assignments: Optional[List[Dict[str, Any]]] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class CreateProjectRequest(BaseModel):
    """Request model for creating projects."""
    name: str = Field(..., min_length=1, max_length=255)
    client_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=10000)
    custom_field_values: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class CreateTimeEntryRequest(BaseModel):
    """Request model for creating time entries."""
    task_id: int = Field(..., gt=0)
    work: float = Field(..., gt=0, le=24)  # Max 24 hours per entry
    work_date: date
    person_id: Optional[int] = Field(None, gt=0)
    note: Optional[str] = Field(None, max_length=1000)
    activity_id: Optional[int] = Field(None, gt=0)
    is_billable: bool = True

    @validator("work_date")
    def validate_work_date(cls, v):
        """Validate work date is not in the future."""
        if v > date.today():
            raise ValueError("Work date cannot be in the future")
        return v


class BulkTimeEntryRequest(BaseModel):
    """Request model for bulk time entry operations."""
    entries: List[CreateTimeEntryRequest]
    deduplication_rules: Optional[Dict[str, Any]] = None
    blacklisted_tasks: Optional[List[int]] = None
    validation_only: bool = False


class CustomFieldUpdateRequest(BaseModel):
    """Request model for custom field updates."""
    item_id: int = Field(..., gt=0)
    item_type: Literal["task", "project", "folder", "package"]
    custom_fields: Dict[str, Any] = Field(..., min_items=1)


class FilterRequest(BaseModel):
    """Request model for filtering operations."""
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = Field(None, gt=0, le=1000)
    offset: Optional[int] = Field(None, ge=0)
    order_by: Optional[str] = None
    include_done: bool = False
    include_custom_fields: bool = True


class ReportRequest(BaseModel):
    """Request model for reports."""
    start_date: date
    end_date: date
    filters: Optional[Dict[str, Any]] = None
    format: Literal["json", "csv"] = "json"
    include_details: bool = True

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations."""
    operation_type: Literal["create", "update", "delete"]
    items: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    validation_only: bool = False
    batch_size: Optional[int] = Field(None, gt=0, le=100)


# Response Models
class CustomFieldResponse(BaseModel):
    """Response model for custom field operations."""
    custom_fields: List[LiquidPlannerCustomField]
    item_type: str
    total_count: int


class TimeEntryResponse(BaseModel):
    """Response model for time entry operations."""
    time_entries: List[LiquidPlannerTimeEntry]
    total_count: int
    total_hours: float


class TaskResponse(BaseModel):
    """Response model for task operations."""
    tasks: List[LiquidPlannerTask]
    total_count: int


class ProjectResponse(BaseModel):
    """Response model for project operations."""
    projects: List[LiquidPlannerProject]
    total_count: int


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    operation_type: str
    total_items: int
    successful_items: int
    failed_items: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: Optional[float] = None


class ReportResponse(BaseModel):
    """Response model for reports."""
    report_type: str
    start_date: date
    end_date: date
    data: Union[Dict[str, Any], str]  # Dict for JSON, str for CSV
    format: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_records: Optional[int] = None


class HealthCheckResponse(BaseModel):
    """Response model for health checks."""
    status: Literal["healthy", "unhealthy"]
    server: str
    version: str
    liquidplanner_api: Literal["connected", "disconnected"]
    workspace_id: int
    account: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None


# CSV Import/Export Models
class CSVImportResult(BaseModel):
    """Result of CSV import operation."""
    total_rows: int
    successful_rows: int
    failed_rows: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    imported_items: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_items: List[Dict[str, Any]] = Field(default_factory=list)


class CSVExportResult(BaseModel):
    """Result of CSV export operation."""
    data_type: str
    csv_data: str
    total_records: int
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    filters_applied: Optional[Dict[str, Any]] = None


# Deduplication Models
class DeduplicationRule(BaseModel):
    """Deduplication rule configuration."""
    enabled: bool = True
    precedence_users: List[str] = Field(default_factory=list)
    skip_duplicates: bool = True
    merge_duplicates: bool = False
    duplicate_threshold_hours: float = 0.01  # Consider times within 0.01 hours as duplicates


class DeduplicationResult(BaseModel):
    """Result of deduplication operation."""
    original_count: int
    deduplicated_count: int
    duplicates_found: int
    duplicates_merged: int
    duplicates_skipped: int
    duplicate_entries: List[Dict[str, Any]] = Field(default_factory=list)


# Cache Models
class CacheEntry(BaseModel):
    """Cache entry model."""
    key: str
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    hit_count: int = 0


class CacheStats(BaseModel):
    """Cache statistics model."""
    total_keys: int
    hit_rate: float
    miss_rate: float
    total_hits: int
    total_misses: int
    cache_size_mb: float
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None
