import streamlit as st

from .workflow_state import WorkflowState


class SessionManager:
    """
    Manages the Streamlit session state for the application.
    """

    @staticmethod
    def initialize_session_state():
        """
        Initializes the session state with a WorkflowState object if not already present.
        """
        if "workflow_state" not in st.session_state:
            st.session_state["workflow_state"] = WorkflowState()

    @staticmethod
    def get_workflow_state() -> WorkflowState:
        """
        Retrieves the WorkflowState object from the session state.

        Initializes the session state if it hasn't been already.

        Returns:
            WorkflowState: The current workflow state.
        """
        SessionManager.initialize_session_state()
        return st.session_state["workflow_state"]
