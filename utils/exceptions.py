"""
MCP Utility Exceptions

Exception classes for MCP utility operations, extracted from working implementation
to maintain compatibility with existing error handling patterns.
"""

import logging

logger = logging.getLogger(__name__)


class MCPUtilityError(Exception):
    """Base exception for MCP utility errors."""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class MCPSessionError(MCPUtilityError):
    """Raised when MCP session operations fail."""

    def __init__(self, message: str, server_name: str = None, details: str = None):
        self.server_name = server_name
        super().__init__(message, details)

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.server_name:
            return f"[{self.server_name}] {base_msg}"
        return base_msg


class MCPConfigError(MCPUtilityError):
    """Raised when MCP configuration operations fail."""

    def __init__(self, message: str, config_path: str = None, details: str = None):
        self.config_path = config_path
        super().__init__(message, details)

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.config_path:
            return f"[Config: {self.config_path}] {base_msg}"
        return base_msg


class MCPRetryError(MCPUtilityError):
    """Raised when retry operations fail after all attempts."""

    def __init__(
        self,
        message: str,
        attempts: int = None,
        last_error: Exception = None,
        details: str = None,
    ):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(message, details)

    def __str__(self) -> str:
        base_msg = super().__str__()
        parts = []
        if self.attempts:
            parts.append(f"attempts: {self.attempts}")
        if self.last_error:
            parts.append(f"last error: {self.last_error}")

        if parts:
            return f"{base_msg} ({', '.join(parts)})"
        return base_msg


class MCPToolError(MCPUtilityError):
    """Raised when MCP tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str = None,
        server_name: str = None,
        details: str = None,
    ):
        self.tool_name = tool_name
        self.server_name = server_name
        super().__init__(message, details)

    def __str__(self) -> str:
        base_msg = super().__str__()
        parts = []
        if self.server_name:
            parts.append(f"server: {self.server_name}")
        if self.tool_name:
            parts.append(f"tool: {self.tool_name}")

        if parts:
            return f"[{', '.join(parts)}] {base_msg}"
        return base_msg
