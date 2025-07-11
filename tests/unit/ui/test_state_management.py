import unittest
from unittest.mock import MagicMock, patch

from concrete.ui.state.workflow_state import WorkflowState
from concrete.ui.state.session_manager import SessionManager

# Mocking streamlit's session_state for unit testing
class MockSessionState(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__dict__ = self

class TestStateManagement(unittest.TestCase):

    @patch('streamlit.session_state', new_callable=MockSessionState)
    def test_initialize_session_state_creates_state(self, mock_session_state):
        """
        Tests that a new WorkflowState is created if one doesn't exist.
        """
        self.assertNotIn('workflow_state', mock_session_state)
        SessionManager.initialize_session_state()
        self.assertIn('workflow_state', mock_session_state)
        self.assertIsInstance(mock_session_state.workflow_state, WorkflowState)

    @patch('streamlit.session_state', new_callable=MockSessionState)
    def test_initialize_session_state_does_not_overwrite(self, mock_session_state):
        """
        Tests that an existing WorkflowState is not overwritten.
        """
        existing_state = WorkflowState(workflow_id="test_id")
        mock_session_state.workflow_state = existing_state
        
        SessionManager.initialize_session_state()
        
        self.assertEqual(mock_session_state.workflow_state, existing_state)
        self.assertEqual(mock_session_state.workflow_state.workflow_id, "test_id")

    @patch('streamlit.session_state', new_callable=MockSessionState)
    def test_get_workflow_state_initializes_and_returns(self, mock_session_state):
        """
        Tests that get_workflow_state returns a valid WorkflowState,
        initializing it if necessary.
        """
        state = SessionManager.get_workflow_state()
        self.assertIsInstance(state, WorkflowState)
        self.assertIn('workflow_state', mock_session_state)

    def test_workflow_state_defaults(self):
        """
        Tests that the WorkflowState dataclass initializes with correct defaults.
        """
        state = WorkflowState()
        self.assertIsNone(state.workflow_id)
        self.assertFalse(state.workflow_running)
        self.assertTrue(state.auto_refresh)
        self.assertEqual(state.progress_percentage, 0.0)
        self.assertEqual(state.log_entries, [])
        self.assertEqual(state.error_count, 0)
        self.assertTrue(state.mock_mode)
        self.assertEqual(state.progress_stats, {})

if __name__ == '__main__':
    unittest.main()
