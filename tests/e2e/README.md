# E2E Test Suite for GraphMCP Database Decommissioning Workflow

This directory contains comprehensive end-to-end tests that validate all MCP tools and clients used in the database decommissioning workflow with real external services.

## Overview

The e2e test suite covers all tools used in `workflows/db_decommission.py` that were previously not tested:

- ✅ **RepomixMCPClient** - Repository packing and analysis
- ✅ **GitHubMCPClient** - Repository operations, forking, branching  
- ✅ **FilesystemMCPClient** - File operations and management
- ✅ **SlackMCPClient** - Real Slack workspace integration
- ✅ **Database Decommissioning Workflow** - Complete end-to-end integration
- ✅ **Multi-client coordination** - Testing client interactions

## Test Coverage Matrix

| Test Case | MCP Client | Tools Tested | Requirements | Cleanup |
|-----------|------------|--------------|--------------|---------|
| `test_repomix_pack_remote_repository` | RepomixMCPClient | `pack_remote_repository` | GITHUB_TOKEN | Automatic |
| `test_repomix_analyze_codebase_structure` | RepomixMCPClient | `analyze_codebase_structure` | GITHUB_TOKEN | Automatic |
| `test_filesystem_operations` | FilesystemMCPClient | `read_file`, `write_file`, `list_directory`, `search_files` | None | Automatic |
| `test_github_repo_operations` | GitHubMCPClient | `analyze_repo_structure`, `get_file_contents` | GITHUB_TOKEN | Automatic |
| `test_github_fork_and_branch_operations` | GitHubMCPClient + GitHub CLI | Fork, branch creation/deletion | GITHUB_TOKEN, gh CLI | **Manual cleanup fixture** |
| `test_slack_real_integration` | SlackMCPClient | `post_message`, `list_users`, `list_channels` | SLACK_BOT_TOKEN, SLACK_TEST_CHANNEL | Automatic |
| `test_db_decommission_workflow_integration` | All clients | Complete workflow | All tokens | **Fork cleanup fixture** |
| `test_multi_client_coordination` | Multiple | Client coordination | GITHUB_TOKEN | Automatic |

## Prerequisites

### Required Environment Variables

```bash
# Required for GitHub operations
export GITHUB_TOKEN="your_github_token_here"

# Required for Slack operations  
export SLACK_BOT_TOKEN="your_slack_bot_token_here"
export SLACK_TEST_CHANNEL="C01234567"  # Your test channel ID

# Optional: GitHub CLI for enhanced fork operations
gh auth login  # If using fork/branch tests
```

### Required Tools

1. **Python 3.11+** with virtual environment
2. **GitHub Personal Access Token** with repo permissions
3. **Slack Bot Token** with chat:write permissions
4. **GitHub CLI (gh)** for fork operations (optional but recommended)

### MCP Server Dependencies

The tests require these MCP servers to be available via npm:

```bash
# These are automatically installed in the test config
npx -y @modelcontextprotocol/server-github@2025.4.8
npx -y @modelcontextprotocol/server-slack  
npx -y repomix --mcp
npx -y @modelcontextprotocol/server-filesystem@2024.12.19
```

## Running Tests

### Individual Test Categories

```bash
# Test RepomixMCPClient operations
make graphmcp-test-e2e-repomix

# Test GitHubMCPClient operations  
make graphmcp-test-e2e-github

# Test FilesystemMCPClient operations
make graphmcp-test-e2e-filesystem

# Test SlackMCPClient operations
make graphmcp-test-e2e-slack

# Test GitHub fork/branch operations (creates real forks!)
make graphmcp-test-e2e-fork-ops

# Test multi-client coordination
make graphmcp-test-e2e-multi-client
```

### Complete Test Suites

```bash
# Run all E2E tests
make graphmcp-test-e2e-all

# Run complete test suite including E2E
make test-all-with-e2e

# Run database decommissioning workflow demo
make dbdecomission-demo-e2e
```

### Manual Test Execution

```bash
# Activate virtual environment (required)
source .venv/bin/activate

# Run specific test categories
python -m pytest tests/e2e/ -m e2e -k "repomix" -v
python -m pytest tests/e2e/ -m e2e -k "github" -v 
python -m pytest tests/e2e/ -m e2e -k "filesystem" -v
python -m pytest tests/e2e/ -m e2e -k "slack" -v

# Run complete workflow integration
python -m pytest tests/e2e/ -m e2e -k "db_decommission_workflow" -v

# Run all E2E tests
python -m pytest tests/e2e/ -m e2e -v
```

## Test Target Repository

All tests use the controlled test repository:
- **Repository**: `https://github.com/bprzybys-nc/postgres-sample-dbs`
- **Owner**: `bprzybys-nc`
- **Purpose**: Contains sample database schemas and configurations for testing

### Why This Repository?

1. **Small size** - Fast to clone and analyze
2. **Known structure** - Predictable file patterns for testing
3. **Database content** - Contains actual database-related files
4. **Controlled** - Maintained specifically for testing purposes

## GitHub Fork/Branch Testing Strategy

Following your requirements, the GitHub integration tests:

### Setup Phase
1. **Fork** the test repository to the authenticated user's account
2. **Create test branch** with timestamp-based naming (`test-e2e-{timestamp}`)
3. **Track creation** in fixture metadata for cleanup

