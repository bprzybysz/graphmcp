"""
Base MCP Client

Provides common functionality for all specialized MCP server clients.
Extracted from proven patterns in db_decommission_workflow for maximum
compatibility and reliability.
"""

import logging
from pathlib import Path
from typing import Any

from ..utils import (
    MCPConfigManager,
    MCPRetryHandler,
    MCPSessionManager,
    ensure_serializable,
)

logger = logging.getLogger(__name__)


class BaseMCPClient:
    """
    Base class for specialized MCP server clients.
    
    Provides common functionality like configuration management,
    session handling, retry logic, and health checks that all
    specialized clients need.
    
    Design principles:
    - Never store actual mcp_use client/session objects
    - Always ensure returned data is serializable
    - Use proven patterns from working implementation
    - Provide consistent error handling and logging
    """

    def __init__(self, config_path: str | Path, server_name: str):
        """
        Initialize base MCP client.
        
        Args:
            config_path: Path to MCP configuration file
            server_name: Name of the MCP server this client manages
        """
        self.config_path = str(config_path)  # Store as string for serialization
        self.server_name = server_name
        
        # Initialize utilities using proven patterns
        self.config_manager = MCPConfigManager.from_file(config_path)
        self.session_manager = MCPSessionManager(self.config_manager)
        self.retry_handler = MCPRetryHandler()
        
        # Validate server exists in configuration
        self._validate_server_config()
        
        logger.info(f"Initialized {self.__class__.__name__} for server: {server_name}")

    def _validate_server_config(self) -> None:
        """
        Validate that the server is properly configured.
        
        Raises:
            MCPConfigError: If server is not found or misconfigured
        """
        try:
            # This will raise MCPConfigError if server doesn't exist
            server_config = self.config_manager.get_server_config(self.server_name)
            logger.debug(f"Validated server configuration for {self.server_name}")
        except Exception as e:
            logger.error(f"Server configuration validation failed for {self.server_name}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if the MCP server is healthy and responsive.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            health_status = await self.session_manager.health_check(self.server_name)
            is_healthy = health_status.get(self.server_name, False)
            
            if is_healthy:
                logger.debug(f"Health check passed for {self.server_name}")
            else:
                logger.warning(f"Health check failed for {self.server_name}")
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check error for {self.server_name}: {e}")
            return False

    async def list_available_tools(self) -> list[str]:
        """
        List all available tools for this MCP server.
        
        Returns:
            List of tool names (guaranteed serializable)
        """
        try:
            async with self.session_manager.session_context(self.server_name) as session:
                tools = await self.session_manager.list_tools(session)
                
                # Ensure result is serializable
                ensure_serializable(tools)
                
                logger.debug(f"Found {len(tools)} tools for {self.server_name}: {tools}")
                return tools
                
        except Exception as e:
            logger.error(f"Failed to list tools for {self.server_name}: {e}")
            return []  # Return empty list (serializable)

    async def call_tool_with_retry(self, tool_name: str, params: dict, max_retries: int = 3) -> Any:
        """
        Call an MCP tool with retry logic using proven patterns.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            max_retries: Maximum retry attempts
            
        Returns:
            Tool result (guaranteed serializable)
        """
        # Temporarily override retry settings if different from default
        original_max_retries = self.retry_handler.max_retries
        self.retry_handler.max_retries = max_retries

        try:
            async def _tool_operation():
                async with self.session_manager.session_context(self.server_name) as session:
                    return await self.session_manager.call_tool(session, tool_name, params)

            result = await self.retry_handler.with_retry(_tool_operation)
            
            # Ensure result is serializable
            ensure_serializable(result)
            
            logger.debug(f"Successfully called tool {tool_name} on {self.server_name}")
            return result
            
        finally:
            # Restore original retry settings
            self.retry_handler.max_retries = original_max_retries

    def get_server_config(self) -> dict[str, Any]:
        """
        Get the configuration for this server.
        
        Returns:
            Server configuration dictionary
        """
        return self.config_manager.get_server_config(self.server_name)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(server_name='{self.server_name}', config_path='{self.config_path}')" 