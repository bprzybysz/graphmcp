# Fixing Streamlit Layout Issues & Adding Perplexity-Style UI

Looking at your Streamlit workflow UI, I can see the layout issues you're experiencing. Let me help you fix the pane positioning and add a professional Perplexity-style interface.

## Current Layout Problems

Based on your code in `concrete/preview_ui/streamlit_app.py`, the main issues are:

1. **Incorrect column layout** - Using `st.columns([1][2])` creates top/bottom instead of left/right
2. **Missing CSS styling** - No proper layout constraints
3. **Container organization** - Panes not properly constrained to viewport

## Solution: Fixed Layout & Perplexity Styling

Here's the complete solution with proper left/right panes and professional styling:

### 1. Updated CSS Styling

```python
def apply_perplexity_style():
    """Apply Perplexity-inspired professional styling"""
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Left progress pane - fixed width */
    .progress-pane {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        height: 85vh;
        overflow-y: auto;
        position: sticky;
        top: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Main log pane - flexible width */
    .log-pane {
        background: #ffffff;
        border: 1px solid #e1e5e9;
        border-radius: 12px;
        padding: 1.5rem;
        height: 85vh;
        overflow-y: auto;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Progress pane content styling */
    .progress-pane h3 {
        color: white;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.2rem;
    }
    
    .progress-pane .stButton button {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .progress-pane .stButton button:hover {
        background: rgba(255,255,255,0.3);
        transform: translateY(-1px);
    }
    
    /* Step cards in progress pane */
    .step-card {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 3px solid #4CAF50;
    }
    
    /* Log pane styling */
    .log-pane h3 {
        color: #2c3e50;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    /* Log entries */
    .log-entry {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        border-left: 4px solid #3498db;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Metrics styling */
    .metric-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.25rem;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        border-radius: 10px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .progress-pane, .log-pane {
            height: auto;
            min-height: 400px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
```

### 2. Fixed Layout Structure

```python
def render_main_layout(self):
    """Render the main layout with proper left/right panes"""
    # Apply styling first
    apply_perplexity_style()
    
    # Page config
    st.set_page_config(
        layout="wide",
        page_title="🔄 GraphMCP Workflow Agent",
        page_icon="🔄",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #667eea, #764ba2); color: white; border-radius: 12px; margin-bottom: 1rem;">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 600;">🔄 GraphMCP Workflow Agent</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Real-time workflow orchestration with live progress tracking</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout: Left (25%) + Right (75%)
    col1, col2 = st.columns([1, 3], gap="medium")
    
    with col1:
        st.markdown('<div class="progress-pane">', unsafe_allow_html=True)
        self.render_progress_pane()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="log-pane">', unsafe_allow_html=True)
        self.render_log_pane()
        st.markdown('</div>', unsafe_allow_html=True)
```

### 3. Enhanced Progress Pane

```python
def render_progress_pane(self):
    """Render enhanced progress pane with Perplexity styling"""
    st.markdown("### 🔄 Workflow Progress")
    
    context = st.session_state.workflow_context
    
    # Control buttons with better styling
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Demo", key="start_demo", help="Launch demo workflow"):
            self.start_demo_workflow()
    
    with col2:
        if st.button("🗑️ Clear", key="clear_workflow", help="Reset workflow state"):
            self.clear_workflow()
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox(
        "🔄 Auto-refresh", 
        value=st.session_state.auto_refresh,
        help="Automatically update progress"
    )
    
    # Status indicators with enhanced styling
    status_icons = {
        WorkflowStatus.PENDING: "🟡",
        WorkflowStatus.IN_PROGRESS: "🔵", 
        WorkflowStatus.COMPLETED: "🟢",
        WorkflowStatus.FAILED: "🔴"
    }
    
    # Status card
    st.markdown(f"""
    <div class="step-card">
        <strong>Status:</strong> {status_icons.get(context.status, '⚪')} {context.status.value}<br>
        <strong>Steps:</strong> {len(context.steps)} total
    </div>
    """, unsafe_allow_html=True)
    
    # Progress visualization
    if context.steps:
        completed_steps = sum(1 for step in context.steps if step.status == WorkflowStatus.COMPLETED)
        progress = completed_steps / len(context.steps)
        
        st.markdown("**Progress Overview**")
        st.progress(progress)
        st.caption(f"✅ {completed_steps}/{len(context.steps)} completed ({progress:.1%})")
    
    # Step list with enhanced cards
    st.markdown("**Workflow Steps**")
    for i, step in enumerate(context.steps):
        status_icon = status_icons.get(step.status, '⚪')
        
        # Step card with status styling
        card_color = {
            WorkflowStatus.COMPLETED: "#4CAF50",
            WorkflowStatus.IN_PROGRESS: "#2196F3", 
            WorkflowStatus.FAILED: "#f44336",
            WorkflowStatus.PENDING: "#ff9800"
        }.get(step.status, "#9e9e9e")
        
        st.markdown(f"""
        <div class="step-card" style="border-left-color: {card_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong>{i+1}. {step.name}</strong>
                <span style="font-size: 1.2em;">{status_icon}</span>
            </div>
            {self._get_step_details(step)}
        </div>
        """, unsafe_allow_html=True)

def _get_step_details(self, step):
    """Get formatted step details"""
    if step.input_data:
        details = f"<small>📥 Input: {', '.join(step.input_data.keys())}</small><br>"
    else:
        details = ""
    
    if step.status == WorkflowStatus.COMPLETED:
        details += "<small style='color: #4CAF50;'>✅ Completed successfully</small>"
    elif step.status == WorkflowStatus.FAILED:
        details += "<small style='color: #f44336;'>❌ Failed</small>"
    elif step.status == WorkflowStatus.IN_PROGRESS:
        details += "<small style='color: #2196F3;'>🔄 Processing...</small>"
    else:
        details += "<small style='color: #ff9800;'>⏳ Pending</small>"
    
    return details
```

