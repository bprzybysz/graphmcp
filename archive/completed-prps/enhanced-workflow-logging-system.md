name: "Enhanced WorkflowBuilder Logging System with Animated Progress and Metrics"
description: |

## Purpose
Implement a comprehensive logging system for GraphMCP workflows with animated progress indicators, bandwidth metrics, and visual feedback elements inspired by claude-code-log patterns. This PRP provides all necessary context for implementing a production-ready logging system in one pass.

## Core Principles
1. **Real-time Visual Feedback**: Animated step indicators and progress tracking
2. **Performance Metrics**: Bandwidth, timing, and efficiency monitoring
3. **Context Preservation**: Maintain existing workflow patterns from examples/
4. **Integration Ready**: Build on concrete/workflow_logger.py foundations
5. **Testing First**: Comprehensive test coverage with async patterns

---

## Goal
Build an enhanced logging system that provides real-time visual feedback during workflow execution, including animated step indicators, progress bars, bandwidth tracking, and comprehensive metrics collection, while maintaining compatibility with existing GraphMCP workflow patterns.

## Why
- **Developer Experience**: Visual feedback improves debugging and monitoring
- **Production Readiness**: Comprehensive metrics enable performance optimization
- **User Confidence**: Progress indicators reduce perceived wait times
- **Operational Insight**: Detailed logs aid in troubleshooting and optimization
- **Integration Value**: Seamless integration with existing WorkflowBuilder pattern

## What
Enhanced logging system with animated progress tracking, metrics collection, and visual feedback

### Success Criteria
- [ ] Animated step indicators with loading states during workflow execution
- [ ] Real-time bandwidth and performance metrics display
- [ ] Backward compatibility with existing concrete/workflow_logger.py
- [ ] Integration with WorkflowBuilder execution pattern
- [ ] Comprehensive test coverage with async patterns
- [ ] Visual progress bars and status indicators
- [ ] Structured JSON output for programmatic consumption
- [ ] HTML output generation inspired by claude-code-log patterns

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: concrete/workflow_logger.py
  why: Existing logging foundation with metrics and formatting patterns
  critical: DatabaseWorkflowLogger class structure and methods to preserve

- file: workflows/builder.py  
  why: WorkflowBuilder and Workflow.execute() integration points
  critical: WorkflowContext usage and step execution flow

- file: examples/data_models.py
  why: @dataclass patterns with serialization methods
  critical: to_dict()/from_dict() and pickle-safe patterns

- file: examples/mcp_base_client.py
  why: Error handling patterns and async context managers
  critical: Exception hierarchies and retry mechanisms

- file: concrete/performance_optimization.py
  why: AsyncCache, PerformanceMetrics, and timing patterns
  critical: Metrics collection and caching strategies

- url: https://github.com/daaain/claude-code-log
  why: HTML template patterns and interactive timeline visualization
  critical: Progress visualization and status indicator patterns

- file: examples/testing_patterns.py
  why: pytest-asyncio patterns and test structure
  critical: Async test patterns and mock strategies

- file: examples/makefile_patterns.md
  why: Build automation and demo command patterns
  critical: Colored output and help system integration
```

### Current Codebase Tree (Core Logging Components)
```bash
concrete/
├── workflow_logger.py           # Base logging with metrics
├── performance_optimization.py  # AsyncCache and PerformanceMetrics
└── monitoring.py               # Additional monitoring utilities

workflows/
├── builder.py                  # WorkflowBuilder and execution
└── context.py                  # WorkflowContext for data sharing

examples/
├── data_models.py             # Serialization patterns
├── testing_patterns.py       # Async test patterns  
└── makefile_patterns.md      # Build automation patterns

tests/
└── data/                     # Mock data and test fixtures
```

### Desired Codebase Tree with New Files
```bash
concrete/
├── workflow_logger.py              # [ENHANCED] Base logging (preserve existing)
├── enhanced_logger.py              # [NEW] Enhanced logger with animations
├── progress_tracker.py             # [NEW] Progress and metrics tracking
├── visual_renderer.py              # [NEW] HTML/terminal output rendering
└── performance_optimization.py     # [EXISTING] Metrics integration

workflows/
└── builder.py                      # [ENHANCED] Integration with enhanced logging

