"""
Base client for all MCP (Model-Context-Protocol) server interactions.

This module provides the abstract base class for MCP client implementations
that communicate with real MCP servers via the Model Context Protocol.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class MCPConnectionError(Exception):
    """Raised when MCP server connection fails."""



class MCPToolError(Exception):
    """Raised when MCP tool execution fails."""



class BaseMCPClient(ABC):
    """
    Abstract base class for MCP clients that communicate with real MCP servers.

    This class handles the low-level communication with MCP servers via stdio,
    session management, and error handling.
    """

    SERVER_NAME: str = None  # Subclasses must override this

    def __init__(self, config_path: str | Path):
        """
        Initialize MCP client. The server_name is determined by the class's SERVER_NAME attribute.

        Args:
            config_path: Path to MCP configuration file
        """
        if self.SERVER_NAME is None:
            raise NotImplementedError(
                f"Subclasses of BaseMCPClient must define a SERVER_NAME class attribute. "
                f"For client {self.__class__.__name__}, SERVER_NAME is not set."
            )

        self.config_path = Path(config_path)
        self.server_name = self.SERVER_NAME  # Get from class attribute
        self._config = None
        self._process = None
        self._session_id = None

        logger.info(
            f"Initialized {self.__class__.__name__} for server '{self.server_name}'"
        )

    async def _load_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from config file and .env."""
        if self._config is None:
            # Load environment variables from .env file first
            load_dotenv()

            # DEBUG: Print initial environment values for GitHub token
            if self.server_name == "ovr_github":
                initial_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "NOT_SET")
                logger.warning(
                    f"🔍 Initial env GITHUB_PERSONAL_ACCESS_TOKEN: '{initial_token}' (length: {len(initial_token)})"
                )

            # Overwrite with secrets.json if it exists
            secrets_path = Path("secrets.json")
            if secrets_path.exists():
                logger.info("Found secrets.json, loading secrets...")
                with open(secrets_path, "r") as f:
                    secrets = json.load(f)
                for key, value in secrets.items():
                    os.environ[key] = str(value)
                    logger.debug(f"Loaded secret: {key}")

                # DEBUG: Print environment value after loading secrets.json
                if self.server_name == "ovr_github":
                    after_secrets_token = os.getenv(
                        "GITHUB_PERSONAL_ACCESS_TOKEN", "NOT_SET"
                    )
                    logger.warning(
                        f"🔍 After secrets.json GITHUB_PERSONAL_ACCESS_TOKEN: '{after_secrets_token}' (length: {len(after_secrets_token)})"
                    )

            if not self.config_path.exists():
                raise MCPConnectionError(
                    f"MCP config file not found: {self.config_path}"
                )

            with open(self.config_path, "r") as f:
                full_config = json.load(f)

            servers = full_config.get("mcpServers", {})
            if self.server_name not in servers:
                raise MCPConnectionError(
                    f"Server '{self.server_name}' not found in config"
                )

            self._config = servers[self.server_name]
            logger.debug(f"Loaded config for server '{self.server_name}'")

        return self._config

    async def _start_server_process(self) -> asyncio.subprocess.Process:
        """Start the MCP server process using asyncio subprocess."""
        config = await self._load_config()
        command = config.get("command")
        args = config.get("args", [])

        # Environment variables from config.json
        config_env_vars = config.get("env", {})

        # Merge environment variables with proper substitution: .env has highest precedence, then config.json, then system env
        env = os.environ.copy()  # Start with system environment variables

        # Perform variable substitution for config.json environment variables
        for key, value in config_env_vars.items():
            if isinstance(value, str) and value.startswith("$"):
                # Substitute environment variable (remove the $ prefix)
                env_var_name = value[1:]
                substituted_value = os.getenv(env_var_name, "")
                env[key] = substituted_value
                logger.debug(
                    f"Substituted env var {key}=${env_var_name} -> {key}={substituted_value[:4]}...{substituted_value[-4:] if len(substituted_value) > 8 else '***'}"
                )

                # TEMPORARY DEBUG: Print GitHub token substitution details
                if self.server_name == "ovr_github" and "GITHUB" in key.upper():
                    logger.warning(
                        f"🔍 SUBSTITUTION: {key}=${env_var_name} -> '{substituted_value}' (length: {len(substituted_value)})"
                    )
                    logger.warning(
                        f"🔍 os.getenv('{env_var_name}') = '{os.getenv(env_var_name, 'NOT_FOUND')}' (length: {len(os.getenv(env_var_name, ''))})"
                    )
            else:
                env[key] = str(value)

        # Note: load_dotenv() is called in _load_config and already modifies os.environ,
        # so values from .env are implicitly included in os.environ.copy() here.

        # Log sensitive environment variables with truncation
        for key, value in env.items():  # Iterate over the final 'env' dictionary
            if (
                "TOKEN" in key.upper() or "PASSWORD" in key.upper()
            ):  # Heuristic for sensitive vars
                log_value = (
                    f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "******"
                )
                logger.debug(
                    f"Sensitive ENV var for '{self.server_name}': {key}={log_value}"
                )

                # TEMPORARY DEBUG: Print full GitHub token for debugging authentication issues
                if self.server_name == "ovr_github" and "GITHUB" in key.upper():
                    logger.warning(
                        f"🔍 DEBUG GitHub token for '{self.server_name}': {key}='{value}' (length: {len(value)})"
                    )
            else:
                logger.debug(f"ENV var for '{self.server_name}': {key}={value}")

        # Start process
        full_command = [command] + args
        logger.debug(f"Starting MCP server: {' '.join(full_command)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # Wait a moment for server to initialize
            await asyncio.sleep(0.1)

            if process.returncode is not None:
                # Use readuntil with timeout for non-blocking stderr read
                try:
                    stderr_data = await asyncio.wait_for(
                        process.stderr.read(1024), timeout=0.5  # Read up to 1KB
                    )
                    stderr = stderr_data.decode() if stderr_data else "No error output"
                except asyncio.TimeoutError:
                    stderr = "Process failed (stderr timeout)"
                logger.error(f"MCP server failed to start: {stderr}")
                raise MCPConnectionError(f"MCP server failed to start: {stderr}")

            self._process = process
            logger.info(f"MCP server '{self.server_name}' started successfully")
            return process

        except Exception as e:
            raise MCPConnectionError(
                f"Failed to start MCP server '{self.server_name}': {e}"
            )

    async def _send_mcp_request(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server using async I/O."""
        if not self._process:
            await self._start_server_process()

        request_id = f"req_{asyncio.current_task().get_name()}_{id(params)}"

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Log outgoing request
        logger.debug(
            f"Sending MCP request: method={method}, params={json.dumps(params)}"
        )

        try:
            # Send request using async write
            request_json = json.dumps(request) + "\n"
            self._process.stdin.write(request_json.encode())
            await self._process.stdin.drain()

            # Read response using async readline with timeout
            try:
                response_line = await asyncio.wait_for(
                    self._process.stdout.readline(), timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"MCP server '{self.server_name}' response timeout")
                raise MCPConnectionError(
                    f"MCP server '{self.server_name}' response timeout"
                )

            if not response_line:
                # Use timeout for non-blocking stderr read
                try:
                    stderr_data = await asyncio.wait_for(
                        self._process.stderr.read(1024), timeout=0.5
                    )
                    stderr_output = (
                        stderr_data.decode() if stderr_data else "No stderr output"
                    )
                except asyncio.TimeoutError:
                    stderr_output = "No stderr available (timeout)"
                logger.error(f"No response from MCP server. Stderr: {stderr_output}")
                raise MCPConnectionError(
                    f"No response from MCP server. Stderr: {stderr_output}"
                )

            response = json.loads(response_line.decode().strip())

            # Log incoming response, truncate if large
            response_str = json.dumps(response)
            if len(response_str) > 500:  # Adjust threshold as needed
                response_str = (
                    response_str[:250] + "...[TRUNCATED]..." + response_str[-250:]
                )
            logger.debug(f"Received MCP response: {response_str}")

            # Check for errors
            if "error" in response:
                error = response["error"]
                # Read any remaining stderr output for more context on the error
                stderr_output = ""
                if self._process.stderr:
                    try:
                        stderr_data = await asyncio.wait_for(
                            self._process.stderr.read(1024), timeout=0.5
                        )
                        stderr_output = stderr_data.decode() if stderr_data else ""
                    except asyncio.TimeoutError:
                        stderr_output = "stderr unavailable (timeout)"

                error_message = error.get("message", "Unknown error")
                if stderr_output:
                    error_message += f"\nServer Stderr: {stderr_output}"

                logger.error(f"MCP tool error: {error_message}")
                raise MCPToolError(f"MCP tool error: {error_message}")

            return response.get("result", {})

        except json.JSONDecodeError as e:
            # Read any remaining stderr output for more context on the error
            try:
                stderr_data = await asyncio.wait_for(
                    self._process.stderr.read(1024), timeout=0.5
                )
                stderr_output = (
                    stderr_data.decode() if stderr_data else "No stderr output"
                )
            except asyncio.TimeoutError:
                stderr_output = "stderr unavailable (timeout)"
            logger.error(
                f"Invalid JSON response from MCP server: {e}. Stderr: {stderr_output}"
            )
            raise MCPConnectionError(
                f"Invalid JSON response from MCP server: {e}. Stderr: {stderr_output}"
            )
        except Exception as e:
            # Read any remaining stderr output for more context on the error
            try:
                stderr_data = await asyncio.wait_for(
                    self._process.stderr.read(1024), timeout=0.5
                )
                stderr_output = (
                    stderr_data.decode() if stderr_data else "No stderr output"
                )
            except asyncio.TimeoutError:
                stderr_output = "stderr unavailable (timeout)"
            logger.error(f"MCP communication error: {e}. Stderr: {stderr_output}")
            raise MCPConnectionError(
                f"MCP communication error: {e}. Stderr: {stderr_output}"
            )

    async def call_tool_with_retry(
        self, tool_name: str, params: Dict[str, Any], retry_count: int = 3
    ) -> Any:
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
                logger.debug(
                    f"Calling tool '{tool_name}' (attempt {attempt + 1}/{retry_count + 1})"
                )

                # Prepare MCP tool call request
                mcp_params = {"name": tool_name, "arguments": params}

                # Send tool call request
                result = await self._send_mcp_request("tools/call", mcp_params)

                logger.debug(f"Tool '{tool_name}' completed successfully")
                return result

            except Exception as e:
                last_error = e
                if attempt < retry_count:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Tool '{tool_name}' failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Tool '{tool_name}' failed after {retry_count + 1} attempts: {e}"
                    )

        raise MCPToolError(
            f"Tool '{tool_name}' failed after {retry_count + 1} attempts: {last_error}"
        )

    async def close(self):
        """Close MCP server connection and cleanup resources."""
        if self._process:
            try:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()
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

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform a health check on the MCP server to verify it's operational.

        Returns:
            True if the server is healthy, False otherwise.
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(server='{self.server_name}', config='{self.config_path}')"
