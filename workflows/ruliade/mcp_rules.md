# MCP Integration Rules (Model Context Protocol)

## MCP Server Configuration

### Server Registration
- **Configure MCP servers in mcp_config.json**
  ```json
  {
    "servers": {
      "ovr_github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
        }
      },
      "ovr_context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp@1.0.14"],
        "env": {
          "UPSTASH_REDIS_REST_URL": "${UPSTASH_REDIS_REST_URL}",
          "UPSTASH_REDIS_REST_TOKEN": "${UPSTASH_REDIS_REST_TOKEN}"
        }
      },
      "ovr_slack": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {
          "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
          "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
        }
      },
      "ovr_repomix": {
        "command": "npx",
        "args": ["-y", "repomix@1.1.0"]
      },
      "ovr_filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem@2025.7.1"],
        "args": ["--allowed-directory", "/allowed/path"]
      },
      "ovr_browser": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search@0.6.2"],
        "env": {
          "BRAVE_SEARCH_API_KEY": "${BRAVE_SEARCH_API_KEY}"
        }
      }
    }
  }
  ```

### Environment Variable Management
- **Use consistent environment variable patterns**
  ```bash
  # GitHub Integration
  GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
  
  # Context7 (Upstash Redis)
  UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
  UPSTASH_REDIS_REST_TOKEN=AxxxX
  
  # Slack Integration
  SLACK_BOT_TOKEN=your_slack_token
  SLACK_TEAM_ID=T123456789
  
  # Browser/Search
  BRAVE_SEARCH_API_KEY=BSA_xxxxx
  ```

- **Load environment variables in centralized location**
  ```python
  import os
  from pathlib import Path
  from dotenv import load_dotenv
  
  def load_mcp_environment():
      """Load MCP-specific environment variables"""
      # Load from .env file
      env_path = Path(__file__).parent / ".env"
      if env_path.exists():
          load_dotenv(env_path)
      
      # Validate required variables
      required_vars = {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub integration",
          "UPSTASH_REDIS_REST_URL": "Context7 documentation search",
          "UPSTASH_REDIS_REST_TOKEN": "Context7 authentication"
      }
      
      missing_vars = []
      for var, description in required_vars.items():
          if not os.getenv(var):
              missing_vars.append(f"{var} ({description})")
      
      if missing_vars:
          raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
  ```

## MCP Tool Integration Patterns

### GitHub Server Integration
- **Use GitHub MCP for repository operations**
  ```python
  # Fetch pull request information
  def get_pull_request_details(repo: str, pr_number: int):
      """Get comprehensive pull request information via MCP"""
      # Use fetch_pull_request tool through MCP
      return {
          "repo": repo,
          "pull_number": pr_number,
          "action": "fetch_pull_request"
      }
  
  # Search for issues and PRs
  def search_github_issues(query: str, repo: str = None):
      """Search GitHub issues and pull requests"""
      search_query = f"{query} repo:{repo}" if repo else query
      return {
          "query": search_query,
          "action": "github_search"
      }
  ```

### Context7 Documentation Search
- **Leverage Context7 for library documentation**
  ```python
  def search_documentation(library_name: str, topic: str = None):
      """Search for library documentation using Context7"""
      # First resolve library ID
      resolve_params = {
          "libraryName": library_name,
          "action": "resolve_library_id"
      }
      
      # Then fetch documentation
      if topic:
          fetch_params = {
              "context7CompatibleLibraryID": f"/{library_name}",
              "topic": topic,
              "tokens": 10000,
              "action": "get_library_docs"
          }
      else:
          fetch_params = {
              "context7CompatibleLibraryID": f"/{library_name}",
              "tokens": 10000,
              "action": "get_library_docs"
          }
      
      return resolve_params, fetch_params
  ```

### Filesystem Operations
- **Secure filesystem access through MCP**
  ```python
  def read_project_files(file_paths: list[str]):
      """Read multiple project files safely through MCP"""
      return {
          "paths": file_paths,
          "action": "read_multiple_files"
      }
  
  def create_project_structure(base_path: str, structure: dict):
      """Create directory structure through MCP"""
      operations = []
      
      # Create directories first
      for dir_path in structure.get("directories", []):
          operations.append({
              "path": f"{base_path}/{dir_path}",
              "action": "create_directory"
          })
      
      # Create files
      for file_path, content in structure.get("files", {}).items():
          operations.append({
              "path": f"{base_path}/{file_path}",
              "content": content,
              "action": "write_file"
          })
      
      return operations
  ```

