"""
Multi-Server MCP Client

Composite client that orchestrates multiple specialized MCP server clients.
Replicates the functionality of DirectMCPClient using the new architecture
while maintaining exact compatibility with existing interfaces.
"""

import logging
from pathlib import Path
from typing import Any

from ..clients import (
    BrowserMCPClient,
    Context7MCPClient,
    FilesystemMCPClient,
    GitHubMCPClient,
)
from ..utils import (
    Context7Documentation,
    FilesystemScanResult,
    GitHubSearchResult,
    MCPConfigManager,
    ensure_serializable,
)

logger = logging.getLogger(__name__)


class MultiServerMCPClient:
    """
    Composite MCP client that orchestrates multiple specialized server clients.

    This class provides the exact same interface as DirectMCPClient but uses
    the new architecture with specialized clients. It maintains full backward
    compatibility while providing better organization and maintainability.
    """

    def __init__(self, config_path: str | Path):
        """
        Initialize multi-server MCP client.

        Args:
            config_path: Path to MCP configuration file
        """
        self.config_path = str(config_path)  # Store as string for serialization
        self.config_manager = MCPConfigManager.from_file(config_path)

        # Initialize specialized clients
        self._github_client: GitHubMCPClient | None = None
        self._context7_client: Context7MCPClient | None = None
        self._filesystem_client: FilesystemMCPClient | None = None
        self._browser_client: BrowserMCPClient | None = None

        logger.info(f"Initialized MultiServerMCPClient with config: {config_path}")

    def _get_github_client(self) -> GitHubMCPClient:
        """Get or create GitHub client."""
        if self._github_client is None:
            self._github_client = GitHubMCPClient(self.config_path)
        return self._github_client

    def _get_context7_client(self) -> Context7MCPClient:
        """Get or create Context7 client."""
        if self._context7_client is None:
            self._context7_client = Context7MCPClient(self.config_path)
        return self._context7_client

    def _get_filesystem_client(self) -> FilesystemMCPClient:
        """Get or create Filesystem client."""
        if self._filesystem_client is None:
            self._filesystem_client = FilesystemMCPClient(self.config_path)
        return self._filesystem_client

    def _get_browser_client(self) -> BrowserMCPClient:
        """Get or create Browser client."""
        if self._browser_client is None:
            self._browser_client = BrowserMCPClient(self.config_path)
        return self._browser_client

    async def health_check_all(self) -> dict[str, bool]:
        """
        Check health of all configured MCP servers.

        Returns:
            Dictionary mapping server names to health status
        """
        health_status = {}

        # Check available servers and their health
        for server_name in self.config_manager.list_servers():
            try:
                if "github" in server_name:
                    client = self._get_github_client()
                elif "context7" in server_name:
                    client = self._get_context7_client()
                elif "filesystem" in server_name:
                    client = self._get_filesystem_client()
                elif "browser" in server_name:
                    client = self._get_browser_client()
                else:
                    logger.warning(f"Unknown server type: {server_name}")
                    health_status[server_name] = False
                    continue

                health_status[server_name] = await client.health_check()

            except Exception as e:
                logger.error(f"Health check failed for {server_name}: {e}")
                health_status[server_name] = False

        return health_status

    # GitHub operations (exact DirectMCPClient interface)

    async def call_github_tools(self, repo_url: str, max_retries: int = 3) -> str:
        """
        Legacy GitHub tools interface - maintains exact DirectMCPClient compatibility.

        Args:
            repo_url: Repository URL to analyze
            max_retries: Maximum retry attempts

        Returns:
            Analysis results as string (exact format as DirectMCPClient)
        """
        github_client = self._get_github_client()
        return await github_client.call_github_tools(repo_url, max_retries)

    async def get_file_contents(self, owner: str, repo: str, path: str) -> str:
        """
        Get file contents from GitHub repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path within repository

        Returns:
            File contents as string
        """
        github_client = self._get_github_client()
        return await github_client.get_file_contents(owner, repo, path)

    async def search_code(self, query: str, sort: str = "indexed") -> str:
        """
        Search code in GitHub repositories.

        Args:
            query: Search query
            sort: Sort order

        Returns:
            Search results as string
        """
        github_client = self._get_github_client()
        return await github_client.search_code(query, sort)

    async def analyze_repository(self, repo_url: str) -> GitHubSearchResult:
        """
        Analyze GitHub repository and return structured results.

        Args:
            repo_url: Repository URL to analyze

        Returns:
            GitHubSearchResult with analysis data
        """
        github_client = self._get_github_client()
        return await github_client.analyze_repository(repo_url)

    async def extract_tech_stack(self, repo_url: str) -> list[str]:
        """
        Extract technology stack from repository analysis.

        Args:
            repo_url: Repository URL to analyze

        Returns:
            List of detected technologies
        """
        github_client = self._get_github_client()
        return await github_client.extract_tech_stack(repo_url)

    # Context7 operations (exact DirectMCPClient interface)

    async def call_context7_tools(
        self,
        search_query: str,
        library_id: str | None = None,
        topic: str | None = None,
        max_retries: int = 3,
    ) -> str:
        """
        Legacy Context7 tools interface - maintains exact DirectMCPClient compatibility.

        Args:
            search_query: Search query for documentation
            library_id: Optional Context7-compatible library ID
            topic: Optional topic to focus on
            max_retries: Maximum retry attempts

        Returns:
            Documentation results as string (exact format as DirectMCPClient)
        """
        context7_client = self._get_context7_client()
        return await context7_client.call_context7_tools(
            search_query, library_id, topic, max_retries
        )

    async def get_library_docs(
        self, library_id: str, topic: str | None = None
    ) -> Context7Documentation:
        """
        Get documentation for a specific library from Context7.

        Args:
            library_id: Context7-compatible library ID
            topic: Optional topic to focus documentation on

        Returns:
            Context7Documentation object with extracted content
        """
        context7_client = self._get_context7_client()
        return await context7_client.get_library_docs(library_id, topic)

    async def search_documentation(
        self, search_query: str, library_id: str | None = None, topic: str | None = None
    ) -> str:
        """
        Search documentation using Context7.

        Args:
            search_query: Search query for documentation
            library_id: Optional specific library to search
            topic: Optional topic to focus on

        Returns:
            Documentation search results as string
        """
        context7_client = self._get_context7_client()
        return await context7_client.search_documentation(
            search_query, library_id, topic
        )

    # Filesystem operations (future expansion)

    async def read_file(self, file_path: str) -> str:
        """
        Read file contents through MCP filesystem server.

        Args:
            file_path: Path to file to read

        Returns:
            File contents as string
        """
        filesystem_client = self._get_filesystem_client()
        return await filesystem_client.read_file(file_path)

    async def search_files(
        self, pattern: str, base_path: str = "."
    ) -> FilesystemScanResult:
        """
        Search for files matching a pattern.

        Args:
            pattern: Search pattern
            base_path: Base directory to search from

        Returns:
            FilesystemScanResult with search results
        """
        filesystem_client = self._get_filesystem_client()
        return await filesystem_client.search_files(pattern, base_path)

    # Browser operations (future expansion)

    async def navigate_to_url(self, url: str) -> str:
        """
        Navigate to a URL and return page content.

        Args:
            url: URL to navigate to

        Returns:
            Page content as string
        """
        browser_client = self._get_browser_client()
        return await browser_client.navigate_to_url(url)

    # Configuration and utility methods

    def get_config(self) -> dict[str, Any]:
        """
        Get the full MCP configuration.

        Returns:
            Complete configuration dictionary
        """
        return self.config_manager.get_config()

    def list_servers(self) -> list[str]:
        """
        List all configured MCP servers.

        Returns:
            List of server names
        """
        return self.config_manager.list_servers()

    def validate_config(self) -> bool:
        """
        Validate MCP configuration.

        Returns:
            True if configuration is valid
        """
        status = self.config_manager.validate_config()
        return status.is_valid

    # Class methods for compatibility with DirectMCPClient patterns

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> "MultiServerMCPClient":
        """
        Create client from configuration file - maintains DirectMCPClient interface.

        Args:
            config_path: Path to MCP configuration file

        Returns:
            MultiServerMCPClient instance
        """
        return cls(config_path)

    def ensure_serializable(self, data: Any) -> Any:
        """
        Ensure data is serializable - maintains DirectMCPClient interface.

        Args:
            data: Data to test for serializability

        Returns:
            The same data if serializable
        """
        return ensure_serializable(data)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"MultiServerMCPClient(config_path='{self.config_path}')"
