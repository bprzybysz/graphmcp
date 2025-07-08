"""
Workflow Data Models

Serializable data classes for workflow building and execution.
These models are designed to be pickle-safe for LangGraph state management
and follow GraphMCP's core design principles.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class StepType(Enum):
    """Types of workflow steps."""
    GITHUB_ANALYSIS = "github_analysis"
    GITHUB_SEARCH = "github_search"
    GITHUB_FILE_READ = "github_file_read"
    CONTEXT7_SEARCH = "context7_search"
    CONTEXT7_DOCS = "context7_docs"
    FILESYSTEM_SCAN = "filesystem_scan"
    BROWSER_NAVIGATE = "browser_navigate"
    CUSTOM = "custom"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


class StepStatus(Enum):
    """Status of workflow step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    This is a serializable data model that describes what to do,
    not how to do it. The actual execution is handled by the workflow engine.
    """
    id: str
    step_type: StepType
    name: str
    description: str = ""
    
    # Step configuration
    server_name: Optional[str] = None
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Flow control
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # Python expression as string
    retry_count: int = 3
    timeout_seconds: int = 30
    
    # Execution state (not persisted in builder)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate step configuration."""
        if self.step_type != StepType.CUSTOM and self.step_type != StepType.CONDITIONAL:
            if not self.server_name:
                raise ValueError(f"server_name required for step type {self.step_type}")
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step execution duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class WorkflowConfig:
    """
    Configuration for workflow execution.
    """
    name: str
    description: str = ""
    config_path: str = ""
    
    # Execution settings
    max_parallel_steps: int = 5
    default_timeout: int = 30
    stop_on_error: bool = True
    
    # Retry settings
    default_retry_count: int = 3
    retry_delay_seconds: float = 1.0
    
    # Logging and monitoring
    enable_step_logging: bool = True
    enable_timing: bool = True
    
    created_at: float = field(default_factory=time.time)


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.
    
    Contains all step results and execution metadata.
    """
    workflow_name: str
    status: str  # "completed", "failed", "partial"
    
    # Results
    step_results: Dict[str, Any] = field(default_factory=dict)
    final_result: Any = None
    
    # Execution metadata
    steps_completed: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    total_steps: int = 0
    
    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Error information
    errors: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total workflow execution duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.steps_completed / self.total_steps) * 100
    
    def get_step_result(self, step_id: str) -> Any:
        """Get result from a specific step."""
        return self.step_results.get(step_id)


@dataclass
class WorkflowExecutionContext:
    """
    Runtime context for workflow execution.
    
    Contains shared state and utilities needed during execution.
    This is NOT serialized - it's created fresh for each execution.
    """
    config: WorkflowConfig
    current_step: Optional[str] = None
    shared_state: Dict[str, Any] = field(default_factory=dict)
    
    # These will be set during execution and are NOT serialized
    _clients: Dict[str, Any] = field(default_factory=dict)
    _session_managers: Dict[str, Any] = field(default_factory=dict)
    
    def get_shared_value(self, key: str, default: Any = None) -> Any:
        """Get a value from shared workflow state."""
        return self.shared_state.get(key, default)
    
    def set_shared_value(self, key: str, value: Any) -> None:
        """Set a value in shared workflow state."""
        # Ensure value is serializable
        try:
            import pickle
            pickle.dumps(value)
            self.shared_state[key] = value
        except (TypeError, AttributeError) as e:
            raise ValueError(f"Value for key '{key}' is not serializable: {e}")
    
    def __getstate__(self):
        """Custom pickling to exclude non-serializable clients."""
        state = self.__dict__.copy()
        state['_clients'] = {}
        state['_session_managers'] = {}
        return state
    
    def __setstate__(self, state):
        """Custom unpickling to restore state."""
        self.__dict__.update(state)
        self._clients = {}
        self._session_managers = {}


# Type alias for step functions
StepFunction = Callable[[WorkflowExecutionContext, WorkflowStep], Any] 