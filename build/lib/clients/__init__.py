"""
GraphMCP Clients Package

Specialized MCP server clients that provide focused interfaces
for specific server types. All clients inherit from BaseMCPClient
and implement the proven patterns from working db_decommission_workflow.
"""

# Base client
from .base import BaseMCPClient

# Specialized server clients
from .browser_client import BrowserMCPClient
from .context7_client import Context7MCPClient
from .filesystem_client import FilesystemMCPClient
from .github_client import GitHubMCPClient

__all__ = [
    # Base client
    "BaseMCPClient",
    
    # Specialized clients
    "GitHubMCPClient",
    "Context7MCPClient", 
    "FilesystemMCPClient",
    "BrowserMCPClient",
]
