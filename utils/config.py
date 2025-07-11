"""
MCP Configuration Manager

Handles MCP configuration loading and validation using proven patterns
from the working DirectMCPClient implementation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from .data_models import MCPConfigStatus, MCPServerConfig
from .exceptions import MCPConfigError

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """
    Handles MCP configuration loading and validation.

    Extracted from proven patterns in DirectMCPClient._load_and_validate_config()
    to ensure compatibility with working MCP server configurations.
    """

    def __init__(self, config_path: str | Path, config_data: dict[str, Any] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to MCP configuration file
            config_data: Optional pre-loaded configuration data
        """
        self.config_path = str(config_path)  # Store as string for serialization
        self._config_data = config_data
        self._validation_status: MCPConfigStatus | None = None

    @classmethod
    def from_file(cls, config_path: str | Path) -> "MCPConfigManager":
        """
        Create configuration manager from file.

        Args:
            config_path: Path to MCP configuration JSON file

        Returns:
            MCPConfigManager instance

        Raises:
            MCPConfigError: If file cannot be loaded or is invalid
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise MCPConfigError(
                f"MCP configuration file not found: {config_path}",
                config_path=str(config_path),
            )

        try:
            with open(config_path) as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise MCPConfigError(
                f"Invalid JSON in MCP config file: {e}", config_path=str(config_path)
            )
        except Exception as e:
            raise MCPConfigError(
                f"Failed to read config file: {e}", config_path=str(config_path)
            )

        return cls(config_path, config_data)

    def _load_and_validate_config(self) -> dict[str, Any]:
        """
        Load and validate MCP configuration from file.

        This is extracted EXACTLY from DirectMCPClient._load_and_validate_config()
        to maintain compatibility with working configurations.

        Returns:
            Validated configuration dictionary

        Raises:
            MCPConfigError: If configuration is invalid
        """
        if self._config_data is not None:
            config = self._config_data
        else:
            config_path = Path(self.config_path)
            if not config_path.exists():
                raise MCPConfigError(
                    f"MCP configuration file not found: {config_path}",
                    config_path=self.config_path,
                )

            try:
                with open(config_path) as f:
                    config = json.load(f)
            except json.JSONDecodeError as e:
                raise MCPConfigError(
                    f"Invalid JSON in MCP config file: {e}",
                    config_path=self.config_path,
                )

        # Validation logic extracted exactly from working implementation
        if "mcpServers" not in config:
            raise MCPConfigError(
                "Configuration missing 'mcpServers' section",
                config_path=self.config_path,
            )

        # Validate server configurations
        for server_name, server_config in config["mcpServers"].items():
            if not isinstance(server_config, dict):
                raise MCPConfigError(
                    f"Invalid server configuration for {server_name}",
                    config_path=self.config_path,
                )

            # Check for required fields based on connection type
            if "command" not in server_config and "url" not in server_config:
                raise MCPConfigError(
                    f"Server {server_name} missing 'command' or 'url'",
                    config_path=self.config_path,
                )

        logger.info(
            f"Validated MCP configuration with {len(config['mcpServers'])} servers"
        )
        return config

    def get_config(self) -> dict[str, Any]:
        """
        Get the full validated configuration.

        Returns:
            Complete configuration dictionary
        """
        return self._load_and_validate_config()

    def get_server_config(self, server_name: str) -> dict[str, Any]:
        """
        Get specific server configuration.

        Args:
            server_name: Name of the server to get config for

        Returns:
            Server configuration dictionary

        Raises:
            MCPConfigError: If server not found
        """
        config = self.get_config()
        servers = config.get("mcpServers", {})

        if server_name not in servers:
            available = list(servers.keys())
            raise MCPConfigError(
                f"Server '{server_name}' not found in configuration. "
                f"Available servers: {available}",
                config_path=self.config_path,
            )

        return servers[server_name]

    def list_servers(self) -> list[str]:
        """
        List all configured MCP servers.

        Returns:
            List of server names
        """
        config = self.get_config()
        return list(config.get("mcpServers", {}).keys())

    def validate_config(self) -> MCPConfigStatus:
        """
        Validate configuration and return status.

        Returns:
            MCPConfigStatus with validation results
        """
        errors = []
        server_count = 0
        is_valid = True

        try:
            config = self._load_and_validate_config()
            server_count = len(config.get("mcpServers", {}))

            # Additional validation beyond basic structure
            for server_name, server_config in config["mcpServers"].items():
                # Validate environment variable references
                env_vars = server_config.get("env", {})
                for var_name, var_value in env_vars.items():
                    if (
                        isinstance(var_value, str)
                        and var_value.startswith("${")
                        and var_value.endswith("}")
                    ):
                        env_name = var_value[2:-1]  # Remove ${ and }
                        if env_name not in os.environ:
                            errors.append(
                                f"Server '{server_name}': Environment variable '{env_name}' not set"
                            )

                # Validate command structure
                if "command" in server_config:
                    command = server_config["command"]
                    if not isinstance(command, str) or not command.strip():
                        errors.append(
                            f"Server '{server_name}': Invalid command '{command}'"
                        )

                # Validate args structure
                if "args" in server_config:
                    args = server_config["args"]
                    if not isinstance(args, list):
                        errors.append(f"Server '{server_name}': 'args' must be a list")

            if errors:
                is_valid = False

        except MCPConfigError as e:
            is_valid = False
            errors.append(str(e))
        except Exception as e:
            is_valid = False
            errors.append(f"Unexpected validation error: {e}")

        self._validation_status = MCPConfigStatus(
            config_path=self.config_path,
            is_valid=is_valid,
            server_count=server_count,
            validation_errors=errors,
        )

        return self._validation_status

    def get_server_args(self, server_name: str) -> list[str]:
        """
        Get npx args for server - supports version locking.

        Args:
            server_name: Name of the server

        Returns:
            List of command arguments including command

        Example:
            For config with "command": "npx", "args": ["@modelcontextprotocol/server-github@0.5.0"]
            Returns: ["npx", "@modelcontextprotocol/server-github@0.5.0"]
        """
        server_config = self.get_server_config(server_name)

        command = server_config.get("command", "")
        args = server_config.get("args", [])

        if command:
            return [command] + args
        else:
            return args

    def resolve_env_vars(self, server_name: str) -> dict[str, str]:
        """
        Resolve environment variables for a server.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary of resolved environment variables
        """
        server_config = self.get_server_config(server_name)
        env_config = server_config.get("env", {})
        resolved_env = {}

        for var_name, var_value in env_config.items():
            if (
                isinstance(var_value, str)
                and var_value.startswith("${")
                and var_value.endswith("}")
            ):
                env_name = var_value[2:-1]  # Remove ${ and }
                resolved_value = os.environ.get(
                    env_name, var_value
                )  # Fallback to original if not found
                resolved_env[var_name] = resolved_value
            else:
                resolved_env[var_name] = str(var_value)

        return resolved_env

    def get_server_config_object(self, server_name: str) -> MCPServerConfig:
        """
        Get server configuration as typed object.

        Args:
            server_name: Name of the server

        Returns:
            MCPServerConfig object
        """
        config = self.get_server_config(server_name)

        return MCPServerConfig(
            name=server_name,
            command=config.get("command", ""),
            args=config.get("args", []),
            env=config.get("env", {}),
            url=config.get("url"),
            timeout=config.get("timeout", 30),
        )

    @property
    def is_valid(self) -> bool | None:
        """Check if configuration is valid (requires validation to have been run)."""
        if self._validation_status is None:
            return None
        return self._validation_status.is_valid
