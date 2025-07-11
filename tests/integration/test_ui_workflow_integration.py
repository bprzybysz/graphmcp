import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from concrete.ui.app import main as run_app
from concrete.ui.state.workflow_state import WorkflowState, LogEntry
from concrete.workflow.manager import WorkflowManager
from datetime import datetime

class TestUIWorkflowIntegration(unittest.TestCase):

    @patch('concrete.ui.app.st')
    @patch('concrete.ui.app.SessionManager')
    @patch('concrete.ui.layouts.three_pane_layout.render_workflow_controls')
    @patch('concrete.ui.layouts.three_pane_layout.render_log_stream')
    @patch('concrete.ui.layouts.three_pane_layout.render_progress_tables')
    def test_app_renders_main_layout_and_components(
        self, 
        mock_render_progress, 
        mock_render_logs, 
        mock_render_controls, 
        mock_session_manager, 
        mock_st
    ):
        """
        Tests that the main application entry point initializes the session,
        sets up the page, and calls the main layout function which in turn
        renders the core UI components.
        """
        # Arrange
        mock_state = WorkflowState()
        mock_session_manager.get_workflow_state.return_value = mock_state

        # Act
        run_app()

        # Assert
        # Check that the page is configured and title is set
        mock_st.set_page_config.assert_called_once()
        mock_st.title.assert_called_once()
        
        # Check that the session is initialized
        mock_session_manager.initialize_session_state.assert_called_once()

        # Check that the main layout components are rendered
        mock_render_controls.assert_called_once()
        mock_render_logs.assert_called_once()
        mock_render_progress.assert_called_once()

    @patch('concrete.ui.components.workflow_controls.st')
    @patch('concrete.ui.components.workflow_controls.SessionManager')
    def test_start_button_triggers_workflow_state_change(
        self,
        mock_session_manager,
        mock_st
    ):
        """
        Tests that clicking the 'Start Workflow' button sets the workflow_running
        state to True and triggers a rerun.
        """
        # Arrange
        mock_state = WorkflowState(workflow_running=False)
        mock_session_manager.get_workflow_state.return_value = mock_state
        mock_st.button.return_value = True # Simulate user clicking the button
        mock_st.columns.return_value = (MagicMock(), MagicMock())

        # Act
        from concrete.ui.components.workflow_controls import render_workflow_controls
        render_workflow_controls()

        # Assert
        self.assertTrue(mock_state.workflow_running)
        self.assertEqual(mock_state.progress_percentage, 0)
        mock_st.rerun.assert_called_once()

if __name__ == '__main__':
    unittest.main()
