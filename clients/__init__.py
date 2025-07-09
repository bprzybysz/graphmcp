"""
GraphMCP Clients Package
"""
from .base import BaseMCPClient
from .repomix import RepomixMCPClient
from .slack import SlackMCPClient
from .github import GitHubMCPClient
from .filesystem import FilesystemMCPClient
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# The document also mentioned Context7 and Browser clients.
# We can add placeholder classes for them for completeness,
# even if they are not used in the final workflow.

class Context7MCPClient(BaseMCPClient):
    SERVER_NAME = "ovr_context7"
    def __init__(self, config_path):
        super().__init__(config_path)

    async def list_available_tools(self) -> List[str]:
        """
        List available Context7 MCP tools.
        """
        try:
            result = await self._send_mcp_request("tools/list", {})
            return [tool.get("name") for tool in result.get("tools", [])]
        except Exception as e:
            logger.warning(f"Failed to list Context7 tools: {e}")
            return [
                "resolve-library-id",
                "get-library-docs"
            ]

    async def health_check(self) -> bool:
        """
        Perform a health check by listing available Context7 tools.
        """
        try:
            await self.list_available_tools()
            logger.debug(f"Context7MCPClient ({self.server_name}) health check successful.")
            return True
        except Exception as e:
            logger.warning(f"Context7MCPClient ({self.server_name}) health check failed: {e}")
            return False

    async def resolve_library_id(self, library_name: str) -> Dict[str, Any]:
        """
        Resolve a library ID based on its name.
        """
        try:
            result = await self.call_tool_with_retry("resolve-library-id", {"libraryName": library_name})
            return result
        except Exception as e:
            logger.warning(f"Failed to resolve library ID for {library_name}: {e}")
            return {"error": str(e)}

    async def get_library_docs(self, library_id: str, topic: str = None, tokens: int = 10000) -> Dict[str, Any]:
        """
        Get documentation for a specific library.
        """
        try:
            params = {
                "context7CompatibleLibraryID": library_id,
                "tokens": tokens
            }
            if topic:
                params["topic"] = topic
                
            result = await self.call_tool_with_retry("get-library-docs", params)
            return result
        except Exception as e:
            logger.warning(f"Failed to get library docs for {library_id}: {e}")
            return {"error": str(e)}

class BrowserMCPClient(BaseMCPClient):
    SERVER_NAME = "ovr_browser"
    def __init__(self, config_path):
        super().__init__(config_path)

    async def list_available_tools(self) -> List[str]:
        """
        List available Browser MCP tools.
        """
        try:
            result = await self._send_mcp_request("tools/list", {})
            return [tool.get("name") for tool in result.get("tools", [])]
        except Exception as e:
            logger.warning(f"Failed to list Browser tools: {e}")
            return [
                "playwright_navigate",
                "playwright_get_visible_text",
                "playwright_click"
            ]

    async def health_check(self) -> bool:
        """
        Perform a health check by listing available Browser tools.
        """
        try:
            await self.list_available_tools()
            logger.debug(f"BrowserMCPClient ({self.server_name}) health check successful.")
            return True
        except Exception as e:
            logger.warning(f"BrowserMCPClient ({self.server_name}) health check failed: {e}")
            return False

    # Example method for BrowserMCPClient (navigate and get text)
    async def navigate_and_get_text(self, url: str) -> str:
        """
        Navigate to a URL and get visible text content.
        """
        try:
            # Use a dummy string for the random_string parameter of playwright_get_visible_text
            result = await self._send_mcp_request("tools/playwright_navigate", {"url": url})
            if result: # Check if navigation was successful
                text_result = await self._send_mcp_request("tools/playwright_get_visible_text", {"random_string": "dummy"})
                return text_result.get("text", "")
            return ""
        except Exception as e:
            logger.error(f"Failed to navigate and get text for {url}: {e}")
            return ""

__all__ = [
    "BaseMCPClient",
    "RepomixMCPClient",
    "SlackMCPClient",
    "GitHubMCPClient",
    "FilesystemMCPClient",
    "Context7MCPClient",
    "BrowserMCPClient",
] 