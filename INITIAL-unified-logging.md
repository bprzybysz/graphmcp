## FEATURE: Unified Dual-Sink Logging System with Independent Thresholds

**Goal**: Replace all 4 fragmented logging systems with single UnifiedLogger featuring dual-sink architecture, severity color coding, and independent threshold management.

**Core Strategy**: Consolidate logging into production-ready system:
1. **UnifiedLogger**: Dual-sink logging (File-only structured + Visual UI) with independent thresholds
2. **File Logging**: Constant LOG_FILEPATH='dbworkflow.log' with rotating file handler
3. **Severity Color Coding**: DEBUG(gray), INFO(white), WARNING(orange), ERROR(red), CRITICAL(bold red)
4. **Migration Strategy**: Replace all logging.getLogger() calls with get_logger() factory function
5. **Threshold Management**: Independent control over file sink (structured logs) and visual sink (UI feedback)

**Implementation Focus**: 🚧 IN PROGRESS
- [ ] **UnifiedLogger Core Implementation**: Dual-sink architecture (file + visual) with threshold filtering
- [ ] **File Logging System**: Constant LOG_FILEPATH='dbworkflow.log' with rotating file handler
- [ ] **Severity Color System**: Rich console color mapping for all log levels  
- [ ] **Migration of workflows/ directory**: Replace all existing logging calls
- [ ] **Factory Function**: get_logger() with configurable threshold defaults for both sinks
- [ ] **Dynamic Configuration**: Runtime threshold adjustment and environment-based settings

## EXAMPLES:

**Core Architecture Patterns** (`concrete/unified_logger.py`):
- Extend EnhancedDatabaseWorkflowLogger as base for unified system
- Implement dual-sink pattern with independent threshold filtering
- Use constant LOG_FILEPATH='dbworkflow.log' with rotating file handler (10MB, 5 backups)
- Use Rich Console for color-coded visual output with timestamp formatting
- Maintain backward compatibility with existing method signatures

**Complete Log Configuration** (`concrete/unified_logger.py`):
```python
# Constant configuration
LOG_FILEPATH = 'dbworkflow.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5                 # Keep 5 rotated files
FILE_LOG_FORMAT = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'

class UnifiedLogger:
    def __init__(self, component_name: str, file_threshold='DEBUG', visual_threshold='INFO'):
        # SINK 1: File logging with rotation
        self.file_handler = RotatingFileHandler(
            LOG_FILEPATH, 
            maxBytes=MAX_LOG_SIZE, 
            backupCount=BACKUP_COUNT
        )
        self.file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
        
        # SINK 2: Visual Rich console  
        self.rich_console = Console()

# Usage patterns
# Production: Full file logs, errors-only UI
prod_logger = get_logger("component", file_threshold='DEBUG', visual_threshold='ERROR')

# Development: Everything visible in both sinks
dev_logger = get_logger("component", file_threshold='DEBUG', visual_threshold='DEBUG')

# Demo: Balanced experience
demo_logger = get_logger("component", file_threshold='INFO', visual_threshold='INFO')
```

**Migration Patterns** (Replace throughout codebase):
```python
# BEFORE: Standard logging
import logging
logger = logging.getLogger(__name__)
logger.info("Message")

# AFTER: Unified dual-sink logging
from concrete.unified_logger import get_logger
logger = get_logger(__name__)
logger.info("Message")  # → dbworkflow.log file + White UI output
```

**Testing Patterns** (`tests/test_unified_logger.py`):
- Use pytest-asyncio for async logging operations
- Mock Rich Console for UI output testing
- Test file logging to 'dbworkflow.log' with rotation (10MB, 5 backups)
- Test threshold filtering behavior for both sinks
- Verify file rotation and persistence
- Verify color mapping and timestamp formatting
- Test dynamic threshold changes and environment configuration

## DOCUMENTATION:

**GraphMCP Unified Logging Documentation:**
- Unified Logger API: `concrete/unified_logger.py` - UnifiedLogger class with dual-sink architecture
- Factory Function: `concrete/unified_logger.py` - get_logger() with threshold configuration
- Migration Guide: `docs/LOGGING_MIGRATION.md` - Step-by-step replacement of existing logging
- Configuration: `docs/LOGGING_CONFIG.md` - Threshold management and environment setup

**Core Implementation Files:**
- Unified Logger: `concrete/unified_logger.py` - Main UnifiedLogger class implementation
- Factory Function: `concrete/unified_logger.py` - get_logger() factory with threshold defaults
- Color Mapping: `concrete/unified_logger.py` - SEVERITY_COLORS dict with Rich color codes
- Migration Script: `scripts/migrate_logging.py` - Automated replacement of logging calls

