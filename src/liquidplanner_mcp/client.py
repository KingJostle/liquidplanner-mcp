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
        key_parts
