"""
GraphMCP Clients Package
"""
from .base import BaseMCPClient
from .repomix import RepomixMCPClient
from .slack import SlackMCPClient
from .github import GitHubMCPClient
from .filesystem import FilesystemMCPClient

# The document also mentioned Context7 and Browser clients.
# We can add placeholder classes for them for completeness,
# even if they are not used in the final workflow.

class Context7MCPClient(BaseMCPClient):
    SERVER_NAME = "context7"
    def __init__(self, config_path):
        super().__init__(config_path)

class BrowserMCPClient(BaseMCPClient):
    SERVER_NAME = "browser"
    def __init__(self, config_path):
        super().__init__(config_path)


__all__ = [
    "BaseMCPClient",
    "RepomixMCPClient",
    "SlackMCPClient",
    "GitHubMCPClient",
    "FilesystemMCPClient",
    "Context7MCPClient",
    "BrowserMCPClient",
] 