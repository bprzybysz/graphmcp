"""
CLI output handler for Claude Code-style command line integration.

Provides --output-format flag support and tool-compatible JSON streaming
for automation and external tool integration.
"""

import sys
import json
import argparse
from typing import Dict, Any, Optional

from .config import LoggingConfig
from .data_models import LogEntry


class CLIOutputHandler:
    """Claude Code-inspired CLI output formatting and flag handling."""
    
    @staticmethod
    def add_logging_args(parser: argparse.ArgumentParser) -> None:
        """
        Add logging-related CLI arguments to argument parser.
        
        Args:
            parser: ArgumentParser to add arguments to
        """
        logging_group = parser.add_argument_group('logging options')
        
        logging_group.add_argument(
            '--output-format',
            choices=['json', 'console', 'dual'],
            default='dual',
            help='Output format: json (for tools), console (human-readable), or dual (both)'
        )
        
        logging_group.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Console logging level (default: INFO)'
        )
        
        logging_group.add_argument(
            '--file-log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='DEBUG',
            help='File logging level (default: DEBUG)'
        )
        
        logging_group.add_argument(
            '--log-file',
            default='dbworkflow.log',
            help='Log file path (default: dbworkflow.log)'
        )
        
        logging_group.add_argument(
            '--json-pretty',
            action='store_true',
            help='Pretty-print JSON output (useful for debugging)'
        )
    
    @staticmethod
    def config_from_args(args) -> LoggingConfig:
        """
        Create LoggingConfig from parsed CLI arguments.
        
        Args:
            args: Parsed arguments from argparse
        
        Returns:
            LoggingConfig: Configuration based on CLI arguments
        """
        return LoggingConfig(
            output_format=getattr(args, 'output_format', 'dual'),
            console_level=getattr(args, 'log_level', 'INFO'),
            file_level=getattr(args, 'file_log_level', 'DEBUG'),
            log_filepath=getattr(args, 'log_file', 'dbworkflow.log'),
            json_pretty_print=getattr(args, 'json_pretty', False)
        )
    
    @staticmethod
    def stream_json_line(data: Dict[str, Any]) -> None:
        """
        Stream single JSON line to stdout for tool integration.
        
        Args:
            data: Data to serialize as JSON
        """
        json_line = json.dumps(data, separators=(',', ':'))
        print(json_line)
        sys.stdout.flush()
    
    @staticmethod
    def stream_json_entry(entry: LogEntry) -> None:
        """
        Stream log entry as JSON line.
        
        Args:
            entry: Log entry to stream
        """
        CLIOutputHandler.stream_json_line(entry.to_json())
    
    @staticmethod
    def format_console_entry(entry: LogEntry, use_colors: bool = True) -> str:
        """
        Format log entry for console output with clean UI format.
        
        Args:
            entry: Log entry to format
            use_colors: Whether to use ANSI color codes
        
        Returns:
            str: Formatted console output
        """
        if use_colors:
            # Color mapping as specified in PRD
            level_colors = {
                "DEBUG": "\033[90m",      # Gray
                "INFO": "\033[97m",       # White
                "WARNING": "\033[93m",    # Orange  
                "ERROR": "\033[91m",      # Red
                "CRITICAL": "\033[1;91m"  # Bold Red
            }
            
            color = level_colors.get(entry.level, "\033[97m")
            reset = "\033[0m"
            
            # Clean UI format: just colored message
            formatted = f"{color}{entry.message}{reset}"
        else:
            # Plain format: just the message
            formatted = entry.message
        
        # Add data if present (structured display)
        if entry.data:
            data_str = json.dumps(entry.data, indent=2) if entry.data else ""
            if use_colors:
                formatted += f"\n{color}  {data_str}{reset}"
            else:
                formatted += f"\n  {data_str}"
        
        return formatted
    
    @staticmethod
    def print_console_entry(entry: LogEntry, use_colors: bool = True) -> None:
        """
        Print log entry to console with formatting.
        
        Args:
            entry: Log entry to print
            use_colors: Whether to use ANSI color codes
        """
        formatted = CLIOutputHandler.format_console_entry(entry, use_colors)
        print(formatted)
        sys.stdout.flush()
    
    @staticmethod
    def configure_output_format() -> LoggingConfig:
        """
        Configure output format from environment and CLI context.
        
        Returns:
            LoggingConfig: Environment-aware configuration
        """
        import os
        
        # Check for CLI context indicators
        if '--output-format' in sys.argv:
            # Parse minimal args for output format
            parser = argparse.ArgumentParser(add_help=False)
            CLIOutputHandler.add_logging_args(parser)
            args, _ = parser.parse_known_args()
            return CLIOutputHandler.config_from_args(args)
        
        # Fall back to environment-based configuration
        return LoggingConfig.from_env()
    
    @staticmethod
    def is_json_output_requested() -> bool:
        """
        Check if JSON output is specifically requested.
        
        Returns:
            bool: True if JSON-only output is requested
        """
        import os
        
        # Check command line arguments
        if '--output-format' in sys.argv:
            try:
                idx = sys.argv.index('--output-format')
                if idx + 1 < len(sys.argv):
                    return sys.argv[idx + 1] == 'json'
            except (ValueError, IndexError):
                pass
        
        # Check environment variable
        return os.getenv('GRAPHMCP_OUTPUT_FORMAT', '').lower() == 'json'
    
    @staticmethod
    def setup_pipeline_mode() -> LoggingConfig:
        """
        Setup configuration optimized for pipeline/automation use.
        
        Returns:
            LoggingConfig: Pipeline-optimized configuration
        """
        return LoggingConfig(
            output_format='json',
            console_level='ERROR',
            file_level='INFO',
            json_pretty_print=False,
            structured_data_enabled=True,
            progress_tracking_enabled=False
        )


def configure_cli_logging(parser: Optional[argparse.ArgumentParser] = None) -> LoggingConfig:
    """
    Convenience function to configure CLI logging.
    
    Args:
        parser: Optional ArgumentParser to add logging arguments to
    
    Returns:
        LoggingConfig: Configured logging setup
    """
    if parser is not None:
        CLIOutputHandler.add_logging_args(parser)
    
    return CLIOutputHandler.configure_output_format()