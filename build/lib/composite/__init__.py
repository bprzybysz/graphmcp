"""
GraphMCP Composite Package

Composite clients that orchestrate multiple specialized MCP server clients
to provide higher-level functionality while maintaining compatibility with
existing interfaces like DirectMCPClient.
"""

from .multi_server_client import MultiServerMCPClient

__all__ = [
    "MultiServerMCPClient",
]
