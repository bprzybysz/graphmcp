import pytest
from don_concrete.workflow.manager import WorkflowManager
from don_concrete.workflow.models import WorkflowPhase

@pytest.fixture
def manager():
    """Returns a new WorkflowManager instance for each test."""
    return WorkflowManager()

@pytest.mark.asyncio
async def test_start_workflow_creates_entry(manager: WorkflowManager):
    """
    Tests that starting a workflow creates a new entry in the manager.
    """
    workflow_id = await manager.start_workflow()
    assert workflow_id is not None
    assert len(manager._workflows) == 1
    
    status = await manager.get_status(workflow_id)
    assert status is not None
    assert status.workflow_id == workflow_id
    assert status.status == WorkflowPhase.PENDING

@pytest.mark.asyncio
async def test_get_status_returns_correct_workflow(manager: WorkflowManager):
    """
    Tests that get_status returns the correct workflow status.
    """
    workflow_id = await manager.start_workflow()
    status = await manager.get_status(workflow_id)
    assert status is not None
    assert status.workflow_id == workflow_id

@pytest.mark.asyncio
async def test_get_status_returns_none_for_invalid_id(manager: WorkflowManager):
    """
    Tests that get_status returns None for an invalid workflow ID.
    """
    status = await manager.get_status("invalid_id")
    assert status is None

@pytest.mark.asyncio
async def test_pause_workflow(manager: WorkflowManager):
    """
    Tests that a workflow can be paused.
    """
    workflow_id = await manager.start_workflow()
    
    # Manually set to RUNNING for the test
    manager._workflows[workflow_id].status = WorkflowPhase.RUNNING
    
    result = await manager.pause_workflow(workflow_id)
    assert result is True
    
    status = await manager.get_status(workflow_id)
    assert status is not None
    assert status.status == WorkflowPhase.PAUSED

@pytest.mark.asyncio
async def test_resume_workflow(manager: WorkflowManager):
    """
    Tests that a workflow can be resumed.
    """
    workflow_id = await manager.start_workflow()
    manager._workflows[workflow_id].status = WorkflowPhase.PAUSED
    
    result = await manager.resume_workflow(workflow_id)
    assert result is True
    
    status = await manager.get_status(workflow_id)
    assert status is not None
    assert status.status == WorkflowPhase.RUNNING

@pytest.mark.asyncio
async def test_stop_workflow(manager: WorkflowManager):
    """
    Tests that a workflow can be stopped.
    """
    workflow_id = await manager.start_workflow()
    manager._workflows[workflow_id].status = WorkflowPhase.RUNNING

    result = await manager.stop_workflow(workflow_id)
    assert result is True

    status = await manager.get_status(workflow_id)
    assert status is not None
    assert status.status == WorkflowPhase.CANCELLED

@pytest.mark.asyncio
async def test_workflow_actions_on_invalid_id(manager: WorkflowManager):
    """
    Tests that actions on an invalid workflow ID return False.
    """
    assert await manager.pause_workflow("invalid_id") is False
    assert await manager.resume_workflow("invalid_id") is False
    assert await manager.stop_workflow("invalid_id") is False
