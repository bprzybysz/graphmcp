# GraphMCP Framework

A reusable framework for building multi-agent systems using the Model Context Protocol (MCP).

## Overview

GraphMCP provides a structured, scalable way to manage complex agentic workflows
by abstracting away the boilerplate of MCP server management, session handling,
and tool calls. It is designed to be a "framework for frameworks" that can power
everything from simple tool-using agents to complex, multi-agent orchestration systems.

This framework was extracted from the `db_decommission_workflow` project to
provide a solid, reusable foundation for future MCP-based applications.

**Current Location**: `lib/graphmcp/`

## Key Features

- **Specialized MCP Clients**: Focused interfaces for GitHub, Context7, Filesystem, and Browser servers
- **Composite Client**: Orchestrates multiple servers with DirectMCPClient-compatible interface
- **Proven Patterns**: Extracted from working db_decommission_workflow implementation
- **Full Backward Compatibility**: Drop-in replacement for DirectMCPClient
- **LangGraph Ready**: Serialization-safe data models for state management
- **Comprehensive Error Handling**: Built-in retry logic and graceful failure handling

## Getting Started

To use GraphMCP in your project:

1.  **Add to your project**:
    ```bash
    # (Recommended) Add as a Git submodule or copy the directory
    cp -r lib/graphmcp/ /path/to/your/project/
    ```

2.  **Install dependencies**:
    See `tests/test_graphmcp.py` for examples of how to test applications
    built with this framework.

## Future Development

The GraphMCP framework is designed for extension. Future improvements may include:

- Support for more MCP servers
- Advanced logging and tracing capabilities
- Richer data models for tool outputs
- Pre-built LangGraph nodes for common agentic tasks
- Integration with other orchestration frameworks (e.g., CrewAI)

## Quick Start

### Drop-in DirectMCPClient Replacement

```python
# Replace this:
# from workbench.db_decommission_workflow.mcp_client import DirectMCPClient

# With this:
from workbench.graphmcp import MultiServerMCPClient

# Same interface, better architecture
client = MultiServerMCPClient.from_config_file("ovora_mcp_config.json")

# All existing methods work exactly the same
github_result = await client.call_github_tools("https://github.com/microsoft/typescript")
context7_result = await client.call_context7_tools("react hooks", library_id="/react/docs")
```

### Specialized Client Usage

```python
from workbench.graphmcp import GitHubMCPClient, Context7MCPClient

# Use specialized clients for focused operations
github = GitHubMCPClient("ovora_mcp_config.json")
context7 = Context7MCPClient("ovora_mcp_config.json")

# Structured results with rich data models
repo_analysis = await github.analyze_repository("https://github.com/facebook/react")
tech_stack = await github.extract_tech_stack("https://github.com/facebook/react")

docs = await context7.get_library_docs("/react/docs", topic="hooks")
```

## Architecture

### Package Structure

```
lib/graphmcp/
├── __init__.py                 # Main package exports
├── README.md                   # This file
├── utils/                      # Core utilities
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── session.py             # Session lifecycle management
│   ├── retry.py               # Retry logic with exponential backoff
│   ├── exceptions.py          # Custom exception classes
│   └── data_models.py         # Serializable data models
├── clients/                    # Specialized server clients
│   ├── __init__.py
│   ├── base.py                # Base client with common functionality
│   ├── github_client.py       # GitHub MCP server client
│   ├── context7_client.py     # Context7 documentation client
│   ├── filesystem_client.py   # Filesystem operations client
│   └── browser_client.py      # Browser automation client
└── composite/                  # Composite clients
    ├── __init__.py
    └── multi_server_client.py  # DirectMCPClient replacement
```

### Design Principles

1. **Never store mcp_use objects**: All clients avoid storing actual MCP session objects to prevent serialization issues
2. **Always ensure serializability**: All returned data is tested for pickle compatibility
3. **Proven patterns only**: Implementation extracted from working db_decommission_workflow
4. **Graceful degradation**: Comprehensive error handling with meaningful fallbacks
5. **Resource cleanup**: Explicit session cleanup in all code paths

## API Reference

### MultiServerMCPClient (DirectMCPClient Replacement)

The main composite client that provides exact compatibility with DirectMCPClient:

```python
client = MultiServerMCPClient.from_config_file("config.json")

# GitHub operations
result = await client.call_github_tools(repo_url)
content = await client.get_file_contents(owner, repo, path)
search_results = await client.search_code(query)

# Context7 operations  
docs = await client.call_context7_tools(query, library_id, topic)

# Health checking
health = await client.health_check_all()

# Configuration
config = client.get_config()
servers = client.list_servers()
```