### Test Phase  
1. **Analyze fork** using GitHubMCPClient.analyze_repo_structure()
2. **Test operations** on the forked repository
3. **Verify results** without affecting source repository

### Cleanup Phase (Automatic)
1. **Delete test branch** using GitHub API
2. **Delete fork** using GitHub API  
3. **Handle errors gracefully** with warning messages
4. **Report cleanup status** for verification

### Cleanup Implementation

```python
@pytest.fixture
async def github_test_fork():
    """Setup and teardown a GitHub fork for testing."""
    fork_data = {
        "source_repo": "https://github.com/bprzybys-nc/postgres-sample-dbs",
        "test_branch": f"test-e2e-{int(time.time())}",
        "created_fork": False,
        "created_branch": False
    }
    
    yield fork_data  # Provide to test
    
    # Automatic cleanup using GitHub API
    if fork_data.get("created_branch"):
        # Delete branch via gh CLI
    if fork_data.get("created_fork"):  
        # Delete fork via gh CLI
```

## Test Results and Reporting

### Output Files
- `test-results-e2e-*.xml` - JUnit XML reports for CI integration
- Console output with detailed progress and results
- Test coverage reports (when applicable)

### Expected Results

| Test | Expected Outcome | Success Criteria |
|------|------------------|------------------|
| Repomix Pack | Repository packaged | `files_packed > 0`, `success: true` |
| GitHub Analysis | Structure analyzed | `config_files` found, `default_branch` identified |
| Filesystem Ops | File operations | Read/write/search successful |
| Slack Integration | Messages posted | `ts` timestamp returned, users listed |
| Fork Operations | Fork created/deleted | Fork lifecycle managed successfully |
| DB Workflow | Complete execution | `status: completed`, `success_rate > 0.5` |

## Common Issues and Troubleshooting

### Authentication Issues

```bash
# Verify GitHub token
gh auth status

# Verify Slack token  
curl -X POST -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-type: application/json" \
  "https://slack.com/api/auth.test"
```

### Fork Cleanup Issues

If cleanup fails, manual cleanup:

```bash
# List your forks
gh repo list --fork

# Delete specific fork
gh repo delete YOUR_USERNAME/postgres-sample-dbs --yes

# Delete branches
gh api -X DELETE /repos/YOUR_USERNAME/postgres-sample-dbs/git/refs/heads/BRANCH_NAME
```

### MCP Server Issues

```bash
# Test MCP servers manually
npx @modelcontextprotocol/server-github@2025.4.8
npx repomix --mcp

# Check MCP server versions
npm list -g | grep mcp
```

### Memory and Performance

Large repository tests may require increased timeouts:

```bash
# Run with extended timeouts
python -m pytest tests/e2e/ -m e2e --timeout=600 -v
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    if: contains(github.event.head_commit.message, '[e2e]')
    
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: make setup
      
    - name: Run E2E tests
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
        SLACK_TEST_CHANNEL: ${{ secrets.SLACK_TEST_CHANNEL }}
      run: make graphmcp-test-e2e-all
```

## Security Considerations

### Token Security
- ✅ Environment variables only - no hardcoded tokens
- ✅ Minimal required permissions 
- ✅ Test channel isolation for Slack
- ✅ Cleanup prevents resource leaks

### Repository Safety
- ✅ Fork-based testing - no direct modification of source
- ✅ Automatic cleanup prevents accumulation
- ✅ Known test repository with expected content
- ✅ No sensitive data in test repositories

### Rate Limiting
- ✅ Sequential test execution to respect API limits
- ✅ Reasonable timeouts to prevent hanging
- ✅ Error handling for rate limit responses

## Contributing

When adding new MCP tools to the database decommissioning workflow:

1. **Add tool usage** to `workflows/db_decommission.py`
2. **Add e2e test** to `tests/e2e/test_real_integration.py`  
3. **Update this documentation** with new test case
4. **Add Makefile target** for individual tool testing
5. **Test with real MCP servers** before committing

### Test Naming Convention

```python
async def test_{client_name}_{operation_type}(self, real_config_path):
    """Test {ClientName} {operation description}."""
```

Example:
```python
async def test_repomix_pack_remote_repository(self, real_config_path):
    """Test RepomixMCPClient pack_remote_repository with real repo."""
```

## Performance Benchmarks

Expected test execution times:

| Test Category | Duration | Factors |
|---------------|----------|---------|
| Filesystem | < 30s | Local file operations |
| Repomix | 60-180s | Repository size, network |
| GitHub | 30-120s | API rate limits |
| Slack | < 30s | Message posting |
| Fork Ops | 120-300s | Fork lifecycle + API calls |
| Full Workflow | 300-600s | All operations combined |

## Maintenance

### Regular Tasks
- [ ] Update MCP server versions in test config
- [ ] Verify test repository accessibility  
- [ ] Check token expiration dates
- [ ] Review and update test timeouts
- [ ] Monitor test execution performance

### Monthly Tasks  
- [ ] Cleanup any orphaned test forks
- [ ] Review Slack test channel messages
- [ ] Update documentation for new MCP tools
- [ ] Performance benchmark comparison

---

**Last Updated**: January 2025  
**Maintainer**: GraphMCP Framework Team 