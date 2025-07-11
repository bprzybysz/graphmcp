"""
GraphMCP Utilities Package

Core utilities for MCP server management, extracted from working
db_decommission_workflow implementation to ensure compatibility
and reusability across different workflow contexts.
"""

# Core configuration management
from .config import MCPConfigManager

# Data models
from .data_models import (
    Context7Documentation,
    FilesystemScanResult,
    GitHubSearchResult,
    MCPConfigStatus,
    MCPServerConfig,
    MCPSession,
    MCPToolCall,
)

# Exception classes
from .exceptions import (
    MCPConfigError,
    MCPRetryError,
    MCPSessionError,
    MCPToolError,
    MCPUtilityError,
)

# Retry handling
from .retry import MCPRetryHandler, TimedRetryHandler, retry_with_exponential_backoff

# Session and connection management
from .session import (
    MCPSessionManager,
    ensure_serializable,
    execute_context7_search,
    execute_github_analysis,
)

__all__ = [
    # Configuration
    "MCPConfigManager",
    # Session management
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
