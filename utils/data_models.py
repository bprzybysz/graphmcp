"""
MCP Utilities Data Models

Serializable data classes for MCP tool responses and session management.
These models are designed to be pickle-safe for LangGraph state management.

IMPORTANT: These are NOT the actual MCP objects from mcp_use.
They are serializable representations for type safety and state tracking.
"""

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class GitHubSearchResult:
    """Serializable result from GitHub MCP tool operations."""

    repository_url: str
    files_found: list[str]
    matches: list[dict]
    search_query: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class Context7Documentation:
    """Serializable result from Context7 documentation search."""

    library_id: str
    topic: str
    content_sections: list[str]
    summary: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class FilesystemScanResult:
    """Serializable result from filesystem MCP operations."""

    base_path: str
    pattern: str
    files_found: list[str]
    matches: list[dict]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class MCPToolCall:
    """Record of an MCP tool call for debugging and monitoring."""

    server_name: str
    tool_name: str
    parameters: dict
    result: Any
    duration_ms: int
    success: bool = True
    error_message: str | None = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class MCPSession:
    """Represents an active MCP server session for type hinting and state tracking.

    WARNING: This is NOT the actual mcp_use session object.
    The actual mcp_use session object (e.g., mcp_use.client.MCPSession)
    cannot be directly pickled. This dataclass represents the *concept* of
    the session for type hinting and internal state tracking within utilities.

    For actual MCP operations, the utilities will create fresh mcp_use
    client instances as needed.
    """

    server_name: str
    session_id: str
    config_path: str
    created_at: float = None
    last_used: float = None

    # Internal references - these will NOT be serialized
    # They are marked with leading underscore to indicate internal use
    _session_ref: Any = None
    _client_ref: Any = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_used is None:
            self.last_used = self.created_at

    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = time.time()

    def __getstate__(self):
        """Custom pickling to exclude non-serializable references."""
        state = self.__dict__.copy()
        # Remove non-serializable internal references
        state["_session_ref"] = None
        state["_client_ref"] = None
        return state

    def __setstate__(self, state):
        """Custom unpickling to restore state."""
        self.__dict__.update(state)
        # Internal references will be None after unpickling
        # This is expected - utilities will create fresh instances as needed


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    url: str | None = None
    timeout: int = 30

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for mcp_use configuration."""
        config = {"command": self.command, "args": self.args, "env": self.env}
        if self.url:
            config["url"] = self.url
        return config


@dataclass
class MCPConfigStatus:
    """Status information for MCP configuration validation."""

    config_path: str
    is_valid: bool
    server_count: int
    validation_errors: list[str]
    validated_at: float = None

    def __post_init__(self):
        if self.validated_at is None:
            self.validated_at = time.time()