tests/
├── test_enhanced_logger.py         # [NEW] Comprehensive test suite
├── test_progress_tracker.py        # [NEW] Progress tracking tests
└── test_visual_renderer.py         # [NEW] Rendering tests

demo/
└── enhanced_logging_demo.py        # [NEW] Demo showcasing enhanced logging
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Existing concrete/workflow_logger.py patterns MUST be preserved
# - DatabaseWorkflowLogger class interface
# - WorkflowMetrics dataclass structure  
# - log_* method signatures for backward compatibility

# CRITICAL: AsyncCache from performance_optimization.py requires event loop
# - Must check if event loop exists before creating cleanup tasks
# - Handle RuntimeError when no event loop available

# CRITICAL: WorkflowBuilder execution in workflows/builder.py
# - Steps execute sequentially in Workflow.execute()
# - context.set_shared_value() pattern for step results
# - Custom functions receive (context, step, **parameters)

# CRITICAL: pytest-asyncio testing patterns
# - Use @pytest.mark.asyncio for async tests
# - Mock external dependencies with AsyncMock
# - Use pytest fixtures for setup/teardown

# CRITICAL: Terminal output formatting
# - Use ANSI escape codes for colors (see Makefile patterns)
# - Handle terminal width for progress bars
# - Graceful fallback for non-TTY environments
```

## Implementation Blueprint

### Data Models and Structure
Create enhanced data models building on existing patterns:
```python
# Enhanced metrics with animation state
@dataclass
class EnhancedWorkflowMetrics(WorkflowMetrics):
    current_step: str = ""
    progress_percentage: float = 0.0
    estimated_completion: Optional[float] = None
    bandwidth_mbps: float = 0.0
    animation_state: str = "idle"  # idle, running, completed, error
    
    def to_dict(self) -> Dict[str, Any]:
        # Include parent metrics + enhanced fields
        result = super().to_dict()
        result.update({
            'current_step': self.current_step,
            'progress_percentage': self.progress_percentage,
            'estimated_completion': self.estimated_completion,
            'bandwidth_mbps': self.bandwidth_mbps,
            'animation_state': self.animation_state
        })
        return result

@dataclass  
class ProgressFrame:
    step_id: str
    step_name: str
    status: str  # pending, running, completed, error
    progress: float  # 0.0 to 1.0
    elapsed_time: float
    estimated_remaining: Optional[float]
    bandwidth_mbps: float
    timestamp: float = field(default_factory=time.time)
```

### Task List in Implementation Order

```yaml
Task 1: Enhance Base Metrics Collection
MODIFY concrete/workflow_logger.py:
  - PRESERVE existing DatabaseWorkflowLogger interface
  - ADD enhanced metrics fields to WorkflowMetrics
  - INJECT bandwidth tracking to existing methods
  - KEEP all existing method signatures intact

Task 2: Create Progress Tracking System  
CREATE concrete/progress_tracker.py:
  - MIRROR async patterns from performance_optimization.py
  - IMPLEMENT real-time progress calculation
  - ADD bandwidth monitoring using AsyncCache patterns
  - FOLLOW @dataclass patterns from examples/data_models.py

Task 3: Build Visual Rendering Engine
CREATE concrete/visual_renderer.py:
  - IMPLEMENT terminal progress bars with ANSI codes
  - ADD animated step indicators (spinner, progress bars)
  - CREATE HTML output inspired by claude-code-log patterns
  - HANDLE terminal width detection and responsive layout

Task 4: Enhanced Logger Integration
CREATE concrete/enhanced_logger.py:
  - EXTEND DatabaseWorkflowLogger with visual features
  - INTEGRATE ProgressTracker and VisualRenderer
  - PRESERVE all existing logging method signatures
  - ADD async context manager for cleanup

Task 5: WorkflowBuilder Integration
MODIFY workflows/builder.py:
  - INJECT enhanced logger into Workflow.execute()
  - ADD progress callbacks during step execution
  - PRESERVE existing custom_function signature
  - MAINTAIN WorkflowContext compatibility

Task 6: Comprehensive Test Suite
CREATE tests/test_enhanced_logger.py:
  - MIRROR patterns from examples/testing_patterns.py
  - USE pytest-asyncio for all async tests
  - MOCK terminal output with StringIO
  - TEST error scenarios and edge cases

