# GraphMCP Framework

A comprehensive framework for orchestrating multiple Model Context Protocol (MCP) servers to build sophisticated workflows for code analysis, repository management, and automated processes.

## Overview

GraphMCP provides a unified interface for managing and coordinating multiple MCP servers, enabling complex workflows that can analyze repositories, interact with GitHub, send Slack notifications, and perform file system operations.

## Features

- **Multi-Client Architecture**: Coordinate multiple MCP servers (GitHub, Slack, Repomix, Filesystem, Preview)
- **Workflow Orchestration**: Build complex workflows with step-by-step execution
- **Database Decommissioning**: Pragmatic database removal with fail-fast strategies
- **Live Streaming**: Real-time workflow visualization with Streamlit UI
- **Async Support**: Full asynchronous operation for high performance
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Testing Framework**: Extensive unit, integration, and E2E testing

## MCP Clients

### Core Clients
- **GitHub Client**: Repository analysis, PR creation, issue management
- **Slack Client**: Team notifications and communication
- **Repomix Client**: Repository packaging and analysis
- **Filesystem Client**: File operations and directory management

### Preview MCP Integration
- **Preview MCP Client**: Live workflow streaming and visualization
- **Streamlit UI**: Real-time workflow monitoring at `http://localhost:8501`
- **Workflow Context**: Step-by-step execution tracking
- **Live Console Output**: Stream workflow progress to browser

## Quick Start

### Setup
```bash
make setup           # Install dependencies and setup environment
source .venv/bin/activate
```

### Basic Usage
```python
from clients import GitHubMCPClient, SlackMCPClient, PreviewMCPClient

# Initialize clients
github = GitHubMCPClient("mcp_config.json")
slack = SlackMCPClient("mcp_config.json") 
preview = PreviewMCPClient("mcp_config.json")

# Create workflow
async with preview:
    result = await preview.run_workflow_end_to_end(
        "Repository Analysis",
        [
            {"name": "analyze_repo", "input_data": {"repo": "owner/repo"}},
            {"name": "generate_report", "input_data": {"format": "markdown"}}
        ]
    )
```

### Preview Demo (Live Streaming)
```bash
# Start complete demo with MCP server + Streamlit UI
make preview-demo

# Or run components separately:
make preview-mcp-server    # Start MCP server
make preview-streamlit     # Start Streamlit UI
```

## Testing

```bash
make test-all              # Run all tests
make preview-test          # Test preview MCP integration
make graphmcp-test-unit    # Unit tests only
make graphmcp-test-integration  # Integration tests
```

## Configuration

Edit `mcp_config.json` to configure MCP servers:

```json
{
  "mcpServers": {
    "ovr_github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"}
    },
    "preview-mcp": {
      "command": "python",
      "args": ["-m", "clients.preview_mcp.server"],
      "env": {"PYTHONPATH": ".", "LOG_LEVEL": "INFO"}
    }
  }
}
```

## Architecture

```
GraphMCP Framework
├── clients/                 # MCP client implementations
│   ├── base.py             # Base MCP client class
│   ├── github.py           # GitHub integration
│   ├── slack.py            # Slack integration
│   ├── repomix.py          # Repository packaging
│   ├── filesystem.py       # File operations
│   └── preview_mcp/        # Live workflow streaming
│       ├── client.py       # Preview MCP client
│       ├── server.py       # Workflow server
│       ├── context.py      # Workflow context management
│       └── logging.py      # Structured logging
├── concrete/               # Concrete implementations
│   ├── file_decommission_processor.py  # Database decommissioning
│   ├── preview_ui/         # Streamlit UI for live streaming
│   └── demo.sh            # Demo script
├── workflows/              # Workflow definitions
├── tests/                  # Test suites
└── utils/                  # Utilities and helpers
```

## Development

### Environment Setup
```bash
make dev                   # Full development setup
make install-pre-commit    # Install git hooks
make lint                  # Code linting
make format               # Code formatting
```

### Adding New MCP Clients
1. Extend `BaseMCPClient` in `clients/`
2. Implement required methods: `list_available_tools()`, `health_check()`
3. Add server configuration to `mcp_config.json`
4. Create tests in `tests/unit/`

## Database Decommissioning

GraphMCP includes a pragmatic database decommissioning processor that safely removes database references while ensuring cluster stability:

### Usage
```python
from concrete.file_decommission_processor import FileDecommissionProcessor

async def decommission_database():
    processor = FileDecommissionProcessor()
    result = await processor.process_files(
        source_dir="/path/to/extracted/files",
        database_name="postgres_air",
        ticket_id="DB-DECOMM-001"
    )
    return result
```

### Strategies
- **Infrastructure**: Comments out Terraform resources and Helm configurations
- **Configuration**: Comments out database configs with clear notices
- **Code**: Adds fail-fast exceptions with contact information
- **Documentation**: Adds decommission notices to markdown files

### Features
- ✅ File categorization by type and complexity
- ✅ Decommission headers with ticket IDs and contact info
- ✅ Preserves original content for emergency rollback
- ✅ Comprehensive test suite with E2E validation
- ✅ Processes real extracted database reference files

## Live Workflow Streaming

The Preview MCP integration provides real-time workflow visualization:

1. **Start the demo**: `make preview-demo`
2. **Open browser**: Navigate to `http://localhost:8501`
3. **Create workflows**: Use the Streamlit interface to create and monitor workflows
4. **Live updates**: See step-by-step execution in real-time
5. **Workflow history**: Track all workflow executions and results

### Workflow Features
- ✅ Real-time step execution tracking
- ✅ Live markdown rendering
- ✅ Session state management
- ✅ Error handling and retry logic
- ✅ Structured logging with context
- ✅ WebSocket-ready for future enhancements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `make test-all` to verify
5. Submit a pull request

## License

[Add your license information here] 