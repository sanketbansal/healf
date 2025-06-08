# Docker Templates

This directory contains Jinja2 templates for generating environment-specific Docker configuration files.

## Template Files

### `docker-compose.template.yml`
Template for generating `docker-compose.{environment}.yml` files with:
- Environment-specific service configurations
- Conditional Redis service inclusion
- Development vs Production optimizations
- Frontend service for development environment

### `Dockerfile.template`
Unified template for generating `Dockerfile.{environment}` files with:
- Multi-stage builds for production (smaller, secure images)
- Single-stage builds for development (faster iteration)
- Environment-specific package installations
- Security configurations (non-root user for production)

## Template Variables

Templates use the following variables from config files:

### Basic Configuration
- `environment`: Target environment (development/production/testing)
- `debug`: Debug mode setting
- `log_level`: Logging level
- `api_port`: API server port
- `python_version`: Python version for Docker image

### LLM Configuration
- `llm_model`: LLM model name
- `llm_temperature`: Temperature setting
- `llm_max_tokens`: Maximum tokens
- `openai_api_key`: OpenAI API key (if provided)

### Docker-Specific Configuration
- `workers`: Number of Uvicorn workers
- `memory_limit`: Container memory limit
- `cpu_limit`: Container CPU limit
- `use_redis`: Whether to include Redis service
- `redis_version`: Redis image version
- `redis_password`: Redis password (for production)
- `include_frontend`: Whether to include frontend service

## Usage

Generate Docker files using the generator script:

```bash
# Generate for specific environment
python scripts/generate_docker_config.py development

# Generate for all environments
python scripts/generate_all_docker_configs.py

# Clean and regenerate
python scripts/generate_docker_config.py production --clean
```

## Environment Differences

### Development
- Hot reload enabled
- Volume mounting for live code changes
- Debug tools included (vim, ipython, debugpy)
- Redis port exposed for local access
- Frontend service included

### Production
- Multi-stage build for optimized image size
- Non-root user for security
- Multiple workers for performance
- Resource limits configured
- Redis with authentication
- No volume mounting

### Testing
- Single-stage build for speed
- Minimal configuration
- No Redis by default
- Fast startup optimized 