"""
Example: GraphMCP Base Client Pattern

This demonstrates the pattern for creating MCP clients in the GraphMCP framework.
Key patterns to follow:
- Abstract base class with SERVER_NAME class attribute
- Async context manager support
- Comprehensive error handling with custom exceptions
- Configuration loading with environment variable substitution
- Health check and tool listing abstractions
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class MCPConnectionError(Exception):
    """Raised when MCP server connection fails."""
    pass

class MCPToolError(Exception):
    """Raised when MCP tool execution fails."""
    pass

class BaseMCPClient(ABC):
    """
    Abstract base class for MCP clients that communicate with real MCP servers.
    
    This class handles the low-level communication with MCP servers via stdio,
    session management, and error handling.
    """
    SERVER_NAME: str = None  # Subclasses must override this

    def __init__(self, config_path: str | Path):
        """
        Initialize MCP client.
        
        Args:
            config_path: Path to MCP configuration file
        """
        if self.SERVER_NAME is None:
            raise NotImplementedError(
                f"Subclasses of BaseMCPClient must define a SERVER_NAME class attribute."
            )

        self.config_path = Path(config_path)
        self.server_name = self.SERVER_NAME
        self._config = None
        self._process = None
        
    async def _load_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from config file and .env."""
        if self._config is None:
            # Load environment variables from .env file first
            load_dotenv()

            # Load secrets.json if it exists
            secrets_path = Path("secrets.json")
            if secrets_path.exists():
                with open(secrets_path, 'r') as f:
                    secrets = json.load(f)
                for key, value in secrets.items():
                    os.environ[key] = str(value)

            if not self.config_path.exists():
                raise MCPConnectionError(f"MCP config file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
            
            servers = full_config.get('mcpServers', {})
            if self.server_name not in servers:
                raise MCPConnectionError(f"Server '{self.server_name}' not found in config")
            
            self._config = servers[self.server_name]
        
        return self._config

    async def call_tool_with_retry(self, tool_name: str, params: Dict[str, Any], retry_count: int = 3) -> Any:
        """
        Call MCP tool with automatic retry on failure.
        
        Args:
            tool_name: Name of the MCP tool to call
            params: Parameters to pass to the tool
            retry_count: Number of retry attempts
            
        Returns:
            Tool execution result
            
        Raises:
            MCPToolError: If tool execution fails after all retries
        """
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"Calling tool '{tool_name}' (attempt {attempt + 1}/{retry_count + 1})")
                # Tool execution logic here
                return {"success": True, "result": "mock_result"}
                
            except Exception as e:
                last_error = e
                if attempt < retry_count:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Tool '{tool_name}' failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
        
        raise MCPToolError(f"Tool '{tool_name}' failed after {retry_count + 1} attempts: {last_error}")

    async def close(self):
        """Close MCP server connection and cleanup resources."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
                logger.info(f"MCP server '{self.server_name}' closed")
            except Exception as e:
                logger.warning(f"Error closing MCP server: {e}")
            finally:
                self._process = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()

    @abstractmethod
    async def list_available_tools(self) -> list[str]:
        """List available tools for this MCP server."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Perform a health check on the MCP server."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(server='{self.server_name}', config='{self.config_path}')"