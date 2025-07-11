from datetime import datetime

import pytest

import pandas as pd

from ui.state.workflow_state import LogEntry, WorkflowState


@pytest.fixture
def running_workflow_state() -> WorkflowState:
    """
    Provides a WorkflowState object representing a workflow that is
    currently running with some sample data.
    """
    return WorkflowState(
        workflow_id="fixture_workflow_123",
        workflow_running=True,
        progress_percentage=50.0,
        log_entries=[
            LogEntry(timestamp=datetime.now(), message="Step 1 complete", level="INFO"),
            LogEntry(timestamp=datetime.now(), message="Step 2 running", level="INFO"),
        ],
        progress_stats={
            "file_processing": {"total_files": 100, "processed": 50, "errors": 2},
        },
    )
