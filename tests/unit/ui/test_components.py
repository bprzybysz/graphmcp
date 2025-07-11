import unittest
from unittest.mock import MagicMock, patch

from concrete.ui.components.workflow_controls import render_workflow_controls
from concrete.ui.state.workflow_state import WorkflowState, LogEntry
from concrete.ui.components.log_stream import render_log_stream
from concrete.ui.components.progress_tables import render_progress_tables

class TestUIComponents(unittest.TestCase):

    @patch('concrete.ui.components.workflow_controls.SessionManager')
    @patch('concrete.ui.components.workflow_controls.st')
    def test_workflow_controls_renders_start_button(self, mock_st, mock_session_manager):
        """
        Tests that the 'Start Workflow' button is rendered when the workflow is not running.
        """
        # Arrange
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        mock_st.button.return_value = False
        mock_state = WorkflowState(workflow_running=False)
        mock_session_manager.get_workflow_state.return_value = mock_state
        
        # Act
        render_workflow_controls()

        # Assert
        mock_st.button.assert_called_with("▶️ Start Workflow", use_container_width=True)
        # Ensure stop button is NOT called
        stop_call = any("Stop Workflow" in call[0][0] for call in mock_st.button.call_args_list)
        self.assertFalse(stop_call, "Stop button should not be rendered")

    @patch('concrete.ui.components.workflow_controls.SessionManager')
    @patch('concrete.ui.components.workflow_controls.st')
    def test_workflow_controls_renders_stop_button(self, mock_st, mock_session_manager):
        """
        Tests that the 'Stop Workflow' button is rendered when the workflow is running.
        """
        # Arrange
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        mock_st.button.return_value = False
        mock_state = WorkflowState(workflow_running=True)
        mock_session_manager.get_workflow_state.return_value = mock_state

        # Act
        render_workflow_controls()

        # Assert
        mock_st.button.assert_called_with("⏹️ Stop Workflow", use_container_width=True)
        # Ensure start button is NOT called
        start_call = any("Start Workflow" in call[0][0] for call in mock_st.button.call_args_list)
        self.assertFalse(start_call, "Start button should not be rendered")

    @patch('concrete.ui.components.workflow_controls.SessionManager')
    @patch('concrete.ui.components.workflow_controls.st')
    def test_workflow_controls_renders_toggle_and_progress(self, mock_st, mock_session_manager):
        """
        Tests that the auto-refresh toggle and progress bar are always rendered.
        """
        # Arrange
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        mock_st.button.return_value = False # Prevent button logic from running
        mock_state = WorkflowState(progress_percentage=50.0)
        mock_session_manager.get_workflow_state.return_value = mock_state

        # Act
        render_workflow_controls()

        # Assert
        mock_st.toggle.assert_called_with("Auto-refresh", value=True, help="Toggle to enable/disable auto-refreshing the log view.")
        mock_st.progress.assert_called_with(0.5, text="Progress: 50.00%")

    @patch('concrete.ui.components.log_stream.SessionManager')
    @patch('concrete.ui.components.log_stream.st')
    def test_log_stream_empty(self, mock_st, mock_session_manager):
        """
        Tests that the log stream shows an info message when there are no logs.
        """
        mock_state = WorkflowState(log_entries=[])
        mock_session_manager.get_workflow_state.return_value = mock_state
        render_log_stream()
        mock_st.info.assert_called_with("Workflow has not started. Log is empty.")

    @patch('concrete.ui.components.log_stream.SessionManager')
    @patch('concrete.ui.components.log_stream.st')
    def test_log_stream_with_entries(self, mock_st, mock_session_manager):
        """
        Tests that the log stream renders log entries.
        """
        from datetime import datetime
        log_entry = LogEntry(timestamp=datetime.now(), message="Test log", level="INFO")
        mock_state = WorkflowState(log_entries=[log_entry])
        mock_session_manager.get_workflow_state.return_value = mock_state
        render_log_stream()
        mock_st.expander.assert_called()

    @patch('concrete.ui.components.progress_tables.SessionManager')
    @patch('concrete.ui.components.progress_tables.st')
    @patch('concrete.ui.components.progress_tables.pd')
    def test_progress_tables_with_stats(self, mock_pd, mock_st, mock_session_manager):
        """
        Tests that the progress tables render metrics and dataframes with stats.
        """
        # Arrange
        mock_cols = (MagicMock(), MagicMock(), MagicMock())
        mock_st.columns.return_value = mock_cols
        stats = {
            "file_processing": {"total_files": 10, "processed": 5, "errors": 1},
            "by_source_type": [{"source_type": "Python", "files": 10}]
        }
        mock_state = WorkflowState(workflow_running=True, progress_stats=stats)
        mock_session_manager.get_workflow_state.return_value = mock_state
        render_progress_tables()
        
        # Assert on the mocked columns
        mock_cols[0].metric.assert_called_with("Total Files", "10")
        mock_cols[1].metric.assert_called_with("Files Processed", "5")
        mock_cols[2].metric.assert_called_with("Errors", "1", delta_color="inverse")
        mock_st.dataframe.assert_called()

if __name__ == '__main__':
    unittest.main()
