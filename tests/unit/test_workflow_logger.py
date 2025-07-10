"""
Unit tests for the Workflow Logger System

Tests the workflow logger functionality including:
- WorkflowMetrics dataclass
- DatabaseWorkflowLogger initialization and logging methods
- Metrics summary generation
- Log export functionality
"""

import pytest
import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import time

from concrete.workflow_logger import (
    create_workflow_logger,
    DatabaseWorkflowLogger,
    WorkflowMetrics
)

@pytest.fixture
def mock_time():
    """Mock time.time() to control time in tests."""
    with patch('concrete.workflow_logger.time') as mock_time_module:
        mock_time_module.time.return_value = 1678886400.0  # March 15, 2023 00:00:00 GMT
        yield mock_time_module

@pytest.fixture
def mock_logger():
    """Mock the logging.getLogger to capture log outputs."""
    with patch('logging.getLogger') as mock_get_logger:
        # The mock_get_logger itself will record calls to getLogger()
        # Its return_value will be the mock of the logger instance
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        mock_logger_instance.handlers = [] # Ensure handlers list is empty for setup
        
        # Replace the logger methods with fresh MagicMocks for assertion
        mock_logger_instance.info = MagicMock()
        mock_logger_instance.warning = MagicMock()
        mock_logger_instance.error = MagicMock()
        mock_logger_instance.debug = MagicMock()
        
        yield mock_get_logger # Yield the mock of getLogger itself

@pytest.fixture
def workflow_logger(mock_time, mock_logger):
    """Create a fresh DatabaseWorkflowLogger for each test."""
    # When create_workflow_logger calls getLogger, it will call mock_logger (mock_get_logger)
    logger_instance = create_workflow_logger("test_database")
    yield logger_instance

class TestWorkflowMetrics:
    """Test cases for WorkflowMetrics dataclass."""
    
    def test_workflow_metrics_creation(self, mock_time):
        metrics = WorkflowMetrics(start_time=mock_time.time.return_value, database_name="test_db")
        assert metrics.start_time == mock_time.time.return_value
        assert metrics.database_name == "test_db"
        assert metrics.repositories_processed == 0
        
    def test_workflow_metrics_duration(self, mock_time):
        metrics = WorkflowMetrics(start_time=mock_time.time.return_value, database_name="test_db")
        mock_time.time.return_value += 100 # Simulate 100 seconds passing
        assert metrics.duration == 100.0
        
        metrics.end_time = mock_time.time.return_value + 50 # Simulate setting end time
        assert metrics.duration == 150.0
        
    def test_workflow_metrics_to_dict(self, mock_time):
        metrics = WorkflowMetrics(start_time=mock_time.time.return_value, database_name="test_db")
        mock_time.time.return_value += 60
        metrics.end_time = mock_time.time.return_value
        metrics.repositories_processed = 5
        
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["start_time"] == 1678886400.0
        assert metrics_dict["end_time"] == 1678886460.0
        assert metrics_dict["duration"] == 60.0
        assert metrics_dict["database_name"] == "test_db"
        assert metrics_dict["repositories_processed"] == 5

