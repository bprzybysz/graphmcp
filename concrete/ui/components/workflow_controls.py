import streamlit as st
from concrete.ui.state.session_manager import SessionManager

def render_workflow_controls():
    """
    Renders the workflow control elements in the UI, such as start/stop buttons,
    auto-refresh toggle, and progress bar.
    """
    state = SessionManager.get_workflow_state()

    st.subheader("Workflow Controls")

    col1, col2 = st.columns([1, 3])

    with col1:
        if not state.workflow_running:
            if st.button("▶️ Start Workflow", use_container_width=True):
                # In a real app, this would trigger the workflow manager
                state.workflow_running = True
                state.progress_percentage = 0
                st.rerun()
        else:
            if st.button("⏹️ Stop Workflow", use_container_width=True):
                # This would call the workflow manager to stop the process
                state.workflow_running = False
                st.rerun()

    with col2:
        state.auto_refresh = st.toggle("Auto-refresh", value=state.auto_refresh, help="Toggle to enable/disable auto-refreshing the log view.")
    
    st.progress(state.progress_percentage / 100.0, text=f"Progress: {state.progress_percentage:.2f}%")