Task 7: Demo Implementation
CREATE demo/enhanced_logging_demo.py:
  - SHOWCASE animated progress during workflow execution
  - DEMONSTRATE bandwidth tracking and metrics
  - PROVIDE both terminal and HTML output modes
  - INTEGRATE with existing demo patterns
```

### Task 1 Pseudocode - Enhanced Metrics Collection
```python
# PRESERVE existing DatabaseWorkflowLogger completely
# ADD new enhanced metrics without breaking changes

@dataclass 
class EnhancedWorkflowMetrics(WorkflowMetrics):
    # EXTEND parent class, don't modify it
    current_step: str = ""
    progress_percentage: float = 0.0
    bandwidth_mbps: float = 0.0
    animation_state: str = "idle"
    
    def calculate_bandwidth(self, bytes_processed: int, duration: float) -> float:
        # PATTERN: Safe division with fallback
        if duration <= 0:
            return 0.0
        return (bytes_processed / duration) / (1024 * 1024)  # MB/s

# PRESERVE existing methods, ADD enhanced tracking
class DatabaseWorkflowLogger:
    def __init__(self, database_name: str, log_level: str = "INFO"):
        # EXISTING initialization preserved
        self.enhanced_metrics = EnhancedWorkflowMetrics(
            start_time=time.time(),
            database_name=database_name
        )
```

### Task 2 Pseudocode - Progress Tracking System
```python
class ProgressTracker:
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.completed_steps = 0
        self.current_step = ""
        self.start_time = time.time()
        # PATTERN: Use AsyncCache for metrics buffering
        self.metrics_cache = AsyncCache(strategy=CacheStrategy.MEMORY)
    
    async def update_progress(self, step_id: str, progress: float):
        # PATTERN: Calculate bandwidth using performance_optimization patterns
        now = time.time()
        elapsed = now - self.start_time
        
        # CRITICAL: Handle division by zero
        if elapsed > 0:
            bandwidth = self.calculate_step_bandwidth(step_id, progress, elapsed)
        else:
            bandwidth = 0.0
            
        # PATTERN: Cache progress frames for smooth animation
        frame = ProgressFrame(
            step_id=step_id,
            progress=progress, 
            bandwidth_mbps=bandwidth,
            timestamp=now
        )
        await self.metrics_cache.set(f"progress_{step_id}", frame)
```

### Task 3 Pseudocode - Visual Rendering
```python
class VisualRenderer:
    def __init__(self, output_mode: str = "terminal"):
        self.output_mode = output_mode
        self.terminal_width = self._detect_terminal_width()
        # PATTERN: Follow Makefile color patterns
        self.colors = {
            'GREEN': '\033[0;32m',
            'YELLOW': '\033[0;33m', 
            'BLUE': '\033[0;34m',
            'NC': '\033[0m'
        }
    
    def render_progress_bar(self, progress: float, step_name: str) -> str:
        # PATTERN: Responsive layout based on terminal width
        bar_width = max(20, self.terminal_width - len(step_name) - 20)
        filled = int(progress * bar_width)
        
        # CRITICAL: Handle edge cases
        if progress >= 1.0:
            status_icon = "✅"
            color = self.colors['GREEN']
        elif progress > 0:
            status_icon = "🔄"  # Animated in real implementation
            color = self.colors['BLUE']
        else:
            status_icon = "⏳"
            color = self.colors['YELLOW']
            
        return f"{color}{status_icon} {step_name} [{'█' * filled}{'░' * (bar_width - filled)}] {progress:.1%}{self.colors['NC']}"
```

### Integration Points
```yaml
WORKFLOWS:
  - modify: workflows/builder.py
  - pattern: "Inject enhanced_logger into Workflow.execute()"
  - preserve: "All existing WorkflowContext patterns"

CACHING:
  - integrate: concrete/performance_optimization.py AsyncCache
  - pattern: "Use for progress frame buffering and metrics"
  - preserve: "Existing cache strategies and cleanup"

TESTING:
  - add to: tests/
  - pattern: "Follow examples/testing_patterns.py async patterns"
  - markers: "@pytest.mark.unit, @pytest.mark.integration"

DEMO:
  - add to: demo/
  - pattern: "Follow existing demo.py structure and CLI patterns"
  - integration: "Use with existing WorkflowBuilder patterns"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check concrete/enhanced_logger.py --fix
