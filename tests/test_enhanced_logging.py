"""
Unit tests for enhanced GraphMCP logging features.

Tests the new clean console output, hierarchical display,
and enhanced progress visualization features.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from io import StringIO

from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig
from graphmcp.logging.structured_logger import StructuredLogger
from graphmcp.logging.workflow_logger import WorkflowLogger


class TestEnhancedConsoleFormatter:
    """Test the enhanced console formatter."""
    
    def test_step_message_formatting(self):
        """Test that step messages are properly formatted with hierarchical icons."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_steps", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("Starting step: Test Step")
            logger.info("Progress: Test Step (50%)")
            logger.info("Completed step: Test Step")
            
        output = mock_stdout.getvalue()
        
        # Check for hierarchical icons
        assert "🔄" in output  # Start icon
        assert "├─" in output  # Progress icon
        assert "└─" in output  # Complete icon
    
    def test_summary_message_formatting(self):
        """Test that summary messages are properly formatted."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_summary", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("Environment validated: 57 parameters")
            logger.info("Workflow completed successfully")
            
        output = mock_stdout.getvalue()
        
        # Check for summary icons
        assert "📊" in output  # Info icon
        assert "✅" in output  # Success icon
    
    def test_error_message_formatting(self):
        """Test that error messages are properly formatted."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_error", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.error("Error in step: Test Step - Something went wrong")
            
        output = mock_stdout.getvalue()
        
        # Check for error formatting
        assert "❌" in output  # Error icon
        assert "\033[91m" in output  # Red color


class TestEnvironmentValidationSummary:
    """Test environment validation summary functionality."""
    
    def test_environment_validation_summary_console(self):
        """Test clean console output for environment validation."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_env", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_environment_validation_summary(
                total_params=57,
                secrets_count=4,
                clients_validated=3,
                validation_time=2.7
            )
            
        output = mock_stdout.getvalue()
        
        # Check for clean summary (not 57 lines of parameters)
        assert "Environment validated: 57 parameters, 4 secrets, 3 clients (2.7s)" in output
        assert "📊" in output  # Info icon
        
        # Should NOT contain individual parameter dumps
        assert "BRAVE_SEARCH_API_KEY" not in output
        assert "length:" not in output
    
    def test_environment_validation_summary_json(self):
        """Test that detailed data goes to JSON log."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_env_json", config)
        
        # Mock the structured logger to capture JSON output
        with patch.object(logger.structured_logger, 'log_structured_data') as mock_log:
            logger.log_environment_validation_summary(
                total_params=57,
                secrets_count=4,
                clients_validated=3,
                validation_time=2.7
            )
            
        # Verify structured data was logged
        mock_log.assert_called_once()
        call_args = mock_log.call_args[0][0]
        
        assert call_args.data_type == "metrics"
        assert call_args.title == "Environment Validation Summary"
        assert call_args.content["validation_summary"]["total_parameters"] == 57


class TestWorkflowStepTree:
    """Test hierarchical step tree visualization."""
    
    def test_workflow_step_tree_display(self):
        """Test tree-based step visualization."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_tree", config)
        
        sub_steps = ["Step 1", "Step 2", "Step 3"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_workflow_step_tree(
                step_name="Main Process",
                sub_steps=sub_steps,
                current_sub_step="Step 2"
            )
            
        output = mock_stdout.getvalue()
        
        # Check for hierarchical tree structure
        assert "🔄 Main Process" in output
        assert "├─" in output  # Tree branches
        assert "└─" in output  # Final branch
        assert "✅" in output  # Completed steps
        assert "⏳" in output  # Pending steps
    
    def test_workflow_step_start_with_numbering(self):
        """Test workflow step start with step numbering."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_numbered", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_workflow_step_start(
                step_name="Repository Analysis",
                step_number=1,
                total_steps=6,
                description="Analyzing repository structure"
            )
            
        output = mock_stdout.getvalue()
        
        # Check for step numbering and description
        assert "[1/6]" in output
        assert "Repository Analysis" in output
        assert "Analyzing repository structure" in output


class TestProgressVisualization:
    """Test enhanced progress visualization."""
    
    def test_progress_bar_creation(self):
        """Test visual progress bar creation."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_progress", config)
        
        # Test progress bar formatting
        progress_bar = logger.structured_logger._create_progress_bar(50.0, 20)
        
        # Check for Unicode progress characters
        assert "█" in progress_bar  # Filled character
        assert "░" in progress_bar  # Empty character
        assert "[" in progress_bar and "]" in progress_bar  # Brackets
        
        # Check correct ratio (50% of 20 = 10 filled chars)
        assert progress_bar.count("█") == 10
        assert progress_bar.count("░") == 10
    
    def test_progress_tracking_with_eta(self):
        """Test progress tracking with ETA calculation."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_progress_eta", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            step_id = logger.start_progress("Test Operation", 100)
            logger.update_progress(step_id, 50, 100)
            
        output = mock_stdout.getvalue()
        
        # Check for progress display with visual bar
        assert "Progress: Test Operation" in output
        assert "50.0%" in output
        assert "█" in output  # Progress bar
        assert "ETA:" in output  # ETA display


