"""
Progress Table Component for Dynamic File Processing Tracking

This module provides a specialized progress table that tracks file processing
status in real-time during database decommissioning workflows.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from .workflow_log import LogEntryType, LogEntry, get_workflow_log

class ProcessingStatus(Enum):
    """File processing status states."""
    PENDING = "pending"           # 🟡 Discovered, awaiting processing  
    PROCESSING = "processing"     # 🔵 Currently being processed
    COMPLETED = "completed"       # 🟢 Successfully processed
    FAILED = "failed"            # 🔴 Processing failed
    EXCLUDED = "excluded"        # 🔵 Excluded (test/example content)

class ProcessingPhase(Enum):
    """Current processing phase."""
    DISCOVERY = "discovery"           # Finding files with database references
    CLASSIFICATION = "classification" # Determining file types and patterns
    RULE_APPLICATION = "rule_application"  # Applying refactoring rules
    VALIDATION = "validation"         # Validating changes
    COMPLETE = "complete"            # Processing finished

@dataclass
class ProgressTableEntry:
    """Single entry in the progress table."""
    file_path: str
    source_type: str = "unknown"
    match_count: int = 0
    confidence: float = 0.0
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress_phase: ProcessingPhase = ProcessingPhase.DISCOVERY
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    processing_time: float = 0.0
    
    def get_status_icon(self) -> str:
        """Get the appropriate status icon."""
        icons = {
            ProcessingStatus.PENDING: "🟡",
            ProcessingStatus.PROCESSING: "🔵", 
            ProcessingStatus.COMPLETED: "🟢",
            ProcessingStatus.FAILED: "🔴",
            ProcessingStatus.EXCLUDED: "🔵"
        }
        return icons.get(self.status, "⚪")
    
    def get_confidence_class(self) -> str:
        """Get CSS class for confidence level."""
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def get_truncated_path(self, max_length: int = 50) -> str:
        """Get truncated file path for display."""
        if len(self.file_path) <= max_length:
            return self.file_path
        return "..." + self.file_path[-(max_length-3):]

@dataclass  
class ProgressTableData:
    """Complete progress table data structure."""
    title: str
    entries: List[ProgressTableEntry] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    excluded_files: int = 0
    
    def update_counts(self):
        """Update summary counts from entries."""
        self.total_files = len(self.entries)
        self.completed_files = sum(1 for e in self.entries if e.status == ProcessingStatus.COMPLETED)
        self.failed_files = sum(1 for e in self.entries if e.status == ProcessingStatus.FAILED)
        self.excluded_files = sum(1 for e in self.entries if e.status == ProcessingStatus.EXCLUDED)
        self.last_updated = datetime.now()
    
    def get_completion_rate(self) -> float:
        """Get completion percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100
    
    def group_by_source_type(self) -> Dict[str, List[ProgressTableEntry]]:
        """Group entries by source type."""
        groups = {}
        for entry in self.entries:
            source_type = entry.source_type.upper()
            if source_type not in groups:
                groups[source_type] = []
            groups[source_type].append(entry)
        return groups
    
    def to_streamlit_data(self) -> Dict[str, List[Any]]:
        """Convert to Streamlit dataframe format."""
        data = {
            "Status": [],
            "File Path": [],
            "Type": [],
            "Matches": [],
            "Confidence": [],
            "Progress": []
        }
        
        for entry in self.entries:
            data["Status"].append(entry.get_status_icon())
            data["File Path"].append(entry.get_truncated_path())
            data["Type"].append(entry.source_type.upper())
            data["Matches"].append(entry.match_count)
            data["Confidence"].append(f"{entry.confidence:.1%}")
            data["Progress"].append(entry.progress_phase.value.title())
            
        return data

# Global progress table registry
_progress_tables: Dict[str, ProgressTableData] = {}