ruff check concrete/progress_tracker.py --fix  
ruff check concrete/visual_renderer.py --fix
mypy concrete/enhanced_logger.py
mypy concrete/progress_tracker.py
mypy concrete/visual_renderer.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE comprehensive test suite following examples/testing_patterns.py

@pytest.mark.asyncio
async def test_enhanced_logger_initialization():
    """Test enhanced logger initializes without breaking existing patterns"""
    logger = EnhancedDatabaseWorkflowLogger("test_db")
    assert logger.database_name == "test_db"
    assert isinstance(logger.enhanced_metrics, EnhancedWorkflowMetrics)
    
@pytest.mark.asyncio  
async def test_progress_tracking_bandwidth_calculation():
    """Test bandwidth calculation handles edge cases"""
    tracker = ProgressTracker(total_steps=5)
    
    # Test normal bandwidth calculation
    await tracker.update_progress("step1", 0.5)
    frame = await tracker.get_current_frame("step1")
    assert frame.bandwidth_mbps >= 0
    
    # Test zero duration edge case
    with patch('time.time', return_value=tracker.start_time):
        await tracker.update_progress("step2", 0.1)
        frame = await tracker.get_current_frame("step2")
        assert frame.bandwidth_mbps == 0.0

@pytest.mark.asyncio
async def test_visual_renderer_terminal_width():
    """Test visual renderer handles various terminal widths"""
    renderer = VisualRenderer()
    
    # Test narrow terminal
    with patch.object(renderer, 'terminal_width', 40):
        bar = renderer.render_progress_bar(0.5, "Test Step")
        assert len(bar) <= 80  # Reasonable length
        
    # Test wide terminal  
    with patch.object(renderer, 'terminal_width', 120):
        bar = renderer.render_progress_bar(0.75, "Long Step Name")
        assert "75.0%" in bar
```

```bash
# Run and iterate until passing:
uv run pytest tests/test_enhanced_logger.py -v
uv run pytest tests/test_progress_tracker.py -v  
uv run pytest tests/test_visual_renderer.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test with existing workflow patterns
uv run python demo/enhanced_logging_demo.py --database test_db --mock

# Expected: Animated progress bars, bandwidth metrics, successful completion
# Check for:
# - Progress bars render correctly
# - Bandwidth metrics show reasonable values  
# - No breaking changes to existing workflow execution
# - All existing log methods still work

# If errors: Check concrete/workflow_logger.py compatibility
```

### Level 4: Performance Test
```bash
# Test performance impact of enhanced logging
uv run python -m pytest tests/ -k "performance" -v

# Expected: Enhanced logging adds <10% overhead to workflow execution
# Check metrics_cache performance with large workflows
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check concrete/`
- [ ] No type errors: `uv run mypy concrete/`
- [ ] Backward compatibility: Existing workflow_logger.py methods unchanged
- [ ] Demo runs successfully: `uv run python demo/enhanced_logging_demo.py`
- [ ] Performance acceptable: <10% overhead over baseline
- [ ] Visual elements render correctly in terminal
- [ ] HTML output generates without errors
- [ ] Bandwidth metrics calculate correctly
- [ ] Error cases handled gracefully with visual feedback

---

## Anti-Patterns to Avoid
- ❌ Don't modify existing DatabaseWorkflowLogger method signatures
- ❌ Don't break backward compatibility with workflow_logger.py
- ❌ Don't create blocking operations in async context
- ❌ Don't hardcode terminal dimensions - detect dynamically  
- ❌ Don't ignore terminal capability detection (TTY vs non-TTY)
- ❌ Don't create memory leaks with cached progress frames
- ❌ Don't skip error handling in visual rendering code
- ❌ Don't assume ANSI color support - provide fallbacks

## Confidence Score: 9/10

This PRP provides comprehensive context for implementing an enhanced logging system with animated progress indicators. The high confidence score is based on:

1. **Complete Context**: All necessary files, patterns, and integration points identified
2. **Backward Compatibility**: Preserves existing concrete/workflow_logger.py interface
3. **Clear Implementation Path**: Step-by-step tasks with specific patterns to follow
4. **Comprehensive Testing**: Async test patterns with edge case coverage
5. **Performance Awareness**: Integration with existing AsyncCache and metrics systems
6. **Visual Design**: Terminal-responsive rendering with graceful fallbacks

The implementation builds directly on existing GraphMCP patterns while adding substantial visual enhancement value.