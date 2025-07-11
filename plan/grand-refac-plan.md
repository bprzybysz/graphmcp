# Grand Refactoring Plan: GraphMCP UI & Workflow

## Executive Summary

This plan outlines a comprehensive refactoring of the GraphMCP application, focusing on:
1. **UI Refactoring**: Complete rebuild of Streamlit UI following clean architecture principles
2. **Workflow Refactoring**: Modular workflow implementation with enhanced features
3. **Testing Strategy**: Comprehensive test coverage with mock/real mode support
4. **Migration Strategy**: Painless transition preserving existing functionality

## Phase 0: Pre-Refactoring Cleanup & Analysis

### 0.1 Garbage File Removal
**Files to Remove:**
- `=1.5.0`, `=3.4.0`, `=5.9.0`, `=6.82.0`, `=0.1.0`, `=0.21.0`, `=23.0.0`, `=3.11.0`, `=3.3.0`, `=4.1.0`, `=7.4.0` (empty dependency files)
- `test-output.txt` (19MB test output - too large)
- `.DS_Store` in tests directory

### 0.2 Legacy Code Migration
**Create Legacy Structure:**
```
legacy/
├── concrete/
│   ├── preview_ui/
│   │   └── streamlit_app.py
│   ├── db_decommission.py
│   ├── pattern_discovery.py
│   ├── contextual_rules_engine.py
│   └── ... (other existing files)
└── tests/
    └── ... (existing test files to reference)
```

### 0.3 Mock Data Validation
- **Repo Pack Mock**: Use `tests/data/postgres_sample_dbs_packed.xml` (20MB)
- **Pattern Discovery Mock**: Use `tests/data/discovery_outcome_context.json` (postgres_air data confirmed)

## Phase 1: UI Architecture Implementation

### 1.1 Directory Structure
```
concrete/ui/
├── __init__.py
├── app.py                    # Main Streamlit entry point
├── components/
│   ├── __init__.py
│   ├── workflow_controls.py  # Left pane controls
│   ├── log_stream.py        # Main pane log display
│   ├── progress_tables.py   # Right pane analytics
│   └── common/
│       ├── __init__.py
│       ├── status_indicators.py
│       └── styled_tables.py
├── state/
│   ├── __init__.py
│   ├── session_manager.py   # Session state management
│   └── workflow_state.py    # Workflow state interface
├── layouts/
│   ├── __init__.py
│   ├── three_pane_layout.py # Main layout orchestration
│   └── responsive_utils.py
└── config/
    ├── __init__.py
    ├── ui_config.py         # UI configuration
    └── theme.py             # Visual theme settings
```

### 1.2 Implementation Steps

#### Step 1.2.1: Core State Management
```python
# concrete/ui/state/workflow_state.py
@dataclass
class WorkflowState:
    workflow_id: Optional[str] = None
    workflow_running: bool = False
    auto_refresh: bool = True
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    log_entries: List[LogEntry] = field(default_factory=list)
    error_count: int = 0
    last_refresh: datetime = field(default_factory=datetime.now)
    expanded_sections: Set[str] = field(default_factory=set)
    mock_mode: bool = True  # For testing
```

#### Step 1.2.2: Component Implementation Priority
1. **Session Manager** (state/session_manager.py)
2. **Three Pane Layout** (layouts/three_pane_layout.py)
3. **Workflow Controls** (components/workflow_controls.py)
4. **Log Stream** (components/log_stream.py)
5. **Progress Tables** (components/progress_tables.py)

### 1.3 Key Features to Preserve
- Live-updatable log entries (spinner → completion)
- Real-time progress tracking
- Batch processing visualization
- Error handling with graceful UI feedback
- Auto-refresh with throttling (500ms)

## Phase 2: Workflow Architecture Implementation

### 2.1 Directory Structure
```
concrete/workflow/
├── __init__.py
├── manager.py               # Enhanced workflow manager
├── progress.py             # Progress tracking system
├── events.py               # Event bus implementation
├── batch.py                # Batch processing logic
├── compat.py               # Backward compatibility
├── steps/
│   ├── __init__.py
│   ├── base_step.py        # Base workflow step class
│   ├── repository_processing.py
│   ├── pattern_discovery.py
│   ├── file_processing.py
│   ├── rule_application.py
│   └── quality_assurance.py
└── mock/
    ├── __init__.py
    ├── mock_manager.py      # Mock workflow manager
    └── mock_data.py         # Mock data providers
```