### Repository Analysis with Repomix
- **Package and analyze codebases**
  ```python
  def analyze_codebase(directory: str, compress: bool = False):
      """Analyze codebase structure using Repomix"""
      return {
          "directory": directory,
          "compress": compress,
          "topFilesLength": 10,
          "action": "pack_codebase"
      }
  
  def analyze_remote_repository(repo_url: str, include_patterns: str = None):
      """Analyze remote repository"""
      params = {
          "remote": repo_url,
          "compress": False,
          "action": "pack_remote_repository"
      }
      
      if include_patterns:
          params["includePatterns"] = include_patterns
      
      return params
  ```

## Error Handling and Resilience

### MCP Connection Management
- **Handle MCP server failures gracefully**
  ```python
  import asyncio
  import logging
  from typing import Dict, Any, Optional
  
  class MCPConnectionManager:
      def __init__(self):
          self.connections: Dict[str, Any] = {}
          self.retry_count = 3
          self.retry_delay = 1.0
          self.logger = logging.getLogger(__name__)
      
      async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Optional[Dict]:
          """Call MCP tool with retry logic"""
          for attempt in range(self.retry_count):
              try:
                  # Attempt MCP call
                  result = await self._make_mcp_call(server_name, tool_name, **kwargs)
                  return result
                  
              except ConnectionError as e:
                  self.logger.warning(f"MCP connection failed (attempt {attempt + 1}): {e}")
                  if attempt < self.retry_count - 1:
                      await asyncio.sleep(self.retry_delay * (2 ** attempt))
                  
              except Exception as e:
                  self.logger.error(f"MCP tool call failed: {e}")
                  return None
          
          self.logger.error(f"All MCP retry attempts failed for {server_name}.{tool_name}")
          return None
      
      async def _make_mcp_call(self, server_name: str, tool_name: str, **kwargs):
          """Internal MCP call implementation"""
          # Implementation depends on MCP client library
          pass
  ```

### Fallback Strategies
- **Implement fallbacks when MCP servers are unavailable**
  ```python
  class DocumentationService:
      def __init__(self, mcp_manager: MCPConnectionManager):
          self.mcp_manager = mcp_manager
          self.local_cache = {}
      
      async def get_documentation(self, library: str, topic: str = None):
          """Get documentation with fallback strategies"""
          # Try Context7 first
          result = await self.mcp_manager.call_mcp_tool(
              "ovr_context7", 
              "get_library_docs",
              context7CompatibleLibraryID=f"/{library}",
              topic=topic
          )
          
          if result:
              # Cache successful results
              cache_key = f"{library}:{topic or 'general'}"
              self.local_cache[cache_key] = result
              return result
          
          # Fallback to cache
          cache_key = f"{library}:{topic or 'general'}"
          if cache_key in self.local_cache:
              self.logger.info(f"Using cached documentation for {library}")
              return self.local_cache[cache_key]
          
          # Final fallback: return basic info
          return {
              "library": library,
              "status": "unavailable",
              "message": "Documentation service temporarily unavailable"
          }
  ```

## Data Flow and Processing

### MCP Response Processing
- **Standardize MCP response handling**
  ```python
  from dataclasses import dataclass
  from typing import Any, Optional
  
  @dataclass
  class MCPResponse:
      success: bool
      data: Any
      error: Optional[str] = None
      server: Optional[str] = None
      tool: Optional[str] = None
  
  class MCPResponseProcessor:
      @staticmethod
      def process_github_response(raw_response: dict) -> MCPResponse:
          """Process GitHub MCP server responses"""
          if "error" in raw_response:
              return MCPResponse(
                  success=False,
                  data=None,
                  error=raw_response["error"],
                  server="github"
              )
          
          return MCPResponse(
              success=True,
              data=raw_response,
              server="github"
          )
      
      @staticmethod
      def process_context7_response(raw_response: dict) -> MCPResponse:
          """Process Context7 documentation responses"""
          if not raw_response or "documentation" not in raw_response:
              return MCPResponse(
                  success=False,
                  data=None,
                  error="No documentation found",
                  server="context7"
              )
          
          return MCPResponse(
              success=True,
              data={
                  "documentation": raw_response["documentation"],
                  "library": raw_response.get("library"),
                  "snippets": raw_response.get("snippets", 0)
              },
              server="context7"
          )
  ```

