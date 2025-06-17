"""
LiquidPlanner API Client
Async HTTP client for LiquidPlanner API with authentication, rate limiting, caching, and error handling
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlencode

import httpx
import redis.asyncio as redis
import structlog
from pydantic import BaseModel

from .exceptions import (
    LiquidPlannerAPIError,
    LiquidPlannerAuthError,
    LiquidPlannerRateLimitError,
    LiquidPlannerNotFoundError,
)
from .models import APIResponse

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API requests."""
    
    def __init__(self, requests_per_period: int, period_seconds: int):
        self.requests_per_period = requests_per_period
        self.period_seconds = period_seconds
        self.tokens = requests_per_period
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token for making a request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            if elapsed > 0:
                tokens_to_add = (elapsed / self.period_seconds) * self.requests_per_period
                self.tokens = min(self.requests_per_period, self.tokens + tokens_to_add)
                self.last_refill = now
            
            if self.tokens < 1:
                # Calculate wait time
                wait_time = (1 - self.tokens) * (self.period_seconds / self.requests_per_period)
                logger.warning("Rate limit exceeded, waiting", wait_time=wait_time)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class CacheManager:
    """Redis-based cache manager for API responses."""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis if URL is provided."""
        if not self.redis_url:
            logger.info("No Redis URL provided, caching disabled")
            return
        
        try:
            self._redis = redis.from_url(self.redis_url)
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache", redis_url=self.redis_url)
        except Exception as e:
            logger.warning("Failed to connect to Redis, caching disabled", error=str(e))
            self._connected = False
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key."""
        if not self._connected:
            return None
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
        
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set cached value with TTL."""
        if not self._connected:
            return
        
        try:
            ttl = ttl or self.default_ttl
            await self._redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))
    
    async def delete(self, key: str) -> None:
        """Delete cached value."""
        if not self._connected:
            return
        
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern."""
        if not self._connected:
            return
        
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.warning("Cache pattern invalidation failed", pattern=pattern, error=str(e))
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


