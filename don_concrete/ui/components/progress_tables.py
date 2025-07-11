import streamlit as st
import pandas as pd
from don_concrete.ui.state.session_manager import SessionManager

def render_progress_tables():
    """
    Renders tables and metrics related to the workflow's progress,
    such as file processing status and source type analysis.
    """
    state = SessionManager.get_workflow_state()

    st.subheader("Progress Analytics")

    if not state.workflow_running and not state.progress_stats:
        st.info("Workflow has not run yet. No progress to display.")
        return

    # Use mock data if the workflow is not running but we want to see the UI
    stats = state.progress_stats
    if not stats and state.workflow_running == False: # for UI design purposes
        stats = {
            "file_processing": {
                "total_files": 100,
                "processed": 50,
                "errors": 5,
            },
            "by_source_type": [
                {"source_type": "Python", "files": 60, "processed": 30, "errors": 3},
                {"source_type": "SQL", "files": 30, "processed": 15, "errors": 2},
                {"source_type": "JSON", "files": 10, "processed": 5, "errors": 0},
            ]
        }

    if not stats:
        st.info("Waiting for progress data...")
        return
        
    # --- Metrics ---
    col1, col2, col3 = st.columns(3)
    file_stats = stats.get("file_processing", {})
    col1.metric("Total Files", f"{file_stats.get('total_files', 0)}")
    col2.metric("Files Processed", f"{file_stats.get('processed', 0)}")
    col3.metric("Errors", f"{file_stats.get('errors', 0)}", delta_color="inverse")

    # --- Source Type Table ---
    st.write("### Progress by Source Type")
    source_type_data = stats.get("by_source_type")
    if source_type_data:
        df = pd.DataFrame(source_type_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No source type data available.")