### Async MCP Operations
- **Handle async MCP operations efficiently**
  ```python
  import asyncio
  from typing import List, Dict
  
  class AsyncMCPOrchestrator:
      def __init__(self, mcp_manager: MCPConnectionManager):
          self.mcp_manager = mcp_manager
      
      async def parallel_documentation_search(self, libraries: List[str]) -> Dict[str, MCPResponse]:
          """Search documentation for multiple libraries in parallel"""
          tasks = []
          
          for library in libraries:
              task = self.mcp_manager.call_mcp_tool(
                  "ovr_context7",
                  "resolve_library_id",
                  libraryName=library
              )
              tasks.append((library, task))
          
          results = {}
          responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
          
          for (library, _), response in zip(tasks, responses):
              if isinstance(response, Exception):
                  results[library] = MCPResponse(
                      success=False,
                      data=None,
                      error=str(response),
                      server="context7"
                  )
              else:
                  results[library] = MCPResponseProcessor.process_context7_response(response)
          
          return results
      
      async def batch_file_operations(self, operations: List[Dict]) -> List[MCPResponse]:
          """Execute multiple file operations in batch"""
          tasks = []
          
          for op in operations:
              if op["action"] == "read_file":
                  task = self.mcp_manager.call_mcp_tool(
                      "ovr_filesystem",
                      "read_file",
                      path=op["path"]
                  )
              elif op["action"] == "write_file":
                  task = self.mcp_manager.call_mcp_tool(
                      "ovr_filesystem",
                      "write_file",
                      path=op["path"],
                      content=op["content"]
                  )
              tasks.append(task)
          
          responses = await asyncio.gather(*tasks, return_exceptions=True)
          
          results = []
          for response in responses:
              if isinstance(response, Exception):
                  results.append(MCPResponse(
                      success=False,
                      data=None,
                      error=str(response),
                      server="filesystem"
                  ))
              else:
                  results.append(MCPResponse(
                      success=True,
                      data=response,
                      server="filesystem"
                  ))
          
          return results
  ```

## Security and Access Control

### MCP Server Security
- **Implement secure MCP server access**
  ```python
  import os
  from pathlib import Path
  
  class MCPSecurityManager:
      def __init__(self):
          self.allowed_directories = self._load_allowed_directories()
          self.sensitive_patterns = {
              r'.*\.env$',
              r'.*secret.*',
              r'.*\.key$',
              r'.*\.pem$',
              r'.*password.*'
          }
      
      def validate_file_access(self, file_path: str) -> bool:
          """Validate that file access is allowed"""
          path = Path(file_path).resolve()
          
          # Check if path is within allowed directories
          for allowed_dir in self.allowed_directories:
              try:
                  path.relative_to(allowed_dir)
                  break
              except ValueError:
                  continue
          else:
              return False
          
          # Check for sensitive file patterns
          for pattern in self.sensitive_patterns:
              if re.match(pattern, str(path), re.IGNORECASE):
                  return False
          
          return True
      
      def _load_allowed_directories(self) -> List[Path]:
          """Load allowed directories from configuration"""
          allowed = os.getenv("MCP_ALLOWED_DIRECTORIES", "").split(":")
          return [Path(d).resolve() for d in allowed if d]
  ```

### API Key Management
- **Secure API key handling for MCP servers**
  ```python
  class MCPCredentialManager:
      def __init__(self):
          self.credentials = self._load_credentials()
      
      def _load_credentials(self) -> Dict[str, str]:
          """Load credentials from secure sources"""
          credentials = {}
          
          # Load from environment variables
          env_mapping = {
              "github": "GITHUB_PERSONAL_ACCESS_TOKEN",
              "slack": "SLACK_BOT_TOKEN",
              "brave": "BRAVE_SEARCH_API_KEY",
              "upstash_url": "UPSTASH_REDIS_REST_URL",
              "upstash_token": "UPSTASH_REDIS_REST_TOKEN"
          }
          
          for service, env_var in env_mapping.items():
              value = os.getenv(env_var)
              if value:
                  credentials[service] = value
          
          return credentials
      
      def get_server_env(self, server_name: str) -> Dict[str, str]:
          """Get environment variables for specific MCP server"""
          env_configs = {
              "ovr_github": {
                  "GITHUB_PERSONAL_ACCESS_TOKEN": self.credentials.get("github")
              },
              "ovr_context7": {
                  "UPSTASH_REDIS_REST_URL": self.credentials.get("upstash_url"),
                  "UPSTASH_REDIS_REST_TOKEN": self.credentials.get("upstash_token")
              },
              "ovr_slack": {
                  "SLACK_BOT_TOKEN": self.credentials.get("slack"),
                  "SLACK_TEAM_ID": os.getenv("SLACK_TEAM_ID")
              },
              "ovr_browser": {
                  "BRAVE_SEARCH_API_KEY": self.credentials.get("brave")
              }
          }
          
          return env_configs.get(server_name, {})
  ```