class LiquidPlannerClient:
    """
    Async HTTP client for LiquidPlanner API.
    
    Features:
    - HTTP Basic authentication
    - Automatic rate limiting with exponential backoff
    - Response caching with Redis
    - Comprehensive error handling
    - Request/response logging
    - Retry logic for transient failures
    """
    
    def __init__(
        self,
        email: str,
        password: str,
        workspace_id: int,
        base_url: str = "https://app.liquidplanner.com/api",
        rate_limit_requests: int = 60,
        rate_limit_period: int = 60,
        max_retries: int = 3,
        timeout: int = 30,
        redis_url: Optional[str] = None,
        cache_ttl: int = 300,
    ):
        self.email = email
        self.password = password
        self.workspace_id = workspace_id
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize components
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_period)
        self.cache = CacheManager(redis_url, cache_ttl)
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        
        logger.info("LiquidPlanner client initialized", 
                   email=email, 
                   workspace_id=workspace_id,
                   base_url=base_url)
    
    async def initialize(self) -> None:
        """Initialize the client and its components."""
        if self._initialized:
            return
        
        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            auth=(self.email, self.password),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "LiquidPlanner-MCP-Server/1.0.0",
            },
            timeout=httpx.Timeout(self.timeout),
        )
        
        # Initialize cache
        await self.cache.connect()
        
        # Test authentication
        await self._test_authentication()
        
        self._initialized = True
        logger.info("LiquidPlanner client initialization completed")
    
    async def _test_authentication(self) -> None:
        """Test API authentication by fetching account information."""
        try:
            response = await self._make_request("GET", "/account")
            logger.info("Authentication successful", user=response.get("user_name"))
        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            raise LiquidPlannerAuthError(f"Authentication failed: {e}") from e
    
    def _build_url(self, endpoint: str, workspace_scoped: bool = True) -> str:
        """Build full URL for API endpoint."""
        if workspace_scoped and self.workspace_id:
            endpoint = f"/workspaces/{self.workspace_id}{endpoint}"
        return urljoin(self.base_url, endpoint.lstrip("/"))
    
    def _build_cache_key(self, method: str, url: str, params: Optional[Dict] = None) -> str:
        """Build cache key for request."""
        key_parts = [f"lp:{method}:{url}"]
        if params:
            key_parts.append(urlencode(sorted(params.items())))
        return ":".join(key_parts)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        workspace_scoped: bool = True,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to LiquidPlanner API with caching and rate limiting."""
        
        if not self._initialized:
            await self.initialize()
        
        url = self._build_url(endpoint, workspace_scoped)
        cache_key = self._build_cache_key(method, url, params) if use_cache else None
        
        # Try cache first for GET requests
        if method == "GET" and use_cache and cache_key:
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                logger.debug("Cache hit", cache_key=cache_key)
                return cached_response
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Make request with retries
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug("Making API request", 
                           method=method, 
                           url=url, 
                           attempt=attempt + 1)
                
                # Prepare request
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "params": params,
                }
                
                if data:
                    request_kwargs["json"] = data
                
                # Make request
                response = await self._client.request(**request_kwargs)
                
                # Handle response
                return await self._handle_response(response, cache_key, cache_ttl)
                
            except httpx.TimeoutException as e:
                last_exception = e
                wait_time = 2 ** attempt
                logger.warning("Request timeout, retrying", 
                             attempt=attempt + 1, 
                             wait_time=wait_time,
                             error=str(e))
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)
                    
            except httpx.ConnectError as e:
                last_exception = e
                wait_time = 2 ** attempt
                logger.warning("Connection error, retrying", 
                             attempt=attempt + 1, 
                             wait_time=wait_time,
                             error=str(e))
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)
                    
            except LiquidPlannerRateLimitError as e:
                last_exception = e
                wait_time = 2 ** attempt * 5  # Longer wait for rate limits
                logger.warning("Rate limit error, retrying", 
                             attempt=attempt + 1, 
                             wait_time=wait_time)
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)
                    
            except (LiquidPlannerAuthError, LiquidPlannerNotFoundError) as e:
                # Don't retry auth or not found errors
                logger.error("Non-retryable error", error=str(e))
                raise
                
            except Exception as e:
                last_exception = e
                logger.error("Unexpected error during request", 
                           attempt=attempt + 1, 
                           error=str(e))
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
        
        # All retries exhausted
        logger.error("Request failed after all retries", 
                   method=method, 
                   url=url, 
                   max_retries=self.max_retries)
        raise LiquidPlannerAPIError(f"Request failed after {self.max_retries + 1} attempts: {last_exception}")
    
    async def _handle_response(
        self, 
        response: httpx.Response, 
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Handle HTTP response and extract data."""
        
        logger.debug("Received response", 
                   status_code=response.status_code,
                   headers=dict(response.headers))
        
        # Handle different status codes
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Cache successful GET responses
                if cache_key and response.request.method == "GET":
                    await self.cache.set(cache_key, data, cache_ttl)
                
                return data
                
            except json.JSONDecodeError as e:
                logger.error("Failed to decode JSON response", error=str(e))
                raise LiquidPlannerAPIError(f"Invalid JSON response: {e}")
                
        elif response.status_code == 401:
            logger.error("Authentication failed", status_code=response.status_code)
            raise LiquidPlannerAuthError("Authentication failed - check credentials")
            
        elif response.status_code == 403:
            logger.error("Access forbidden", status_code=response.status_code)
            raise LiquidPlannerAuthError("Access forbidden - insufficient permissions")
            
        elif response.status_code == 404:
            logger.error("Resource not found", status_code=response.status_code)
            raise LiquidPlannerNotFoundError("Resource not found")
            
        elif response.status_code == 429:
            logger.error("Rate limit exceeded", status_code=response.status_code)
            raise LiquidPlannerRateLimitError("Rate limit exceeded")
            
        elif 400 <= response.status_code < 500:
            error_msg = f"Client error {response.status_code}"
            try:
                error_data = response.json()
                if "errors" in error_data:
                    error_msg += f": {error_data['errors']}"
            except:
                pass
            logger.error("Client error", status_code=response.status_code, error=error_msg)
            raise LiquidPlannerAPIError(error_msg)
            
        elif response.status_code >= 500:
            error_msg = f"Server error {response.status_code}"
            logger.error("Server error", status_code=response.status_code)
            raise LiquidPlannerAPIError(error_msg)
            
        else:
            error_msg = f"Unexpected status code {response.status_code}"
            logger.error("Unexpected response", status_code=response.status_code)
            raise LiquidPlannerAPIError(error_msg)
    
    # Account and Workspace Operations
    async def get_account(self) -> Dict[str, Any]:
        """Get current user account information."""
        return await self._make_request("GET", "/account", workspace_scoped=False)
    
    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get list of available workspaces."""
        return await self._make_request("GET", "/workspaces", workspace_scoped=False)
    
    async def get_workspace(self, workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """Get workspace information."""
        ws_id = workspace_id or self.workspace_id
        return await self._make_request("GET", f"/workspaces/{ws_id}", workspace_scoped=False)
    
    # Custom Fields Operations
    async def get_custom_fields(self, item_type: str) -> List[Dict[str, Any]]:
        """Get custom fields for a specific item type."""
        return await self._make_request("GET", f"/{item_type}s/custom_field_definitions")
    
    async def get_item_custom_fields(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get custom field values for a specific item."""
        item = await self._make_request("GET", f"/{item_type}s/{item_id}")
        return item.get("custom_field_values", {})
    
    async def update_item_custom_fields(
        self, 
        item_type: str, 
        item_id: int, 
        custom_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update custom field values for an item."""
        data = {item_type: {"custom_field_values": custom_fields}}
        response = await self._make_request("PUT", f"/{item_type}s/{item_id}", data=data, use_cache=False)
        
        # Invalidate cache for this item
        await self.cache.invalidate_pattern(f"lp:GET:*/{item_type}s/{item_id}*")
        
        return response
    
    # Task Operations
    async def get_tasks(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tasks with optional filtering."""
        params = filters or {}
        params["limit"] = limit
        return await self._make_request("GET", "/tasks", params=params)
    
    async def get_task(self, task_id: int) -> Dict[str, Any]:
        """Get a specific task."""
        return await self._make_request("GET", f"/tasks/{task_id}")
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        data = {"task": task_data}
        response = await self._make_request("POST", "/tasks", data=data, use_cache=False)
        
        # Invalidate tasks cache
        await self.cache.invalidate_pattern("lp:GET:*/tasks*")
        
        return response
    
    async def update_task(self, task_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task."""
        data = {"task": task_data}
        response = await self._make_request("PUT", f"/tasks/{task_id}", data=data, use_cache=False)
        
        # Invalidate cache for this task and tasks list
        await self.cache.invalidate_pattern(f"lp:GET:*/tasks/{task_id}*")
        await self.cache.invalidate_pattern("lp:GET:*/tasks*")
        
        return response
    
    async def delete_task(self, task_id: int) -> Dict[str, Any]:
        """Delete a task."""
        response = await self._make_request("DELETE", f"/tasks/{task_id}", use_cache=False)
        
        # Invalidate cache
        await self.cache.invalidate_pattern(f"lp:GET:*/tasks/{task_id}*")
        await self.cache.invalidate_pattern("lp:GET:*/tasks*")
        
        return response
    
    # Project Operations
    async def get_projects(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get projects with optional filtering."""
        params = filters or {}
        return await self._make_request("GET", "/projects", params=params)
    
    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get a specific project."""
        return await self._make_request("GET", f"/projects/{project_id}")
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        data = {"project": project_data}
        response = await self._make_request("POST", "/projects", data=data, use_cache=False)
        
        # Invalidate projects cache
        await self.cache.invalidate_pattern("lp:GET:*/projects*")
        
        return response
    
    async def update_project(self, project_id: int, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a project."""
        data = {"project": project_data}
        response = await self._make_request("PUT", f"/projects/{project_id}", data=data, use_cache=False)
        
        # Invalidate cache
        await self.cache.invalidate_pattern(f"lp:GET:*/projects/{project_id}*")
        await self.cache.invalidate_pattern("lp:GET:*/projects*")
        
        return response
    
    # Time Entry Operations
    async def get_time_entries(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get time entries with optional filtering."""
        params = filters or {}
        params["limit"] = limit
        return await self._make_request("GET", "/timesheet_entries", params=params)
    
    async def get_time_entry(self, entry_id: int) -> Dict[str, Any]:
        """Get a specific time entry."""
        return await self._make_request("GET", f"/timesheet_entries/{entry_id}")
    
    async def create_time_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new time entry."""
        data = {"timesheet_entry": entry_data}
        response = await self._make_request("POST", "/timesheet_entries", data=data, use_cache=False)
        
        # Invalidate time entries cache
        await self.cache.invalidate_pattern("lp:GET:*/timesheet_entries*")
        
        return response
    
    async def update_time_entry(self, entry_id: int, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a time entry."""
        data = {"timesheet_entry": entry_data}
        response = await self._make_request("PUT", f"/timesheet_entries/{entry_id}", data=data, use_cache=False)
        
        # Invalidate cache
        await self.cache.invalidate_pattern(f"lp:GET:*/timesheet_entries/{entry_id}*")
        await self.cache.invalidate_pattern("lp:GET:*/timesheet_entries*")
        
        return response
    
    async def delete_time_entry(self, entry_id: int) -> Dict[str, Any]:
        """Delete a time entry."""
        response = await self._make_request("DELETE", f"/timesheet_entries/{entry_id}", use_cache=False)
        
        # Invalidate cache
        await self.cache.invalidate_pattern(f"lp:GET:*/timesheet_entries/{entry_id}*")
        await self.cache.invalidate_pattern("lp:GET:*/timesheet_entries*")
        
        return response
    
    # People and Assignment Operations
    async def get_people(self) -> List[Dict[str, Any]]:
        """Get workspace members."""
        return await self._make_request("GET", "/members")
    
    async def get_person(self, person_id: int) -> Dict[str, Any]:
        """Get a specific person."""
        return await self._make_request("GET", f"/members/{person_id}")
    
    # Activity and Cost Code Operations
    async def get_activities(self) -> List[Dict[str, Any]]:
        """Get available activities."""
        return await self._make_request("GET", "/activities")
    
    # Client Operations
    async def get_clients(self) -> List[Dict[str, Any]]:
        """Get clients."""
        return await self._make_request("GET", "/clients")
    
    async def get_client(self, client_id: int) -> Dict[str, Any]:
        """Get a specific client."""
        return await self._make_request("GET", f"/clients/{client_id}")
    
    # Folder Operations
    async def get_folders(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get folders with optional filtering."""
        params = filters or {}
        return await self._make_request("GET", "/folders", params=params)
    
    async def create_folder(self, folder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new folder."""
        data = {"folder": folder_data}
        response = await self._make_request("POST", "/folders", data=data, use_cache=False)
        
        # Invalidate folders cache
        await self.cache.invalidate_pattern("lp:GET:*/folders*")
        
        return response
    
    # Package Operations
    async def get_packages(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get packages with optional filtering."""
        params = filters or {}
        return await self._make_request("GET", "/packages", params=params)
    
    async def create_package(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new package."""
        data = {"package": package_data}
        response = await self._make_request("POST", "/packages", data=data, use_cache=False)
        
        # Invalidate packages cache
        await self.cache.invalidate_pattern("lp:GET:*/packages*")
        
        return response
    
    async def close(self) -> None:
        """Close the client and cleanup resources."""
        logger.info("Closing LiquidPlanner client")
        
        if self._client:
            await self._client.aclose()
        
        await self.cache.close()
        
        logger.info("LiquidPlanner client closed")
