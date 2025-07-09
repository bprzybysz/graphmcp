"""
GraphMCP - Reusable MCP Server Management Framework

A structured, reusable framework for managing MCP (Model Context Protocol) servers
extracted from working implementations. Provides both specialized clients for
individual server types and composite clients for orchestrating multiple servers.

Key Features:
- Specialized clients for GitHub, Context7, Filesystem, and Browser MCP servers
- Composite clients that orchestrate multiple servers
- Proven patterns extracted from working db_decommission_workflow
- Full backward compatibility with DirectMCPClient interfaces
- Comprehensive error handling and retry logic
- Serialization-safe data models for LangGraph integration

Usage:
    # For direct replacement of DirectMCPClient
    from workbench.graphmcp import MultiServerMCPClient
    client = MultiServerMCPClient.from_config_file("config.json")
    
    # For specialized server access
    from workbench.graphmcp import GitHubMCPClient, Context7MCPClient
    github = GitHubMCPClient("config.json")
    context7 = Context7MCPClient("config.json")
"""

# Core utilities
from .utils import (
    # Configuration
    MCPConfigManager,
    
    # Session management
    MCPSessionManager,
    ensure_serializable,
    execute_github_analysis,
    execute_context7_search,
    
    # Retry handling
    MCPRetryHandler,
    TimedRetryHandler,
    retry_with_exponential_backoff,
    
    # Exceptions
    MCPUtilityError,
    MCPSessionError,
    MCPConfigError,
    MCPRetryError,
    MCPToolError,
    
    # Data models
    GitHubSearchResult,
    Context7Documentation,
    FilesystemScanResult,
    MCPToolCall,
    MCPSession,
    MCPServerConfig,
    MCPConfigStatus,
)

# Specialized clients
from .clients import (
    BaseMCPClient,
    GitHubMCPClient,
    Context7MCPClient,
    FilesystemMCPClient,
    BrowserMCPClient,
)

# Composite clients
from .composite import (
    MultiServerMCPClient,
)

# Workflow builders
from .workflows import (
    WorkflowBuilder,
    WorkflowStep,
    WorkflowResult,
    WorkflowConfig,
    WorkflowExecutionContext,
)

__all__ = [
    # Main composite client (DirectMCPClient replacement)
    "MultiServerMCPClient",
    
    # Specialized clients
    "BaseMCPClient",
    "GitHubMCPClient",
    "Context7MCPClient", 
    "FilesystemMCPClient",
    "BrowserMCPClient",
    
    # Workflow builders
    "WorkflowBuilder",
    "WorkflowStep",
    "WorkflowResult",
    "WorkflowConfig",
    "WorkflowExecutionContext",
    
    # Core utilities
    "MCPConfigManager",
    "MCPSessionManager",
    "ensure_serializable",
    "execute_github_analysis",
    "execute_context7_search",
    
    # Retry handling
    "MCPRetryHandler",
    "TimedRetryHandler",
    "retry_with_exponential_backoff",
    
    # Exceptions
    "MCPUtilityError",
    "MCPSessionError",
    "MCPConfigError",
    "MCPRetryError",
    "MCPToolError",
    
    # Data models
    "GitHubSearchResult",
    "Context7Documentation",
    "FilesystemScanResult",
    "MCPToolCall",
    "MCPSession",
    "MCPServerConfig",
    "MCPConfigStatus",
]

# Version information
__version__ = "1.0.0"
__author__ = "Extracted from db_decommission_workflow"
__description__ = "Reusable MCP Server Management Framework"