### Specialized Clients

#### GitHubMCPClient

```python
github = GitHubMCPClient("config.json")

# File operations
content = await github.get_file_contents("microsoft", "typescript", "README.md")

# Code search
results = await github.search_code("repo:microsoft/typescript extension:ts")

# Repository analysis (structured results)
analysis = await github.analyze_repository("https://github.com/microsoft/typescript")
print(f"Found files: {analysis.files_found}")
print(f"Matches: {len(analysis.matches)}")

# Technology stack detection
tech_stack = await github.extract_tech_stack("https://github.com/facebook/react")
print(f"Technologies: {tech_stack}")  # ['javascript', 'react', 'nodejs']
```

#### Context7MCPClient

```python
context7 = Context7MCPClient("config.json")

# Get library documentation (structured results)
docs = await context7.get_library_docs("/react/docs", topic="hooks")
print(f"Documentation sections: {len(docs.content_sections)}")
print(f"Summary: {docs.summary}")

# Search documentation (string results for compatibility)
results = await context7.search_documentation("useState hook", "/react/docs")
```

#### FilesystemMCPClient & BrowserMCPClient

```python
filesystem = FilesystemMCPClient("config.json")
browser = BrowserMCPClient("config.json")

# Basic operations (minimal implementation, ready for expansion)
content = await filesystem.read_file("/path/to/file")
files = await filesystem.search_files("*.py", "/project/src")

page_content = await browser.navigate_to_url("https://example.com")
success = await browser.click_element(".button")
```

### Data Models

All clients return serialization-safe data models:

```python
# GitHubSearchResult
@dataclass
class GitHubSearchResult:
    repository_url: str
    files_found: list[str]
    matches: list[dict]
    search_query: str
    timestamp: float

# Context7Documentation  
@dataclass
class Context7Documentation:
    library_id: str
    topic: str
    content_sections: list[str]
    summary: str
    timestamp: float

# FilesystemScanResult
@dataclass
class FilesystemScanResult:
    base_path: str
    pattern: str
    files_found: list[str]
    matches: list[dict]
    timestamp: float
```

## Migration Guide

### From DirectMCPClient

1. **Update imports**:
   ```python
   # Before
   from workbench.db_decommission_workflow.mcp_client import DirectMCPClient
   
   # After  
   from workbench.graphmcp import MultiServerMCPClient as DirectMCPClient
   ```

2. **No code changes needed** - all existing method calls work identically

3. **Optional: Use structured results**:
   ```python
   # Old way (still works)
   result_str = await client.call_github_tools(repo_url)
   
   # New way (richer data)
   result_obj = await client.analyze_repository(repo_url)
   ```

### From Custom MCP Code

If you have custom MCP server interaction code, you can:

1. **Use specialized clients** for focused operations
2. **Extend base client** for custom server types
3. **Use utilities directly** for low-level session management

## Testing

The graphmcp package includes the exact utilities and patterns from the working db_decommission_workflow, ensuring reliability:

```python
# Health checks
client = MultiServerMCPClient("config.json")
health = await client.health_check_all()
assert health["ovr_github"] == True

# Serialization safety
data = await client.analyze_repository("https://github.com/test/repo")
import pickle
pickle.dumps(data)  # Should not raise
```

## Configuration

Uses the same MCP configuration format as db_decommission_workflow:

```json
{
  "mcpServers": {
    "ovr_github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"
      }
    },
    "ovr_context7": {
      "command": "mcp-server-context7",
      "args": []
    }
  }
}
```

## Error Handling

Comprehensive error handling with meaningful messages:

```python
try:
    result = await client.call_github_tools("invalid-url")
except MCPToolError as e:
    print(f"Tool error: {e.message}")
    print(f"Server: {e.server_name}")
    print(f"Tool: {e.tool_name}")
except MCPSessionError as e:
    print(f"Session error: {e.message}")
    print(f"Details: {e.details}")
```

## Best Practices

1. **Use MultiServerMCPClient** for most use cases - it provides the richest interface
2. **Use specialized clients** when you need focused operations on a single server type  
3. **Always handle exceptions** - network operations can fail
4. **Check health status** before critical operations
5. **Use structured results** when available for richer data

## Contributing

To extend graphmcp:

1. **Add new specialized clients** by inheriting from `BaseMCPClient`
2. **Extend data models** in `utils/data_models.py` for new result types
3. **Follow proven patterns** from existing implementations
4. **Ensure serialization safety** for all returned data
5. **Add comprehensive error handling** with specific exception types

---

**Note**: This package extracts and consolidates the working MCP functionality from db_decommission_workflow to create a reusable, well-structured framework for future MCP-based applications. 