### 2.2 Implementation Steps

#### Step 2.2.1: Enhanced Workflow Manager
```python
# concrete/workflow/manager.py
class WorkflowManager:
    async def start_workflow(self, config: Optional[Dict] = None) -> str
    async def pause_workflow(self, workflow_id: str) -> bool
    async def resume_workflow(self, workflow_id: str) -> bool
    async def stop_workflow(self, workflow_id: str, force: bool = False) -> bool
    async def get_status(self, workflow_id: str) -> WorkflowStatus
    async def get_step_details(self, workflow_id: str, step_id: str) -> StepDetails
```

#### Step 2.2.2: Progress Tracking System
```python
# concrete/workflow/progress.py
class ProgressTracker:
    def track_batch(self, batch_id: str, total_files: int) -> BatchContext
    def update_progress(self, batch_id: str, processed: int, status: str)
    def get_statistics(self, workflow_id: str) -> Dict[str, Any]
```

### 2.3 Mock Implementation Strategy
- **USE_MOCK_PACK**: Control repo packing mock
- **USE_MOCK_DISCOVERY**: Control pattern discovery mock
- **USE_MOCK_PROCESSING**: Control file processing mock
- Each step has mock/real implementation with clear HACK/TODO markers

## Phase 3: Testing Strategy

### 3.1 Test Structure
```
tests/
├── unit/
│   ├── ui/
│   │   ├── test_components.py
│   │   ├── test_state_management.py
│   │   └── test_layouts.py
│   └── workflow/
│       ├── test_manager.py
│       ├── test_progress.py
│       └── test_steps.py
├── integration/
│   ├── test_ui_workflow_integration.py
│   └── test_mock_workflow_e2e.py
└── fixtures/
    ├── mock_data.py
    └── test_helpers.py
```

### 3.2 Test Implementation Priority
1. **State Management Tests** (critical for UI)
2. **Workflow Manager Tests** (core functionality)
3. **Component Tests** (UI elements)
4. **Integration Tests** (UI + Workflow)
5. **Mock Workflow E2E** (full flow validation)

## Phase 4: Migration & Deployment

