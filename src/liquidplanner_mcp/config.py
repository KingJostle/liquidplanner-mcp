"""
Configuration module for LiquidPlanner MCP Server
Environment-based configuration with validation and secrets handling
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, SecretStr
from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """
    Configuration for LiquidPlanner MCP Server.
    
    Loads configuration from environment variables with sensible defaults.
    Supports both LiquidPlanner Classic and Next.
    """
    
    # LiquidPlanner API Configuration
    liquidplanner_email: str = Field(
        ..., 
        description="LiquidPlanner account email address"
    )
    liquidplanner_password: SecretStr = Field(
        ..., 
        description="LiquidPlanner account password"
    )
    liquidplanner_workspace_id: int = Field(
        ..., 
        description="LiquidPlanner workspace ID to connect to"
    )
    liquidplanner_base_url: str = Field(
        default="https://app.liquidplanner.com/api",
        description="LiquidPlanner API base URL (Classic or Next)"
    )
    
    # Rate Limiting Configuration
    rate_limit_requests: int = Field(
        default=60,
        description="Maximum requests per period",
        ge=1,
        le=1000
    )
    rate_limit_period: int = Field(
        default=60,
        description="Rate limit period in seconds",
        ge=1,
        le=3600
    )
    
    # Request Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests",
        ge=0,
        le=10
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300
    )
    
    # Caching Configuration
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for caching (optional)"
    )
    cache_ttl: int = Field(
        default=300,
        description="Default cache TTL in seconds",
        ge=0,
        le=86400
    )
    
    # Server Configuration
    server_host: str = Field(
        default="127.0.0.1",
        description="MCP server host"
    )
    server_port: int = Field(
        default=8080,
        description="MCP server port",
        ge=1,
        le=65535
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        description="Log format: 'json' or 'text'"
    )
    
    # Development Configuration
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    development_mode: bool = Field(
        default=False,
        description="Enable development mode with additional logging"
    )
    
    # Bulk Operations Configuration
    bulk_batch_size: int = Field(
        default=100,
        description="Batch size for bulk operations",
        ge=1,
        le=1000
    )
    bulk_max_concurrent: int = Field(
        default=5,
        description="Maximum concurrent bulk operations",
        ge=1,
        le=20
    )
    
    # Time Entry Configuration
    time_entry_deduplication: bool = Field(
        default=True,
        description="Enable time entry deduplication by default"
    )
    time_entry_blacklisted_tasks: List[int] = Field(
        default_factory=list,
        description="Default blacklisted task IDs for time entries"
    )
    time_entry_user_precedence: List[str] = Field(
        default_factory=list,
        description="User precedence order for deduplication (usernames or emails)"
    )
    
    # Custom Fields Configuration
    custom_fields_cache_ttl: int = Field(
        default=3600,
        description="Cache TTL for custom field definitions in seconds",
        ge=60,
        le=86400
    )
    
    # Security Configuration
    require_https: bool = Field(
        default=True,
        description="Require HTTPS for API connections"
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_prefix = "LIQUIDPLANNER_MCP_"
        case_sensitive = False
        secrets_dir = "/run/secrets"  # Docker secrets support
        
        # Define which fields should be treated as secrets
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
    
    @validator("liquidplanner_base_url")
    def validate_base_url(cls, v):
        """Validate and normalize base URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip("/")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("log_format")
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()
    
    @validator("redis_url")
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if v and not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v
    
    def get_password(self) -> str:
        """Get the plaintext password."""
        return self.liquidplanner_password.get_secret_value()
    
    def model_dump(self, exclude_secrets: bool = False, **kwargs) -> Dict[str, Any]:
        """Override model_dump to handle secrets."""
        data = super().model_dump(**kwargs)
        
        if exclude_secrets:
            # Replace secret values with masked strings
            if "liquidplanner_password" in data:
                data["liquidplanner_password"] = "***MASKED***"
        
        return data
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not (self.debug or self.development_mode)
    
    def get_liquidplanner_auth(self) -> tuple[str, str]:
        """Get LiquidPlanner authentication tuple."""
        return (self.liquidplanner_email, self.get_password())
    
    def get_redis_config(self) -> Optional[Dict[str, Any]]:
        """Get Redis configuration if available."""
        if not self.redis_url:
            return None
        
        return {
            "url": self.redis_url,
            "default_ttl": self.cache_ttl,
        }
    
    def get_rate_limit_config(self) -> Dict[str, int]:
        """Get rate limiting configuration."""
        return {
            "requests_per_period": self.rate_limit_requests,
            "period_seconds": self.rate_limit_period,
        }
    
    def get_bulk_operation_config(self) -> Dict[str, Any]:
        """Get bulk operation configuration."""
        return {
            "batch_size": self.bulk_batch_size,
            "max_concurrent": self.bulk_max_concurrent,
            "deduplication_enabled": self.time_entry_deduplication,
            "blacklisted_tasks": self.time_entry_blacklisted_tasks,
            "user_precedence": self.time_entry_user_precedence,
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.log_level,
            "format": self.log_format,
            "debug": self.debug,
            "development_mode": self.development_mode,
        }


class DevelopmentConfig(MCPConfig):
    """Development configuration with sensible defaults for local development."""
    
    debug: bool = True
    development_mode: bool = True
    log_level: str = "DEBUG"
    require_https: bool = False
    verify_ssl: bool = False
    cache_ttl: int = 60  # Shorter cache for development
    
    class Config(MCPConfig.Config):
        env_file = ".env.development"


class ProductionConfig(MCPConfig):
    """Production configuration with security-focused defaults."""
    
    debug: bool = False
    development_mode: bool = False
    log_level: str = "INFO"
    require_https: bool = True
    verify_ssl: bool = True
    
    class Config(MCPConfig.Config):
        env_file = ".env.production"


class TestingConfig(MCPConfig):
    """Testing configuration for unit and integration tests."""
    
    debug: bool = True
    development_mode: bool = True
    log_level: str = "DEBUG"
    require_https: bool = False
    verify_ssl: bool = False
    cache_ttl: int = 0  # No caching in tests
    
    # Override with test values
    liquidplanner_email: str = "test@example.com"
    liquidplanner_password: SecretStr = SecretStr("test_password")
    liquidplanner_workspace_id: int = 12345
    
    class Config(MCPConfig.Config):
        env_file = ".env.testing"


def get_config(environment: Optional[str] = None) -> MCPConfig:
    """
    Get configuration based on environment.
    
    Args:
        environment: Environment name ('development', 'production', 'testing')
                   If None, uses ENVIRONMENT env var or defaults to 'development'
    
    Returns:
        Appropriate configuration instance
    """
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        "production": ProductionConfig,
        "prod": ProductionConfig,
        "testing": TestingConfig,
        "test": TestingConfig,
    }
    
    config_class = config_map.get(environment, DevelopmentConfig)
    
    try:
        return config_class()
    except Exception as e:
        raise ValueError(f"Failed to load configuration for environment '{environment}': {e}") from e


# Default configuration instance
config = get_config()
