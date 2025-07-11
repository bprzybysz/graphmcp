from ..manager import WorkflowManager
from ..models import WorkflowStatus, StepDetails, WorkflowPhase
from .mock_data import MockDataProvider

class MockWorkflowManager(WorkflowManager):
    """
    A mock implementation of the WorkflowManager for testing and UI development.
    It simulates a workflow run using mock data.
    """

    async def start_workflow(self, config=None) -> str:
        """
        Simulates the execution of a full workflow, step by step.
        """
        workflow_id = await super().start_workflow(config)
        
        print(f"Starting MOCK workflow: {workflow_id}")
        
        # Simulate repository processing
        self._workflows[workflow_id].status = WorkflowPhase.RUNNING
        self._workflows[workflow_id].current_step_id = "repository_processing"
        
        # Simulate pattern discovery
        self._workflows[workflow_id].current_step_id = "pattern_discovery"
        
        # Simulate file processing
        self._workflows[workflow_id].current_step_id = "file_processing"
        
        # Finish workflow
        self._workflows[workflow_id].status = WorkflowPhase.COMPLETED
        self._workflows[workflow_id].current_step_id = None
        
        print(f"Mock workflow {workflow_id} finished.")
        return workflow_id
