"""
Example: GraphMCP Data Models Pattern

This demonstrates the pattern for creating serializable data models in GraphMCP.
Key patterns to follow:
- Use dataclasses with type hints
- Include timestamps for tracking
- Make models pickle-safe for state management
- Include proper serialization methods
- Add utility methods for state management
"""

import time
from dataclasses import dataclass
from typing import Any

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
    This dataclass represents the *concept* of the session for type hinting
    and internal state tracking within utilities.
    """
    server_name: str
    session_id: str
    config_path: str
    created_at: float = None
    last_used: float = None

    # Internal references - these will NOT be serialized
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
        state['_session_ref'] = None
        state['_client_ref'] = None
        return state

    def __setstate__(self, state):
        """Custom unpickling to restore state."""
        self.__dict__.update(state)

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
        config = {
            "command": self.command,
            "args": self.args,
            "env": self.env
        }
        if self.url:
            config["url"] = self.url
        return config

@dataclass  
class WorkflowResult:
    """Result from a GraphMCP workflow execution."""
    workflow_id: str
    steps_completed: int
    total_steps: int
    success: bool
    duration_seconds: float
    results: dict[str, Any]
    errors: list[str] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.errors is None:
            self.errors = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.steps_completed / self.total_steps) * 100.0

    def get_step_result(self, step_name: str, default=None) -> Any:
        """Get result for a specific step."""
        return self.results.get(step_name, default)