**Testing Coverage:**
- Unit Tests: `tests/unit/test_unified_logger.py` - Core functionality and threshold behavior
- Integration Tests: `tests/integration/test_logging_migration.py` - End-to-end logging behavior
- Workflow Tests: `tests/e2e/test_workflow_logging.py` - Real workflow logging integration
- Performance Tests: `tests/performance/test_logging_overhead.py` - Dual-sink performance impact

**Migration Target Areas:**
- Workflow Builder: `workflows/builder.py` - Replace logging.getLogger() calls
- Context Management: `workflows/context.py` - Unified logging in workflow context
- All Workflow Steps: `workflows/*.py` - Systematic replacement of logging calls
- Demo System: `demo/*.py` - Migration from EnhancedDemoLogger to UnifiedLogger

## OTHER CONSIDERATIONS:

**Essential Implementation Details:**

1. **Dual-Sink Architecture**:
   - SINK 1: File logging to 'dbworkflow.log' with configurable threshold (default: DEBUG)
     - Rotating file handler: 10MB max size, 5 backup files
     - Format: '[2025-07-14 23:48:15] INFO component.name: Message {context}'
   - SINK 2: Visual Rich console with configurable threshold (default: INFO)
     - Format: '23:48:15 INFO Message' (color-coded by severity)
   - Independent filtering: Messages only output to sinks that meet threshold

2. **Migration Strategy**:
   - Phase 1: Implement UnifiedLogger core with threshold management
   - Phase 2: Create get_logger() factory function with environment detection
   - Phase 3: Systematic replacement in workflows/ directory (highest impact)
   - Phase 4: Replace remaining logging calls across entire codebase

3. **Critical Requirements**:
   - **Backward Compatibility**: All existing method signatures must work unchanged
   - **Performance**: Dual-sink overhead must be minimal and measurable
   - **Environment Adaptation**: Automatic threshold adjustment for dev/prod environments
   - **Zero Breaking Changes**: Existing workflows continue working during migration
   - **Thread Safety**: Support concurrent logging from async workflow operations

**Implementation Priority:**

1. **Week 1 - Core Implementation** (Vital):
   - ✅ UnifiedLogger class with dual-sink architecture
   - ✅ Severity color mapping with Rich console integration
   - ✅ Independent threshold filtering for both sinks
   - ✅ get_logger() factory function with configurable defaults

2. **Week 2 - Workflow Migration** (Crucial):
   - ✅ Replace all logging in `workflows/builder.py`
   - ✅ Replace all logging in `workflows/context.py`
   - ✅ Migrate remaining `workflows/*.py` files
   - ✅ Update demo system to use UnifiedLogger

3. **Week 3 - Full Codebase** (Important):
   - ✅ Replace logging calls in `clients/` directory
   - ✅ Replace logging calls in `concrete/` directory
   - ✅ Remove deprecated logging systems (EnhancedDemoLogger, etc.)
   - ✅ Environment-based configuration and documentation

**Testing Strategy:**

**Crucial E2E Tests:**
- `test_workflow_logging_integration()`: Full workflow execution with unified logging
- `test_threshold_filtering_e2e()`: End-to-end threshold behavior across components
- `test_production_environment_logging()`: Production threshold configuration validation
- `test_logging_migration_compatibility()`: Verify no breaking changes during migration
- `test_file_logging_persistence()`: Verify logs persist to 'dbworkflow.log' across restarts

**Vital Unit Tests:**
- `test_dual_sink_filtering()`: Independent threshold filtering for file and visual sinks
- `test_file_rotation()`: Test 10MB limit and 5 backup file rotation
- `test_severity_color_mapping()`: Color assignment for all log levels in visual sink
- `test_dynamic_threshold_changes()`: Runtime threshold modification
- `test_get_logger_factory()`: Factory function with various threshold configurations
- `test_rich_console_output()`: Visual formatting and timestamp generation
- `test_file_logger_structure()`: File logging format and context preservation
- `test_async_logging_safety()`: Concurrent logging operations to both sinks
- `test_log_file_permissions()`: File creation and write permissions for 'dbworkflow.log'

**Environment Test Coverage:**
- Development environment: DEBUG/DEBUG thresholds
- Production environment: DEBUG/ERROR thresholds  
- Demo environment: INFO/INFO thresholds
- Testing environment: WARNING/CRITICAL thresholds

**Performance Benchmarks:**
- Dual-sink overhead vs single logging: < 10% performance impact
- File I/O efficiency: < 2ms per file write with rotation
- Threshold filtering efficiency: < 1ms per log call
- Rich console rendering: < 5ms per visual log
- Memory usage: < 50MB additional for visual components
- File rotation performance: < 100ms for 10MB file rotation