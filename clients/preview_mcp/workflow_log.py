"""
Workflow Log System for real-time workflow visualization.

This module provides a structured logging system that supports three types of append operations:
1. Log entries (markdown with structured bullet lists)
2. Tables (markdown table format)
3. Sunburst charts (plotly integration)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import plotly.graph_objects as go
import plotly.io as pio


class LogEntryType(Enum):
    """Types of log entries supported by the workflow log system."""
    LOG = "log"
    TABLE = "table"
    SUNBURST = "sunburst"


@dataclass
class LogEntry:
    """A single log entry in the workflow log."""
    entry_type: LogEntryType
    timestamp: datetime
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    entry_id: str = field(default_factory=lambda: f"entry_{int(time.time() * 1000)}")


@dataclass
class TableData:
    """Data structure for table log entries."""
    headers: List[str]
    rows: List[List[str]]
    title: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert table data to markdown format."""
        if not self.headers or not self.rows:
            return "| No data available |\n|---|\n"
        
        # Create header row
        header_row = "| " + " | ".join(self.headers) + " |"
        
        # Create separator row
        separator_row = "|" + "|".join([" --- " for _ in self.headers]) + "|"
        
        # Create data rows
        data_rows = []
        for row in self.rows:
            # Ensure row has same length as headers
            padded_row = row[:len(self.headers)] + [""] * (len(self.headers) - len(row))
            data_rows.append("| " + " | ".join(str(cell) for cell in padded_row) + " |")
        
        # Combine all parts
        markdown_table = "\n".join([header_row, separator_row] + data_rows)
        
        if self.title:
            return f"**{self.title}**\n\n{markdown_table}"
        return markdown_table


@dataclass
class SunburstData:
    """Data structure for sunburst chart log entries."""
    labels: List[str]
    parents: List[str]
    values: List[float]
    title: Optional[str] = None
    colors: Optional[List[str]] = None
    
    def to_plotly_figure(self) -> go.Figure:
        """Convert sunburst data to plotly figure."""
        fig = go.Figure(go.Sunburst(
            labels=self.labels,
            parents=self.parents,
            values=self.values,
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percentParent}<extra></extra>',
            maxdepth=3,
        ))
        
        fig.update_layout(
            title=self.title or "Sunburst Chart",
            font_size=12,
            height=400,
            margin=dict(t=50, l=0, r=0, b=0)
        )
        
        return fig
    
    def to_json(self) -> str:
        """Convert sunburst figure to JSON for storage/transmission."""
        fig = self.to_plotly_figure()
        return pio.to_json(fig)


