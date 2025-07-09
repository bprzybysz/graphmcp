"""
Streamlit UI for MCP Workflow Agent with real-time workflow visualization.

This module provides a web interface using Streamlit for interacting with
the MCP workflow agent and visualizing workflow execution in real-time.

Features:
- Left thin pane (25%): Workflow steps with real-time progress tracking
- Main pane (75%): Workflow log supporting logs, tables, and sunburst charts

Requires Python 3.11+
"""

from __future__ import annotations

import time
from unittest.mock import Mock
from typing import Optional, Generator

try:
    import streamlit as st
    import plotly.io as pio
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # Mock streamlit for type checking when not available
    class MockStreamlit:
        def __init__(self):
            # Mock session_state to be a dynamic object like real Streamlit session_state
            self.session_state = Mock()
            
            # Mock sidebar to support context manager protocol
            self.sidebar = Mock()
            self.sidebar.__enter__ = Mock(return_value=self.sidebar)
            self.sidebar.__exit__ = Mock(return_value=None)

        def title(self, text): pass
        def markdown(self, text, unsafe_allow_html=False): pass
        def chat_message(self, role): return Mock()
        def chat_input(self, placeholder): return ""
        def selectbox(self, label, options, help=None): return options[0] if options else None
        def button(self, text): return False
        def write(self, text): pass
        def error(self, text): pass
        def spinner(self, text): 
            mock_spinner = Mock()
            mock_spinner.__enter__ = Mock(return_value=mock_spinner)
            mock_spinner.__exit__ = Mock(return_value=None)
            return mock_spinner
        def empty(self): return Mock()
        def columns(self, widths): 
            mock_cols = [Mock() for _ in widths]
            for col in mock_cols:
                col.__enter__ = Mock(return_value=col)
                col.__exit__ = Mock(return_value=None)
                col.metric = Mock() # Mock metric for columns as well
            return mock_cols
        def expander(self, title, expanded=False): 
            mock_expander = Mock()
            mock_expander.__enter__ = Mock(return_value=mock_expander)
            mock_expander.__exit__ = Mock(return_value=None)
            return mock_expander
        def subheader(self, text): pass
        def caption(self, text): pass
        def metric(self, label, value): pass
        def rerun(self): pass
        def set_page_config(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def json(self, data): pass
        def plotly_chart(self, fig, **kwargs): pass
        def container(self): 
            mock_container = Mock()
            mock_container.__enter__ = Mock(return_value=mock_container)
            mock_container.__exit__ = Mock(return_value=None)
            return mock_container
    
    st = MockStreamlit()

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Generator
import time
import traceback

# Add the project's root directory to sys.path for module discovery
# This is necessary for absolute imports to work when the script is run directly
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
sys.path.insert(0, project_root)

# Import our components
from clients.preview_mcp.context import WorkflowContext, WorkflowStatus
from clients.preview_mcp.logging import create_workflow_logger, WorkflowLogger
from clients.preview_mcp.workflow_log import (
    get_workflow_log, LogEntryType, LogEntry, TableData, SunburstData,
    log_info, log_warning, log_error, log_table, log_sunburst
)


class StreamlitWorkflowUI:
    """Streamlit UI for workflow visualization with left progress pane and main log pane."""
    
    def __init__(self):
        """Initialize the Streamlit UI."""
        if not STREAMLIT_AVAILABLE:
            print("Warning: Streamlit not available. Install with: pip install streamlit")
            return
            
        self.workflow_logger: Optional[WorkflowLogger] = None
        
    def _get_logger(self) -> WorkflowLogger:
        """Get or create workflow logger."""
        if not self.workflow_logger:
            workflow_id = getattr(st.session_state, 'workflow_id', 'streamlit-session')
            session_id = getattr(st.session_state, 'session_id', 'default')
            self.workflow_logger = create_workflow_logger(workflow_id, session_id)
        return self.workflow_logger
        
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Initialize workflow context
        if not hasattr(st.session_state, 'workflow_context'):
            st.session_state.workflow_context = WorkflowContext(
                workflow_id="streamlit-session"
            )
            st.session_state.workflow_id = "streamlit-session"
            st.session_state.session_id = "default"
        
        # Initialize workflow log
        if not hasattr(st.session_state, 'workflow_log'):
            st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
            
        # Initialize demo mode
        if not hasattr(st.session_state, 'demo_mode'):
            st.session_state.demo_mode = False
            
        # Initialize auto-refresh
        if not hasattr(st.session_state, 'auto_refresh'):
            st.session_state.auto_refresh = True
    
    def render_progress_pane(self):
        """Render the left progress pane with workflow steps."""
        if not STREAMLIT_AVAILABLE:
            return
            
        st.subheader("🔄 Workflow Progress")
        
        context = st.session_state.workflow_context
        
        # Workflow controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Demo", help="Start demo workflow"):
                self.start_demo_workflow()
        with col2:
            if st.button("🗑️ Clear", help="Clear workflow and logs"):
                self.clear_workflow()
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh", value=st.session_state.auto_refresh)
        
        # Workflow status
        status_icons = {
            WorkflowStatus.PENDING: "🟡",
            WorkflowStatus.IN_PROGRESS: "🔵", 
            WorkflowStatus.COMPLETED: "🟢",
            WorkflowStatus.FAILED: "🔴"
        }
        
        st.markdown(f"**Status:** {status_icons.get(context.status, '⚪')} {context.status.value}")
        st.markdown(f"**Steps:** {len(context.steps)}")
        
        # Progress bar
        if context.steps:
            completed_steps = sum(1 for step in context.steps if step.status == WorkflowStatus.COMPLETED)
            progress = completed_steps / len(context.steps)
            st.progress(progress)
            st.caption(f"{completed_steps}/{len(context.steps)} completed")
        
        # Step list with real-time updates
        st.markdown("---")
        st.markdown("**Steps:**")
        
        for i, step in enumerate(context.steps):
            status_icon = status_icons.get(step.status, '⚪')
            
            # Create expandable step
            with st.container():
                # Step header
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{i+1}.** {step.name}")
                with col2:
                    st.markdown(f"{status_icon}")
                
                # Step details
                if step.input_data:
                    st.caption(f"📥 Input: {', '.join(step.input_data.keys())}")
                
                if step.output_data and step.status == WorkflowStatus.COMPLETED:
                    st.caption("✅ Completed")
                elif step.status == WorkflowStatus.FAILED:
                    st.caption("❌ Failed")
                elif step.status == WorkflowStatus.IN_PROGRESS:
                    st.caption("🔄 Running...")
                
                st.markdown("---")
    
    def render_log_pane(self):
        """Render the main log pane with workflow logs."""
        if not STREAMLIT_AVAILABLE:
            return
            
        st.subheader("📋 Workflow Log")
        
        workflow_log = st.session_state.workflow_log
        entries = workflow_log.get_entries()
        
        if not entries:
            st.info("No log entries yet. Start a workflow to see logs here.")
            return
        
        # Log summary
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
        
    def run(self):
        """Run the Streamlit application."""
        if not STREAMLIT_AVAILABLE:
            st.error("Streamlit is not installed. Please install it with: pip install streamlit")
            return

        st.set_page_config(
            layout="wide", 
            page_title="MCP Workflow Agent",
            page_icon="🔄"
        )

        # Custom CSS for layout and styling
        st.markdown(
            """
            <style>
            /* Main container styling */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            
            /* Progress pane styling */
            .progress-pane {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 1rem;
                height: 80vh;
                overflow-y: auto;
            }
            
            /* Log pane styling */
            .log-pane {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 1rem;
                height: 80vh;
                overflow-y: auto;
                border: 1px solid #e0e0e0;
            }
            
            /* Workflow step styling */
            .workflow-step {
                margin-bottom: 0.5rem;
                padding: 0.5rem;
                border-radius: 5px;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
            
            /* Log entry styling */
            .log-entry {
                margin-bottom: 1rem;
                padding: 0.75rem;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
            
            /* Reduce font size for compact display */
            .small-text {
                font-size: 0.85em;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        self.initialize_session_state()

        st.title("🔄 MCP Workflow Agent")
        st.markdown("Real-time workflow visualization with live progress tracking and log streaming")

        # Main layout: Left pane (25%) and Right pane (75%)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Left pane: Workflow progress
            with st.container():
                st.markdown('<div class="progress-pane">', unsafe_allow_html=True)
                self.render_progress_pane()
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Right pane: Workflow log
            with st.container():
                st.markdown('<div class="log-pane">', unsafe_allow_html=True)
                self.render_log_pane()
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-refresh for demo mode
        if st.session_state.demo_mode and st.session_state.auto_refresh:
            time.sleep(2)  # Wait 2 seconds between steps
            self.simulate_demo_progress()
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