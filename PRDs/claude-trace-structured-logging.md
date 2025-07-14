# GraphMCP Structured Logging System PRD
## Following Claude Code's JSON-First Approach

### Overview
Design a high-performance structured logging system inspired by Claude Code's JSON-first approach, emphasizing composability, integration, and structured data output over visual animations.

### Objectives
- **Primary**: Unified logging system across all GraphMCP workflows
- **Secondary**: Claude Code-style structured JSON output for tool integration
- **Tertiary**: Performance-focused design with minimal dependencies
- **Quaternary**: Composable and pipeable logging for automation

---

## Core Architecture

### 1. JSON-First Logging Engine
```python
class StructuredLogger:
    """Claude Code-inspired structured logging with JSON output."""
    
    def __init__(self, 
                 workflow_id: str,
                 output_format: Literal["json", "console", "dual"] = "dual",
                 log_filepath: str = "dbworkflow.log"):
        self.workflow_id = workflow_id
        self.output_format = output_format
        self.log_filepath = log_filepath
        self.session_start = time.time()
```

### 2. Structured Data Types
```python
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

@dataclass 
class ProgressEntry:
    timestamp: float
    workflow_id: str
    step_name: str
    status: Literal["started", "progress", "completed", "failed"]
    progress_percent: Optional[float] = None
    eta_seconds: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None

@dataclass
class StructuredData:
    timestamp: float
    workflow_id: str
    data_type: Literal["table", "tree", "json", "metrics"]
    title: str
    content: Dict[str, Any]
```

---

## Implementation Specification

### 3. Dual-Sink Architecture
```python
class DualSinkLogger:
    """Dual output: structured JSON + human-readable console."""
    
    def log_structured(self, entry: LogEntry) -> None:
        """Log with dual output format based on configuration."""
        # JSON output (for tools/automation)
        if self.output_format in ["json", "dual"]:
            json_line = {
                "timestamp": entry.timestamp,
                "workflow_id": entry.workflow_id,
                "level": entry.level,
                "component": entry.component,
                "message": entry.message,
                "data": entry.data
            }
            self._write_json_line(json_line)
        
        # Console output (for humans)
        if self.output_format in ["console", "dual"]:
            console_line = self._format_console_line(entry)
            self._write_console_line(console_line)
    
    def log_table(self, title: str, headers: List[str], 
                  rows: List[List[str]], metadata: Dict = None) -> None:
        """Log structured table data."""
        structured_data = StructuredData(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            data_type="table",
            title=title,
            content={
                "headers": headers,
                "rows": rows,
                "metadata": metadata or {}
            }
        )
        self._output_structured_data(structured_data)
    
    def log_tree(self, title: str, tree_data: Dict, 
                 metadata: Dict = None) -> None:
        """Log hierarchical tree structure."""
        structured_data = StructuredData(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            data_type="tree", 
            title=title,
            content={
                "tree": tree_data,
                "metadata": metadata or {}
            }
        )
        self._output_structured_data(structured_data)
```

### 4. Progress Tracking System
```python
class ProgressTracker:
    """High-performance progress tracking without heavy animations."""
    
    def start_step(self, step_name: str, total_items: Optional[int] = None) -> str:
        """Start tracking a workflow step."""
        step_id = f"{self.workflow_id}_{step_name}_{int(time.time())}"
        progress_entry = ProgressEntry(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            step_name=step_name,
            status="started",
            metrics={"total_items": total_items} if total_items else None
        )
        self._log_progress(progress_entry)
        return step_id
    
    def update_progress(self, step_id: str, current: int, 
                       total: int, eta_seconds: float = None) -> None:
        """Update step progress with structured metrics."""
        progress_percent = (current / total) * 100 if total > 0 else None
        progress_entry = ProgressEntry(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            step_name=step_id,
            status="progress",
            progress_percent=progress_percent,
            eta_seconds=eta_seconds,
            metrics={
                "current": current,
                "total": total,
                "rate_per_second": self._calculate_rate(step_id, current)
            }
        )
        self._log_progress(progress_entry)
```

---

## Integration Points

### 5. GraphMCP Workflow Integration
```python
class WorkflowLogger:
    """Main logger for GraphMCP workflows - replaces all existing loggers."""
    
    def __init__(self, workflow_id: str, config: LoggingConfig):
        self.structured_logger = StructuredLogger(workflow_id, **config.dict())
        self.progress_tracker = ProgressTracker(workflow_id, self.structured_logger)
        self.workflow_id = workflow_id
    
    # Replace EnhancedDatabaseWorkflowLogger methods
    def log_step_start(self, step_name: str, metadata: Dict = None) -> None:
        self.structured_logger.log_structured(LogEntry(
            timestamp=time.time(),
            workflow_id=self.workflow_id,
            level="INFO",
            component="workflow",
            message=f"Starting step: {step_name}",
            data=metadata
        ))
    
    # Replace DatabaseWorkflowLogger methods  
    def log_file_discovery(self, files: List[str], repo: str) -> None:
        self.structured_logger.log_table(
            title="File Discovery Results",
            headers=["File", "Repository", "Size"],
            rows=[[f, repo, "TBD"] for f in files],
            metadata={"repository": repo, "total_files": len(files)}
        )
    
    # Replace EnhancedDemoLogger methods
    def log_workflow_tree(self, workflow_structure: Dict) -> None:
        self.structured_logger.log_tree(
            title="Workflow Structure", 
            tree_data=workflow_structure,
            metadata={"workflow_id": self.workflow_id}
        )
```

