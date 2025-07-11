import pytest
from unittest.mock import AsyncMock, patch
import unittest.mock

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

@pytest.mark.asyncio
@pytest.mark.parametrize("use_mock_env, expected_mock_calls, expected_real_calls", [
    ("true", 1, 0),
    ("false", 0, 1),
    (None, 1, 0), # Default should be mock
])
async def test_workflow_step_mock_switching(
    monkeypatch, use_mock_env, expected_mock_calls, expected_real_calls
):
    """
    Tests that workflow steps correctly switch between mock and real execution
    based on environment variables.
    """
    # Arrange
    if use_mock_env is not None:
        monkeypatch.setenv("USE_MOCK_PACK", use_mock_env)
    else:
        monkeypatch.delenv("USE_MOCK_PACK", raising=False)

    from concrete.workflow.steps.repository_processing import RepositoryProcessingStep

    # Patch the actual implementation methods
    with patch(
        'concrete.workflow.steps.repository_processing.RepositoryProcessingStep._execute_mock',
        new_callable=AsyncMock
    ) as mock_execute_mock, patch(
        'concrete.workflow.steps.repository_processing.RepositoryProcessingStep._execute_real',
        new_callable=AsyncMock
    ) as mock_execute_real:

        mock_execute_mock.return_value = {"status": "mock"}
        mock_execute_real.return_value = {"status": "real"}

        step = RepositoryProcessingStep(step_config={"repo_url": "test_url"})

        # Act
        await step.execute(context={}, step={})

        # Assert
        assert mock_execute_mock.call_count == expected_mock_calls
        assert mock_execute_real.call_count == expected_real_calls 