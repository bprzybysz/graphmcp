"""
Enhanced Streamlit UI for GraphMCP Preview with real-time workflow visualization.

This module provides a modern, responsive UI with:
- Left progress pane (25%): Real-time workflow step tracking
- Main log pane (75%): Live workflow logs with multiple content types
"""

import time
from datetime import datetime
from typing import Optional

# Import logging system
from clients.preview_mcp.workflow_log import (
    get_workflow_log, log_info, log_table, log_sunburst,
    LogEntry, LogEntryType, TableData, SunburstData
)
from clients.preview_mcp.context import WorkflowContext, WorkflowStatus

# Try to import Streamlit with graceful fallback
try:
    import streamlit as st
    import plotly.graph_objects as go
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    
    # Mock Streamlit for testing
    class MockStreamlit:
        def __init__(self):
            # Mock session_state to be a dynamic object like real Streamlit session_state
            self.session_state = type('MockSessionState', (), {})()
            
        def title(self, text): print(f"TITLE: {text}")
        def markdown(self, text, unsafe_allow_html=False): print(f"MARKDOWN: {text}")
        def button(self, text, key=None, help=None): return False
        def checkbox(self, text, value=False, key=None): return value
        def metric(self, label, value): print(f"METRIC: {label}={value}")
        def info(self, text): print(f"INFO: {text}")
        def error(self, text): print(f"ERROR: {text}")
        def caption(self, text): print(f"CAPTION: {text}")
        def progress(self, value): print(f"PROGRESS: {value}")
        def rerun(self): pass
        def set_page_config(self, **kwargs): pass
        
        def spinner(self, text): 
            return type('MockSpinner', (), {'__enter__': lambda s: None, '__exit__': lambda s, *a: None})()
        
        def columns(self, widths): 
            return [type('MockColumn', (), {'__enter__': lambda s: None, '__exit__': lambda s, *a: None})() for _ in range(len(widths) if isinstance(widths, list) else widths)]
        
        def expander(self, title, expanded=False): 
            return type('MockExpander', (), {'__enter__': lambda s: None, '__exit__': lambda s, *a: None})()
        
        def container(self): 
            return type('MockContainer', (), {'__enter__': lambda s: None, '__exit__': lambda s, *a: None})()
        
        def plotly_chart(self, fig, use_container_width=True): 
            print(f"PLOTLY_CHART: {fig}")

    st = MockStreamlit()

