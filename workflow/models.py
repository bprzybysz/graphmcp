from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, List, Optional


class WorkflowPhase(Enum):
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class StepDetails:
    """Detailed information about a single workflow step."""

    step_id: str
    status: WorkflowPhase
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class WorkflowStatus:
    """Overall status of a workflow."""

    workflow_id: str
    status: WorkflowPhase
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_step_id: Optional[str] = None
    steps: List[StepDetails] = field(default_factory=list)
    error: Optional[str] = None