def log_progress_table(workflow_id: str, 
                      title: str = "File Processing Progress",
                      files: Optional[List[Dict]] = None,
                      file_path: Optional[str] = None,
                      status: Optional[str] = None,
                      confidence: Optional[float] = None,
                      phase: Optional[str] = None,
                      update_type: str = "update") -> ProgressTableData:
    """
    Log and update progress table for workflow tracking.
    
    Args:
        workflow_id: Unique workflow identifier
        title: Table title
        files: List of file dictionaries for initialization
        file_path: Specific file to update
        status: New status for the file
        confidence: New confidence score
        phase: Current processing phase
        update_type: 'initialize', 'update', or 'complete'
    """
    
    # Get or create progress table
    if workflow_id not in _progress_tables:
        _progress_tables[workflow_id] = ProgressTableData(title=title)
    
    progress_table = _progress_tables[workflow_id]
    
    if update_type == "initialize" and files:
        # Initialize with discovered files
        progress_table.entries.clear()
        for file_info in files:
            entry = ProgressTableEntry(
                file_path=file_info.get('path', 'Unknown'),
                source_type=file_info.get('source_type', 'unknown'),
                match_count=file_info.get('match_count', 0),
                confidence=file_info.get('confidence', 0.0),
                status=ProcessingStatus.PENDING,
                progress_phase=ProcessingPhase.DISCOVERY
            )
            progress_table.entries.append(entry)
    
    elif update_type == "update" and file_path:
        # Update specific file
        for entry in progress_table.entries:
            if entry.file_path == file_path:
                if status:
                    entry.status = ProcessingStatus(status)
                if confidence is not None:
                    entry.confidence = confidence
                if phase:
                    entry.progress_phase = ProcessingPhase(phase)
                entry.timestamp = datetime.now()
                break
    
    # Update summary counts
    progress_table.update_counts()
    
    # Log to workflow system as table entry
    workflow_log = get_workflow_log(workflow_id)
    
    # Create log entry
    log_entry = LogEntry(
        entry_type=LogEntryType.PROGRESS_TABLE,
        content=progress_table,
        timestamp=datetime.now(),
        metadata={
            "update_type": update_type,
            "total_files": progress_table.total_files,
            "completion_rate": progress_table.get_completion_rate()
        }
    )
    
    workflow_log.add_entry(log_entry)
    
    return progress_table

def get_progress_table(workflow_id: str) -> Optional[ProgressTableData]:
    """Get progress table for a workflow."""
    return _progress_tables.get(workflow_id)

def clear_progress_table(workflow_id: str):
    """Clear progress table for a workflow."""
    if workflow_id in _progress_tables:
        del _progress_tables[workflow_id]

def update_file_status(workflow_id: str, file_path: str, 
                      status: ProcessingStatus,
                      phase: Optional[ProcessingPhase] = None,
                      error_message: Optional[str] = None):
    """Convenience function to update file status."""
    log_progress_table(
        workflow_id=workflow_id,
        file_path=file_path,
        status=status.value,
        phase=phase.value if phase else None,
        update_type="update"
    )
    
    # Add error message if failed
    if status == ProcessingStatus.FAILED and error_message:
        progress_table = get_progress_table(workflow_id)
        if progress_table:
            for entry in progress_table.entries:
                if entry.file_path == file_path:
                    entry.error_message = error_message
                    break 


def get_source_type_from_path(file_path: str) -> str:
    """
    Determine source type from file path extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Source type string (e.g., 'PYTHON', 'SQL', 'MARKDOWN', etc.)
    """
    if not file_path:
        return "UNKNOWN"
    
    # Get file extension
    ext = file_path.lower().split('.')[-1] if '.' in file_path else ""
    
    # Map extensions to source types
    extension_map = {
        'py': 'PYTHON',
        'sql': 'SQL', 
        'md': 'MARKDOWN',
        'txt': 'TEXT',
        'yaml': 'YAML',
        'yml': 'YAML',
        'json': 'JSON',
        'js': 'JAVASCRIPT',
        'ts': 'TYPESCRIPT',
        'jsx': 'REACT',
        'tsx': 'REACT',
        'html': 'HTML',
        'css': 'CSS',
        'sh': 'SHELL',
        'bash': 'SHELL',
        'dockerfile': 'DOCKER',
        'env': 'ENVIRONMENT',
        'cfg': 'CONFIG',
        'conf': 'CONFIG',
        'ini': 'CONFIG',
        'toml': 'CONFIG'
    }
    
    return extension_map.get(ext, "OTHER") 