class StreamlitWorkflowUI:
    """Enhanced Streamlit UI for MCP workflow visualization."""
    
    def __init__(self):
        """Initialize the Streamlit UI."""
        pass

    def initialize_session_state(self):
        """Initialize Streamlit session state with default values."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Initialize session state
        if 'workflow_context' not in st.session_state:
            st.session_state.workflow_context = WorkflowContext(
                workflow_id=f"session-{int(time.time())}"
            )
        
        if 'workflow_id' not in st.session_state:
            st.session_state.workflow_id = st.session_state.workflow_context.workflow_id
            
        if 'workflow_log' not in st.session_state:
            st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
            
        if 'demo_mode' not in st.session_state:
            st.session_state.demo_mode = False
            
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        
    def run(self):
        """Run the Streamlit application with proper left progress and main log panes."""
        if not STREAMLIT_AVAILABLE:
            st.error("Streamlit is not installed. Please install it with: pip install streamlit")
            return

        st.set_page_config(
            layout="wide", 
            page_title="MCP Workflow Agent",
            page_icon="🔄"
        )

        # Initialize session state
        self.initialize_session_state()

        st.title("🔄 MCP Workflow Agent")
        st.markdown("Real-time workflow visualization with live progress tracking and log streaming")

        # Create the main layout: Left pane (25%) and Main pane (75%)
        left_col, main_col = st.columns([1, 3])
        
        # Left Progress Pane (25%)
        with left_col:
            st.markdown("### 🔄 Workflow Progress")
            self.render_progress_pane()
        
        # Main Log Pane (75%) 
        with main_col:
            st.markdown("### 📋 Workflow Log")
            self.render_log_pane()
        
        # Auto-refresh for demo mode
        if st.session_state.demo_mode and st.session_state.auto_refresh:
            time.sleep(2)  # Wait 2 seconds between steps
            self.simulate_demo_progress()
            st.rerun()

    def render_progress_pane(self):
        """Render the left progress pane with workflow controls and step tracking."""
        if not STREAMLIT_AVAILABLE:
            return
            
        context = st.session_state.workflow_context
        
        # Workflow controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start Demo", key="start_demo"):
                self.start_demo_workflow()
        with col2:
            if st.button("🗑️ Clear", key="clear_logs"):
                self.clear_workflow()
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.checkbox(
            "🔄 Auto-refresh", 
            value=st.session_state.auto_refresh,
            key="auto_refresh_checkbox"
        )
        
        # Workflow status
        status_icons = {
            WorkflowStatus.PENDING: "🟡",
            WorkflowStatus.IN_PROGRESS: "🔵", 
            WorkflowStatus.COMPLETED: "🟢",
            WorkflowStatus.FAILED: "🔴"
        }
        
        st.markdown(f"**Status:** {status_icons.get(context.status, '⚪')} {context.status.value}")
        
        # Progress bar and steps
        if context.steps:
            completed_steps = sum(1 for step in context.steps if step.status == WorkflowStatus.COMPLETED)
            progress = completed_steps / len(context.steps)
            st.progress(progress)
            st.caption(f"{completed_steps}/{len(context.steps)} completed")
            
            # Step list
            st.markdown("**Steps:**")
            for i, step in enumerate(context.steps):
                status_icon = status_icons.get(step.status, '⚪')
                st.markdown(f"{status_icon} **{i+1}.** {step.name}")
                
                if step.status == WorkflowStatus.IN_PROGRESS:
                    st.caption("🔄 Running...")
                elif step.status == WorkflowStatus.COMPLETED:
                    st.caption("✅ Completed")
        else:
            st.info("No workflow steps yet. Click 'Start Demo' to begin!")

    def render_log_pane(self):
        """Render the main log pane with workflow logs."""
        if not STREAMLIT_AVAILABLE:
            return
            
        workflow_log = st.session_state.workflow_log
        entries = workflow_log.get_entries()
        
        if not entries:
            st.info("No log entries yet. Start a workflow to see logs here.")
            return
        
        # Log summary metrics
        summary = workflow_log.get_summary()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", summary["total_entries"])
        with col2:
            st.metric("Log Entries", summary["entry_counts"].get("log", 0))
        with col3:
            st.metric("Charts/Tables", 
                     summary["entry_counts"].get("table", 0) + summary["entry_counts"].get("sunburst", 0))
        
        st.markdown("---")
        
        # Render log entries
        for entry in entries:
            self.render_log_entry(entry)

    def render_log_entry(self, entry: LogEntry):
        """Render a single log entry based on its type."""
        if not STREAMLIT_AVAILABLE:
            return
            
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        
        if entry.entry_type == LogEntryType.LOG:
            # Render log entry with level styling
            level = entry.metadata.get("level", "info")
            level_icons = {
                "info": "ℹ️",
                "warning": "⚠️", 
                "error": "❌",
                "debug": "🐛"
            }
            
            icon = level_icons.get(level, "📝")
            st.markdown(f"**{timestamp}** {icon} {entry.content}")
            
        elif entry.entry_type == LogEntryType.TABLE:
            # Render table entry
            table_data: TableData = entry.content
            st.markdown(f"**{timestamp}** 📊 **Table**")
            st.markdown(table_data.to_markdown())
            
        elif entry.entry_type == LogEntryType.SUNBURST:
            # Render sunburst chart
            sunburst_data: SunburstData = entry.content
            st.markdown(f"**{timestamp}** 🌞 **{sunburst_data.title or 'Sunburst Chart'}**")
            
            try:
                fig = sunburst_data.to_plotly_figure()
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering sunburst chart: {e}")
        
        # Add separator
        st.markdown("---")

    def start_demo_workflow(self):
        """Start a demo workflow with sample data."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Reset workflow context
        st.session_state.workflow_context = WorkflowContext(
            workflow_id=f"demo-{int(time.time())}"
        )
        st.session_state.workflow_id = st.session_state.workflow_context.workflow_id
        st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
        
        # Create demo steps
        steps = [
            ("Initialize Workflow", {"config": "demo_config"}),
            ("Analyze Data", {"source": "sample_data.csv"}),
            ("Generate Report", {"format": "markdown"}),
            ("Create Visualizations", {"charts": ["pie", "sunburst"]}),
            ("Finalize Results", {"output": "results.json"})
        ]
        
        # Add steps to context
        context = st.session_state.workflow_context
        for step_name, input_data in steps:
            context.add_step(step_name, input_data)
        
        context.status = WorkflowStatus.IN_PROGRESS
        st.session_state.demo_mode = True
        
        # Log initial message
        log_info(st.session_state.workflow_id, "🚀 **Demo workflow started**\n\n- Workflow ID: `{}`\n- Total steps: {}".format(
            st.session_state.workflow_id, len(steps)
        ))
        
        st.rerun()

    def simulate_demo_progress(self):
        """Simulate demo workflow progress."""
        if not st.session_state.demo_mode:
            return
            
        context = st.session_state.workflow_context
        
        # Find next pending step
        for step in context.steps:
            if step.status == WorkflowStatus.PENDING:
                # Start this step
                step.status = WorkflowStatus.IN_PROGRESS
                log_info(st.session_state.workflow_id, f"🔄 **Starting step:** {step.name}")
                
                # Simulate step completion after a delay
                time.sleep(1)
                step.status = WorkflowStatus.COMPLETED
                step.output_data = {"status": "completed", "timestamp": datetime.now().isoformat()}
                
                # Log step completion with different content types
                if "Analyze" in step.name:
                    # Log a table
                    log_table(
                        st.session_state.workflow_id,
                        headers=["Metric", "Value", "Status"],
                        rows=[
                            ["Records Processed", "1,234", "✅"],
                            ["Errors Found", "0", "✅"],
                            ["Processing Time", "2.3s", "✅"]
                        ],
                        title="Analysis Results"
                    )
                    
                elif "Visualizations" in step.name:
                    # Log a sunburst chart
                    log_sunburst(
                        st.session_state.workflow_id,
                        labels=["Total", "Backend", "Frontend", "Database", "API", "UI", "Auth", "Cache"],
                        parents=["", "Total", "Total", "Total", "Backend", "Frontend", "Backend", "Backend"],
                        values=[100, 45, 30, 25, 20, 15, 15, 10],
                        title="System Components Breakdown"
                    )
                    
                else:
                    # Regular log entry
                    log_info(st.session_state.workflow_id, f"✅ **Completed:** {step.name}\n\n- Duration: {1.0:.1f}s\n- Status: Success")
                
                break
        
        # Check if all steps are completed
        if all(step.status == WorkflowStatus.COMPLETED for step in context.steps):
            context.status = WorkflowStatus.COMPLETED
            st.session_state.demo_mode = False
            log_info(st.session_state.workflow_id, "🎉 **Workflow completed successfully!**\n\n- All steps finished\n- No errors encountered")

    def clear_workflow(self):
        """Clear current workflow and logs."""
        if not STREAMLIT_AVAILABLE:
            return
            
        st.session_state.workflow_context = WorkflowContext(
            workflow_id=f"session-{int(time.time())}"
        )
        st.session_state.workflow_id = st.session_state.workflow_context.workflow_id
        st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
        st.session_state.demo_mode = False
        
        st.rerun()


def main():
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not available. Exiting.")
        return

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Environment variables loaded from .env file.")
    except ImportError:
        print("python-dotenv not installed. Skipping .env loading.")
        print("Install with: pip install python-dotenv")
    except Exception as e:
        print(f"Error loading .env file: {e}")

    app = StreamlitWorkflowUI()
    app.run()


if __name__ == "__main__":
    main()