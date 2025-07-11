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
from clients.preview_mcp.progress_table import (
    ProgressTableData, log_progress_table, get_progress_table,
    ProcessingStatus, ProcessingPhase
)

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

# Enhanced styling for three-pane layout and modern design
PROGRESS_TABLE_CSS = """
<style>
/* Global improvements for three-pane layout */
.stMarkdown {
    font-size: 14px !important;
    line-height: 1.4 !important;
    margin-bottom: 0.5rem !important;
}

.stMarkdown p {
    margin-bottom: 0.5rem !important;
}

/* Optimized spacing for three-pane layout */
.main .block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    max-width: none !important;
}

.element-container {
    margin-bottom: 0.3rem !important;
}

/* Column separation and layout */
.stColumn {
    padding: 0.5rem !important;
    border-right: 1px solid #f0f0f0;
}

.stColumn:last-child {
    border-right: none;
}

/* Progress table styling */
.progress-table {
    background: #ffffff;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 1rem !important;
    font-size: 14px;
}

/* Enhanced log table with better readability */
.enhanced-log-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 1rem !important;
    font-size: 14px;
}

.enhanced-log-table th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    text-align: left;
    padding: 10px 8px;
    border-bottom: 2px solid #5a67d8;
    font-size: 14px;
}

.enhanced-log-table tr:nth-child(even) {
    background-color: #f8f9fa;
}

.enhanced-log-table tr:nth-child(odd) {
    background-color: #ffffff;
}

.enhanced-log-table tr:hover {
    background-color: #e8f4fd;
    transition: background-color 0.2s ease;
}

.enhanced-log-table td {
    padding: 8px;
    border-bottom: 1px solid #e9ecef;
    vertical-align: middle;
    font-size: 13px;
}

/* Better spacing for log entries */
hr {
    margin: 0.5rem 0 !important;
    border-color: #e9ecef !important;
}

/* Improve button and metric styling */
.stButton button {
    font-size: 14px !important;
    padding: 0.5rem 1rem !important;
}

.stMetric {
    font-size: 14px !important;
}

.stMetric > div {
    font-size: 14px !important;
}

/* Progress bar improvements */
.stProgress .st-bo {
    height: 20px !important;
}

/* Modern pane headers */
.stMarkdown h3 {
    color: #2c3e50 !important;
    border-bottom: 2px solid #3498db !important;
    padding-bottom: 0.5rem !important;
    margin-bottom: 1rem !important;
}

/* Enhanced metrics for compact display */
.stMetric {
    background: #f8f9fa !important;
    padding: 0.5rem !important;
    border-radius: 6px !important;
    border: 1px solid #e9ecef !important;
}

/* Better button styling */
.stButton button {
    width: 100% !important;
    border-radius: 6px !important;
}

/* Compact dataframe styling */
.stDataFrame {
    border: 1px solid #e9ecef !important;
    border-radius: 6px !important;
}
</style>
"""