### 4.1 Migration Steps
1. **Move existing code to legacy/**
2. **Implement new UI structure**
3. **Implement new workflow structure**
4. **Update imports in main entry points**
5. **Run compatibility tests**
6. **Update documentation**

### 4.2 Compatibility Layer
```python
# concrete/workflow/compat.py
class WorkflowManagerCompat:
    """Maintains backward compatibility with existing code"""
    def __init__(self, new_manager: WorkflowManager):
        self._manager = new_manager
    
    async def start_workflow(self) -> str:
        return await self._manager.start_workflow()
```

## Phase 5: Memory & Rules Update

### 5.1 Memory Updates Required
1. Update UI implementation memory to point to new structure
2. Update workflow implementation patterns
3. Update mock configuration locations
4. Update test execution patterns

### 5.2 Rules to Update
1. Python execution rules (maintain .venv usage)
2. UI best practices (new component structure)
3. Workflow patterns (new async patterns)
4. Testing guidelines (new test structure)

## Implementation Timeline

### Week 1: Foundation
- **Day 1-2**: Cleanup & Legacy Migration
- **Day 3-4**: Core State Management & UI Structure
- **Day 5**: Basic Component Implementation

### Week 2: Core Features
- **Day 6-7**: Workflow Manager & Progress Tracking
- **Day 8-9**: UI Components (Controls, Log Stream)
- **Day 10**: Integration & Testing

### Week 3: Advanced Features & Polish
- **Day 11-12**: Mock Implementation & Testing
- **Day 13**: Migration & Compatibility
- **Day 14**: Documentation & Memory Updates
- **Day 15**: Final Testing & Deployment

## Risk Mitigation

### Technical Risks
1. **State Synchronization**: Mitigated by centralized state management
2. **Import Cycles**: Mitigated by clear dependency direction
3. **Performance**: Mitigated by caching and efficient updates
4. **Compatibility**: Mitigated by compatibility layer

### Process Risks
1. **Scope Creep**: Strict adherence to plan phases
2. **Testing Gaps**: Comprehensive test coverage from start
3. **Migration Issues**: Legacy code preserved for reference

## Success Criteria

### Functional
- ✅ All existing features preserved
- ✅ Mock/Real mode switching works
- ✅ UI responsive and performant
- ✅ Workflow steps execute correctly

### Non-Functional
- ✅ Clean, modular architecture
- ✅ Comprehensive test coverage
- ✅ Clear documentation
- ✅ Maintainable codebase

## Economic Considerations

### Token Optimization
1. **Reuse Proven Code**: Copy working snippets from legacy
2. **Incremental Changes**: Use search_replace for small edits
3. **Batch Operations**: Group similar changes
4. **Focused Testing**: Test critical paths first

### Time Optimization
1. **Parallel Development**: UI and Workflow can progress independently
2. **Mock-First**: Develop with mocks, integrate real later
3. **Automated Testing**: Reduce manual verification time

## Conclusion

This plan provides a structured approach to refactoring the GraphMCP application while:
- Maintaining all existing functionality
- Improving code organization and maintainability
- Adding new features (pause/resume, better progress tracking)
- Ensuring smooth migration with minimal disruption

The phased approach allows for incremental progress with clear milestones and success criteria at each stage.

## Detailed Implementation Checklist

### Phase 0: Pre-Refactoring (Day 1-2)
- [x] Remove garbage files (=1.5.0, etc.)
- [x] Remove test-output.txt (19MB)
- [x] Remove .DS_Store files
- [x] Create legacy/ directory structure
- [x] Move concrete/ to legacy/concrete/
- [x] Move relevant test files to legacy/tests/
- [x] Validate mock data files exist and are correct

### Phase 1: UI Implementation (Day 3-5)
- [x] Create concrete/ui/ directory structure
- [x] Implement WorkflowState dataclass
- [x] Implement SessionManager with state initialization
- [x] Create ThreePaneLayout with responsive columns
- [x] Implement WorkflowControls component
  - [x] Start/Stop buttons
  - [x] Auto-refresh toggle
  - [x] Progress bar
- [x] Implement LogStream component
  - [x] Live-updatable entries
  - [x] Status indicators
  - [x] Timestamp display
- [x] Implement ProgressTables component
  - [x] File processing status
  - [x] Source type grouping
  - [x] Metrics display
- [x] Create main app.py entry point
- [x] Add UI configuration and theme

### Phase 2: Workflow Implementation (Day 6-10)
- [x] Create concrete/workflow/ directory structure
- [x] Implement WorkflowManager with async methods
- [x] Implement ProgressTracker for batch processing
- [x] Create EventBus for workflow events
- [x] Implement base WorkflowStep class
- [x] Create workflow steps:
  - [x] RepositoryProcessingStep (with mock)
  - [x] PatternDiscoveryStep (with mock)
  - [x] FileProcessingStep (with mock)
  - [x] RuleApplicationStep
  - [x] QualityAssuranceStep
- [x] Implement BatchContext for file processing
- [x] Create compatibility layer
- [x] Add mock data providers

### Phase 3: Testing (Day 11-12)
- [x] Create test directory structure
- [x] Write state management tests
- [x] Write workflow manager tests
- [x] Write UI component tests
- [x] Write integration tests
- [x] Write mock workflow E2E tests
- [x] Create test fixtures and helpers
- [x] Run all tests and fix issues
- [ ] Test backward compatibility
- [ ] Update configuration files
- [ ] Verify mock mode switching
- [ ] Document breaking changes

### Phase 4: Migration & Deployment
- [x] Update main entry points (demo.py, ui_demo.py)
- [x] Update imports throughout codebase
- [ ] Test backward compatibility
- [ ] Update configuration files
- [ ] Verify mock mode switching
- [ ] Document breaking changes

### Phase 5: Documentation & Cleanup (Day 14-15)
- [ ] Update README.md
- [ ] Create migration guide
- [ ] Update memory entries
- [ ] Update rule entries
- [ ] Remove old implementation references
- [ ] Final testing and validation
- [ ] Create release notes

### Quality Gates
Each phase must pass these criteria before proceeding:
- [ ] All tests pass
- [ ] No import errors
- [ ] UI renders correctly
- [ ] Workflow executes end-to-end
- [ ] Mock mode works correctly
- [ ] Performance metrics met (<2s load, <100ms response) 