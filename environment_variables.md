# GraphMCP Environment Variables

This document lists all environment variables used in the GraphMCP codebase with their current default values.

## Demo Configuration Variables

```bash
# Demo execution mode - controls mock vs real execution
export DEMO_MODE="real"

# Target repository for analysis
export TARGET_REPO="https://github.com/bprzybysz/postgres-sample-dbs"

# Target database name for decommissioning
export TARGET_DATABASE="postgres_air"

# Cache directory for storing cached data
export CACHE_DIR="tests/data"

# Cache time-to-live in seconds (1 hour)
export CACHE_TTL="3600"

# Logging level for demo execution
export LOG_LEVEL="INFO"

# Enable quick mode for faster execution
export QUICK_MODE="false"
```

## MCP Client Authentication Variables

```bash
# GitHub Personal Access Token for GitHub MCP client
export GITHUB_PERSONAL_ACCESS_TOKEN="your_github_token_here"

# Alternative GitHub token name
export GITHUB_TOKEN="your_github_token_here"

# Slack Bot Token for Slack MCP client
export SLACK_BOT_TOKEN="your_slack_bot_token_here"

# Slack Team ID
export SLACK_TEAM_ID="your_slack_team_id_here"

# Slack test channel for testing
export SLACK_TEST_CHANNEL="C01234567"

# Repomix API Key
export REPOMIX_API_KEY="your_repomix_api_key_here"
```

## AI Model Configuration

```bash
# OpenAI API Key for AI-powered analysis
export OPENAI_API_KEY="your_openai_api_key_here"
```

## Database Configuration

```bash
# Primary database URL for pattern discovery
export DATABASE_URL="postgresql://postgres:password@localhost:5432/postgres_air"

# Mock database URL for testing
export MOCK_DATABASE_URL="postgresql://postgres:password@localhost:5432/mock-test-db"

# Database host for testing
export DB_HOST="localhost"
```

## MCP Server Configuration

```bash
# MCP operation timeout (5 minutes)
export MCP_TIMEOUT="300"

# MCP retry count for failed operations
export MCP_RETRY_COUNT="5"

# Allowed directories for MCP filesystem operations (colon-separated)
export MCP_ALLOWED_DIRECTORIES="/path/to/allowed/dir1:/path/to/allowed/dir2"
```

## Development & Testing Variables

```bash
# Environment type (development, production, testing)
export ENVIRONMENT="development"

# Virtual environment detection (automatically set)
export VIRTUAL_ENV="/path/to/your/venv"
```

## Redis Configuration (if using Redis MCP)

```bash
# Upstash Redis REST URL
export UPSTASH_REDIS_REST_URL="your_redis_url_here"

# Upstash Redis REST Token
export UPSTASH_REDIS_REST_TOKEN="your_redis_token_here"
```

## Search Configuration (if using Brave Search MCP)

```bash
# Brave Search API Key
export BRAVE_SEARCH_API_KEY="your_brave_search_api_key_here"
```

## Makefile Variables

```bash
# Database name for Makefile targets
export DB="postgres_air"

# Repository URL for Makefile targets
export REPO="https://github.com/bprzybys-nc/postgres-sample-dbs"
```

## Usage Examples

### Basic Demo Execution
```bash
# Run demo in mock mode with default settings
export DEMO_MODE="mock"
python demo.py --database postgres_air

# Run demo in real mode with custom repository
export DEMO_MODE="real"
export TARGET_REPO="https://github.com/your-org/your-repo"
export TARGET_DATABASE="your_database"
python demo.py --database your_database
```

### Real Mode with MCP Services
```bash
# Set up authentication for real mode
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_your_token_here"
export OPENAI_API_KEY="sk-your_openai_key_here"
export DEMO_MODE="real"

# Run with live services
python demo.py --database postgres_air --real
```

### Testing Configuration
```bash
# Set up for integration tests
export GITHUB_PERSONAL_ACCESS_TOKEN="test_token"
export SLACK_BOT_TOKEN="xoxb-test-token"
export SLACK_TEST_CHANNEL="C01234567"
export ENVIRONMENT="testing"

# Run tests
pytest tests/e2e/ -v
```

## Notes

- Variables with `${VAR_NAME}` syntax in config files will be automatically substituted
- Missing required variables will cause MCP client initialization to fail
- Use `.env` files for local development (automatically loaded by python-dotenv)
- Production deployments should use secure secret management systems
- Some variables have intelligent defaults that work for development/testing

## Current Values Check

To see current values of these variables in your environment:
```bash
env | grep -E "(DEMO_|TARGET_|CACHE_|LOG_|GITHUB_|SLACK_|OPENAI_|DATABASE_|MCP_)" | sort
```