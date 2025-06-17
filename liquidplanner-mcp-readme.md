# LiquidPlanner MCP Server

A Model Context Protocol (MCP) server for LiquidPlanner integration, enabling Claude AI to interact with your LiquidPlanner workspace through a comprehensive set of tools and operations.

## 🚀 Features

### Core Functionality
- **Time Entry Management**: Create, read, update, delete time entries with bulk operations
- **Task Management**: Full CRUD operations on tasks, assignments, and dependencies
- **Project & Planning**: Project creation, package management, folder operations
- **Custom Fields**: Complete read/write access to all custom field types (text, picklist, number, date)
- **Reporting & Analytics**: Timesheet exports, project reports, resource utilization
- **Bulk Operations**: CSV import/export, batch processing with smart deduplication

### Advanced Features
- **Smart Deduplication**: Intelligent handling of duplicate time entries with configurable precedence
- **Activity/Cost Code Management**: Full cost code and activity operations
- **Assignment Management**: Resource allocation, workload balancing
- **Real-time Monitoring**: Task status tracking, deadline monitoring
- **Integration Ready**: Webhook support, API rate limiting, error handling

## 🏗️ Architecture

```
liquidplanner-mcp/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container definition
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config/
│   ├── config.yaml            # Main configuration
│   ├── .env.template          # Environment variables template
│   └── docker.env.template    # Docker environment template
├── src/
│   ├── liquidplanner_mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # Main MCP server
│   │   ├── client.py          # LiquidPlanner API client
│   │   ├── models/            # Data models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── tasks.py
│   │   │   ├── time_entries.py
│   │   │   ├── projects.py
│   │   │   └── custom_fields.py
│   │   ├── tools/             # MCP tools
│   │   │   ├── __init__.py
│   │   │   ├── time_entries.py    # Time tracking operations
│   │   │   ├── tasks.py           # Task management
│   │   │   ├── projects.py        # Project operations
│   │   │   ├── custom_fields.py   # Custom field operations
│   │   │   ├── reports.py         # Reporting and analytics
│   │   │   ├── bulk_operations.py # CSV and batch operations
│   │   │   └── utilities.py       # Helper functions
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── auth.py        # Authentication handling
│   │       ├── cache.py       # Caching mechanism
│   │       ├── validation.py  # Data validation
│   │       └── exceptions.py  # Custom exceptions
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_tools/
│   └── fixtures/
├── scripts/                   # Utility scripts
│   ├── setup.py             # Initial setup
│   ├── migrate.py           # Data migration helpers
│   └── backup.py            # Backup utilities
└── docs/                    # Documentation
    ├── API.md               # API documentation
    ├── TOOLS.md             # Tool descriptions
    ├── EXAMPLES.md          # Usage examples
    └── TROUBLESHOOTING.md   # Common issues
```

## 🔧 Installation & Setup

### Prerequisites
- Docker and Docker Compose
- LiquidPlanner account with API access
- Claude Desktop or compatible MCP client

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/[YOUR-USERNAME]/liquidplanner-mcp.git
   cd liquidplanner-mcp
   ```

2. **Configure environment**
   ```bash
   cp config/.env.template config/.env
   # Edit config/.env with your LiquidPlanner credentials
   ```

3. **Start the MCP server**
   ```bash
   docker-compose up -d
   ```

4. **Configure Claude Desktop**
   Add to your Claude Desktop configuration:
   ```json
   {
     "mcpServers": {
       "liquidplanner": {
         "command": "docker",
         "args": ["exec", "liquidplanner-mcp", "python", "-m", "liquidplanner_mcp.server"],
         "env": {
           "LP_API_TOKEN": "your-token-here",
           "LP_WORKSPACE_ID": "your-workspace-id"
         }
       }
     }
   }
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LP_API_TOKEN` | LiquidPlanner API token | Yes | - |
| `LP_WORKSPACE_ID` | LiquidPlanner workspace ID | Yes | - |
| `LP_BASE_URL` | API base URL | No | `https://app.liquidplanner.com/api/v1` |
| `LP_RATE_LIMIT` | API rate limit (requests/minute) | No | `60` |
| `MCP_PORT` | MCP server port | No | `8000` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `CACHE_ENABLED` | Enable response caching | No | `true` |
| `CACHE_TTL` | Cache TTL in seconds | No | `300` |

### Custom Field Configuration

