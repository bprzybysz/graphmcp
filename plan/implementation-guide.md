# GraphMCP Implementation Guide

## Reusable Code Snippets

### 1. State Management Pattern
```python
# From legacy: concrete/preview_ui/streamlit_app.py
# Session state initialization pattern
def initialize_session_state():
    """Initialize session state with defaults"""
    defaults = {
        'workflow_id': None,
        'workflow_running': False,
        'auto_refresh': True,
        'refresh_interval': 0.5,
        'last_refresh': datetime.now(),
        'log_entries': [],
        'error_count': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
```

### 2. Live-Updatable Log Entry Pattern
```python
# From memory ID: 2966612
# Pattern for live-updating log entries
def log_step_start(step_name: str) -> str:
    """Log step start with updatable entry"""
    entry_id = str(uuid.uuid4())
    log_entry = {
        'id': entry_id,
        'timestamp': datetime.now(),
        'message': f"🔄 Starting step: {step_name}",
        'type': 'info',
        'updatable': True
    }
    st.session_state.log_entries.append(log_entry)
    return entry_id

def log_step_complete(entry_id: str, step_name: str, success: bool = True):
    """Update existing log entry to show completion"""
    for entry in st.session_state.log_entries:
        if entry['id'] == entry_id:
            entry['message'] = f"{'✅' if success else '❌'} Completed: {step_name}"
            entry['updatable'] = False
            break
```

### 3. Three-Pane Layout Pattern
```python
# From memory ID: 2964650
# Three-pane layout with proportional columns
def render_three_pane_layout():
    """Render the three-pane UI layout"""
    # Create columns with 25%, 37.5%, 37.5% distribution
    left_pane, main_pane, right_pane = st.columns([2, 3, 3])
    
    with left_pane:
        st.markdown("### Workflow Control")
        render_workflow_controls()
    
    with main_pane:
        st.markdown("### Workflow Logs")
        render_log_stream()
    
    with right_pane:
        st.markdown("### Progress & Analytics")
        render_progress_tables()
```

### 4. Mock Data Loading Pattern
```python
# From memory ID: 2973108
# Mock data loading with flags
USE_MOCK_PACK = True  # HACK/TODO: User must approve restoration
USE_MOCK_DISCOVERY = True  # HACK/TODO: User must approve restoration

def load_mock_repo_data():
    """Load mock repository data from local file"""
    if USE_MOCK_PACK:
        with open("tests/data/postgres_sample_dbs_packed.xml", "r") as f:
            return f.read()
    else:
        # Real implementation
        return pack_remote_repository(...)

def load_mock_discovery_data():
    """Load mock discovery data from local file"""
    if USE_MOCK_DISCOVERY:
        with open("tests/data/discovery_outcome_context.json", "r") as f:
            return json.load(f)
    else:
        # Real implementation
        return discover_patterns(...)
```

### 5. Workflow Step Pattern
```python
# Base workflow step pattern
class BaseWorkflowStep:
    """Base class for workflow steps"""
    
    def __init__(self, name: str, mock_enabled: bool = True):
        self.name = name
        self.mock_enabled = mock_enabled
        self.status = "pending"
        self.progress = 0.0
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow step"""
        if self.mock_enabled:
            return await self._execute_mock(context)
        return await self._execute_real(context)
    
    async def _execute_mock(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation"""
        raise NotImplementedError
    
    async def _execute_real(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Real implementation"""
        raise NotImplementedError
```

### 6. Progress Tracking Pattern
```python
# From agentic workflow integration
def track_batch_progress(batch_id: str, total_files: int):
    """Track progress for a batch of files"""
    batch_context = {
        'batch_id': batch_id,
        'total_files': total_files,
        'processed_files': 0,
        'start_time': datetime.now(),
        'status': 'running'
    }
    st.session_state[f'batch_{batch_id}'] = batch_context
    return batch_context

def update_batch_progress(batch_id: str, processed: int, status: str = 'running'):
    """Update batch processing progress"""
    key = f'batch_{batch_id}'
    if key in st.session_state:
        st.session_state[key]['processed_files'] = processed
        st.session_state[key]['status'] = status
        progress = processed / st.session_state[key]['total_files']
        st.session_state[key]['progress'] = progress
```

### 7. Error Handling Pattern
```python
# Graceful error handling with UI feedback
def handle_workflow_error(error: Exception, context: str):
    """Handle workflow errors gracefully"""
    error_entry = {
        'timestamp': datetime.now(),
        'context': context,
        'error': str(error),
        'type': 'error',
        'traceback': traceback.format_exc()
    }
    
    # Add to session state
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    st.session_state.errors.append(error_entry)
    st.session_state.error_count += 1
    
    # Log for debugging
    logger.error(f"Workflow error in {context}: {error}", exc_info=True)
    
    # Display in UI
    st.error(f"Error in {context}: {error}")
```

### 8. File Processing Table Pattern
```python
# From memory ID: 2963072
# Table display for file processing
def render_file_processing_table(files: List[Dict]):
    """Render a table of files being processed"""
    df = pd.DataFrame(files)
    
    # Style the dataframe
    styled_df = df.style.apply(
        lambda x: ['background-color: #28a745' if v == 'success' 
                  else 'background-color: #dc3545' if v == 'error'
                  else '' for v in x],
        subset=['status']
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "file_path": st.column_config.TextColumn("File Path", width="medium"),
            "size": st.column_config.NumberColumn("Size", format="%d KB"),
            "status": st.column_config.TextColumn("Status", width="small")
        }
    )
```

### 9. Auto-refresh Pattern
```python
# Auto-refresh implementation
def setup_auto_refresh():
    """Setup auto-refresh functionality"""
    if st.session_state.auto_refresh and st.session_state.workflow_running:
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
        
        if time_since_refresh >= st.session_state.refresh_interval:
            st.session_state.last_refresh = datetime.now()
            st.rerun()
```

### 10. Test Fixtures Pattern
```python
# Test fixture patterns from existing tests
@pytest.fixture
def mock_workflow_state():
    """Create a mock workflow state for testing"""
    return WorkflowState(
        workflow_id="test-workflow-123",
        workflow_running=True,
        current_step="pattern_discovery",
        progress_percentage=45.0,
        mock_mode=True
    )

@pytest.fixture
def mock_discovery_context():
    """Load mock discovery context for testing"""
    with open("tests/data/discovery_outcome_context.json", "r") as f:
        return json.load(f)
```

## Key Implementation Notes

1. **Always use session state** for UI state management
2. **Implement mock mode first**, then add real implementations
3. **Use async/await** for workflow operations
4. **Log everything** - both to UI and files
5. **Handle errors gracefully** - never crash the UI
6. **Test with real data sizes** - 20MB XML files, etc.
7. **Optimize for performance** - cache expensive operations
8. **Keep UI responsive** - use progress indicators
9. **Document mock switches** - clear HACK/TODO comments
10. **Preserve working patterns** - reuse proven code

## Migration Checklist
- [ ] Copy working patterns from legacy code
- [ ] Update imports to new structure
- [ ] Test each component in isolation
- [ ] Test integration between components
- [ ] Verify mock/real mode switching
- [ ] Check performance with real data
- [ ] Update documentation 