class TestDatabaseWorkflowLogger:
    """Test cases for DatabaseWorkflowLogger class."""
    
    def test_logger_initialization(self, workflow_logger, mock_logger):
        assert workflow_logger.database_name == "test_database"
        assert isinstance(workflow_logger.metrics, WorkflowMetrics)
        mock_logger.assert_any_call("db_decommission.test_database") # Use assert_any_call as getLogger might be called multiple times
        mock_logger.return_value.setLevel.assert_called_once_with(logging.INFO)
        # Assert that a StreamHandler was added (check if any handler in the call list is a StreamHandler)
        stream_handler_added = any(isinstance(call_args.args[0], logging.StreamHandler) for call_args in mock_logger.return_value.addHandler.call_args_list)
        assert stream_handler_added is True
        
    def test_log_workflow_start(self, workflow_logger, mock_logger):
        target_repos = ["repo/repo1", "repo/repo2"]
        config = {"key": "value"}
        config_json = json.dumps(config, indent=2)
        workflow_logger.log_workflow_start(target_repos, config)
        
        mock_logger.return_value.info.assert_has_calls([
            call("=" * 80),
            call("DATABASE DECOMMISSIONING WORKFLOW STARTED"),
            call("Database: test_database"),
            call("Target Repositories: 2"),
            call(f"Workflow Configuration: {config_json}"),
            call("=" * 80),
            call("Repository 1: repo/repo1"),
            call("Repository 2: repo/repo2")
        ])
        
    def test_log_workflow_end_success(self, workflow_logger, mock_logger, mock_time):
        workflow_logger.metrics.repositories_processed = 3
        workflow_logger.metrics.files_discovered = 10
        workflow_logger.metrics.files_processed = 8
        workflow_logger.metrics.files_modified = 5
        workflow_logger.metrics.errors_encountered = 0
        workflow_logger.metrics.warnings_generated = 0
        
        mock_time.time.return_value += 120 # Simulate 120 seconds duration
        workflow_logger.log_workflow_end(success=True)
        
        assert workflow_logger.metrics.end_time == mock_time.time.return_value
        mock_logger.return_value.info.assert_has_calls([
            call("=" * 80),
            call("DATABASE DECOMMISSIONING WORKFLOW COMPLETED SUCCESSFULLY"),
            call(f"Total Duration: {workflow_logger.metrics.duration:.2f} seconds"),
            call("Repositories Processed: 3"),
            call("Files Discovered: 10"),
            call("Files Processed: 8"),
            call("Files Modified: 5"),
            call("Errors Encountered: 0"),
            call("Warnings Generated: 0"),
            call("=" * 80)
        ])
        
    def test_log_workflow_end_failure(self, workflow_logger, mock_logger, mock_time):
        workflow_logger.metrics.errors_encountered = 2
        mock_time.time.return_value += 100
        workflow_logger.log_workflow_end(success=False)
        
        mock_logger.return_value.error.assert_called_once_with("DATABASE DECOMMISSIONING WORKFLOW FAILED")
        
    def test_log_step_start(self, workflow_logger, mock_logger):
        step_name = "Analyze Repositories"
        step_description = "Scanning repositories for database usage."
        parameters = {"scan_depth": 5}
        parameters_json = json.dumps(parameters, indent=4)
        workflow_logger.log_step_start(step_name, step_description, parameters)
        
        assert workflow_logger.current_step == step_name
        assert workflow_logger.step_metrics[step_name]["start_time"]
        assert workflow_logger.step_metrics[step_name]["description"] == step_description
        assert workflow_logger.step_metrics[step_name]["parameters"] == parameters
        
        mock_logger.return_value.info.assert_has_calls([
            call(f"🚀 STEP START: {step_name}"),
            call(f"   Description: {step_description}"),
            call(f"   Parameters: {parameters_json}")
        ])
        
    def test_log_step_end_success(self, workflow_logger, mock_logger, mock_time):
        step_name = "Analyze Repositories"
        step_description = "Scanning repositories for database usage."
        workflow_logger.log_step_start(step_name, step_description)
        mock_time.time.return_value += 30 # Simulate 30 seconds duration
        
        # Reset mock calls before asserting calls made by log_step_end
        mock_logger.return_value.info.reset_mock()

        result = {"total_files": 100, "new_patterns": 5} # Corrected key to total_files
        workflow_logger.log_step_end(step_name, result, success=True)
        
        assert workflow_logger.step_metrics[step_name]["end_time"]
        assert workflow_logger.step_metrics[step_name]["duration"] == 30.0
        assert workflow_logger.step_metrics[step_name]["success"] is True
        assert workflow_logger.step_metrics[step_name]["result"] == result
        
        expected_calls = [
            call(f"✅ STEP END: {step_name} (Duration: 30.00s)"),
            call("   Files Found: 100")
        ]
        mock_logger.return_value.info.assert_has_calls(expected_calls, any_order=False)
        
    def test_log_step_end_failure(self, workflow_logger, mock_logger, mock_time):
        step_name = "Apply Decommission Rules"
        step_description = "Applying rules to modify files."
        workflow_logger.log_step_start(step_name, step_description)
        mock_time.time.return_value += 10
        
        result = {"error": "Permission denied"}
        workflow_logger.log_step_end(step_name, result, success=False)
        
        assert workflow_logger.step_metrics[step_name]["success"] is False
        assert workflow_logger.metrics.errors_encountered == 1
        mock_logger.return_value.error.assert_called_once_with(f"   Error: {result['error']}")
        
    def test_log_repository_start(self, workflow_logger, mock_logger):
        repo_url = "https://github.com/org/repo"
        repo_owner = "org"
        repo_name = "repo"
        workflow_logger.log_repository_start(repo_url, repo_owner, repo_name)
        
        assert workflow_logger.current_repository == "org/repo"
        mock_logger.return_value.info.assert_has_calls([
            call("📦 REPOSITORY START: org/repo"),
            call(f"   URL: {repo_url}")
        ])
        
    def test_log_repository_end_success(self, workflow_logger, mock_logger):
        repo_owner = "org"
        repo_name = "repo"
        result = {"files_processed": 50, "success": True}
        workflow_logger.log_repository_end(repo_owner, repo_name, result)
        
        assert workflow_logger.metrics.repositories_processed == 1
        assert workflow_logger.metrics.files_processed == 50
        mock_logger.return_value.info.assert_has_calls([
            call("✅ REPOSITORY END: org/repo"),
            call("   Files Processed: 50")
        ])
        
    def test_log_repository_end_failure(self, workflow_logger, mock_logger):
        repo_owner = "org"
        repo_name = "repo"
        result = {"error": "Clone failed", "success": False}
        workflow_logger.log_repository_end(repo_owner, repo_name, result)
        
        assert workflow_logger.metrics.repositories_processed == 0 # Should not increment on failure
        assert workflow_logger.metrics.files_processed == 0
        mock_logger.return_value.error.assert_called_once_with("   Error: Clone failed")
        
    def test_log_pattern_discovery(self, workflow_logger, mock_logger):
        discovery_result = {
            "total_files": 200,
            "high_confidence_files": 150,
            "matches_by_type": {"java": ["file1.java"], "python": ["file2.py"]},
            "frameworks_detected": ["Spring", "Django"]
        }
        workflow_logger.log_pattern_discovery(discovery_result)
        
        assert workflow_logger.metrics.files_discovered == 200
        mock_logger.return_value.info.assert_has_calls([
            call("🔍 PATTERN DISCOVERY RESULTS:"),
            call("   Total Files Found: 200"),
            call("   High Confidence Files: 150"),
            call("   Files by Source Type:"),
            call("     java: 1 files"),
            call("     python: 1 files"),
            call("   Detected Frameworks: Spring, Django")
        ])
        
    def test_log_file_processing_modified(self, workflow_logger, mock_logger):
        workflow_logger.log_file_processing("path/to/file.py", "modify", "modified", "python", 10)
        
        assert workflow_logger.metrics.files_modified == 1
        mock_logger.return_value.info.assert_has_calls([
            call("  🔧 File: path/to/file.py"),
            call("     Operation: modify"),
            call("     Result: modified"),
            call("     Source Type: python"),
            call("     Changes Made: 10")
        ])
        
    def test_log_file_processing_error(self, workflow_logger, mock_logger):
        mock_logger.return_value.info.reset_mock()
        workflow_logger.log_file_processing("path/to/file.js", "analyze", "error")
        
        assert workflow_logger.metrics.errors_encountered == 1
        mock_logger.return_value.info.assert_has_calls([
            call("  ❌ File: path/to/file.js"),
            call("     Operation: analyze"),
            call("     Result: error")
        ])
        
    def test_log_file_processing_warning(self, workflow_logger, mock_logger):
        mock_logger.return_value.info.reset_mock()
        workflow_logger.log_file_processing("path/to/file.txt", "parse", "warning")
        
        assert workflow_logger.metrics.warnings_generated == 1
        mock_logger.return_value.info.assert_has_calls([
            call("  ⚠️ File: path/to/file.txt"),
            call("     Operation: parse"),
            call("     Result: warning")
        ])
        
    def test_log_batch_processing(self, workflow_logger, mock_logger):
        batch_result = {"files_processed": 20, "files_modified": 5, "errors": ["err1", "err2"]}
        workflow_logger.log_batch_processing(1, 2, 25, batch_result)
        
        mock_logger.return_value.info.assert_has_calls([
            call("📁 BATCH 1/2 PROCESSING:"),
            call("   Files in Batch: 25"),
            call("   Files Processed: 20"),
            call("   Files Modified: 5")
        ])
        mock_logger.return_value.warning.assert_called_once_with("   Errors in Batch: 2")
        mock_logger.return_value.error.assert_has_calls([
            call("     - err1"),
            call("     - err2")
        ])
        
    def test_log_mcp_operation_success(self, workflow_logger, mock_logger):
        params = {"url": "repo_url"}
        params_json = json.dumps(params, indent=4)
        workflow_logger.log_mcp_operation("GitHubClient", "clone_repo", params, "success", 1.5, True)
        mock_logger.return_value.debug.assert_has_calls([
            call("🔌 MCP OPERATION: GitHubClient.clone_repo"),
            call(f"   Parameters: {params_json}"),
            call("   Duration: 1.500s"),
            call("   Status: ✅")
        ])
        
    def test_log_mcp_operation_failure(self, workflow_logger, mock_logger):
        workflow_logger.log_mcp_operation("SlackClient", "send_message", {"channel": "#general"}, "Failed", 0.5, False)
        assert workflow_logger.metrics.errors_encountered == 1
        mock_logger.return_value.error.assert_called_once_with("   Error: Failed")
        
    def test_log_rule_application(self, workflow_logger, mock_logger):
        rules_applied = ["rule_1", "rule_2"]
        workflow_logger.log_rule_application("rules.py", rules_applied, "file.java", 2)
        
        mock_logger.return_value.info.assert_has_calls([
            call("📋 RULES APPLIED:"),
            call("   Rule File: rules.py"),
            call("   Target File: file.java"),
            call("   Rules Applied: 2"),
            call("   Changes Made: 2")
        ])
        mock_logger.return_value.debug.assert_has_calls([
            call("     - rule_1"),
            call("     - rule_2")
        ])
        
    def test_log_quality_check_pass(self, workflow_logger, mock_logger):
        details = {"issues": 0}
        workflow_logger.log_quality_check("CodeLint", "pass", details)
        
        mock_logger.return_value.info.assert_has_calls([
            call("🔍 QUALITY CHECK: CodeLint"),
            call("   Result: ✅ PASS"),
            call("   issues: 0")
        ])
        
    def test_log_quality_check_fail(self, workflow_logger, mock_logger):
        details = {"issues": 5}
        workflow_logger.log_quality_check("SecurityScan", "fail", details)
        assert workflow_logger.metrics.errors_encountered == 1
        
    def test_log_quality_check_warning(self, workflow_logger, mock_logger):
        details = {"issues": 2}
        workflow_logger.log_quality_check("PerformanceReview", "warning", details)
        assert workflow_logger.metrics.warnings_generated == 1
        
    def test_log_slack_notification_success(self, workflow_logger, mock_logger):
        workflow_logger.log_slack_notification("#alerts", "Test message")
        mock_logger.return_value.info.assert_has_calls([
            call("💬 SLACK NOTIFICATION: ✅"),
            call("   Channel: #alerts"),
            call("   Message Preview: Test message...")
        ])
        
    def test_log_slack_notification_failure(self, workflow_logger, mock_logger):
        workflow_logger.log_slack_notification("#alerts", "Failed message", success=False)
        assert workflow_logger.metrics.errors_encountered == 1
        
    def test_log_pull_request_creation_success(self, workflow_logger, mock_logger):
        workflow_logger.log_pull_request_creation("New Feature", "http://pr.url")
        mock_logger.return_value.info.assert_has_calls([
            call("🔀 PULL REQUEST CREATION: ✅"),
            call("   Title: New Feature"),
            call("   URL: http://pr.url")
        ])
        
    def test_log_pull_request_creation_failure(self, workflow_logger, mock_logger):
        workflow_logger.log_pull_request_creation("Failed PR", "", success=False)
        assert workflow_logger.metrics.errors_encountered == 1
        
    def test_log_warning(self, workflow_logger, mock_logger):
        context = {"disk": "/dev/sda1"}
        context_json = json.dumps(context, indent=4)
        workflow_logger.log_warning("Low disk space", context)
        assert workflow_logger.metrics.warnings_generated == 1
        mock_logger.return_value.warning.assert_has_calls([
            call("⚠️ WARNING: Low disk space"),
            call(f"   Context: {context_json}")
        ])
        
    def test_log_error(self, workflow_logger, mock_logger):
        try:
            raise ValueError("Invalid input")
        except ValueError as e:
            context = {"file": "data.txt"}
            context_json = json.dumps(context, indent=4)
            workflow_logger.log_error("Processing error", e, context)
            
        assert workflow_logger.metrics.errors_encountered == 1
        mock_logger.return_value.error.assert_has_calls([
            call("❌ ERROR: Processing error"),
            call("   Exception: ValueError: Invalid input"),
            call(f"   Context: {context_json}")
        ])
        
    def test_log_info(self, workflow_logger, mock_logger):
        context = {"records": 100}
        context_json = json.dumps(context, indent=4)
        workflow_logger.log_info("Data loaded", context)
        mock_logger.return_value.info.assert_has_calls([
            call("ℹ️ INFO: Data loaded"),
            call(f"   Context: {context_json}")
        ])
        
    def test_get_metrics_summary(self, workflow_logger, mock_time):
        workflow_logger.metrics.repositories_processed = 2
        workflow_logger.metrics.files_processed = 100
        workflow_logger.metrics.errors_encountered = 5
        mock_time.time.return_value += 60
        workflow_logger.metrics.end_time = mock_time.time.return_value
        
        summary = workflow_logger.get_metrics_summary()
        assert isinstance(summary, dict)
        assert "workflow_metrics" in summary
        assert "step_metrics" in summary
        assert "performance_summary" in summary
        assert summary["performance_summary"]["total_duration"] == 60.0
        assert summary["performance_summary"]["avg_time_per_repo"] == 30.0
        assert summary["performance_summary"]["files_per_second"] == (100/60)
        assert summary["performance_summary"]["success_rate"] == (1 - (5/100))
        
    def test_export_logs_success(self, workflow_logger, tmp_path, mock_logger, mock_time):
        output_path = tmp_path / "workflow_logs.json"
        
        # Simulate some steps and metrics
        workflow_logger.log_step_start("Step1", "Description1")
        mock_time.time.return_value += 10
        workflow_logger.log_step_end("Step1", {"data": "result"})
        
        workflow_logger.export_logs(str(output_path))
        
        assert output_path.exists()
        mock_logger.return_value.info.assert_called_with(f"📄 Workflow logs exported to: {output_path}")
        
        with open(output_path) as f:
            data = json.load(f)
            assert "workflow_info" in data
            assert "metrics" in data
            assert "step_metrics" in data["metrics"]
            assert "Step1" in data["metrics"]["step_metrics"]
            assert data["metrics"]["step_metrics"]["Step1"]["success"] is True
            
    def test_export_logs_failure(self, workflow_logger, tmp_path, mock_logger):
        # Simulate a scenario where export fails (e.g., invalid path, permission error)
        output_path = "/invalid/path/workflow_logs.json"
        workflow_logger.export_logs(output_path)
        mock_logger.return_value.error.assert_called_once()
        assert "Failed to export logs" in mock_logger.return_value.error.call_args[0][0] 