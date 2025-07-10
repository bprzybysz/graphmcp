# GraphMCP Quick Reference

> **⚡ Fast reference for GraphMCP patterns, APIs, and troubleshooting**
> **🎉 NEW: Complete Pull Request Creation & Database Decommission Workflow**

## Client Types & Use Cases

| Client Type | Best For | Returns | Example |
|-------------|----------|---------|---------|
| `MultiServerMCPClient` | Legacy migration, multi-server ops | String results | `await client.call_github_tools(repo_url)` |
| `GitHubMCPClient` | **GitHub workflows, fork/branch/PR** | Structured data | `await github.fork_repository("owner", "repo")` |
| `Context7MCPClient` | Documentation search | Structured data | `await context7.get_library_docs(lib_id)` |
| `FilesystemMCPClient` | File operations | Structured data | `await fs.search_files("*.py", "/src")` |
| `BrowserMCPClient` | Web automation | String/basic data | `await browser.navigate_to_url(url)` |

## 🚀 NEW: GitHub Workflow Operations

| Operation | Method | Returns | Example |
|-----------|--------|---------|---------|
| **Fork Repository** | `fork_repository(owner, repo, org=None)` | Fork details | `await github.fork_repository("microsoft", "typescript")` |
| **Create Branch** | `create_branch(owner, repo, branch, from_branch=None)` | Branch details | `await github.create_branch(owner, repo, "feature-branch")` |
| **Create Pull Request** | `create_pull_request(owner, repo, title, head, base, body)` | PR details | `await github.create_pull_request(...)` |
| **Repository Info** | `get_repository(owner, repo)` | Repo metadata | `await github.get_repository("owner", "repo")` |

## 📊 Database Decommission Workflow

```python
from concrete.db_decommission import create_db_decommission_workflow

# Complete automated workflow: Fork → Branch → Process → PR
workflow = create_db_decommission_workflow(
    database_name="user_sessions",
    target_repos=["https://github.com/company/service-a"],
    slack_channel="C01234567",
    config_path="clients/mcp_config.json"
)

result = await workflow.execute()
# Returns: WorkflowResult with success_rate, duration, step_results
```

## Common Import Patterns

```python
# Drop-in replacement
from graphmcp import MultiServerMCPClient as DirectMCPClient

# Specialized clients
from graphmcp import GitHubMCPClient, Context7MCPClient

# Utilities and models
from graphmcp import (
    MCPConfigManager, MCPSessionManager, MCPRetryHandler,
    GitHubSearchResult, Context7Documentation, 
    MCPUtilityError, MCPSessionError
)

# Everything at once
from graphmcp import *
```

## Data Models

| Model | Fields | Use Case |
|-------|--------|----------|
| `GitHubSearchResult` | `repository_url`, `files_found`, `matches`, `tech_stack` | Repository analysis results |
| `Context7Documentation` | `library_id`, `content_sections`, `summary`, `topic` | Documentation content |
| `FilesystemScanResult` | `base_path`, `pattern`, `files_found`, `matches` | File search results |
| `MCPSession` | `server_name`, `session_id`, `config_path` | Session metadata |
| `MCPConfigStatus` | `is_valid`, `validation_errors`, `server_count` | Config validation |

## Error Types & Handling

| Exception | Cause | Retry? | Example Handler |
|-----------|--------|--------|-----------------|
| `MCPConfigError` | Invalid configuration | ❌ No | Fix config, validate first |
| `MCPSessionError` | Session creation/mgmt | ❌ No | Check server health |
| `MCPToolError` | Tool call failure | ✅ Yes | Use retry handler |
| `MCPUtilityError` | Network/temp issues | ✅ Yes | Use retry handler |
| `MCPRetryError` | Retries exhausted | ❌ No | Check root cause |

## Essential Methods

### MultiServerMCPClient

```python
# Initialization
client = MultiServerMCPClient.from_config_file("config.json")

# GitHub operations
result = await client.call_github_tools(repo_url)
content = await client.get_file_contents(owner, repo, path)
search = await client.search_code(query)

# Context7 operations
docs = await client.call_context7_tools(query, library_id="/react/docs")

# Health & config
health = await client.health_check_all()
config = client.get_config()
servers = client.list_servers()
```

### Specialized Clients

