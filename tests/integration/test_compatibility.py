import pytest
from unittest.mock import AsyncMock

from concrete.workflow.manager import WorkflowManager
from concrete.workflow.compat import WorkflowManagerCompat

@pytest.mark.asyncio
async def test_compatibility_layer_forwards_calls():
    """
    Tests that the compatibility layer correctly forwards calls
    to the new WorkflowManager.
    """
    # Arrange
    mock_new_manager = AsyncMock(spec=WorkflowManager)
    mock_new_manager.start_workflow.return_value = "test_workflow_id"
    
    compat_manager = WorkflowManagerCompat(new_manager=mock_new_manager)

    # Act
    workflow_id = await compat_manager.start_workflow(some_legacy_arg=True)

    # Assert
    mock_new_manager.start_workflow.assert_called_once()
    assert workflow_id == "test_workflow_id"
    
    # Check that the config was passed, even if empty
    call_args, call_kwargs = mock_new_manager.start_workflow.call_args
    assert "config" in call_kwargs
    assert call_kwargs["config"] == {} 