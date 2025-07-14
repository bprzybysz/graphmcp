# INITIAL: Claude-Trace Structured Logging System
## Implementation Specification Following Claude Code's JSON-First Approach

### Project Overview
**Name**: GraphMCP Claude-Trace Structured Logging System  
**Type**: Core Infrastructure - Logging Framework Replacement  
**Priority**: High (Consolidates 4 existing logging systems)  
**Dependencies**: None (Standard Library Only)  

### Implementation Details

#### Core Architecture
```python
# File: graphmcp/logging/structured_logger.py
class StructuredLogger:
    """JSON-first logging system inspired by Claude Code."""
    
    def __init__(self, workflow_id: str, config: LoggingConfig):
        self.workflow_id = workflow_id
        self.config = config
        self.session_start = time.time()
        
        # File handler with rotation
        self.file_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_filepath,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        
        # Console handler for human output
        self.console_handler = logging.StreamHandler(sys.stdout)
        
    def log_structured(self, entry: LogEntry) -> None:
        """Core method: dual-sink JSON + console output."""
        if self.config.output_format in ["json", "dual"]:
            self._write_json_output(entry)
        if self.config.output_format in ["console", "dual"]:
            self._write_console_output(entry)

# File: graphmcp/logging/data_models.py
@dataclass
class LogEntry:
    timestamp: float
    workflow_id: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    component: str
    message: str
    data: Optional[Dict[str, Any]] = None
    step_index: Optional[int] = None
    duration_ms: Optional[float] = None
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "level": self.level,
            "component": self.component,
            "message": self.message,
            "data": self.data,
            "step_index": self.step_index,
            "duration_ms": self.duration_ms
        }

@dataclass
class StructuredData:
    timestamp: float
    workflow_id: str
    data_type: Literal["table", "tree", "json", "metrics"]
    title: str
    content: Dict[str, Any]
    
    def to_json(self) -> Dict[str, Any]:
        """Convert structured data to JSON."""
        return {
            "type": "structured_data",
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "data_type": self.data_type,
            "title": self.title,
            "content": self.content
        }
```

#### Configuration System
```python
# File: graphmcp/logging/config.py
@dataclass
class LoggingConfig:
    """Centralized logging configuration - constant LOG_FILEPATH."""
    log_filepath: str = "dbworkflow.log"  # Constant as requested
    output_format: Literal["json", "console", "dual"] = "dual"
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    max_file_size_mb: int = 100
    backup_count: int = 5
    json_structured_output: bool = True
    
    @classmethod
    def for_automation(cls) -> 'LoggingConfig':
        """Configuration for automation/CI - JSON only."""
        return cls(output_format="json", console_level="ERROR")
    
    @classmethod 
    def for_development(cls) -> 'LoggingConfig':
        """Configuration for development - dual output."""
        return cls(output_format="dual", console_level="DEBUG")
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Load from environment variables."""
        return cls(
            output_format=os.getenv("GRAPHMCP_OUTPUT_FORMAT", "dual"),
            console_level=os.getenv("GRAPHMCP_CONSOLE_LEVEL", "INFO"),
            file_level=os.getenv("GRAPHMCP_FILE_LEVEL", "DEBUG")
        )
```