class WorkflowLog:
    """
    Main workflow log system that manages log entries and provides append operations.
    """
    
    def __init__(self, workflow_id: str):
        """Initialize workflow log for a specific workflow."""
        self.workflow_id = workflow_id
        self.entries: List[LogEntry] = []
        self.created_at = datetime.now()
        
    def append_log(self, content: str, level: str = "info", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Append a log entry with markdown content.
        
        Args:
            content: Markdown content (supports structured bullet lists)
            level: Log level (info, warning, error, debug)
            metadata: Additional metadata for the log entry
            
        Returns:
            Entry ID for the created log entry
        """
        entry_metadata = {"level": level}
        if metadata:
            entry_metadata.update(metadata)
            
        entry = LogEntry(
            entry_type=LogEntryType.LOG,
            timestamp=datetime.now(),
            content=content,
            metadata=entry_metadata
        )
        
        self.entries.append(entry)
        return entry.entry_id
    
    def append_table(self, headers: List[str], rows: List[List[str]], title: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Append a table entry.
        
        Args:
            headers: Table column headers
            rows: Table data rows
            title: Optional table title
            metadata: Additional metadata for the table entry
            
        Returns:
            Entry ID for the created table entry
        """
        table_data = TableData(headers=headers, rows=rows, title=title)
        
        entry = LogEntry(
            entry_type=LogEntryType.TABLE,
            timestamp=datetime.now(),
            content=table_data,
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        return entry.entry_id
    
    def append_sunburst(self, labels: List[str], parents: List[str], values: List[float],
                       title: Optional[str] = None, colors: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Append a sunburst chart entry.
        
        Args:
            labels: Node labels for the sunburst chart
            parents: Parent nodes for each label (empty string for root)
            values: Values for each node
            title: Optional chart title
            colors: Optional colors for each node
            metadata: Additional metadata for the chart entry
            
        Returns:
            Entry ID for the created sunburst entry
        """
        sunburst_data = SunburstData(
            labels=labels,
            parents=parents,
            values=values,
            title=title,
            colors=colors
        )
        
        entry = LogEntry(
            entry_type=LogEntryType.SUNBURST,
            timestamp=datetime.now(),
            content=sunburst_data,
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        return entry.entry_id
    
    def get_entries(self, entry_type: Optional[LogEntryType] = None) -> List[LogEntry]:
        """
        Get log entries, optionally filtered by type.
        
        Args:
            entry_type: Optional filter by entry type
            
        Returns:
            List of log entries
        """
        if entry_type is None:
            return self.entries.copy()
        return [entry for entry in self.entries if entry.entry_type == entry_type]
    
    def get_entry_by_id(self, entry_id: str) -> Optional[LogEntry]:
        """Get a specific log entry by ID."""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    def clear(self):
        """Clear all log entries."""
        self.entries.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow log."""
        entry_counts = {}
        for entry_type in LogEntryType:
            entry_counts[entry_type.value] = len([e for e in self.entries if e.entry_type == entry_type])
        
        return {
            "workflow_id": self.workflow_id,
            "total_entries": len(self.entries),
            "entry_counts": entry_counts,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.entries[-1].timestamp.isoformat() if self.entries else None
        }


class WorkflowLogManager:
    """
    Manager for multiple workflow logs.
    """
    
    def __init__(self):
        """Initialize the workflow log manager."""
        self.logs: Dict[str, WorkflowLog] = {}
    
    def get_or_create_log(self, workflow_id: str) -> WorkflowLog:
        """Get existing log or create new one for workflow."""
        if workflow_id not in self.logs:
            self.logs[workflow_id] = WorkflowLog(workflow_id)
        return self.logs[workflow_id]
    
    def get_log(self, workflow_id: str) -> Optional[WorkflowLog]:
        """Get existing log for workflow."""
        return self.logs.get(workflow_id)
    
    def delete_log(self, workflow_id: str) -> bool:
        """Delete log for workflow."""
        if workflow_id in self.logs:
            del self.logs[workflow_id]
            return True
        return False
    
    def list_workflows(self) -> List[str]:
        """List all workflow IDs with logs."""
        return list(self.logs.keys())
    
    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries for all workflow logs."""
        return {workflow_id: log.get_summary() for workflow_id, log in self.logs.items()}


# Global log manager instance
_log_manager = WorkflowLogManager()


def get_workflow_log(workflow_id: str) -> WorkflowLog:
    """Get or create workflow log for the given workflow ID."""
    return _log_manager.get_or_create_log(workflow_id)


def get_log_manager() -> WorkflowLogManager:
    """Get the global log manager instance."""
    return _log_manager


# Convenience functions for common log operations
def log_info(workflow_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Log an info message."""
    log = get_workflow_log(workflow_id)
    return log.append_log(message, level="info", metadata=metadata)


def log_warning(workflow_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Log a warning message."""
    log = get_workflow_log(workflow_id)
    return log.append_log(message, level="warning", metadata=metadata)


def log_error(workflow_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Log an error message."""
    log = get_workflow_log(workflow_id)
    return log.append_log(message, level="error", metadata=metadata)


def log_table(workflow_id: str, headers: List[str], rows: List[List[str]], 
              title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Log a table."""
    log = get_workflow_log(workflow_id)
    return log.append_table(headers, rows, title, metadata)


def log_sunburst(workflow_id: str, labels: List[str], parents: List[str], values: List[float],
                title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Log a sunburst chart."""
    log = get_workflow_log(workflow_id)
    return log.append_sunburst(labels, parents, values, title, metadata) 