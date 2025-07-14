"""
Logging configuration for GraphMCP structured logging system.

Environment-aware configuration with constant log file path
and dual-sink threshold management.
"""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class LoggingConfig:
    """
    Centralized logging configuration with constant LOG_FILEPATH.
    
    Supports environment-based configuration with Claude Code-style
    output format options and independent threshold management.
    """
    # Constant log filepath as requested
    log_filepath: str = "dbworkflow.log"
    
    # Claude Code-style output format options
    output_format: Literal["json", "console", "dual"] = "dual"
    
    # Independent threshold management for dual sinks
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    
    # File rotation settings
    max_file_size_mb: int = 100
    backup_count: int = 5
    
    # Feature toggles
    structured_data_enabled: bool = True
    progress_tracking_enabled: bool = True
    json_pretty_print: bool = False
    
    @classmethod
    def for_automation(cls) -> 'LoggingConfig':
        """
        Configuration optimized for automation/CI environments.
        
        Returns:
            LoggingConfig: JSON-only output with minimal verbosity
        """
        return cls(
            output_format="json",
            console_level="ERROR",
            file_level="INFO",
            json_pretty_print=False,
            structured_data_enabled=True,
            progress_tracking_enabled=False
        )
    
    @classmethod
    def for_development(cls) -> 'LoggingConfig':
        """
        Configuration optimized for development environments.
        
        Returns:
            LoggingConfig: Dual output with maximum verbosity
        """
        return cls(
            output_format="dual",
            console_level="DEBUG",
            file_level="DEBUG",
            json_pretty_print=True,
            structured_data_enabled=True,
            progress_tracking_enabled=True
        )
    
    @classmethod
    def for_production(cls) -> 'LoggingConfig':
        """
        Configuration optimized for production environments.
        
        Returns:
            LoggingConfig: File logging with console errors only
        """
        return cls(
            output_format="dual",
            console_level="ERROR",
            file_level="DEBUG",
            json_pretty_print=False,
            structured_data_enabled=True,
            progress_tracking_enabled=True
        )
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """
        Load configuration from environment variables.
        
        Environment variables:
        - GRAPHMCP_OUTPUT_FORMAT: json|console|dual (default: dual)
        - GRAPHMCP_CONSOLE_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
        - GRAPHMCP_FILE_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: DEBUG)
        - GRAPHMCP_LOG_FILE: Custom log file path (default: dbworkflow.log)
        - GRAPHMCP_JSON_PRETTY: true|false (default: false)
        
        Returns:
            LoggingConfig: Environment-configured instance
        """
        return cls(
            log_filepath=os.getenv("GRAPHMCP_LOG_FILE", "dbworkflow.log"),
            output_format=os.getenv("GRAPHMCP_OUTPUT_FORMAT", "dual"),
            console_level=os.getenv("GRAPHMCP_CONSOLE_LEVEL", "INFO").upper(),
            file_level=os.getenv("GRAPHMCP_FILE_LEVEL", "DEBUG").upper(),
            max_file_size_mb=int(os.getenv("GRAPHMCP_MAX_FILE_SIZE_MB", "100")),
            backup_count=int(os.getenv("GRAPHMCP_BACKUP_COUNT", "5")),
            json_pretty_print=os.getenv("GRAPHMCP_JSON_PRETTY", "false").lower() == "true",
            structured_data_enabled=os.getenv("GRAPHMCP_STRUCTURED_DATA", "true").lower() == "true",
            progress_tracking_enabled=os.getenv("GRAPHMCP_PROGRESS_TRACKING", "true").lower() == "true"
        )
    
    def is_level_enabled(self, level: str, sink: Literal["console", "file"]) -> bool:
        """
        Check if a log level is enabled for a specific sink.
        
        Args:
            level: Log level to check
            sink: Target sink (console or file)
        
        Returns:
            bool: True if level is enabled for the sink
        """
        level_hierarchy = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50
        }
        
        threshold = self.console_level if sink == "console" else self.file_level
        
        return level_hierarchy.get(level.upper(), 0) >= level_hierarchy.get(threshold, 0)
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid
        """
        valid_formats = ["json", "console", "dual"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output_format: {self.output_format}. Must be one of {valid_formats}")
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.console_level.upper() not in valid_levels:
            raise ValueError(f"Invalid console_level: {self.console_level}. Must be one of {valid_levels}")
        
        if self.file_level.upper() not in valid_levels:
            raise ValueError(f"Invalid file_level: {self.file_level}. Must be one of {valid_levels}")
        
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.backup_count < 0:
            raise ValueError("backup_count must be non-negative")