## Testing MCP Integration

### MCP Mock Framework
- **Create mocks for testing MCP functionality**
  ```python
  import pytest
  from unittest.mock import AsyncMock, MagicMock
  
  class MCPMockFramework:
      def __init__(self):
          self.mock_responses = {}
      
      def mock_github_server(self):
          """Mock GitHub MCP server responses"""
          mock_responses = {
              "fetch_pull_request": {
                  "title": "Test PR",
                  "number": 123,
                  "state": "open",
                  "diff": "sample diff content"
              },
              "search_issues": [
                  {"title": "Test Issue", "number": 456, "state": "open"}
              ]
          }
          return mock_responses
      
      def mock_context7_server(self):
          """Mock Context7 documentation server"""
          return {
              "resolve_library_id": "/test/library",
              "get_library_docs": {
                  "documentation": "Sample documentation content",
                  "library": "test-library",
                  "snippets": 100
              }
          }
  
  @pytest.fixture
  def mcp_mocks():
      """Pytest fixture for MCP mocks"""
      framework = MCPMockFramework()
      
      with patch('mcp_client.call_tool') as mock_call:
          def mock_implementation(server, tool, **kwargs):
              if server == "ovr_github":
                  return framework.mock_github_server().get(tool, {})
              elif server == "ovr_context7":
                  return framework.mock_context7_server().get(tool, {})
              return {}
          
          mock_call.side_effect = mock_implementation
          yield framework
  
  # Test example
  def test_documentation_search(mcp_mocks):
      service = DocumentationService(mcp_manager)
      result = await service.get_documentation("fastapi", "routing")
      
      assert result["library"] == "test-library"
      assert "documentation" in result
  ```

## Performance Optimization

### MCP Caching Strategy
- **Implement intelligent caching for MCP responses**
  ```python
  import time
  import hashlib
  from typing import Dict, Any, Optional
  
  class MCPCache:
      def __init__(self, ttl: int = 3600):  # 1 hour default TTL
          self.cache: Dict[str, Dict] = {}
          self.ttl = ttl
      
      def _generate_key(self, server: str, tool: str, **kwargs) -> str:
          """Generate cache key from MCP call parameters"""
          content = f"{server}:{tool}:{sorted(kwargs.items())}"
          return hashlib.md5(content.encode()).hexdigest()
      
      def get(self, server: str, tool: str, **kwargs) -> Optional[Any]:
          """Get cached response if available and valid"""
          key = self._generate_key(server, tool, **kwargs)
          
          if key in self.cache:
              entry = self.cache[key]
              if time.time() - entry["timestamp"] < self.ttl:
                  return entry["data"]
              else:
                  del self.cache[key]
          
          return None
      
      def set(self, server: str, tool: str, data: Any, **kwargs) -> None:
          """Cache MCP response"""
          key = self._generate_key(server, tool, **kwargs)
          self.cache[key] = {
              "data": data,
              "timestamp": time.time()
          }
      
      def invalidate_pattern(self, pattern: str) -> None:
          """Invalidate cache entries matching pattern"""
          keys_to_remove = [
              key for key in self.cache.keys() 
              if pattern in key
          ]
          for key in keys_to_remove:
              del self.cache[key]
  
  # Integration with MCP manager
  class CachedMCPManager(MCPConnectionManager):
      def __init__(self):
          super().__init__()
          self.cache = MCPCache()
      
      async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Optional[Dict]:
          # Check cache first
          cached_result = self.cache.get(server_name, tool_name, **kwargs)
          if cached_result:
              self.logger.debug(f"Cache hit for {server_name}.{tool_name}")
              return cached_result
          
          # Call parent implementation
          result = await super().call_mcp_tool(server_name, tool_name, **kwargs)
          
          # Cache successful results
          if result:
              self.cache.set(server_name, tool_name, result, **kwargs)
          
          return result
  ``` 