"""
Data models for structured logging.

JSON-serializable data classes for log entries, structured data,
and progress tracking following Claude Code patterns.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Literal


@dataclass
class LogEntry:
    """
    Core log entry for JSON-first logging.
    
    Represents a single log message with metadata, designed for
    both human consumption and tool integration.
    """
    timestamp: float
    workflow_id: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    component: str
    message: str
    data: Optional[Dict[str, Any]] = None
    step_index: Optional[int] = None
    duration_ms: Optional[float] = None
    
    @classmethod
    def create(cls, 
               workflow_id: str,
               level: str,
               component: str,
               message: str,
               **kwargs) -> 'LogEntry':
        """
        Factory method for creating log entries.
        
        Args:
            workflow_id: Workflow identifier
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            component: Component name
            message: Log message
            **kwargs: Additional fields (data, step_index, duration_ms)
        
        Returns:
            LogEntry: New log entry instance
        """
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            level=level.upper(),
            component=component,
            message=message,
            **kwargs
        )
    
    def to_json(self) -> Dict[str, Any]:
        """
        Convert to JSON-serializable dictionary.
        
        Returns:
            Dict: JSON representation for tool integration
        """
        return {
            "type": "log",
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "level": self.level.lower(),
            "component": self.component,
            "message": self.message,
            "data": self.data,
            "step_index": self.step_index,
            "duration_ms": self.duration_ms
        }


@dataclass 
class ProgressEntry:
    """
    Progress tracking entry for workflow steps.
    
    High-performance progress tracking without heavy animations,
    optimized for Claude Code-style structured output.
    """
    timestamp: float
    workflow_id: str
    step_name: str
    status: Literal["started", "progress", "completed", "failed"]
    progress_percent: Optional[float] = None
    eta_seconds: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create_started(cls, workflow_id: str, step_name: str, 
                      total_items: Optional[int] = None) -> 'ProgressEntry':
        """Create progress start entry."""
        metrics = {"total_items": total_items} if total_items else None
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            step_name=step_name,
            status="started",
            metrics=metrics
        )
    
    @classmethod
    def create_progress(cls, workflow_id: str, step_name: str,
                       current: int, total: int, 
                       rate_per_second: Optional[float] = None) -> 'ProgressEntry':
        """Create progress update entry."""
        progress_percent = (current / total) * 100 if total > 0 else None
        eta_seconds = (total - current) / rate_per_second if rate_per_second and rate_per_second > 0 else None
        
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            step_name=step_name,
            status="progress",
            progress_percent=progress_percent,
            eta_seconds=eta_seconds,
            metrics={
                "current": current,
                "total": total,
                "rate_per_second": rate_per_second
            }
        )
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON for tool integration."""
        return {
            "type": "progress",
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "step_name": self.step_name,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "eta_seconds": self.eta_seconds,
            "metrics": self.metrics
        }


@dataclass
class StructuredData:
    """
    Structured data entry for tables, trees, and metrics.
    
    Supports rich data visualization in both JSON and console formats,
    replacing Rich library functionality with simple structured data.
    """
    timestamp: float
    workflow_id: str
    data_type: Literal["table", "tree", "json", "metrics"]
    title: str
    content: Dict[str, Any]
    
    @classmethod
    def create_table(cls, workflow_id: str, title: str, 
                    headers: List[str], rows: List[List[str]],
                    metadata: Optional[Dict] = None) -> 'StructuredData':
        """Create table data entry."""
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            data_type="table",
            title=title,
            content={
                "headers": headers,
                "rows": rows,
                "metadata": metadata or {}
            }
        )
    
    @classmethod
    def create_tree(cls, workflow_id: str, title: str,
                   tree_data: Dict, metadata: Optional[Dict] = None) -> 'StructuredData':
        """Create tree data entry."""
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            data_type="tree", 
            title=title,
            content={
                "tree": tree_data,
                "metadata": metadata or {}
            }
        )
    
    @classmethod
    def create_metrics(cls, workflow_id: str, title: str,
                      metrics: Dict[str, Any]) -> 'StructuredData':
        """Create metrics data entry."""
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            data_type="metrics",
            title=title,
            content=metrics
        )
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON for tool integration."""
        return {
            "type": "structured_data",
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "data_type": self.data_type,
            "title": self.title,
            "content": self.content
        }
    
    def to_console_table(self) -> str:
        """
        Convert table data to console-friendly format.
        
        Returns:
            str: Human-readable table representation
        """
        if self.data_type != "table":
            return f"[{self.title}] {self.content}"
        
        headers = self.content.get("headers", [])
        rows = self.content.get("rows", [])
        
        if not headers or not rows:
            return f"[{self.title}] Empty table"
        
        # Simple ASCII table formatting
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Header
        result = []
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        result.append(f"[{self.title}]")
        result.append(header_line)
        result.append("-" * len(header_line))
        
        # Rows
        for row in rows:
            row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            result.append(row_line)
        
        return "\n".join(result)
    
    def to_console_diff(self) -> str:
        """
        Convert diff data to Claude Code style with dark theme.
        
        Returns:
            str: Styled diff output
        """
        if self.data_type != "diff":
            return self.to_console_table()
        
        diff_content = self.content.get("diff", "")
        file_path = self.content.get("file_path", "")
        
        if not diff_content:
            return f"[{self.title}] No diff content"
        
        # Claude Code dark theme colors
        colors = {
            'file_header': '\033[38;5;75m',      # Light blue
            'hunk_header': '\033[38;5;245m',     # Gray
            'added': '\033[38;5;46m',            # Bright green  
            'removed': '\033[38;5;196m',         # Bright red
            'context': '\033[38;5;250m',         # Light gray
            'line_num': '\033[38;5;242m',        # Dark gray
            'reset': '\033[0m'
        }
        
        result = []
        
        # File header with styling
        if file_path:
            result.append(f"{colors['file_header']}📄 {file_path}{colors['reset']}")
            result.append(f"{colors['file_header']}{'─' * (len(file_path) + 3)}{colors['reset']}")
        
        lines = diff_content.split('\n')
        for line in lines:
            if line.startswith('@@'):
                # Hunk header
                result.append(f"{colors['hunk_header']}{line}{colors['reset']}")
            elif line.startswith('+'):
                # Added line
                if line.startswith('+++'):
                    result.append(f"{colors['file_header']}{line}{colors['reset']}")
                else:
                    result.append(f"{colors['added']}+{line[1:]}{colors['reset']}")
            elif line.startswith('-'):
                # Removed line  
                if line.startswith('---'):
                    result.append(f"{colors['file_header']}{line}{colors['reset']}")
                else:
                    result.append(f"{colors['removed']}-{line[1:]}{colors['reset']}")
            elif line.startswith(' '):
                # Context line
                result.append(f"{colors['context']} {line[1:]}{colors['reset']}")
            else:
                # Other lines
                result.append(f"{colors['context']}{line}{colors['reset']}")
        
        return '\n'.join(result)


@dataclass
class DiffData(StructuredData):
    """Specialized structured data for diff output."""
    
    @classmethod
    def create_diff(cls, workflow_id: str, title: str, 
                   file_path: str, diff_content: str,
                   metadata: Optional[Dict] = None) -> 'DiffData':
        """Create diff data entry with Claude Code styling."""
        return cls(
            timestamp=time.time(),
            workflow_id=workflow_id,
            data_type="diff",
            title=title,
            content={
                "file_path": file_path,
                "diff": diff_content,
                "metadata": metadata or {}
            }
        )
    
    def to_console_output(self) -> str:
        """Convert to styled console output."""
        return self.to_console_diff()