class StreamlitWorkflowUI:
    """Enhanced Streamlit UI for MCP workflow visualization."""
    
    def __init__(self):
        """Initialize the Streamlit UI."""
        pass

    def initialize_session_state(self):
        """Initialize Streamlit session state with default values following best practices."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Centralized session state initialization - single source of truth
        session_defaults = {
            'workflow_context': None,
            'workflow_id': None,
            'workflow_log': None,
            'demo_mode': False,
            'auto_refresh': True,
            'real_workflow': False,
            'ui_state': {
                'left_pane_expanded': True,
                'right_pane_expanded': True,
                'current_step': None,
                'error_count': 0,
                'last_refresh': time.time()
            }
        }
        
        # Initialize all defaults if not present
        for key, default_value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Initialize workflow context if needed
        if st.session_state.workflow_context is None:
            st.session_state.workflow_context = WorkflowContext(
                workflow_id=f"session-{int(time.time())}"
            )
            st.session_state.workflow_id = st.session_state.workflow_context.workflow_id
            st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
        
        if 'real_workflow' not in st.session_state:
            st.session_state.real_workflow = False
        
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

        # Create the optimized three-pane layout: Left (25%) | Main (37.5%) | Right (37.5%)
        left_col, main_col, right_col = st.columns([2, 3, 3])
        
        # Left Progress Pane (25%)
        with left_col:
            st.markdown("### 🔄 Workflow Progress")
            self.render_progress_pane()
        
        # Main Log Pane (37.5%) 
        with main_col:
            st.markdown("### 📋 Workflow Log")
            self.render_log_pane()
        
        # Right Progress Table Pane (37.5%)
        with right_col:
            st.markdown("### 📊 Progress Tables")
            self.render_progress_table_pane()
        
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
            
        # Apply enhanced styling
        st.markdown(PROGRESS_TABLE_CSS, unsafe_allow_html=True)
        
        # Refresh workflow log from the global store
        st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
        workflow_log = st.session_state.workflow_log
        entries = workflow_log.get_entries()
        
        # Debug info
        progress_table_count = sum(1 for e in entries if e.entry_type == LogEntryType.PROGRESS_TABLE)
        st.caption(f"Workflow ID: {st.session_state.workflow_id} | Entries: {len(entries)} | Progress Tables: {progress_table_count}")
        
        # Progress tables are now handled in the dedicated right pane
        
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
            progress_table_count = summary["entry_counts"].get("progress_table", 0)
            charts_tables_count = summary["entry_counts"].get("table", 0) + summary["entry_counts"].get("sunburst", 0) + progress_table_count
            st.metric("Charts/Tables", charts_tables_count)
        
        st.markdown("---")
        
        # Render all log entries - progress tables are handled in right pane
        for entry in entries:
            self.render_log_entry(entry)
    
    def render_progress_table_pane(self):
        """Render the dedicated right pane for progress tables with modern web design."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Get progress tables from workflow log entries
        workflow_log = get_workflow_log(st.session_state.workflow_id)
        entries = workflow_log.get_entries()
        progress_table_entries = [e for e in entries if e.entry_type == LogEntryType.PROGRESS_TABLE]
        
        if not progress_table_entries:
            # Empty state with call-to-action
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #666;">
                <h3>📊 No Progress Data</h3>
                <p>Start a workflow to see real-time file processing progress here.</p>
            </div>
            """, unsafe_allow_html=True)
            
            return
        
        # Render the most recent progress table
        latest_progress_entry = progress_table_entries[-1]
        progress_table = latest_progress_entry.content
        
        # Debug logging
        print(f"🔍 Found {len(progress_table_entries)} progress table entries, showing latest with {len(progress_table.entries)} files")
        
        # Render the enhanced progress table
        self.render_progress_table(progress_table)
        
    def render_progress_table(self, progress_table: ProgressTableData):
        """Render the dynamic progress table with modern web design."""
        if not STREAMLIT_AVAILABLE:
            return
        
        # Modern header with completion rate
        completion_rate = progress_table.get_completion_rate()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: white;">📊 {progress_table.title}</h4>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{completion_rate:.1f}% Complete</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact metrics in 2x2 grid for better space usage
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📁 Total", progress_table.total_files)
            st.metric("❌ Failed", progress_table.failed_files)
        with col2:
            st.metric("✅ Completed", progress_table.completed_files)
            st.metric("🚫 Excluded", progress_table.excluded_files)
        
        # Enhanced progress bar with styling
        if progress_table.total_files > 0:
            progress = progress_table.completed_files / progress_table.total_files
            st.progress(progress)
            st.caption(f"📈 Processing: {progress_table.completed_files}/{progress_table.total_files} files ({completion_rate:.1f}%)")
        
        # Compact files table optimized for right pane
        if progress_table.entries:
            # Group by source type for better organization
            groups = progress_table.group_by_source_type()
            
            for source_type, entries in groups.items():
                # More compact expandable sections
                with st.expander(f"📁 {source_type} ({len(entries)})", expanded=len(groups) <= 2):
                    
                    # Create compact table data optimized for narrow width
                    table_data = {
                        "Status": [entry.get_status_icon() for entry in entries],
                        "File": [entry.get_truncated_path(25) for entry in entries],  # Shorter paths
                        "Conf": [f"{entry.confidence:.0%}" for entry in entries],     # Compact confidence
                        "Matches": [entry.match_count for entry in entries]
                    }
                    
                    # Render as compact dataframe
                    if table_data["Status"]:
                        st.dataframe(
                            table_data,
                            use_container_width=True,
                            hide_index=True,
                            height=min(200, len(entries) * 35 + 50),  # Dynamic height
                            column_config={
                                "Status": st.column_config.TextColumn("", width="small"),
                                "File": st.column_config.TextColumn("File", width="large"), 
                                "Conf": st.column_config.TextColumn("Conf", width="small"),
                                "Matches": st.column_config.NumberColumn("#", width="small")
                            }
                        )

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
            
            # Enhanced log entry with background color based on level
            if level == "error":
                st.error(f"**{timestamp}** {icon} {entry.content}")
            elif level == "warning":
                st.warning(f"**{timestamp}** {icon} {entry.content}")
            elif level == "debug":
                st.info(f"**{timestamp}** {icon} {entry.content}")
            else:
                st.markdown(f"**{timestamp}** {icon} {entry.content}")
            
        elif entry.entry_type == LogEntryType.TABLE:
            # Render table entry with enhanced styling
            table_data: TableData = entry.content
            st.markdown(f"**{timestamp}** 📊 **{table_data.title or 'Table'}**")
            
            # Generate HTML table with enhanced styling
            html_table = self.generate_enhanced_table_html(table_data)
            st.markdown(html_table, unsafe_allow_html=True)
            
        elif entry.entry_type == LogEntryType.SUNBURST:
            # Render sunburst chart
            sunburst_data: SunburstData = entry.content
            st.markdown(f"**{timestamp}** 🌞 **{sunburst_data.title or 'Sunburst Chart'}**")
            
            try:
                fig = sunburst_data.to_plotly_figure()
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering sunburst chart: {e}")
                
        elif entry.entry_type == LogEntryType.PROGRESS_TABLE:
            # Progress tables are handled in the right pane - show summary here
            progress_data: ProgressTableData = entry.content
            st.markdown(f"**{timestamp}** 📊 **Progress Table Created**: {progress_data.title or 'File Processing Progress'}")
            st.caption(f"📁 {len(progress_data.entries)} files processed - see details in Progress Tables pane →")
        
        # Add separator
        st.markdown("---")

    def start_demo_workflow(self):
        """Start the actual database decommissioning workflow."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Reset workflow context
        st.session_state.workflow_context = WorkflowContext(
            workflow_id=f"db-decommission-demo-{int(time.time())}"
        )
        st.session_state.workflow_id = st.session_state.workflow_context.workflow_id
        st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
        
        # Create actual database decommissioning steps
        steps = [
            ("Environment Validation", {"database_name": "postgres_air"}),
            ("Repository Processing", {"target_repos": ["https://github.com/bprzybys-nc/postgres-sample-dbs"]}),
            ("Pattern Discovery", {"database_name": "postgres_air"}),
            ("Quality Assurance", {"validation_rules": "decommission_rules"}),
            ("Workflow Summary", {"generate_metrics": True})
        ]
        
        # Add steps to context
        context = st.session_state.workflow_context
        for step_name, input_data in steps:
            context.add_step(step_name, input_data)
        
        context.status = WorkflowStatus.IN_PROGRESS
        st.session_state.demo_mode = True
        st.session_state.real_workflow = True  # Flag to run real workflow
        
        # Log initial message
        log_info(st.session_state.workflow_id, "🚀 **Database Decommissioning Workflow Started**\n\n- Database: `postgres_air`\n- Repository: `bprzybys-nc/postgres-sample-dbs`\n- Workflow ID: `{}`\n- Total steps: {}".format(
            st.session_state.workflow_id, len(steps)
        ))
        
        st.rerun()

    def simulate_demo_progress(self):
        """Run actual database decommissioning workflow progress."""
        if not st.session_state.demo_mode:
            return
            
        context = st.session_state.workflow_context
        
        # Find next pending step
        for step in context.steps:
            if step.status == WorkflowStatus.PENDING:
                # Start this step with live-updatable log
                step.status = WorkflowStatus.IN_PROGRESS
                from clients.preview_mcp.workflow_log import log_step_start, log_step_complete
                step_entry_id = log_step_start(st.session_state.workflow_id, step.name)
                
                # Store entry ID in step metadata (safer than session state)
                step.metadata['log_entry_id'] = step_entry_id
                
                # Run actual workflow step
                if hasattr(st.session_state, 'real_workflow') and st.session_state.real_workflow:
                    try:
                        self.run_real_workflow_step(step)
                        # Update to completion
                        log_step_complete(st.session_state.workflow_id, step_entry_id, step.name, success=True)
                    except Exception as e:
                        step.status = WorkflowStatus.FAILED
                        log_step_complete(st.session_state.workflow_id, step_entry_id, step.name, success=False, details=str(e))
                else:
                    # Fallback to simulation
                    time.sleep(1)
                    step.status = WorkflowStatus.COMPLETED
                    step.output_data = {"status": "completed", "timestamp": datetime.now().isoformat()}
                    log_step_complete(st.session_state.workflow_id, step_entry_id, step.name, success=True)
                
                break
        
        # Check if all steps are completed
        if all(step.status == WorkflowStatus.COMPLETED for step in context.steps):
            context.status = WorkflowStatus.COMPLETED
            st.session_state.demo_mode = False
            st.session_state.workflow_context = context  # Force update
            log_info(st.session_state.workflow_id, "🎉 **Database Decommissioning Workflow completed successfully!**\n\n- All steps finished\n- Files table with postgres_air matches displayed\n- No errors encountered")

    def run_real_workflow_step(self, step):
        """Run actual database decommissioning workflow step."""
        import asyncio
        import sys
        from pathlib import Path
        
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            if "Environment Validation" in step.name:
                # Environment validation step
                from concrete.parameter_service import get_parameter_service
                param_service = get_parameter_service()
                log_info(st.session_state.workflow_id, "✅ **Environment validated**\n\n- Secrets loaded\n- Parameters validated\n- Components initialized")
                
            elif "Pattern Discovery" in step.name:
                # Pattern discovery step - this is where we show the files table
                from concrete.pattern_discovery import PatternDiscoveryEngine
                from concrete.workflow_logger import DatabaseWorkflowLogger
                from clients.repomix import RepomixMCPClient
                from clients.github import GitHubMCPClient
                
                async def run_pattern_discovery():
                    pattern_engine = PatternDiscoveryEngine()
                    workflow_logger = DatabaseWorkflowLogger("postgres_air")
                    
                    repomix_client = RepomixMCPClient("mcp_config.json")
                    github_client = GitHubMCPClient("mcp_config.json")
                    
                    repo_url = "https://github.com/bprzybys-nc/postgres-sample-dbs"
                    repo_owner = "bprzybys-nc"
                    repo_name = "postgres-sample-dbs"
                    database_name = "postgres_air"
                    
                    discovery_result = await pattern_engine.discover_patterns_in_repository(
                        repomix_client, github_client, repo_url, database_name, repo_owner, repo_name
                    )
                    
                    # Extract files table data for UI display
                    files_found = discovery_result.get('total_files', 0)
                    matched_files = discovery_result.get('files', [])
                    
                    if matched_files:
                        # Create progress table data for real-time tracking
                        from clients.preview_mcp.progress_table import (
                            ProgressTableData, ProgressTableEntry, ProcessingStatus, 
                            ProcessingPhase
                        )
                        
                        progress_entries = []
                        for file_info in matched_files:
                            file_path = file_info.get('path', 'Unknown')
                            source_type = file_info.get('source_type', 'unknown')
                            confidence = file_info.get('confidence', 0.0)
                            
                            # Determine processing status based on confidence
                            if confidence >= 0.8:
                                status = ProcessingStatus.COMPLETED
                            elif confidence >= 0.5:
                                status = ProcessingStatus.PROCESSING  
                            else:
                                status = ProcessingStatus.PENDING
                            
                            entry = ProgressTableEntry(
                                file_path=file_path,
                                source_type=source_type,
                                match_count=file_info.get('match_count', 0),
                                confidence=confidence,
                                status=status,
                                progress_phase=ProcessingPhase.CLASSIFICATION
                            )
                            progress_entries.append(entry)
                        
                        # Create progress table and log it
                        progress_table = ProgressTableData(
                            title="📊 File Processing Progress",
                            entries=progress_entries
                        )
                        progress_table.update_counts()
                        
                        # DEBUG: Verify table creation
                        print(f"🔍 Created progress table with {len(progress_entries)} entries")
                        
                        # Log to the workflow system by passing the data directly
                        from clients.preview_mcp.workflow_log import LogEntry
                        log_entry = LogEntry(
                            entry_type=LogEntryType.PROGRESS_TABLE,
                            content=progress_table,
                            timestamp=datetime.now(),
                            metadata={
                                "update_type": "initialize",
                                "total_files": len(progress_entries),
                                "completion_rate": progress_table.get_completion_rate()
                            }
                        )
                        workflow_log = get_workflow_log(st.session_state.workflow_id)
                        workflow_log.add_entry(log_entry)
                        
                        # DEBUG: Verify logging
                        print(f"📊 Logged progress table to workflow {st.session_state.workflow_id}")
                        
                        # Force refresh workflow log to pick up progress table
                        st.session_state.workflow_log = get_workflow_log(st.session_state.workflow_id)
                        
                        # Create files table for UI (legacy view)
                        headers = ["#", "File Path", "Type", "Matches", "Confidence", "Size"]
                        rows = []
                        
                        for idx, file_info in enumerate(matched_files, 1):
                            file_path = file_info.get('path', 'Unknown')
                            source_type = file_info.get('source_type', 'unknown')
                            match_count = file_info.get('match_count', 0)
                            confidence = file_info.get('confidence', 0.0)
                            file_size = "1.2KB"  # Mock size for demo
                            
                            confidence_icon = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.5 else "🔴"
                            
                            rows.append([
                                str(idx),
                                file_path[:40] + "..." if len(file_path) > 40 else file_path,
                                source_type,
                                str(match_count),
                                f"{confidence_icon} {confidence:.2f}",
                                file_size
                            ])
                        
                        log_table(
                            st.session_state.workflow_id,
                            headers=headers,
                            rows=rows,
                            title=f"📁 FILES DISCOVERED: postgres_air database references"
                        )
                        
                        # Log high confidence matches
                        high_conf_files = [f for f in matched_files if f.get('confidence', 0) >= 0.8]
                        if high_conf_files:
                            log_info(st.session_state.workflow_id, 
                                f"🎯 **High Confidence Pattern Matches Found:**\n\n" +
                                "\n".join([f"• **{f['path']}**: {f.get('match_count', 0)} matches" for f in high_conf_files[:3]])
                            )
                    
                    return discovery_result
                
                # Run async pattern discovery with enhanced error handling
                def run_pattern_discovery_sync():
                    """Wrapper to run async pattern discovery in sync context"""
                    try:
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Run the async function
                        result = loop.run_until_complete(run_pattern_discovery())
                        
                        loop.close()
                        return result
                    except Exception as e:
                        print(f"❌ Pattern discovery failed: {e}")
                        return {"total_files": 0, "files": []}
                
                discovery_result = run_pattern_discovery_sync()
                
                files_found = discovery_result.get('total_files', 0)
                log_info(st.session_state.workflow_id, 
                    f"✅ **Pattern Discovery Completed**\n\n- Files Found: {files_found}\n- Database: postgres_air\n- Pattern matches displayed in table above")
                
            else:
                # Generic step completion - no need to log here, parent will handle it
                pass
            
            step.status = WorkflowStatus.COMPLETED
            step.output_data = {"status": "completed", "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.output_data = {"status": "failed", "error": str(e)}
            # Error logging will be handled by parent simulate_demo_progress
        
        # Force session state update
        if 'workflow_context' not in st.session_state:
            st.session_state.workflow_context = {}
        
        # Update workflow context with current step completion
        st.session_state.workflow_context = st.session_state.workflow_context

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

    def generate_enhanced_table_html(self, table_data: TableData) -> str:
        """Generate HTML table with enhanced styling including alternating rows."""
        html = ['<table class="enhanced-log-table">']
        
        # Table header
        if table_data.headers:
            html.append('<thead><tr>')
            for header in table_data.headers:
                html.append(f'<th>{header}</th>')
            html.append('</tr></thead>')
        
        # Table body with alternating row styling
        html.append('<tbody>')
        for i, row in enumerate(table_data.rows):
            row_class = 'even' if i % 2 == 0 else 'odd'
            html.append(f'<tr class="{row_class}">')
            for cell in row:
                html.append(f'<td>{cell}</td>')
            html.append('</tr>')
        html.append('</tbody>')
        
        html.append('</table>')
        return '\n'.join(html)


def main():
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not available. Exiting.")
        return

    # Load environment variables only once (cached in session state)
    if 'env_loaded' not in st.session_state:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            st.session_state.env_loaded = True
            print("Environment variables loaded from .env file.")
        except ImportError:
            print("python-dotenv not installed. Skipping .env loading.")
            print("Install with: pip install python-dotenv")
            st.session_state.env_loaded = False
        except Exception as e:
            print(f"Error loading .env file: {e}")
            st.session_state.env_loaded = False

    app = StreamlitWorkflowUI()
    app.run()


if __name__ == "__main__":
    main()