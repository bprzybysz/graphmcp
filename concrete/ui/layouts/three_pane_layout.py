import streamlit as st

from concrete.ui.components.workflow_controls import render_workflow_controls
from concrete.ui.components.log_stream import render_log_stream
from concrete.ui.components.progress_tables import render_progress_tables

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
        render_workflow_controls()

    with main_pane_col:
        render_log_stream()

    with right_pane_col:
        render_progress_tables()

    return left_pane_col, main_pane_col, right_pane_col