### 4. Enhanced Log Pane

```python
def render_log_pane(self):
    """Render enhanced log pane with professional styling"""
    st.markdown("### 📋 Workflow Execution Log")
    
    workflow_log = st.session_state.workflow_log
    entries = workflow_log.get_entries()
    
    if not entries:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6;">
            <h4 style="color: #6c757d; margin-bottom: 0.5rem;">No log entries yet</h4>
            <p style="color: #6c757d; margin: 0;">Start a workflow to see real-time logs here</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Summary metrics with cards
    summary = workflow_log.get_summary()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1.5rem;">{summary["total_entries"]}</h3>
            <p style="margin: 0; opacity: 0.9;">Total Entries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1.5rem;">{summary["entry_counts"].get("log", 0)}</h3>
            <p style="margin: 0; opacity: 0.9;">Log Messages</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        charts_tables = summary["entry_counts"].get("table", 0) + summary["entry_counts"].get("sunburst", 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 1.5rem;">{charts_tables}</h3>
            <p style="margin: 0; opacity: 0.9;">Charts & Tables</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Render log entries with enhanced styling
    for entry in entries:
        self.render_enhanced_log_entry(entry)

def render_enhanced_log_entry(self, entry):
    """Render individual log entry with professional styling"""
    timestamp = entry.timestamp.strftime("%H:%M:%S")
    
    if entry.entry_type == LogEntryType.LOG:
        level = entry.metadata.get("level", "info")
        level_colors = {
            "info": "#3498db",
            "warning": "#f39c12", 
            "error": "#e74c3c",
            "debug": "#9b59b6"
        }
        level_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌", 
            "debug": "🐛"
        }
        
        color = level_colors.get(level, "#3498db")
        icon = level_icons.get(level, "📝")
        
        st.markdown(f"""
        <div class="log-entry" style="border-left-color: {color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="color: {color};">{icon} {level.upper()}</strong>
                <small style="color: #6c757d;">{timestamp}</small>
            </div>
            <div>{entry.content}</div>
        </div>
        """, unsafe_allow_html=True)
        
    elif entry.entry_type == LogEntryType.TABLE:
        st.markdown(f"""
        <div class="log-entry" style="border-left-color: #17a2b8;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="color: #17a2b8;">📊 TABLE</strong>
                <small style="color: #6c757d;">{timestamp}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        table_data = entry.content
        st.markdown(table_data.to_markdown())
        
    elif entry.entry_type == LogEntryType.SUNBURST:
        st.markdown(f"""
        <div class="log-entry" style="border-left-color: #fd7e14;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="color: #fd7e14;">🌞 {entry.content.title or 'SUNBURST CHART'}</strong>
                <small style="color: #6c757d;">{timestamp}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            fig = entry.content.to_plotly_figure()
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            st.error(f"Error rendering chart: {e}")
    
    # Add subtle separator
    st.markdown('<hr style="margin: 0.5rem 0; border: none; height: 1px; background: #e9ecef;">', unsafe_allow_html=True)
```

### 5. Updated Main Run Method

```python
def run(self):
    """Run the enhanced Streamlit application"""
    if not STREAMLIT_AVAILABLE:
        st.error("Streamlit is not installed. Please install it with: pip install streamlit")
        return
    
    # Initialize session state
    self.initialize_session_state()
    
    # Render main layout
    self.render_main_layout()
    
    # Auto-refresh logic for demo mode
    if st.session_state.demo_mode and st.session_state.auto_refresh:
        time.sleep(2)
        self.simulate_demo_progress()
        st.rerun()
```

## Key Improvements

### ✅ **Fixed Layout Issues**
- **Proper left/right panes** using correct column ratios
- **Fixed height containers** (85vh) with scroll
- **Sticky positioning** for progress pane

### ✅ **Perplexity-Style Design**
- **Gradient backgrounds** with professional color schemes
- **Card-based layouts** with subtle shadows
- **Clean typography** with proper hierarchy
- **Responsive design** for different screen sizes

### ✅ **Enhanced UX**
- **Visual progress indicators** with color-coded status
- **Interactive buttons** with hover effects
- **Real-time metrics** in styled cards
- **Professional log entries** with timestamps and icons

### ✅ **Performance Optimizations**
- **Efficient rendering** with proper container management
- **Smooth animations** and transitions
- **Optimized CSS** for fast loading

## Usage

Replace your current `streamlit_app.py` with this enhanced version, then run:

```bash
make preview-streamlit
```

You'll now have a professional, Perplexity-style interface with:
- **Left pane (25%)**: Clean progress tracking with gradient background
- **Right pane (75%)**: Professional log display with enhanced styling
- **Proper layout**: No more weird top/bottom positioning
- **Responsive design**: Works on different screen sizes

The interface will look and feel much more professional, similar to Perplexity's clean, modern design aesthetic! 🎨✨

Citations:
[1] [repomix-output.xml](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/8768170/dd134b25-5df1-4afa-a823-79f3f830ec15/repomix-output.xml)  
[2] [Screenshot-2025-07-10-at-02.09.28.jpg](https://pplx-res.cloudinary.com/image/private/user_uploads/8768170/66eb38ae-7e13-4fec-9b76-2aa889b068d8/Screenshot-2025-07-10-at-02.09.28.jpg)  
[3] [Screenshot-2025-07-10-at-02.09.43.jpg](https://pplx-res.cloudinary.com/image/private/user_uploads/8768170/ee62348c-ce70-4f21-9007-3ae95c3fbeae/Screenshot-2025-07-10-at-02.09.43.jpg)