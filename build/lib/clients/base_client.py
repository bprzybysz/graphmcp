"""
Base MCP client providing common patterns and utilities.

This base class encapsulates common MCP operations like session management,
configuration loading, retry logic, and health checks. Specific client types
inherit from this to add specialized functionality.
"""

import logging
from pathlib import Path
from typing import Any

from graphmcp.utils import (
    MCPConfigManager,
    MCPRetryHandler,
    MCPSessionManager,
    MCPUtilityError,
    ensure_serializable,
)

logger = logging.getLogger(__name__)


class BaseMCPClient:
    """
    Base MCP client providing common patterns and utilities.

    This base class encapsulates common MCP operations like session management,
    configuration loading, retry logic, and health checks. Specific client types
    inherit from this to add specialized functionality.
    """

    def __init__(self, config_path: str | Path):
        """
        Initialize base MCP client.

        Args:
            config_path: Path to MCP configuration JSON file
        """
        self.config_path = str(config_path)
        self.config_manager = MCPConfigManager.from_file(config_path)
        self.session_manager = MCPSessionManager(self.config_manager)
        self.retry_handler = MCPRetryHandler(max_retries=3, base_delay=1.0, max_delay=30.0)

        logger.info(f"Initialized MCP client with config: {self.config_path}")

    async def health_check(self) -> dict[str, bool]:
        """
        Check health of all configured MCP servers.

        Returns:
            Dictionary mapping server names to health status
        """
        logger.info("Performing health check on all MCP servers")

        health_status = {}

        for server_name in self.config_manager.list_servers():
            try:
                async with self.session_manager.session_context(server_name) as session:
                    # Try to list tools as a simple health check
                    tools = await self.session_manager.list_tools(session)
                    health_status[server_name] = len(tools) > 0
                    logger.debug(f"Server {server_name}: {len(tools)} tools available")

            except Exception as e:
                logger.error(f"Health check failed for server {server_name}: {e}")
                health_status[server_name] = False

        logger.info(f"Health check complete: {sum(health_status.values())}/{len(health_status)} servers healthy")
        return health_status

    async def call_tool_with_retry(self, server_name: str, tool_name: str, params: dict) -> Any:
        """
        Call an MCP tool with retry logic.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            params: Parameters for the tool

        Returns:
            Tool result
        """
        async def _tool_operation():
            async with self.session_manager.session_context(server_name) as session:
                return await self.session_manager.call_tool(session, tool_name, params)

        return await self.retry_handler.with_retry(_tool_operation)

    async def list_available_tools(self, server_name: str) -> list[str]:
        """
        List available tools for a specific server.

        Args:
            server_name: Name of the MCP server

        Returns:
            List of available tool names
        """
        async with self.session_manager.session_context(server_name) as session:
            tools = await self.session_manager.list_tools(session)
            return [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools] 