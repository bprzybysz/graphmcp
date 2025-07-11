from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


@dataclass
class LogEntry:
    """Represents a single log entry in the UI."""

    timestamp: datetime
    message: str
    level: str = "INFO"
    details: Optional[Any] = None
    log_id: Optional[str] = None


@dataclass
class WorkflowState:
    """Manages the state of a single workflow run."""

    workflow_id: Optional[str] = None
    workflow_running: bool = False
    auto_refresh: bool = True
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    log_entries: List[LogEntry] = field(default_factory=list)
    error_count: int = 0
    last_refresh: datetime = field(default_factory=datetime.now)
    expanded_sections: Set[str] = field(default_factory=set)
    mock_mode: bool = True  # For testing
    progress_stats: Dict[str, Any] = field(default_factory=dict)
