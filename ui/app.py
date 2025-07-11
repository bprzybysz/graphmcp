import streamlit as st

from ui.layouts.three_pane_layout import create_three_pane_layout
from ui.state.session_manager import SessionManager


def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(page_title="GraphMCP Workflow Orchestrator", layout="wide")

    st.title("GraphMCP: Database Decommissioning Workflow")

    # Initialize session state
    SessionManager.initialize_session_state()

    # Create the main layout
    create_three_pane_layout()


if __name__ == "__main__":
    main()
