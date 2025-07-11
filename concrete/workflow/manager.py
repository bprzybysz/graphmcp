from typing import Optional, Dict, Any
from .models import WorkflowStatus, StepDetails, WorkflowPhase
import uuid
from datetime import datetime

class WorkflowManager:
    """
    Manages the execution, state, and lifecycle of workflows.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowStatus] = {}

    async def start_workflow(self, config: Optional[Dict] = None) -> str:
        """
        Starts a new workflow based on the provided configuration.
        
        Returns:
            str: The unique ID of the started workflow.
        """
        workflow_id = str(uuid.uuid4())
        self._workflows[workflow_id] = WorkflowStatus(
            workflow_id=workflow_id,
            status=WorkflowPhase.PENDING,
            start_time=datetime.utcnow()
        )
        return workflow_id

    async def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pauses a running workflow.
        """
        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = WorkflowPhase.PAUSED
            return True
        return False

    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resumes a paused workflow.
        """
        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = WorkflowPhase.RUNNING
            return True
        return False

    async def stop_workflow(self, workflow_id: str, force: bool = False) -> bool:
        """
        Stops a workflow.
        """
        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = WorkflowPhase.CANCELLED
            return True
        return False

    async def get_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """
        Gets the current status of a workflow.
        """
        return self._workflows.get(workflow_id)

    async def get_step_details(self, workflow_id: str, step_id: str) -> Optional[StepDetails]:
        """
        Gets the details of a specific step within a workflow.
        """
        if workflow_id in self._workflows:
            for step in self._workflows[workflow_id].steps:
                if step.step_id == step_id:
                    return step
        return None
