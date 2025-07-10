"""
Enhanced Streamlit UI for Database Decommissioning Workflow

Displays real-time logs from the workflow_logger system.
"""

import streamlit as st
import time
import json
import os
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Database Decommissioning Monitor",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ Enhanced Database Decommissioning Monitor")

# Auto-refresh every 2 seconds
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

# Create columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Workflow Progress")
    
    # Look for log files in logs directory and current directory
    log_files = []
    
    # Check logs directory
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files.extend(list(logs_dir.glob("*.log")))
    
    # Check current directory for enhanced_db_demo.log
    current_log = Path("enhanced_db_demo.log")
    if current_log.exists():
        log_files.append(current_log)
    
    if log_files:
        # Show latest log file
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        
        st.subheader(f"📋 Latest Log: {latest_log.name}")
        
        try:
            with open(latest_log, 'r') as f:
                log_content = f.read()
            
            # Show only recent lines (last 100 lines)
            lines = log_content.split('\n')
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            recent_content = '\n'.join(recent_lines)
            
            # Display in a scrollable text area
            st.text_area(
                "Recent Log Output (Last 100 lines)",
                value=recent_content,
                height=400,
                key=f"log_display_{st.session_state.refresh_count}"
            )
            
            # Count log levels in recent content
            info_count = len([l for l in recent_lines if ' - INFO - ' in l])
            warning_count = len([l for l in recent_lines if ' - WARNING - ' in l])
            error_count = len([l for l in recent_lines if ' - ERROR - ' in l])
            
            # Show metrics
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Info Messages", info_count)
            with metric_col2:
                st.metric("Warnings", warning_count)
            with metric_col3:
                st.metric("Errors", error_count)
            
            # Show workflow status
            if "Demo running" in recent_content:
                st.success("🔄 Workflow is running")
            elif "completed successfully" in recent_content:
                st.success("✅ Workflow completed successfully")
            elif "failed" in recent_content or error_count > 0:
                st.error("❌ Workflow has errors")
            else:
                st.info("⏳ Workflow status unknown")
                
        except Exception as e:
            st.error(f"Error reading log file: {e}")
    else:
        st.info("No log files found. Make sure the enhanced workflow is running.")

with col2:
    st.header("⚙️ Controls")
    
    # Refresh button
    if st.button("🔄 Refresh Now"):
        st.session_state.refresh_count += 1
        st.rerun()
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh (2s)", value=True)
    
    # Status indicators
    st.subheader("📡 Status")
    st.success("✅ Workflow Logger Active")
    st.info(f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    if st.button("📊 Show Parameter Service Status"):
        try:
            from concrete.parameter_service import get_parameter_service
            param_service = get_parameter_service()
            st.json({
                "total_parameters": len(param_service.parameters),
                "validation_issues": len(param_service.validation_issues),
                "has_github_token": bool(param_service.get_parameter("GITHUB_PERSONAL_ACCESS_TOKEN")),
                "has_slack_token": bool(param_service.get_parameter("SLACK_BOT_TOKEN"))
            })
        except Exception as e:
            st.error(f"Failed to load parameter service: {e}")
    
    if st.button("🗂️ Show Available Log Files"):
        try:
            all_logs = []
            
            # Logs directory
            logs_dir = Path("logs")
            if logs_dir.exists():
                all_logs.extend([f"logs/{f.name}" for f in logs_dir.glob("*")])
            
            # Current directory
            for pattern in ["*.log", "enhanced_db_*.log"]:
                all_logs.extend([f.name for f in Path(".").glob(pattern)])
            
            if all_logs:
                st.write("Available log files:")
                for log_file in sorted(set(all_logs)):
                    st.text(f"• {log_file}")
            else:
                st.write("No log files found")
        except Exception as e:
            st.error(f"Error listing files: {e}")

# Auto-refresh logic
if auto_refresh:
    time.sleep(2)
    st.session_state.refresh_count += 1
    st.rerun() 