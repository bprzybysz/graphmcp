"""
Core structured logger with JSON-first architecture.

High-performance dual-sink logging inspired by Claude Code,
emphasizing structured data and tool integration.
"""

import json
import sys
import time
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional, TextIO

from .data_models import LogEntry, StructuredData, ProgressEntry
from .config import LoggingConfig


class StructuredLogger:
    """
    JSON-first logging system inspired by Claude Code.
    
    Provides dual-sink architecture (JSON + console) with independent
    threshold management and structured data support.
    """
    
    def __init__(self, workflow_id: str, config: LoggingConfig):
        """
        Initialize structured logger.
        
        Args:
            workflow_id: Unique identifier for the workflow
            config: Logging configuration
        """
        self.workflow_id = workflow_id
        self.config = config
        self.session_start = time.time()
        
        # Validate configuration
        config.validate()
        
        # Initialize file handler with rotation
        self._setup_file_handler()
        
        # Initialize console handler
        self._setup_console_handler()
        
        # Progress tracking state
        self._progress_state: Dict[str, Dict[str, Any]] = {}
    
    def _setup_file_handler(self) -> None:
        """Setup rotating file handler for structured logging."""
        self.file_handler = logging.handlers.RotatingFileHandler(
            filename=self.config.log_filepath,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        # JSON formatter for file output
        formatter = logging.Formatter('%(message)s')
        self.file_handler.setFormatter(formatter)
        
        # Set file logging level
        self.file_handler.setLevel(getattr(logging, self.config.file_level))
    
    def _setup_console_handler(self) -> None:
        """Setup console handler for human-readable output."""
        self.console_handler = logging.StreamHandler(sys.stdout)
        
        # Console formatter with clean UI output (no timestamps/levels)
        class ConsoleFormatter(logging.Formatter):
            """Custom formatter with clean UI output."""
            
            COLORS = {
                'DEBUG': '\033[90m',     # Gray
                'INFO': '\033[97m',      # White
                'WARNING': '\033[93m',   # Orange
                'ERROR': '\033[91m',     # Red  
                'CRITICAL': '\033[1;91m' # Bold Red
            }
            RESET = '\033[0m'
            
            def format(self, record):
                color = self.COLORS.get(record.levelname, '\033[97m')
                
                # Clean UI format: just colored message
                return f"{color}{record.getMessage()}{self.RESET}"
        
        self.console_handler.setFormatter(ConsoleFormatter())
        self.console_handler.setLevel(getattr(logging, self.config.console_level))
    
    def log_structured(self, entry: LogEntry) -> None:
        """
        Core method for dual-sink structured logging.
        
        Args:
            entry: Log entry to output
        """
        # File output (JSON format)
        if (self.config.output_format in ["json", "dual"] and 
            self.config.is_level_enabled(entry.level, "file")):
            self._write_json_output(entry)
        
        # Console output (human-readable format)
        if (self.config.output_format in ["console", "dual"] and
            self.config.is_level_enabled(entry.level, "console")):
            self._write_console_output(entry)
    
    def _write_json_output(self, entry: LogEntry) -> None:
        """Write JSON output to file."""
        json_data = entry.to_json()
        
        if self.config.json_pretty_print:
            json_line = json.dumps(json_data, indent=2, separators=(',', ': '))
        else:
            json_line = json.dumps(json_data, separators=(',', ':'))
        
        # Create a log record for the file handler
        record = logging.LogRecord(
            name=f"graphmcp.{entry.component}",
            level=getattr(logging, entry.level),
            pathname="",
            lineno=0,
            msg=json_line,
            args=(),
            exc_info=None
        )
        record.created = entry.timestamp
        
        self.file_handler.emit(record)
    
    def _write_console_output(self, entry: LogEntry) -> None:
        """Write human-readable output to console."""
        # Create a log record for the console handler
        record = logging.LogRecord(
            name=entry.component,
            level=getattr(logging, entry.level),
            pathname="",
            lineno=0,
            msg=entry.message,
            args=(),
            exc_info=None
        )
        record.created = entry.timestamp
        
        self.console_handler.emit(record)
        
        # If there's additional data, format it nicely
        if entry.data:
            data_record = logging.LogRecord(
                name=entry.component,
                level=getattr(logging, entry.level),
                pathname="",
                lineno=0,
                msg=f"  Data: {json.dumps(entry.data, indent=2)}",
                args=(),
                exc_info=None
            )
            data_record.created = entry.timestamp
            self.console_handler.emit(data_record)
    
    def log_structured_data(self, data: StructuredData) -> None:
        """
        Log structured data (tables, trees, metrics).
        
        Args:
            data: Structured data to log
        """
        if not self.config.structured_data_enabled:
            return
        
        # JSON output
        if self.config.output_format in ["json", "dual"]:
            json_data = data.to_json()
            
            if self.config.json_pretty_print:
                json_line = json.dumps(json_data, indent=2, separators=(',', ': '))
            else:
                json_line = json.dumps(json_data, separators=(',', ':'))
            
            record = logging.LogRecord(
                name=f"graphmcp.{self.workflow_id}",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=json_line,
                args=(),
                exc_info=None
            )
            record.created = data.timestamp
            self.file_handler.emit(record)
        
        # Console output (formatted)
        if self.config.output_format in ["console", "dual"]:
            if data.data_type == "table":
                console_output = data.to_console_table()
            elif data.data_type == "diff":
                console_output = data.to_console_diff()
            else:
                console_output = f"[{data.title}] {data.data_type}: {json.dumps(data.content, indent=2)}"
            
            print(console_output)
            sys.stdout.flush()
    
    def log_progress(self, progress: ProgressEntry) -> None:
        """
        Log progress tracking entry.
        
        Args:
            progress: Progress entry to log
        """
        if not self.config.progress_tracking_enabled:
            return
        
        # Update internal progress state
        self._progress_state[progress.step_name] = {
            "status": progress.status,
            "progress_percent": progress.progress_percent,
            "eta_seconds": progress.eta_seconds,
            "metrics": progress.metrics,
            "last_update": progress.timestamp
        }
        
        # JSON output
        if self.config.output_format in ["json", "dual"]:
            json_data = progress.to_json()
            json_line = json.dumps(json_data, separators=(',', ':'))
            
            record = logging.LogRecord(
                name=f"graphmcp.{self.workflow_id}",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=json_line,
                args=(),
                exc_info=None
            )
            record.created = progress.timestamp
            self.file_handler.emit(record)
        
        # Console output (simple progress indication)
        if self.config.output_format in ["console", "dual"]:
            if progress.status == "started":
                message = f"Started: {progress.step_name}"
            elif progress.status == "progress" and progress.progress_percent is not None:
                message = f"Progress: {progress.step_name} ({progress.progress_percent:.1f}%)"
            elif progress.status == "completed":
                message = f"Completed: {progress.step_name}"
            elif progress.status == "failed":
                message = f"Failed: {progress.step_name}"
            else:
                message = f"Update: {progress.step_name}"
            
            entry = LogEntry.create(
                workflow_id=self.workflow_id,
                level="INFO",
                component="progress",
                message=message,
                data=progress.metrics
            )
            entry.timestamp = progress.timestamp
            self._write_console_output(entry)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked progress.
        
        Returns:
            Dict: Current progress state for all steps
        """
        return dict(self._progress_state)
    
    def flush(self) -> None:
        """Flush all handlers."""
        self.file_handler.flush()
        self.console_handler.flush()
        sys.stdout.flush()
    
    def close(self) -> None:
        """Close all handlers and cleanup resources."""
        self.file_handler.close()
        self.console_handler.close()