```python
# GitHub - Complete Workflow Operations
github = GitHubMCPClient("config.json")

# Repository operations
analysis = await github.analyze_repository(repo_url)  # -> GitHubSearchResult
tech_stack = await github.extract_tech_stack(repo_url)  # -> List[str]
repo_info = await github.get_repository("owner", "repo")  # -> dict

# Fork & Branch operations  
fork_result = await github.fork_repository("owner", "repo")  # -> dict
branch_result = await github.create_branch("owner", "repo", "feature-branch")  # -> dict

# Pull Request operations
pr_result = await github.create_pull_request(
    owner="owner", repo="repo", title="Feature", 
    head="fork-owner:feature-branch", base="main", body="Description"
)  # -> dict

# Context7
context7 = Context7MCPClient("config.json")
docs = await context7.get_library_docs("/react/docs")  # -> Context7Documentation
search = await context7.search_documentation(query)  # -> str

# Health checks (all clients)
is_healthy = await client.health_check()
tools = await client.list_available_tools()
```

## Configuration Structure

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"}
    },
    "context7": {
      "command": "npx", 
      "args": ["-y", "@context7/mcp-server@1.1.0"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem@2024.12.19"],
      "env": {"BASE_DIR": "/project/root"}
    }
  }
}
```

## Common Patterns

### Pattern: Safe Initialization

```python
async def safe_client_setup(config_path: str):
    try:
        # Validate config first
        config_mgr = MCPConfigManager.from_file(config_path)
        status = config_mgr.validate_config()
        
        if not status.is_valid:
            return None, status.validation_errors
        
        # Create client
        client = MultiServerMCPClient.from_config_file(config_path)
        
        # Check health
        health = await client.health_check_all()
        
        return client, health
        
    except Exception as e:
        return None, [str(e)]
```

### Pattern: Retry with Backoff

```python
from graphmcp import MCPRetryHandler

retry_handler = MCPRetryHandler(max_retries=3, base_delay=1.0, max_delay=30.0)

async def robust_operation():
    return await retry_handler.with_retry(
        lambda: client.call_github_tools(repo_url)
    )
```

### Pattern: Parallel Processing

```python
import asyncio