class TestQualityAssuranceSummary:
    """Test quality assurance summary functionality."""
    
    def test_qa_summary_console_output(self):
        """Test clean QA summary console output."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_qa", config)
        
        qa_results = [
            {"check_name": "Test 1", "status": "passed", "confidence": 95, "description": "OK"},
            {"check_name": "Test 2", "status": "failed", "confidence": 0, "description": "Failed"}
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_quality_assurance_summary(qa_results)
            
        output = mock_stdout.getvalue()
        
        # Check for clean summary
        assert "📋 Quality Assurance: 1/2 checks passed" in output
        assert "📊" in output  # Info icon
    
    def test_qa_summary_structured_data(self):
        """Test QA summary structured data output."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_qa_structured", config)
        
        qa_results = [
            {"check_name": "Test 1", "status": "passed", "confidence": 95, "description": "OK"}
        ]
        
        with patch.object(logger.structured_logger, 'log_structured_data') as mock_log:
            logger.log_quality_assurance_summary(qa_results)
            
        # Verify structured table was created
        mock_log.assert_called_once()
        call_args = mock_log.call_args[0][0]
        
        assert call_args.data_type == "table"
        assert call_args.title == "Quality Assurance Results"
        assert len(call_args.content["rows"]) == 1
        assert "✅" in call_args.content["rows"][0][1]  # Status with icon
    
    def test_qa_summary_empty_results(self):
        """Test QA summary with no results."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_qa_empty", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_quality_assurance_summary([])
            
        output = mock_stdout.getvalue()
        
        # Check for empty state message
        assert "⚠️  Quality Assurance: No checks performed" in output


class TestOperationDurationLogging:
    """Test operation duration logging functionality."""
    
    def test_operation_duration_with_items(self):
        """Test operation duration logging with item count."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_duration", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_operation_duration(
                operation_name="GitHub PR Creation",
                duration_seconds=14.4,
                items_processed=13
            )
            
        output = mock_stdout.getvalue()
        
        # Check for comprehensive duration info
        assert "✅ GitHub PR Creation completed:" in output
        assert "13 items in 14.4s" in output
        assert "items/sec" in output  # Rate calculation
    
    def test_operation_duration_without_items(self):
        """Test operation duration logging without item count."""
        config = LoggingConfig.for_development()
        logger = get_logger("test_duration_simple", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.log_operation_duration(
                operation_name="Configuration Load",
                duration_seconds=2.7
            )
            
        output = mock_stdout.getvalue()
        
        # Check for simple duration info
        assert "✅ Configuration Load completed in 2.7s" in output
        assert "items/sec" not in output  # No rate calculation


class TestJSONStructuredOutput:
    """Test that JSON structured output is preserved."""
    
    def test_json_output_maintained(self):
        """Test that JSON output is maintained for tool integration."""
        config = LoggingConfig.for_automation()  # JSON-only config
        logger = get_logger("test_json", config)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Mock the file handler
            with patch.object(logger.structured_logger.file_handler, 'emit') as mock_emit:
                logger.info("Test message", test_data={"key": "value"})
                
        # Verify JSON logging was called
        mock_emit.assert_called_once()
        
        # Check that the log record contains JSON
        log_record = mock_emit.call_args[0][0]
        json_content = json.loads(log_record.msg)
        
        assert json_content["type"] == "log"
        assert json_content["message"] == "Test message"
        assert json_content["data"]["test_data"]["key"] == "value"


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    def test_full_workflow_logging_scenario(self):
        """Test a complete workflow logging scenario."""
        config = LoggingConfig.for_development()
        logger = get_logger("integration_test", config)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # Environment validation
            logger.log_environment_validation_summary(57, 4, 3, 2.7)
            
            # Workflow steps
            logger.log_workflow_step_start("Analysis", 1, 3, "Analyzing repository")
            
            # Progress tracking
            step_id = logger.start_progress("File Processing", 10)
            logger.update_progress(step_id, 5, 10)
            logger.complete_progress(step_id)
            
            # QA Results
            qa_results = [{"check_name": "Test", "status": "passed", "confidence": 95, "description": "OK"}]
            logger.log_quality_assurance_summary(qa_results)
            
            # Operation completion
            logger.log_operation_duration("GitHub PR Creation", 14.4, 13)
            
            # Summary
            logger.log_workflow_summary()
            
        output = mock_stdout.getvalue()
        
        # Verify all components are present and properly formatted
        assert "📊 Environment validated:" in output
        assert "🔄 Starting step:" in output
        assert "Progress: File Processing" in output
        assert "📋 Quality Assurance:" in output
        assert "✅ GitHub PR Creation completed:" in output
        assert "Workflow completed" in output
        
        # Verify no verbose parameter dumps
        assert "BRAVE_SEARCH_API_KEY" not in output
        assert "length:" not in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])