#### Main Workflow Logger
```python
# File: graphmcp/logging/workflow_logger.py
class WorkflowLogger:
    """Main logger replacing all existing GraphMCP loggers."""
    
    def __init__(self, workflow_id: str, config: Optional[LoggingConfig] = None):
        self.workflow_id = workflow_id
        self.config = config or LoggingConfig.from_env()
        self.structured_logger = StructuredLogger(workflow_id, self.config)
        self.progress_tracker = ProgressTracker(workflow_id, self.structured_logger)
        
    # Replace EnhancedDatabaseWorkflowLogger methods
    def log_step_start(self, step_name: str, metadata: Dict = None) -> None:
        """Log workflow step start with structured data."""
        entry = LogEntry(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            level="INFO",
            component="workflow",
            message=f"Starting step: {step_name}",
            data=metadata
        )
        self.structured_logger.log_structured(entry)
    
    def log_step_complete(self, step_name: str, duration_ms: float, 
                         result: Dict = None) -> None:
        """Log workflow step completion."""
        entry = LogEntry(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            level="INFO", 
            component="workflow",
            message=f"Completed step: {step_name}",
            data=result,
            duration_ms=duration_ms
        )
        self.structured_logger.log_structured(entry)
    
    # Replace DatabaseWorkflowLogger methods
    def log_file_discovery(self, files: List[str], repo: str, 
                          pattern_matches: Dict = None) -> None:
        """Log file discovery with structured table data."""
        table_data = StructuredData(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            data_type="table",
            title="File Discovery Results",
            content={
                "headers": ["File", "Repository", "Pattern Matches"],
                "rows": [
                    [f, repo, str(pattern_matches.get(f, 0))] 
                    for f in files
                ],
                "metadata": {
                    "repository": repo,
                    "total_files": len(files),
                    "total_matches": sum(pattern_matches.values()) if pattern_matches else 0
                }
            }
        )
        self.structured_logger.log_structured_data(table_data)
    
    def log_repository_structure(self, repo: str, structure: Dict) -> None:
        """Log repository structure as tree data."""
        tree_data = StructuredData(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            data_type="tree",
            title=f"Repository Structure: {repo}",
            content={
                "tree": structure,
                "metadata": {"repository": repo}
            }
        )
        self.structured_logger.log_structured_data(tree_data)
    
    # Replace EnhancedDemoLogger methods  
    def log_workflow_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log workflow metrics as structured JSON."""
        metrics_data = StructuredData(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            data_type="metrics",
            title="Workflow Metrics",
            content=metrics
        )
        self.structured_logger.log_structured_data(metrics_data)
    
    # Progress tracking methods
    def start_progress(self, step_name: str, total_items: int = None) -> str:
        """Start progress tracking for a step."""
        return self.progress_tracker.start_step(step_name, total_items)
    
    def update_progress(self, step_id: str, current: int, total: int) -> None:
        """Update progress with current/total counts."""
        self.progress_tracker.update_progress(step_id, current, total)
    
    def complete_progress(self, step_id: str, final_metrics: Dict = None) -> None:
        """Complete progress tracking."""
        self.progress_tracker.complete_step(step_id, final_metrics)
```

#### CLI Integration (Claude Code Style)
```python
# File: graphmcp/logging/cli_output.py
class CLIOutputHandler:
    """Claude Code-inspired CLI output formatting."""
    
    @staticmethod
    def configure_from_args(args) -> LoggingConfig:
        """Configure logging from CLI arguments."""
        output_format = getattr(args, 'output_format', 'dual')
        return LoggingConfig(
            output_format=output_format,
            console_level=getattr(args, 'log_level', 'INFO')
        )
    
    @staticmethod
    def stream_json_line(data: Dict[str, Any]) -> None:
        """Stream single JSON line for tool integration."""
        json_line = json.dumps(data, separators=(',', ':'))
        print(json_line)
        sys.stdout.flush()
    
    @staticmethod  
    def format_console_line(entry: LogEntry) -> str:
        """Format human-readable console output."""
        timestamp_str = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S.%f")[:-3]
        
        # Color mapping as requested
        level_colors = {
            "DEBUG": "\033[90m",      # Gray
            "INFO": "\033[97m",       # White
            "WARNING": "\033[93m",    # Orange  
            "ERROR": "\033[91m",      # Red
            "CRITICAL": "\033[1;91m"  # Bold Red
        }
        
        color = level_colors.get(entry.level, "\033[97m")
        reset = "\033[0m"
        
        formatted = f"{color}[{timestamp_str}] {entry.level:8s} | {entry.component:15s} | {entry.message}{reset}"
        
        if entry.data:
            formatted += f"\n{color}  Data: {json.dumps(entry.data, indent=2)}{reset}"
            
        return formatted
```

### Testing Requirements

#### Unit Tests  
```python
# File: tests/unit/test_structured_logger.py
class TestStructuredLogger:
    def test_json_output_format(self):
        """Test JSON output matches Claude Code format."""
        
    def test_console_output_colors(self):
        """Test console colors match specification."""
        
    def test_dual_sink_logging(self):
        """Test both JSON and console output work simultaneously."""
        
    def test_file_rotation(self):
        """Test log file rotation with constant LOG_FILEPATH."""

# File: tests/unit/test_workflow_logger.py  
class TestWorkflowLogger:
    def test_replaces_enhanced_database_workflow_logger(self):
        """Test compatibility with existing workflow methods."""
        
    def test_structured_data_logging(self):
        """Test table, tree, and metrics logging."""
        
    def test_progress_tracking(self):
        """Test progress tracking without animations."""

# File: tests/unit/test_cli_integration.py
class TestCLIIntegration:
    def test_output_format_flag(self):
        """Test --output-format json|console|dual."""
        
    def test_json_pipeline_compatibility(self):
        """Test JSON output can be piped to other tools."""
```

#### Integration Tests
```python
# File: tests/integration/test_logger_migration.py
class TestLoggerMigration:
    def test_complete_workflow_with_new_logger(self):
        """Test full workflow using new structured logger."""
        
    def test_performance_vs_old_loggers(self):
        """Test performance improvement over Rich/alive-progress."""
        
    def test_json_output_parsing(self):
        """Test external tools can parse JSON output."""

# File: tests/integration/test_makefile_integration.py
class TestMakefileIntegration:
    def test_demo_with_structured_logging(self):
        """Test make demo uses new logging system."""
        
    def test_cli_output_format_options(self):
        """Test CLI output format options work with make targets."""
```

