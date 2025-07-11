import streamlit as st

def create_three_pane_layout():
    """
    Creates the main three-pane layout for the application.

    The layout consists of:
    - A left pane for workflow controls (25%)
    - A main pane for the live log stream (37.5%)
    - A right pane for progress tables and analytics (37.5%)

    Returns:
        tuple: A tuple containing the three Streamlit columns (left, main, right).
    """
    left_pane_col, main_pane_col, right_pane_col = st.columns((0.25, 0.375, 0.375))

    with left_pane_col:
        st.header("Controls")
        # Placeholder for workflow_controls.py content
        st.info("Workflow controls will be here.")

    with main_pane_col:
        st.header("Log Stream")
        # Placeholder for log_stream.py content
        st.info("Live log stream will be here.")

    with right_pane_col:
        st.header("Progress")
        # Placeholder for progress_tables.py content
        st.info("Progress tables will be here.")

    return left_pane_col, main_pane_col, right_pane_col
