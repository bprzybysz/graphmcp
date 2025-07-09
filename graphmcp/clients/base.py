"""
Base client for all MCP (Model-Context-Protocol) server interactions.

This module provides the abstract base class for MCP client implementations
that communicate with real MCP servers via the Model Context Protocol.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import subprocess
import tempfile
import os

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
    
    def __init__(self, config_path: str | Path, server_name: str):
        """
        Initialize MCP client for a specific server.
        
        Args:
            config_path: Path to MCP configuration file
            server_name: Name of the MCP server in the configuration
        """
        self.config_path = Path(config_path)
        self.server_name = server_name
        self._config = None
        self._process = None
        self._session_id = None
        
        logger.info(f"Initialized {self.__class__.__name__} for server '{server_name}'")

    async def _load_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from config file."""
        if self._config is None:
            if not self.config_path.exists():
                raise MCPConnectionError(f"MCP config file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
            
            servers = full_config.get('mcpServers', {})
            if self.server_name not in servers:
                raise MCPConnectionError(f"Server '{self.server_name}' not found in config")
            
            self._config = servers[self.server_name]
            logger.debug(f"Loaded config for server '{self.server_name}'")
        
        return self._config

    async def _start_server_process(self) -> subprocess.Popen:
        """Start the MCP server process."""
        config = await self._load_config()
        command = config.get('command')
        args = config.get('args', [])
        env_vars = config.get('env', {})
        
        if not command:
            raise MCPConnectionError(f"No command specified for server '{self.server_name}'")
        
        # Prepare environment
        env = os.environ.copy()
        env.update(env_vars)
        
        # Start process
        full_command = [command] + args
        logger.debug(f"Starting MCP server: {' '.join(full_command)}")
        
        try:
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=0
            )
            
            # Wait a moment for server to initialize
            await asyncio.sleep(0.1)
            
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else "No error output"
                raise MCPConnectionError(f"MCP server failed to start: {stderr}")
            
            self._process = process
            logger.info(f"MCP server '{self.server_name}' started successfully")
            return process
            
        except Exception as e:
            raise MCPConnectionError(f"Failed to start MCP server '{self.server_name}': {e}")

    async def _send_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server."""
        if not self._process:
            await self._start_server_process()
        
        request_id = f"req_{asyncio.current_task().get_name()}_{id(params)}"
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            self._process.stdin.write(request_json)
            self._process.stdin.flush()
            
            # Read response
            response_line = self._process.stdout.readline()
            if not response_line:
                raise MCPConnectionError("No response from MCP server")
            
            response = json.loads(response_line.strip())
            
            # Check for errors
            if 'error' in response:
                error = response['error']
                raise MCPToolError(f"MCP tool error: {error.get('message', 'Unknown error')}")
            
            return response.get('result', {})
            
        except json.JSONDecodeError as e:
            raise MCPConnectionError(f"Invalid JSON response from MCP server: {e}")
        except Exception as e:
            raise MCPConnectionError(f"MCP communication error: {e}")

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
                
                # Prepare MCP tool call request
                mcp_params = {
                    "name": tool_name,
                    "arguments": params
                }
                
                # Send tool call request
                result = await self._send_mcp_request("tools/call", mcp_params)
                
                logger.debug(f"Tool '{tool_name}' completed successfully")
                return result
                
            except Exception as e:
                last_error = e
                if attempt < retry_count:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Tool '{tool_name}' failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Tool '{tool_name}' failed after {retry_count + 1} attempts: {e}")
        
        raise MCPToolError(f"Tool '{tool_name}' failed after {retry_count + 1} attempts: {last_error}")

    async def close(self):
        """Close MCP server connection and cleanup resources."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.sleep(0.1)
                if self._process.poll() is None:
                    self._process.kill()
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
        """
        List available tools for this MCP server.
        
        Returns:
            List of available tool names
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(server='{self.server_name}', config='{self.config_path}')" 