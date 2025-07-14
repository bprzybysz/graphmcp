"""
Unit tests for GraphMCP structured logging system.

Tests JSON-first architecture, dual-sink logging, and CLI integration
following Claude Code patterns.
"""

import json
import tempfile
import time
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

from graphmcp.logging import (
    StructuredLogger, 
    LogEntry, 
    StructuredData, 
    ProgressEntry,
    LoggingConfig,
    WorkflowLogger,
    CLIOutputHandler,
    get_logger
)


class TestLoggingConfig:
    """Test logging configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LoggingConfig()
        
        assert config.log_filepath == "dbworkflow.log"
        assert config.output_format == "dual"
        assert config.console_level == "INFO"
        assert config.file_level == "DEBUG"
        assert config.max_file_size_mb == 100
        assert config.backup_count == 5
    
    def test_environment_config(self):
        """Test configuration from environment variables."""
        with patch.dict('os.environ', {
            'GRAPHMCP_OUTPUT_FORMAT': 'json',
            'GRAPHMCP_CONSOLE_LEVEL': 'ERROR',
            'GRAPHMCP_FILE_LEVEL': 'WARNING',
            'GRAPHMCP_LOG_FILE': 'custom.log'
        }):
            config = LoggingConfig.from_env()
            
            assert config.output_format == "json"
            assert config.console_level == "ERROR"
            assert config.file_level == "WARNING"
            assert config.log_filepath == "custom.log"
    
    def test_automation_config(self):
        """Test automation-optimized configuration."""
        config = LoggingConfig.for_automation()
        
        assert config.output_format == "json"
        assert config.console_level == "ERROR"
        assert config.file_level == "INFO"
        assert config.json_pretty_print == False
        assert config.progress_tracking_enabled == False
    
    def test_development_config(self):
        """Test development-optimized configuration."""
        config = LoggingConfig.for_development()
        
        assert config.output_format == "dual"
        assert config.console_level == "DEBUG"
        assert config.file_level == "DEBUG"
        assert config.json_pretty_print == True
        assert config.progress_tracking_enabled == True
    
    def test_level_enabled_check(self):
        """Test log level threshold checking."""
        config = LoggingConfig(console_level="WARNING", file_level="DEBUG")
        
        # Console sink (WARNING threshold)
        assert config.is_level_enabled("DEBUG", "console") == False
        assert config.is_level_enabled("INFO", "console") == False
        assert config.is_level_enabled("WARNING", "console") == True
        assert config.is_level_enabled("ERROR", "console") == True
        
        # File sink (DEBUG threshold)
        assert config.is_level_enabled("DEBUG", "file") == True
        assert config.is_level_enabled("INFO", "file") == True
        assert config.is_level_enabled("WARNING", "file") == True
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid output format
        config = LoggingConfig(output_format="invalid")
        with pytest.raises(ValueError, match="Invalid output_format"):
            config.validate()
        
        # Invalid console level
        config = LoggingConfig(console_level="INVALID")
        with pytest.raises(ValueError, match="Invalid console_level"):
            config.validate()
        
        # Valid configuration
        config = LoggingConfig()
        config.validate()  # Should not raise


class TestLogEntry:
    """Test log entry data model."""
    
    def test_log_entry_creation(self):
        """Test LogEntry creation and serialization."""
        entry = LogEntry.create(
            workflow_id="test_workflow",
            level="INFO",
            component="test_component",
            message="Test message",
            data={"key": "value"}
        )
        
        assert entry.workflow_id == "test_workflow"
        assert entry.level == "INFO"
        assert entry.component == "test_component"
        assert entry.message == "Test message"
        assert entry.data == {"key": "value"}
        assert entry.timestamp > 0
    
    def test_log_entry_to_json(self):
        """Test LogEntry JSON serialization."""
        entry = LogEntry.create(
            workflow_id="test_workflow",
            level="ERROR",
            component="test_component",
            message="Error message"
        )
        
        json_data = entry.to_json()
        
        assert json_data["type"] == "log"
        assert json_data["workflow_id"] == "test_workflow"
        assert json_data["level"] == "error"  # Lowercase in JSON
        assert json_data["component"] == "test_component"
        assert json_data["message"] == "Error message"
        assert "timestamp" in json_data


class TestStructuredData:
    """Test structured data models."""
    
    def test_table_creation(self):
        """Test table structured data creation."""
        table = StructuredData.create_table(
            workflow_id="test_workflow",
            title="Test Table",
            headers=["Column1", "Column2"],
            rows=[["Value1", "Value2"], ["Value3", "Value4"]],
            metadata={"row_count": 2}
        )
        
        assert table.data_type == "table"
        assert table.title == "Test Table"
        assert table.content["headers"] == ["Column1", "Column2"]
        assert len(table.content["rows"]) == 2
        assert table.content["metadata"]["row_count"] == 2
    
    def test_table_console_output(self):
        """Test table console formatting."""
        table = StructuredData.create_table(
            workflow_id="test_workflow",
            title="Files",
            headers=["File", "Status"],
            rows=[["file1.py", "Modified"], ["file2.py", "Created"]]
        )
        
        console_output = table.to_console_table()
        
        assert "[Files]" in console_output
        assert "File" in console_output
        assert "Status" in console_output
        assert "file1.py" in console_output
        assert "Modified" in console_output
    
    def test_tree_creation(self):
        """Test tree structured data creation."""
        tree_data = {
            "root": {
                "child1": {"leaf1": None},
                "child2": {"leaf2": None, "leaf3": None}
            }
        }
        
        tree = StructuredData.create_tree(
            workflow_id="test_workflow",
            title="Repository Structure",
            tree_data=tree_data,
            metadata={"total_nodes": 5}
        )
        
        assert tree.data_type == "tree"
        assert tree.title == "Repository Structure"
        assert tree.content["tree"] == tree_data
        assert tree.content["metadata"]["total_nodes"] == 5
    
    def test_metrics_creation(self):
        """Test metrics structured data creation."""
        metrics = {
            "files_processed": 42,
            "duration_seconds": 123.45,
            "success_rate": 98.5
        }
        
        metrics_data = StructuredData.create_metrics(
            workflow_id="test_workflow",
            title="Workflow Metrics",
            metrics=metrics
        )
        
        assert metrics_data.data_type == "metrics"
        assert metrics_data.title == "Workflow Metrics"
        assert metrics_data.content == metrics


class TestProgressEntry:
    """Test progress tracking models."""
    
    def test_progress_started(self):
        """Test progress start entry creation."""
        progress = ProgressEntry.create_started(
            workflow_id="test_workflow",
            step_name="file_processing",
            total_items=100
        )
        
        assert progress.status == "started"
        assert progress.step_name == "file_processing"
        assert progress.metrics["total_items"] == 100
    
    def test_progress_update(self):
        """Test progress update entry creation."""
        progress = ProgressEntry.create_progress(
            workflow_id="test_workflow",
            step_name="file_processing",
            current=25,
            total=100,
            rate_per_second=5.0
        )
        
        assert progress.status == "progress"
        assert progress.progress_percent == 25.0
        assert progress.metrics["current"] == 25
        assert progress.metrics["total"] == 100
        assert progress.metrics["rate_per_second"] == 5.0
        assert progress.eta_seconds == 15.0  # (100-25)/5.0


class TestStructuredLogger:
    """Test core structured logger functionality."""
    
    def test_logger_initialization(self):
        """Test StructuredLogger initialization."""
        config = LoggingConfig.for_development()
        logger = StructuredLogger("test_workflow", config)
        
        assert logger.workflow_id == "test_workflow"
        assert logger.config == config
        assert logger.session_start > 0
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_console_output(self, mock_stdout):
        """Test console output formatting (clean UI format)."""
        config = LoggingConfig(output_format="console")
        logger = StructuredLogger("test_workflow", config)
        
        entry = LogEntry.create(
            workflow_id="test_workflow",
            level="INFO",
            component="test_component",
            message="Test message"
        )
        
        logger.log_structured(entry)
        
        output = mock_stdout.getvalue()
        # Clean UI format: just colored message, no timestamps/levels
        assert "Test message" in output
        assert "\033[97m" in output  # White color for INFO
        assert "INFO" not in output  # No log level displayed
        assert "test_component" not in output  # No component displayed
    
    def test_json_output_to_file(self):
        """Test JSON output to file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
            config = LoggingConfig(
                output_format="json",
                log_filepath=tmp_file.name
            )
            logger = StructuredLogger("test_workflow", config)
            
            entry = LogEntry.create(
                workflow_id="test_workflow",
                level="INFO", 
                component="test_component",
                message="Test message"
            )
            
            logger.log_structured(entry)
            logger.flush()
            
            # Read and verify JSON output
            tmp_file.seek(0)
            json_line = tmp_file.read().strip()
            json_data = json.loads(json_line)
            
            assert json_data["type"] == "log"
            assert json_data["workflow_id"] == "test_workflow"
            assert json_data["level"] == "info"
            assert json_data["message"] == "Test message"
    
    def test_structured_data_logging(self):
        """Test structured data logging."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
            config = LoggingConfig(
                output_format="json",
                log_filepath=tmp_file.name
            )
            logger = StructuredLogger("test_workflow", config)
            
            table_data = StructuredData.create_table(
                workflow_id="test_workflow",
                title="Test Table",
                headers=["Col1", "Col2"],
                rows=[["A", "B"]]
            )
            
            logger.log_structured_data(table_data)
            logger.flush()
            
            tmp_file.seek(0)
            json_line = tmp_file.read().strip()
            json_data = json.loads(json_line)
            
            assert json_data["type"] == "structured_data"
            assert json_data["data_type"] == "table"
            assert json_data["title"] == "Test Table"


class TestWorkflowLogger:
    """Test main WorkflowLogger functionality."""
    
    def test_workflow_logger_creation(self):
        """Test WorkflowLogger initialization."""
        config = LoggingConfig.for_development()
        logger = WorkflowLogger("test_workflow", config)
        
        assert logger.workflow_id == "test_workflow"
        assert logger.database_name == "test_workflow"  # Legacy compatibility
        assert logger.config == config
    
    def test_basic_logging_methods(self):
        """Test basic logging methods (debug, info, warning, error, critical)."""
        config = LoggingConfig(output_format="json", log_filepath="/dev/null")
        logger = WorkflowLogger("test_workflow", config)
        
        # Test all logging levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Should not raise any exceptions
    
    def test_enhanced_database_workflow_compatibility(self):
        """Test compatibility with EnhancedDatabaseWorkflowLogger methods."""
        config = LoggingConfig(output_format="console")
        logger = WorkflowLogger("test_workflow", config)
        
        # Test step logging methods
        logger.log_step_start("test_step", "Step description", {"param": "value"})
        logger.log_step_complete("test_step", 1000.0, {"result": "success"})
        logger.log_step_error("test_step", "Test error", {"context": "test"})
        
        # Should not raise exceptions
    
    def test_database_workflow_compatibility(self):
        """Test compatibility with DatabaseWorkflowLogger methods."""
        config = LoggingConfig(output_format="console")
        logger = WorkflowLogger("test_workflow", config)
        
        # Test file discovery logging
        files = ["file1.py", "file2.py"]
        pattern_matches = {"file1.py": 5, "file2.py": 3}
        
        logger.log_file_discovery(files, "test_repo", pattern_matches)
        
        # Test repository structure logging
        structure = {"src": {"main.py": None, "util.py": None}}
        logger.log_repository_structure("test_repo", structure)
        
        # Test pattern discovery logging
        patterns = {"pattern1": ["file1.py"], "pattern2": ["file2.py"]}
        logger.log_pattern_discovery(patterns, 8)
        
        # Verify metrics were updated
        assert logger.metrics["files_discovered"] == 2
    
    def test_enhanced_demo_logger_compatibility(self):
        """Test compatibility with EnhancedDemoLogger methods."""
        config = LoggingConfig(output_format="console")
        logger = WorkflowLogger("test_workflow", config)
        
        # Test section header
        logger.print_section_header("Test Section", "🧪")
        
        # Test file hits table
        file_hits = [
            {"file_path": "file1.py", "hit_count": 5, "source_type": "python", "confidence": 0.95},
            {"file_path": "file2.py", "hit_count": 3, "source_type": "python", "confidence": 0.85}
        ]
        logger.print_file_hits_table(file_hits, "Test Files")
        
        # Test refactoring groups
        groups = [
            {"group_name": "Group1", "files": ["file1.py"], "patterns_count": 5, "priority": "high"},
            {"group_name": "Group2", "files": ["file2.py", "file3.py"], "patterns_count": 3, "priority": "medium"}
        ]
        logger.print_refactoring_groups(groups, "Test Groups")
        
        # Should not raise exceptions
    
    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        config = LoggingConfig(output_format="console")
        logger = WorkflowLogger("test_workflow", config)
        
        # Start progress tracking
        step_id = logger.start_progress("test_step", 100)
        assert step_id is not None
        
        # Update progress
        logger.update_progress(step_id, 25, 100)
        logger.update_progress(step_id, 50, 100)
        logger.update_progress(step_id, 100, 100)
        
        # Complete progress
        logger.complete_progress(step_id, {"final_result": "success"})
        
        # Should not raise exceptions
    
    def test_workflow_metrics(self):
        """Test workflow metrics logging."""
        config = LoggingConfig(output_format="console")
        logger = WorkflowLogger("test_workflow", config)
        
        # Log metrics
        metrics = {
            "files_processed": 42,
            "duration_seconds": 123.45,
            "success_rate": 98.5
        }
        logger.log_workflow_metrics(metrics)
        
        # Log summary
        logger.log_workflow_summary()
        
        # Verify metrics were updated
        stored_metrics = logger.get_metrics()
        assert stored_metrics["files_processed"] == 42
        assert stored_metrics["duration_seconds"] == 123.45


class TestCLIIntegration:
    """Test CLI integration functionality."""
    
    def test_cli_argument_addition(self):
        """Test adding CLI arguments to parser."""
        import argparse
        
        parser = argparse.ArgumentParser()
        CLIOutputHandler.add_logging_args(parser)
        
        # Test parsing with logging arguments
        args = parser.parse_args([
            '--output-format', 'json',
            '--log-level', 'DEBUG',
            '--log-file', 'custom.log'
        ])
        
        assert args.output_format == 'json'
        assert args.log_level == 'DEBUG'
        assert args.log_file == 'custom.log'
    
    def test_config_from_args(self):
        """Test creating configuration from CLI arguments."""
        import argparse
        
        args = argparse.Namespace(
            output_format='json',
            log_level='ERROR',
            file_log_level='WARNING',
            log_file='test.log',
            json_pretty=True
        )
        
        config = CLIOutputHandler.config_from_args(args)
        
        assert config.output_format == 'json'
        assert config.console_level == 'ERROR'
        assert config.file_level == 'WARNING'
        assert config.log_filepath == 'test.log'
        assert config.json_pretty_print == True
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_json_streaming(self, mock_stdout):
        """Test JSON line streaming."""
        test_data = {"type": "log", "message": "test"}
        
        CLIOutputHandler.stream_json_line(test_data)
        
        output = mock_stdout.getvalue().strip()
        parsed_data = json.loads(output)
        
        assert parsed_data == test_data
    
    def test_console_formatting(self):
        """Test console output formatting."""
        entry = LogEntry.create(
            workflow_id="test_workflow",
            level="WARNING",
            component="test_component",
            message="Test warning"
        )
        
        # Test with colors
        formatted_with_colors = CLIOutputHandler.format_console_entry(entry, use_colors=True)
        assert "\033[93m" in formatted_with_colors  # Orange color for WARNING
        assert "Test warning" in formatted_with_colors
        # Clean UI format: no log level displayed
        
        # Test without colors
        formatted_no_colors = CLIOutputHandler.format_console_entry(entry, use_colors=False)
        assert "\033[" not in formatted_no_colors  # No ANSI codes
        assert "Test warning" in formatted_no_colors
        # Clean UI format: no log level displayed


class TestGetLogger:
    """Test main get_logger factory function."""
    
    def test_get_logger_default(self):
        """Test get_logger with default configuration."""
        logger = get_logger("test_workflow")
        
        assert isinstance(logger, WorkflowLogger)
        assert logger.workflow_id == "test_workflow"
        assert logger.config.output_format == "dual"  # Default from environment
    
    def test_get_logger_custom_config(self):
        """Test get_logger with custom configuration."""
        config = LoggingConfig.for_automation()
        logger = get_logger("test_workflow", config)
        
        assert isinstance(logger, WorkflowLogger)
        assert logger.workflow_id == "test_workflow"
        assert logger.config.output_format == "json"  # Automation config
        assert logger.config.console_level == "ERROR"


# Integration test markers for pytest
@pytest.mark.integration
class TestIntegration:
    """Integration tests for complete logging system."""
    
    def test_full_workflow_logging(self):
        """Test complete workflow with structured logging."""
        config = LoggingConfig.for_development()
        logger = get_logger("integration_test", config)
        
        # Simulate a workflow
        logger.info("Starting integration test workflow")
        
        # Progress tracking
        step_id = logger.start_progress("file_processing", 10)
        for i in range(11):
            logger.update_progress(step_id, i, 10)
        logger.complete_progress(step_id)
        
        # Structured data
        files = ["file1.py", "file2.py", "file3.py"]
        logger.log_file_discovery(files, "test_repo")
        
        # Workflow summary
        logger.log_workflow_summary()
        
        logger.info("Integration test workflow completed")
        
        # Should complete without errors
        assert True