#### E2E Tests
```python
# File: tests/e2e/test_complete_system.py
class TestCompleteSystem:
    def test_database_decommission_workflow_logging(self):
        """Test complete database decommission with structured logs."""
        
    def test_automation_script_integration(self):
        """Test JSON logs work with automation scripts."""
        
    def test_log_analysis_tools(self):
        """Test logs can be analyzed by external tools."""
```

### Migration Plan

#### Phase 1: Core Implementation (Week 1)
```python
# Files to create:
- graphmcp/logging/__init__.py
- graphmcp/logging/structured_logger.py  
- graphmcp/logging/data_models.py
- graphmcp/logging/config.py
- graphmcp/logging/workflow_logger.py
- graphmcp/logging/cli_output.py

# Tests to create:
- tests/unit/test_structured_logger.py
- tests/unit/test_workflow_logger.py
- tests/unit/test_cli_integration.py
```

#### Phase 2: Migration (Week 2-3)
```python
# Files to update:
MIGRATION_TARGETS = [
    "concrete/db_decommission.py",           # Replace DatabaseWorkflowLogger
    "clients/preview_mcp/workflow_log.py",   # Replace EnhancedDemoLogger  
    "concrete/preview_ui/streamlit_app.py",  # Replace StreamlitWorkflowUI
    "demo.py",                               # Update to use WorkflowLogger
    "ui_demo.py"                             # Update to use WorkflowLogger
]

# Import replacements:
OLD_IMPORTS = [
    "from clients.preview_mcp.workflow_log import get_workflow_log",
    "from concrete.db_decommission import DatabaseWorkflowLogger", 
    "from concrete.preview_ui.streamlit_app import EnhancedDemoLogger"
]

NEW_IMPORT = "from graphmcp.logging import WorkflowLogger"
```

#### Phase 3: Cleanup (Week 4)
```python
# Files to remove:
FILES_TO_REMOVE = [
    "clients/preview_mcp/workflow_log.py",
    "concrete/db_decommission.py:DatabaseWorkflowLogger",  # Class only
    "concrete/preview_ui/streamlit_app.py:EnhancedDemoLogger"  # Class only
]

# Update imports across codebase
# Update Makefile targets to use --output-format flag
# Update README with new logging documentation
```

### Configuration Files

#### Environment Variables
```bash
# .env additions
GRAPHMCP_OUTPUT_FORMAT=dual              # json|console|dual
GRAPHMCP_CONSOLE_LEVEL=INFO             # DEBUG|INFO|WARNING|ERROR|CRITICAL  
GRAPHMCP_FILE_LEVEL=DEBUG               # DEBUG|INFO|WARNING|ERROR|CRITICAL
GRAPHMCP_LOG_FILE=dbworkflow.log        # Constant as requested
```

#### Makefile Updates
```makefile
# Add CLI flags to demo targets
demo-json: check-deps ## Run demo with JSON output for tools
	PYTHONPATH=. $(VENV_PATH)/bin/python demo.py --database postgres_air --output-format json

demo-console: check-deps ## Run demo with console output only  
	PYTHONPATH=. $(VENV_PATH)/bin/python demo.py --database postgres_air --output-format console

demo-pipeline: check-deps ## Demo JSON pipeline integration
	PYTHONPATH=. $(VENV_PATH)/bin/python demo.py --output-format json | jq '.level == "ERROR"'
```

### Success Criteria

#### Functional Requirements  
✅ **Consolidation**: Replace 4 existing loggers with 1 unified system  
✅ **JSON Output**: Claude Code-compatible structured JSON  
✅ **Console Output**: Human-readable with color coding  
✅ **File Logging**: Rotating logs to constant `dbworkflow.log`  
✅ **Structured Data**: Tables, trees, metrics logging  
✅ **Progress Tracking**: Performance-focused progress without animations  
✅ **CLI Integration**: `--output-format` flag support  

#### Performance Requirements
✅ **Speed**: 50%+ faster than Rich/alive-progress  
✅ **Memory**: <50MB for 10K log entries  
✅ **Dependencies**: Standard library only  
✅ **Startup**: <100ms initialization time  

#### Integration Requirements  
✅ **Tool Compatibility**: JSON output pipeable to external tools  
✅ **Automation**: Structured data for CI/CD integration  
✅ **Backward Compatibility**: Drop-in replacement for existing loggers  
✅ **Makefile Integration**: All demo targets use new logging  

---

**Implementation Status**: Ready to Begin  
**Estimated Timeline**: 4 weeks  
**Risk Assessment**: Low (no external dependencies)  
**Success Probability**: High (standard library approach)