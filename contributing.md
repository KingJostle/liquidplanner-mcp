# Contributing to LiquidPlanner MCP Server

Thank you for your interest in contributing to the LiquidPlanner MCP Server! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or request features
- Search existing issues before creating a new one
- Provide detailed information including:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version, Docker version)
  - LiquidPlanner API version
  - Log excerpts (with sensitive data removed)

### Submitting Changes

1. **Fork the repository**
   ```bash
   git clone https://github.com/KingJostle/liquidplanner-mcp.git
   cd liquidplanner-mcp
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or for bug fixes:
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run tests
   docker-compose -f docker-compose.dev.yml exec liquidplanner-mcp pytest
   
   # Run linting
   docker-compose -f docker-compose.dev.yml exec liquidplanner-mcp black .
   docker-compose -f docker-compose.dev.yml exec liquidplanner-mcp isort .
   docker-compose -f docker-compose.dev.yml exec liquidplanner-mcp flake8 .
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new custom field validation tool"
   # Use conventional commit format (see below)
   ```

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Development Setup

### Local Development

1. **Prerequisites**
   - Python 3.9+
   - Docker and Docker Compose
   - Git

2. **Environment Setup**
   ```bash
   # Clone the repository
   git clone https://github.com/KingJostle/liquidplanner-mcp.git
   cd liquidplanner-mcp
   
   # Copy environment template
   cp config/.env.template config/.env
   # Edit config/.env with your LiquidPlanner credentials
   
   # Start development environment
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/liquidplanner_mcp --cov-report=html

# Run specific test file
pytest tests/test_time_entries.py

# Run with verbose output
pytest -v

# Run integration tests (requires valid API credentials)
pytest tests/integration/ --integration
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Auto-format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run all quality checks
./scripts/quality-check.sh
```

## 🎯 Coding Standards

### Python Style
- Follow PEP 8
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 88 characters
- Use type hints for all functions and methods

### Code Organization
- Keep functions focused and small
- Use descriptive variable and function names
- Add docstrings to all public functions and classes
- Organize imports: standard library, third-party, local imports

### Example Code Style
```python
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel

from liquidplanner_mcp.models.base import BaseModel
from liquidplanner_mcp.utils.validation import validate_task_id


class TimeEntry(BaseModel):
    """Represents a time entry in LiquidPlanner."""
    
    task_id: int
    hours: float
    date: str
    comment: Optional[str] = None
    custom_fields: Dict[str, Any] = {}


async def create_time_entry(
    client: httpx.AsyncClient,
    task_id: int,
    hours: float,
    date: str,
    member_id: Optional[int] = None,
    **kwargs
) -> TimeEntry:
    """Create a new time entry.
    
    Args:
        client: HTTP client for API requests
        task_id: LiquidPlanner task ID
        hours: Hours to log
        date: Date in YYYY-MM-DD format
        member_id: Optional member ID (defaults to current user)
        **kwargs: Additional time entry parameters
        
    Returns:
        Created time entry object
        
    Raises:
        ValidationError: If input data is invalid
        APIError: If LiquidPlanner API request fails
    """
    validate_task_id(task_id)
    # Implementation...
```

### Documentation
- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include examples in docstrings when helpful
- Update README.md for significant changes
- Add inline comments for complex logic

### Testing
- Write tests for all new functionality
- Use pytest framework
- Mock external API calls in unit tests
- Create integration tests for end-to-end workflows
- Aim for >80% code coverage

## 🏗️ Architecture Guidelines

### MCP Tools
- Each tool should be focused on a single operation
- Use consistent naming: `verb_noun` (e.g., `create_task`, `get_time_entries`)
- Include comprehensive input validation
- Return structured data using Pydantic models
- Handle errors gracefully with informative messages

### API Client
- Use async/await for all HTTP operations
- Implement proper rate limiting and retries
- Cache responses when appropriate
- Log all API interactions (with sensitive data redacted)

### Data Models
- Use Pydantic for all data models
- Include field validation and constraints
- Provide sensible defaults
- Document all fields

## 🚀 Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(time-entries): add bulk creation with CSV support

fix(api): handle rate limiting with exponential backoff

docs(readme): update installation instructions

test(custom-fields): add validation tests for picklist fields
```

## 🔍 Pull Request Guidelines

### Before Submitting
- [ ] Tests pass locally
- [ ] Code is properly formatted
- [ ] Documentation is updated
- [ ] Commit messages follow conventional format
- [ ] No sensitive data in commits

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🐛 Debugging

### Logging
```python
import structlog

logger = structlog.get_logger(__name__)

logger.info("Creating time entry", task_id=task_id, hours=hours)
logger.error("API request failed", error=str(e), task_id=task_id)
```

### Development Mode
```bash
# Start with debug logging
LOG_LEVEL=DEBUG docker-compose -f docker-compose.dev.yml up

# Enable API request/response logging
DEBUG_LOGGING=true docker-compose -f docker-compose.dev.yml up
```

## 🎯 Feature Requests

### Large Features
For significant features:
1. Open an issue to discuss the feature
2. Get feedback from maintainers
3. Create a design document if needed
4. Break into smaller, reviewable PRs

### Tool Development Priority
1. Core functionality (time entries, tasks, projects)
2. Custom field operations
3. Bulk operations and CSV support
4. Reporting and analytics
5. Advanced integrations

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the `/docs` directory
- **Examples**: See `/examples` directory for usage patterns

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributors graph

Thank you for contributing to the LiquidPlanner MCP Server! 🎉