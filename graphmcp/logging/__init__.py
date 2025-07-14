"""
GraphMCP Structured Logging System.

Claude Code-inspired JSON-first logging with dual-sink architecture,
structured data support, and high-performance design.
"""

from .structured_logger import StructuredLogger
from .data_models import LogEntry, StructuredData, ProgressEntry, DiffData
from .config import LoggingConfig
from .workflow_logger import WorkflowLogger
from .cli_output import CLIOutputHandler, configure_cli_logging

# Main factory function - replaces all logging.getLogger() calls
def get_logger(workflow_id: str, config: LoggingConfig = None) -> WorkflowLogger:
    """
    Get WorkflowLogger instance - replaces all existing logging calls.
    
    Args:
        workflow_id: Unique identifier for the workflow/component
        config: Optional logging configuration (defaults to environment-based)
    
    Returns:
        WorkflowLogger: Unified logger with JSON-first dual-sink architecture
    """
    if config is None:
        config = LoggingConfig.from_env()
    
    return WorkflowLogger(workflow_id, config)

__all__ = [
    'StructuredLogger',
    'LogEntry', 
    'StructuredData',
    'ProgressEntry',
    'DiffData',
    'LoggingConfig',
    'WorkflowLogger',
    'CLIOutputHandler',
    'configure_cli_logging',
    'get_logger'
]