async def analyze_multiple_repos(repo_urls: List[str]):
    github = GitHubMCPClient("config.json")
    
    tasks = [github.analyze_repository(url) for url in repo_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    return successful, failed
```

### Pattern: LangGraph Integration

```python
from typing import TypedDict

class State(TypedDict):
    repo_url: str
    analysis: dict
    
async def analysis_node(state: State) -> State:
    github = GitHubMCPClient("config.json")
    result = await github.analyze_repository(state["repo_url"])
    
    return {
        **state,
        "analysis": result.dict()  # Must call .dict() for serialization!
    }
```

## GitHub Workflow Patterns

### Pattern: Complete Fork → Branch → PR Flow

```python
async def automated_pr_workflow(source_owner: str, source_repo: str, changes_description: str):
    github = GitHubMCPClient("config.json")
    
    # 1. Fork repository
    fork_result = await github.fork_repository(source_owner, source_repo)
    if not fork_result["success"]:
        return {"error": f"Fork failed: {fork_result['error']}"}
    
    fork_owner = fork_result["owner"]["login"]
    fork_name = fork_result["name"]
    
    # 2. Create feature branch
    branch_name = f"automated-changes-{int(time.time())}"
    branch_result = await github.create_branch(fork_owner, fork_name, branch_name)
    if not branch_result["success"]:
        return {"error": f"Branch creation failed: {branch_result['error']}"}
    
    # 3. (Make your file changes here using filesystem/file upload operations)
    
    # 4. Create pull request
    pr_result = await github.create_pull_request(
        owner=source_owner,
        repo=source_repo,
        title=f"Automated: {changes_description}",
        head=f"{fork_owner}:{branch_name}",
        base="main",
        body=f"Automated changes: {changes_description}\\n\\nGenerated via GraphMCP framework"
    )
    
    return {
        "success": pr_result.get("success", False),
        "pr_url": pr_result.get("html_url"),
        "pr_number": pr_result.get("number")
    }
```

### Pattern: Database Decommission Workflow

```python
from concrete.db_decommission import create_db_decommission_workflow

async def decommission_database_across_repos():
    """Production-ready database decommissioning with PR creation."""
    
    workflow = create_db_decommission_workflow(
        database_name="legacy_user_sessions",
        target_repos=[
            "https://github.com/company/user-service",
            "https://github.com/company/auth-service", 
            "https://github.com/company/shared-configs"
        ],
        slack_channel="C01234567",  # Optional
        config_path="clients/mcp_config.json"
    )
    
    result = await workflow.execute()
    
    # Check results
    print(f"✅ Status: {result.status}")
    print(f"📊 Success Rate: {result.success_rate:.1f}%")
    print(f"⏱️ Duration: {result.duration_seconds:.1f}s")
    
    # Extract PR information
    for step_name, step_result in result.step_results.items():
        if step_name == 'create_pull_request' and step_result.get('success'):
            pr_info = step_result.get('pull_request', {})
            print(f"🔄 Created PR #{pr_info.get('number')}: {pr_info.get('html_url')}")
    
    return result
```

### Pattern: Error Handling for GitHub Operations

```python
async def robust_github_operation():
    github = GitHubMCPClient("config.json")
    
    try:
        # Test connectivity first
        tools = await github.list_available_tools()
        if not tools:
            raise Exception("GitHub MCP server not available")
        
        # Perform operations with proper error checking
        fork_result = await github.fork_repository("owner", "repo")
        
        if not fork_result.get("success", False):
            error_msg = fork_result.get("error", "Unknown fork error")
            if "already exists" in error_msg.lower():
                print("⚠️ Repository already forked, continuing...")
                # Handle existing fork scenario
            else:
                raise Exception(f"Fork failed: {error_msg}")
        
        return fork_result
        
    except Exception as e:
        print(f"❌ GitHub operation failed: {e}")
        return {"success": False, "error": str(e)}
```

## Performance Tips

| Tip | Impact | Implementation |
|-----|--------|----------------|
| **Use context managers** | High | `async with session_manager.session_context():` |
| **Parallel requests** | High | `await asyncio.gather(*tasks)` |
| **Cache expensive calls** | Medium | Store results with TTL |
| **Lazy client creation** | Medium | Create clients only when needed |
| **Check fork before creating** | Medium | Avoid duplicate fork operations |
| **Batch repository operations** | High | Process multiple repos in parallel |
| **Monitor session count** | Medium | Use logging to track sessions |

## Debugging Checklist

- [ ] **Config Valid?** → `MCPConfigManager.validate_config()`
- [ ] **Servers Healthy?** → `await client.health_check_all()`
- [ ] **Logs Enabled?** → `logging.getLogger("graphmcp").setLevel(logging.DEBUG)`
- [ ] **Session Cleanup?** → Use context managers or explicit cleanup
- [ ] **Serialization OK?** → Call `.dict()` on data models
- [ ] **Imports Correct?** → Check for mixed old/new imports
- [ ] **Paths Relative?** → Avoid hardcoded absolute paths

## Troubleshooting

| Problem | Check | Solution |
|---------|-------|----------|
| Import errors | Python path | Add lib/graphmcp to PYTHONPATH |
| Config not found | Working directory | Use absolute paths or check CWD |
| Session timeouts | Network/server | Implement retry + timeout |
| Memory growth | Session cleanup | Use context managers |
| Serialization errors | Data models | Call `.dict()` on models |
| Empty results | Server health | Check `health_check_all()` |

## Migration Shortcuts

### From DirectMCPClient

```python
# Minimal change - just update import
from graphmcp import MultiServerMCPClient as DirectMCPClient

# Everything else stays the same!
client = DirectMCPClient.from_config_file("config.json")
result = await client.call_github_tools(repo_url)
```

### To Specialized Clients

```python
# OLD: String results
result_str = await client.call_github_tools(repo_url)

# NEW: Structured results  
github = GitHubMCPClient("config.json")
result_obj = await github.analyze_repository(repo_url)
files = result_obj.files_found  # Direct access
stack = result_obj.tech_stack   # Type-safe
```

## Testing Patterns

```python
# Basic functionality test
async def test_basic():
    client = MultiServerMCPClient.from_config_file("test_config.json")
    health = await client.health_check_all()
    assert all(health.values()), f"Unhealthy servers: {health}"

# Mock for unit tests  
from unittest.mock import AsyncMock, patch

@patch('graphmcp.MCPSessionManager')
async def test_with_mock(mock_session_mgr):
    mock_session_mgr.return_value.call_tool = AsyncMock(return_value={"test": "data"})
    # Test your code...
```

---

*For comprehensive examples and detailed explanations, see [USAGE_GUIDE.md](USAGE_GUIDE.md)* 