The server automatically discovers custom fields in your workspace and provides tools for:
- **Text Fields**: Read/write text values
- **Picklist Fields**: Read options, set values by ID or name
- **Number Fields**: Read/write numeric values with validation
- **Date Fields**: Read/write dates with format conversion
- **Checkbox Fields**: Read/write boolean values

## 🛠️ Available Tools

### Time Entry Tools
- `create_time_entry`: Create single time entry
- `bulk_create_time_entries`: Create multiple time entries from CSV
- `get_time_entries`: Retrieve time entries with filtering
- `update_time_entry`: Modify existing time entry
- `delete_time_entry`: Remove time entry
- `deduplicate_time_entries`: Smart deduplication with precedence rules

### Task Management Tools
- `create_task`: Create new task with assignments
- `get_task`: Retrieve task details with custom fields
- `update_task`: Modify task properties and custom fields
- `delete_task`: Remove task
- `manage_task_assignments`: Add/remove/modify assignments
- `update_task_custom_fields`: Bulk custom field updates
- `get_task_custom_fields`: Retrieve all custom field values

### Project & Planning Tools
- `create_project`: Create new project with structure
- `get_project`: Retrieve project details and hierarchy
- `update_project`: Modify project properties
- `manage_project_structure`: Organize folders and packages
- `duplicate_project`: Clone project structure

### Custom Field Tools
- `get_custom_field_definitions`: List all custom field schemas
- `get_custom_field_values`: Get values for specific items
- `update_custom_field_values`: Bulk update custom field values
- `validate_custom_field_data`: Validate data before updates
- `get_picklist_options`: Retrieve picklist options and IDs

### Reporting Tools
- `export_timesheet`: Export timesheet data
- `generate_project_report`: Create project status reports
- `analyze_resource_utilization`: Resource allocation analysis
- `export_tasks_csv`: Export task data with custom fields
- `import_tasks_csv`: Import tasks from CSV with validation

### Utility Tools
- `test_connection`: Verify API connectivity
- `get_workspace_info`: Retrieve workspace metadata
- `bulk_validate_data`: Validate large datasets before operations
- `backup_workspace_data`: Export complete workspace backup

## 📊 Usage Examples

### Creating Time Entries with Custom Fields
```python
# Create time entry with custom field
await create_time_entry(
    task_id=12345,
    hours=4.5,
    date="2025-06-17",
    comment="Development work",
    custom_fields={
        "custom_field_123456": 567890,  # Picklist value ID
        "custom_field_789012": "Project work"  # Text field
    }
)
```

### Bulk Operations with CSV
```python
# Process CSV with deduplication
await bulk_create_time_entries(
    csv_data=csv_content,
    deduplication_rules={
        "precedence": ["UserA", "UserB"],  # Priority order for conflicts
        "skip_duplicates": True
    },
    blacklisted_tasks=[12345, 67890]  # Tasks to exclude
)
```

### Custom Field Management
```python
# Update multiple custom fields
await update_task_custom_fields(
    task_id=12345,
    custom_fields={
        "Priority": "High",  # By field name
        "custom_field_789": 42,  # By field ID
        "Due Date": "2025-07-01"  # Date field
    }
)
```

## 🔒 Security & Authentication

- **API Token Management**: Secure token storage and rotation
- **Rate Limiting**: Configurable API rate limiting with backoff
- **Input Validation**: Comprehensive data validation and sanitization
- **Error Handling**: Graceful error handling with detailed logging
- **Audit Logging**: Complete operation logging for compliance

## 🐳 Docker Support

### Development
```bash
# Start in development mode
docker-compose -f docker-compose.dev.yml up

# Run tests
docker-compose exec liquidplanner-mcp pytest

# Access logs
docker-compose logs -f liquidplanner-mcp
```

### Production
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:8000/health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -am 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See `/docs` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## 🔄 Roadmap

- [ ] Webhook support for real-time updates
- [ ] Advanced reporting dashboard
- [ ] Integration with external calendar systems
- [ ] Machine learning for project estimation
- [ ] Mobile app support
- [ ] Advanced workflow automation
- [ ] Multi-workspace support
- [ ] SSO integration

## 📋 Requirements

See [requirements.txt](requirements.txt) for detailed Python dependencies.

Core dependencies:
- Python 3.9+
- FastAPI for MCP server
- httpx for HTTP client
- pydantic for data validation
- pandas for CSV operations
- redis for caching (optional)

---

**Built with ❤️ for LiquidPlanner power users**