### 6. Command Line Integration (Claude Code Style)
```python
class CLIOutputHandler:
    """Claude Code-inspired CLI output formatting."""
    
    @staticmethod
    def get_output_format() -> str:
        """Support --output-format flag like Claude Code."""
        return os.getenv("GRAPHMCP_OUTPUT_FORMAT", "dual")
    
    @staticmethod  
    def stream_json_output(log_entry: LogEntry) -> None:
        """Stream JSON output for tool integration."""
        json_output = {
            "type": "log",
            "timestamp": log_entry.timestamp,
            "level": log_entry.level.lower(), 
            "workflow_id": log_entry.workflow_id,
            "component": log_entry.component,
            "message": log_entry.message,
            "data": log_entry.data
        }
        print(json.dumps(json_output, separators=(',', ':')))
        sys.stdout.flush()
    
    @staticmethod
    def format_console_output(log_entry: LogEntry) -> str:
        """Human-readable console format."""
        timestamp_str = datetime.fromtimestamp(log_entry.timestamp).strftime("%H:%M:%S")
        level_color = {
            "DEBUG": "\033[90m",    # Gray
            "INFO": "\033[97m",     # White  
            "WARNING": "\033[93m",  # Orange
            "ERROR": "\033[91m",    # Red
            "CRITICAL": "\033[1;91m" # Bold Red
        }.get(log_entry.level, "\033[97m")
        
        return f"{level_color}[{timestamp_str}] {log_entry.level:8s} | {log_entry.component:15s} | {log_entry.message}\033[0m"
```

---

## Configuration System

### 7. Logging Configuration
```python
@dataclass
class LoggingConfig:
    """Centralized logging configuration."""
    log_filepath: str = "dbworkflow.log"
    output_format: Literal["json", "console", "dual"] = "dual"
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    max_file_size_mb: int = 100
    backup_count: int = 5
    structured_data_enabled: bool = True
    progress_tracking_enabled: bool = True
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Load configuration from environment variables."""
        return cls(
            log_filepath=os.getenv("GRAPHMCP_LOG_FILE", "dbworkflow.log"),
            output_format=os.getenv("GRAPHMCP_OUTPUT_FORMAT", "dual"),
            console_level=os.getenv("GRAPHMCP_CONSOLE_LEVEL", "INFO"),
            file_level=os.getenv("GRAPHMCP_FILE_LEVEL", "DEBUG")
        )
```

---

## Testing & Validation

### 8. Test Requirements
```python
# Unit Tests Required:
- test_structured_logger_json_output()
- test_dual_sink_console_formatting() 
- test_progress_tracker_metrics()
- test_table_logging_structure()
- test_tree_logging_hierarchy()
- test_cli_output_format_compatibility()

# Integration Tests Required:
- test_workflow_logger_replacement()
- test_claude_code_style_cli_integration()
- test_json_output_pipeline_compatibility()
- test_performance_vs_existing_loggers()

# E2E Tests Required:
- test_complete_workflow_with_structured_logging()
- test_automation_script_json_parsing()
- test_log_file_rotation_and_cleanup()
```

### 9. Migration Strategy
```python
# Phase 1: Create new StructuredLogger
# Phase 2: Replace EnhancedDatabaseWorkflowLogger usage
# Phase 3: Replace DatabaseWorkflowLogger usage  
# Phase 4: Replace EnhancedDemoLogger usage
# Phase 5: Remove old logging classes
# Phase 6: Update all workflow imports

MIGRATION_MAPPING = {
    "EnhancedDatabaseWorkflowLogger": "WorkflowLogger",
    "DatabaseWorkflowLogger": "WorkflowLogger", 
    "EnhancedDemoLogger": "WorkflowLogger",
    "get_workflow_log": "WorkflowLogger.get_instance"
}
```

---

## Performance & Dependencies

### 10. Minimal Dependencies
```python
# Core Dependencies (Standard Library Only):
import json
import time
import logging
import logging.handlers
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Literal, Any

# No External Dependencies Required:
# ❌ rich 
# ❌ alive-progress
# ❌ colorama
# ❌ termcolor
```

### 11. Performance Targets
- **JSON Output**: <1ms per log entry
- **Console Formatting**: <2ms per log entry  
- **File I/O**: Async/buffered writes
- **Memory Usage**: <50MB for 10K log entries
- **Startup Time**: <100ms logger initialization

---

## Expected Outcomes

### 12. Success Metrics
1. **Consolidation**: 4 logging systems → 1 unified system
2. **Integration**: Claude Code-compatible JSON output  
3. **Performance**: 50%+ faster than Rich/alive-progress
4. **Composability**: Pipeable output for automation
5. **Maintainability**: Single source of truth for logging
6. **Tool Compatibility**: Structured data for external tools

### 13. Usage Examples
```bash
# JSON output for tools
python demo.py --output-format json | jq '.level == "ERROR"'

# Console output for humans  
python demo.py --output-format console

# Dual output (default)
python demo.py

# Pipe structured data
python demo.py --output-format json | claude -p "analyze these logs"
```

---

## Implementation Timeline
- **Week 1**: Core StructuredLogger + DualSinkLogger
- **Week 2**: ProgressTracker + WorkflowLogger 
- **Week 3**: Migration of existing loggers
- **Week 4**: Testing + CLI integration
- **Week 5**: Documentation + final validation

---

**Status**: Ready for Implementation  
**Dependencies**: None (Standard Library Only)  
**Estimated Effort**: 5 weeks  
**Risk Level**: Low (No external dependencies)