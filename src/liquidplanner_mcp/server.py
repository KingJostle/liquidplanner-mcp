#!/usr/bin/env python3
"""
LiquidPlanner MCP Server - Core Implementation
Model Context Protocol server for LiquidPlanner integration with Claude AI
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from contextlib import asynccontextmanager

import structlog
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from pydantic import BaseModel, Field

from .client import LiquidPlannerClient
from .config import MCPConfig
from .tools import (
    CustomFieldsManager,
    TimeEntriesManager,
    TaskManager,
    ProjectManager,
    ReportsManager,
    BulkOperationsManager,
)
from .exceptions import LiquidPlannerMCPError
from .models import (
    ErrorResponse,
    SuccessResponse,
    ToolCallResult,
)


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class LiquidPlannerMCPServer:
    """
    Main LiquidPlanner MCP Server implementation.
    
    Provides comprehensive LiquidPlanner integration through MCP tools including:
    - Custom field management
    - Time entry operations  
    - Task management
    - Project operations
    - Reporting and analytics
    - Bulk operations
    """
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.app = FastMCP("LiquidPlanner MCP Server")
        self.client: Optional[LiquidPlannerClient] = None
        
        # Tool managers
        self.custom_fields: Optional[CustomFieldsManager] = None
        self.time_entries: Optional[TimeEntriesManager] = None
        self.tasks: Optional[TaskManager] = None
        self.projects: Optional[ProjectManager] = None
        self.reports: Optional[ReportsManager] = None
        self.bulk_ops: Optional[BulkOperationsManager] = None
        
        # Server state
        self._initialized = False
        self._shutdown = False
        
        logger.info("LiquidPlanner MCP Server initialized", config=config.model_dump(exclude_secrets=True))
    
    async def initialize(self) -> None:
        """Initialize the server and all components."""
        if self._initialized:
            return
            
        try:
            logger.info("Starting LiquidPlanner MCP Server initialization")
            
            # Initialize LiquidPlanner API client
            self.client = LiquidPlannerClient(
                email=self.config.liquidplanner_email,
                password=self.config.liquidplanner_password,
                workspace_id=self.config.liquidplanner_workspace_id,
                base_url=self.config.liquidplanner_base_url,
                rate_limit_requests=self.config.rate_limit_requests,
                rate_limit_period=self.config.rate_limit_period,
                max_retries=self.config.max_retries,
                timeout=self.config.request_timeout,
                redis_url=self.config.redis_url,
                cache_ttl=self.config.cache_ttl,
            )
            
            await self.client.initialize()
            
            # Initialize tool managers
            self.custom_fields = CustomFieldsManager(self.client)
            self.time_entries = TimeEntriesManager(self.client)
            self.tasks = TaskManager(self.client)
            self.projects = ProjectManager(self.client)
            self.reports = ReportsManager(self.client)
            self.bulk_ops = BulkOperationsManager(self.client)
            
            # Register all tools
            await self._register_tools()
            
            # Set up health check
            self._setup_health_check()
            
            self._initialized = True
            logger.info("LiquidPlanner MCP Server initialization completed successfully")
            
        except Exception as e:
            logger.error("Failed to initialize LiquidPlanner MCP Server", error=str(e), exc_info=True)
            raise LiquidPlannerMCPError(f"Server initialization failed: {e}") from e
    
    async def _register_tools(self) -> None:
        """Register all MCP tools with the server."""
        
        # Custom Fields Tools
        @self.app.tool()
        async def list_custom_fields(
            item_type: str = Field(description="Type of item: 'task', 'project', 'folder', 'package'"),
        ) -> List[Dict[str, Any]]:
            """List all available custom fields for a specific item type."""
            try:
                return await self.custom_fields.list_custom_fields(item_type)
            except Exception as e:
                logger.error("Error listing custom fields", error=str(e), item_type=item_type)
                raise LiquidPlannerMCPError(f"Failed to list custom fields: {e}") from e
        
        @self.app.tool()
        async def get_custom_field_values(
            item_id: int = Field(description="ID of the item to get custom field values for"),
            item_type: str = Field(description="Type of item: 'task', 'project', 'folder', 'package'"),
        ) -> Dict[str, Any]:
            """Get all custom field values for a specific item."""
            try:
                return await self.custom_fields.get_custom_field_values(item_id, item_type)
            except Exception as e:
                logger.error("Error getting custom field values", error=str(e), item_id=item_id, item_type=item_type)
                raise LiquidPlannerMCPError(f"Failed to get custom field values: {e}") from e
        
        @self.app.tool()
        async def update_custom_fields(
            item_id: int = Field(description="ID of the item to update"),
            item_type: str = Field(description="Type of item: 'task', 'project', 'folder', 'package'"),
            custom_fields: Dict[str, Any] = Field(description="Custom fields to update (field name/ID -> value)"),
        ) -> Dict[str, Any]:
            """Update custom field values for an item. Supports field names and field IDs."""
            try:
                return await self.custom_fields.update_custom_fields(item_id, item_type, custom_fields)
            except Exception as e:
                logger.error("Error updating custom fields", error=str(e), item_id=item_id, item_type=item_type)
                raise LiquidPlannerMCPError(f"Failed to update custom fields: {e}") from e
        
        # Time Entries Tools
        @self.app.tool()
        async def list_time_entries(
            filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters for time entries"),
            limit: int = Field(default=100, description="Maximum number of entries to return"),
        ) -> List[Dict[str, Any]]:
            """List time entries with optional filtering."""
            try:
                return await self.time_entries.list_time_entries(filters, limit)
            except Exception as e:
                logger.error("Error listing time entries", error=str(e), filters=filters)
                raise LiquidPlannerMCPError(f"Failed to list time entries: {e}") from e
        
        @self.app.tool()
        async def create_time_entry(
            task_id: int = Field(description="ID of the task to log time for"),
            work: float = Field(description="Hours of work to log"),
            work_date: str = Field(description="Date of work (YYYY-MM-DD format)"),
            person_id: Optional[int] = Field(default=None, description="Person ID (defaults to current user)"),
            note: Optional[str] = Field(default=None, description="Note for the time entry"),
            activity_id: Optional[int] = Field(default=None, description="Activity ID"),
        ) -> Dict[str, Any]:
            """Create a new time entry."""
            try:
                return await self.time_entries.create_time_entry(
                    task_id=task_id,
                    work=work,
                    work_date=work_date,
                    person_id=person_id,
                    note=note,
                    activity_id=activity_id,
                )
            except Exception as e:
                logger.error("Error creating time entry", error=str(e), task_id=task_id)
                raise LiquidPlannerMCPError(f"Failed to create time entry: {e}") from e
        
        @self.app.tool()
        async def bulk_import_time_entries(
            csv_data: str = Field(description="CSV data containing time entries"),
            deduplication_rules: Optional[Dict[str, Any]] = Field(default=None, description="Rules for handling duplicates"),
            blacklisted_tasks: Optional[List[int]] = Field(default=None, description="Task IDs to exclude from import"),
        ) -> Dict[str, Any]:
            """Bulk import time entries from CSV data with deduplication."""
            try:
                return await self.time_entries.bulk_import_time_entries(
                    csv_data=csv_data,
                    deduplication_rules=deduplication_rules,
                    blacklisted_tasks=blacklisted_tasks,
                )
            except Exception as e:
                logger.error("Error bulk importing time entries", error=str(e))
                raise LiquidPlannerMCPError(f"Failed to bulk import time entries: {e}") from e
        
        # Task Management Tools
        @self.app.tool()
        async def list_tasks(
            filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters for tasks"),
            limit: int = Field(default=100, description="Maximum number of tasks to return"),
        ) -> List[Dict[str, Any]]:
            """List tasks with optional filtering."""
            try:
                return await self.tasks.list_tasks(filters, limit)
            except Exception as e:
                logger.error("Error listing tasks", error=str(e), filters=filters)
                raise LiquidPlannerMCPError(f"Failed to list tasks: {e}") from e
        
        @self.app.tool()
        async def get_task(
            task_id: int = Field(description="ID of the task to retrieve"),
        ) -> Dict[str, Any]:
            """Get detailed information about a specific task."""
            try:
                return await self.tasks.get_task(task_id)
            except Exception as e:
                logger.error("Error getting task", error=str(e), task_id=task_id)
                raise LiquidPlannerMCPError(f"Failed to get task: {e}") from e
        
        @self.app.tool()
        async def create_task(
            name: str = Field(description="Name of the task"),
            parent_id: int = Field(description="ID of parent project/folder/package"),
            description: Optional[str] = Field(default=None, description="Task description"),
            assignments: Optional[List[Dict[str, Any]]] = Field(default=None, description="Task assignments"),
            custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Custom field values"),
        ) -> Dict[str, Any]:
            """Create a new task."""
            try:
                return await self.tasks.create_task(
                    name=name,
                    parent_id=parent_id,
                    description=description,
                    assignments=assignments,
                    custom_fields=custom_fields,
                )
            except Exception as e:
                logger.error("Error creating task", error=str(e), name=name, parent_id=parent_id)
                raise LiquidPlannerMCPError(f"Failed to create task: {e}") from e
        
        @self.app.tool()
        async def update_task(
            task_id: int = Field(description="ID of the task to update"),
            updates: Dict[str, Any] = Field(description="Fields to update"),
        ) -> Dict[str, Any]:
            """Update an existing task."""
            try:
                return await self.tasks.update_task(task_id, updates)
            except Exception as e:
                logger.error("Error updating task", error=str(e), task_id=task_id)
                raise LiquidPlannerMCPError(f"Failed to update task: {e}") from e
        
        # Project Management Tools
        @self.app.tool()
        async def list_projects(
            filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters for projects"),
        ) -> List[Dict[str, Any]]:
            """List projects with optional filtering."""
            try:
                return await self.projects.list_projects(filters)
            except Exception as e:
                logger.error("Error listing projects", error=str(e), filters=filters)
                raise LiquidPlannerMCPError(f"Failed to list projects: {e}") from e
        
        @self.app.tool()
        async def create_project(
            name: str = Field(description="Name of the project"),
            client_id: Optional[int] = Field(default=None, description="Client ID"),
            description: Optional[str] = Field(default=None, description="Project description"),
            custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Custom field values"),
        ) -> Dict[str, Any]:
            """Create a new project."""
            try:
                return await self.projects.create_project(
                    name=name,
                    client_id=client_id,
                    description=description,
                    custom_fields=custom_fields,
                )
            except Exception as e:
                logger.error("Error creating project", error=str(e), name=name)
                raise LiquidPlannerMCPError(f"Failed to create project: {e}") from e
        
        # Reporting Tools
        @self.app.tool()
        async def generate_timesheet_report(
            start_date: str = Field(description="Start date (YYYY-MM-DD)"),
            end_date: str = Field(description="End date (YYYY-MM-DD)"),
            filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters"),
            format: str = Field(default="json", description="Output format: 'json' or 'csv'"),
        ) -> Dict[str, Any]:
            """Generate a timesheet report for the specified date range."""
            try:
                return await self.reports.generate_timesheet_report(
                    start_date=start_date,
                    end_date=end_date,
                    filters=filters,
                    format=format,
                )
            except Exception as e:
                logger.error("Error generating timesheet report", error=str(e), start_date=start_date, end_date=end_date)
                raise LiquidPlannerMCPError(f"Failed to generate timesheet report: {e}") from e
        
        @self.app.tool()
        async def generate_project_status_report(
            project_ids: Optional[List[int]] = Field(default=None, description="Specific project IDs (or all projects)"),
            include_tasks: bool = Field(default=True, description="Include task details"),
            include_time_tracking: bool = Field(default=True, description="Include time tracking data"),
        ) -> Dict[str, Any]:
            """Generate a comprehensive project status report."""
            try:
                return await self.reports.generate_project_status_report(
                    project_ids=project_ids,
                    include_tasks=include_tasks,
                    include_time_tracking=include_time_tracking,
                )
            except Exception as e:
                logger.error("Error generating project status report", error=str(e), project_ids=project_ids)
                raise LiquidPlannerMCPError(f"Failed to generate project status report: {e}") from e
        
        # Bulk Operations Tools
        @self.app.tool()
        async def bulk_update_tasks(
            updates: List[Dict[str, Any]] = Field(description="List of task updates (each with task_id and fields to update)"),
            validate_only: bool = Field(default=False, description="Only validate updates without applying them"),
        ) -> Dict[str, Any]:
            """Perform bulk updates on multiple tasks."""
            try:
                return await self.bulk_ops.bulk_update_tasks(updates, validate_only)
            except Exception as e:
                logger.error("Error bulk updating tasks", error=str(e))
                raise LiquidPlannerMCPError(f"Failed to bulk update tasks: {e}") from e
        
        @self.app.tool()
        async def export_data_to_csv(
            data_type: str = Field(description="Type of data to export: 'tasks', 'time_entries', 'projects'"),
            filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters to apply"),
            include_custom_fields: bool = Field(default=True, description="Include custom field values"),
        ) -> Dict[str, Any]:
            """Export LiquidPlanner data to CSV format."""
            try:
                return await self.bulk_ops.export_data_to_csv(
                    data_type=data_type,
                    filters=filters,
                    include_custom_fields=include_custom_fields,
                )
            except Exception as e:
                logger.error("Error exporting data to CSV", error=str(e), data_type=data_type)
                raise LiquidPlannerMCPError(f"Failed to export data to CSV: {e}") from e
        
        logger.info("All MCP tools registered successfully")
    
    def _setup_health_check(self) -> None:
        """Set up health check endpoint."""
        @self.app.tool()
        async def health_check() -> Dict[str, Any]:
            """Check the health status of the LiquidPlanner MCP server."""
            try:
                # Test LiquidPlanner API connectivity
                account_info = await self.client.get_account()
                
                return {
                    "status": "healthy",
                    "server": "LiquidPlanner MCP Server",
                    "version": "1.0.0",
                    "liquidplanner_api": "connected",
                    "workspace_id": self.config.liquidplanner_workspace_id,
                    "account": account_info.get("user_name", "Unknown"),
                    "timestamp": logger._context.get("timestamp", "unknown"),
                }
            except Exception as e:
                logger.error("Health check failed", error=str(e))
                return {
                    "status": "unhealthy",
                    "server": "LiquidPlanner MCP Server",
                    "error": str(e),
                    "timestamp": logger._context.get("timestamp", "unknown"),
                }
    
    async def run(self) -> None:
        """Run the MCP server."""
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Starting LiquidPlanner MCP Server")
            await self.app.run()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down gracefully")
        except Exception as e:
            logger.error("Server error", error=str(e), exc_info=True)
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Graceful shutdown of the server."""
        if self._shutdown:
            return
            
        self._shutdown = True
        logger.info("Shutting down LiquidPlanner MCP Server")
        
        try:
            if self.client:
                await self.client.close()
        except Exception as e:
            logger.error("Error during client shutdown", error=str(e))
        
        logger.info("LiquidPlanner MCP Server shutdown completed")


async def main():
    """Main entry point for the LiquidPlanner MCP Server."""
    
    # Load configuration
    config = MCPConfig()
    
    # Create and run server
    server = LiquidPlannerMCPServer(config)
    
    try:
        await server.run()
    except Exception as e:
        logger.error("Fatal server error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
