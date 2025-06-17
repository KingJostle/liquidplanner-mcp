# LiquidPlanner MCP Server Configuration Template
# Copy this file to .env and fill in your values

# ============================================================================
# LIQUIDPLANNER API CONFIGURATION
# ============================================================================

# Your LiquidPlanner API token (required)
# Get this from your LiquidPlanner workspace: Administration > API Access
LP_API_TOKEN=your-api-token-here

# Your LiquidPlanner workspace ID (required)
# Found in your LiquidPlanner URL: app.liquidplanner.com/workspaces/[WORKSPACE_ID]
LP_WORKSPACE_ID=your-workspace-id-here

# LiquidPlanner API base URL (optional)
# Use default unless you're using LiquidPlanner Classic or custom instance
LP_BASE_URL=https://app.liquidplanner.com/api/v1

# API rate limiting (requests per minute)
LP_RATE_LIMIT=60

# ============================================================================
# MCP SERVER CONFIGURATION
# ============================================================================

# Port for the MCP server
MCP_PORT=8000

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Enable request/response logging for debugging
DEBUG_LOGGING=false

# ============================================================================
# CACHING CONFIGURATION
# ============================================================================

# Enable caching for API responses
CACHE_ENABLED=true

# Cache TTL in seconds (5 minutes default)
CACHE_TTL=300

# Redis connection (if using Redis for caching)
REDIS_URL=redis://redis:6379/0

# ============================================================================
# BULK OPERATIONS CONFIGURATION
# ============================================================================

# Maximum batch size for bulk operations
MAX_BATCH_SIZE=250

# Delay between API requests (seconds) to respect rate limits
REQUEST_DELAY=0.5

# Maximum retry attempts for failed requests
MAX_RETRIES=3

# ============================================================================
# DEDUPLICATION SETTINGS
# ============================================================================

# Default user precedence for deduplication (comma-separated)
# Users listed first take precedence over users listed later
DEFAULT_USER_PRECEDENCE=UserA,UserB,UserC

# Skip duplicate entries by default
SKIP_DUPLICATES=true

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

# JWT secret for internal authentication (optional)
JWT_SECRET=your-jwt-secret-here

# CORS origins (comma-separated) for web interface
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# ============================================================================
# DATA STORAGE
# ============================================================================

# Data directory for file operations
DATA_DIR=/app/data

# Log directory
LOG_DIR=/app/logs

# Backup directory
BACKUP_DIR=/app/backups

# ============================================================================
# MONITORING & METRICS
# ============================================================================

# Enable Prometheus metrics
METRICS_ENABLED=true

# Metrics port
METRICS_PORT=9000

# Grafana admin password (for monitoring stack)
GRAFANA_PASSWORD=admin

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

# Enable development mode (auto-reload, debug endpoints)
DEVELOPMENT_MODE=false

# Mock API responses for testing
MOCK_API=false

# Test workspace ID for development
TEST_WORKSPACE_ID=test-workspace-id

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable experimental features
ENABLE_EXPERIMENTAL_FEATURES=false

# Enable webhook support
ENABLE_WEBHOOKS=false

# Enable background task processing
ENABLE_BACKGROUND_TASKS=true

# ============================================================================
# BACKUP & EXPORT SETTINGS
# ============================================================================

# Automatic backup schedule (cron format)
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM

# AWS S3 settings for backup storage (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-backup-bucket
AWS_S3_REGION=us-west-2

# ============================================================================
# EMAIL NOTIFICATIONS (optional)
# ============================================================================

# SMTP settings for notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# Notification recipients (comma-separated)
NOTIFICATION_EMAILS=admin@yourdomain.com

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Database URL for persistent storage (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/liquidplanner_mcp

# Celery broker URL for background tasks
CELERY_BROKER_URL=redis://redis:6379/1

# Sentry DSN for error tracking (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Timezone for scheduling and reports
TIMEZONE=UTC