"""Workflow context management for MCP server."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """Individual workflow step."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowContext(BaseModel):
    """Workflow execution context."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    # Workflow definition
    steps: List[WorkflowStep] = Field(default_factory=list)
    current_step_index: int = 0
    
    # Context data
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    
    @property
    def current_step(self) -> Optional[WorkflowStep]:
        """Get current workflow step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def add_step(self, name: str, input_data: Optional[Dict[str, Any]] = None) -> WorkflowStep:
        """Add a new step to the workflow."""
        step = WorkflowStep(
            name=name,
            input_data=input_data or {}
        )
        self.steps.append(step)
        self.updated_at = datetime.utcnow()
        return step
    
    def start_step(self, step_id: str) -> bool:
        """Start executing a specific step."""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                step.status = WorkflowStatus.IN_PROGRESS
                step.started_at = datetime.utcnow()
                self.current_step_index = i
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def complete_step(self, step_id: str, output_data: Dict[str, Any]) -> bool:
        """Complete a workflow step."""
        for step in self.steps:
            if step.id == step_id:
                step.status = WorkflowStatus.COMPLETED
                step.output_data = output_data
                step.completed_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
                
                # Move to next step if available
                if self.current_step_index < len(self.steps) - 1:
                    self.current_step_index += 1
                else:
                    self.status = WorkflowStatus.COMPLETED
                
                return True
        return False
    
    def fail_step(self, step_id: str, error_message: str) -> bool:
        """Mark a workflow step as failed."""
        for step in self.steps:
            if step.id == step_id:
                step.status = WorkflowStatus.FAILED
                step.error_message = error_message
                step.completed_at = datetime.utcnow()
                self.status = WorkflowStatus.FAILED
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def update_shared_context(self, key: str, value: Any) -> None:
        """Update shared context data."""
        self.shared_context[key] = value
        self.updated_at = datetime.utcnow()
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary."""
        completed_steps = sum(1 for step in self.steps if step.status == WorkflowStatus.COMPLETED)
        failed_steps = sum(1 for step in self.steps if step.status == WorkflowStatus.FAILED)
        
        return {
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "status": self.status,
            "total_steps": len(self.steps),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "current_step": self.current_step.name if self.current_step else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class WorkflowResult(BaseModel):
    """Result of workflow execution."""
    
    workflow_id: str
    status: WorkflowStatus
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    steps_completed: int = 0
    total_steps: int = 0
    
    @classmethod
    def from_context(cls, context: WorkflowContext) -> "WorkflowResult":
        """Create result from workflow context."""
        completed_steps = sum(1 for step in context.steps if step.status == WorkflowStatus.COMPLETED)
        
        execution_time = None
        if context.created_at and context.updated_at:
            execution_time = (context.updated_at - context.created_at).total_seconds()
        
        # Aggregate output data from completed steps
        result_data = {}
        for step in context.steps:
            if step.status == WorkflowStatus.COMPLETED:
                result_data[step.name] = step.output_data
        
        return cls(
            workflow_id=context.workflow_id,
            status=context.status,
            result_data=result_data,
            execution_time_seconds=execution_time,
            steps_completed=completed_steps,
            total_steps=len(context.steps)
        ) 