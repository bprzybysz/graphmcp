import streamlit as st

from ui.state.session_manager import SessionManager


def render_log_stream():
    """
    Renders the log stream, displaying log entries from the current workflow state.
    """
    state = SessionManager.get_workflow_state()

    st.subheader("Live Workflow Log")

    log_container = st.container()

    with log_container:
        if not state.log_entries:
            st.info("Workflow has not started. Log is empty.")
            return

        for entry in sorted(state.log_entries, key=lambda x: x.timestamp, reverse=True):
            log_level_icon = {
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "🔥",
                "DEBUG": "🐞",
            }.get(entry.level, "➡️")

            with st.expander(
                f"{log_level_icon} [{entry.timestamp.strftime('%H:%M:%S')}] {entry.message}",
                expanded=False,
            ):
                if entry.details:
                    st.json(entry.details)
                else:
                    st.text("No additional details.")
