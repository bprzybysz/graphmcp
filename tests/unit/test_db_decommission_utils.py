"""
Comprehensive unit tests for Database Decommissioning Utils

Tests the utils module with:
- Workflow creation and configuration
- MCP configuration creation
- Repository URL extraction
- Workflow parameter validation
- Metrics calculation
- Summary formatting
- Error handling scenarios
"""

import pytest
import asyncio
import json
import time
from unittest.mock import MagicMock, AsyncMock, patch, mock_open, call
from typing import Dict, List, Any, Optional

from concrete.db_decommission.utils import (
    create_db_decommission_workflow,
    run_decommission,
    initialize_environment_with_centralized_secrets,
    create_mcp_config,
    extract_repo_details,
    generate_workflow_id,
    validate_workflow_parameters,
    create_workflow_config,
    calculate_workflow_metrics,
    format_workflow_summary,
    create_logger_adapter
)


class TestCreateDbDecommissionWorkflow:
    """Test create_db_decommission_workflow function."""
    
    @patch('concrete.db_decommission.utils.WorkflowBuilder')
    def test_create_workflow_with_defaults(self, mock_workflow_builder):
        """Test creating workflow with default parameters."""
        # Setup mocks
        mock_builder_instance = MagicMock()
        mock_workflow_builder.return_value = mock_builder_instance
        mock_builder_instance.custom_step.return_value = mock_builder_instance
        mock_builder_instance.with_config.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()
        
        # Execute
        workflow = create_db_decommission_workflow()
        
        # Verify
        mock_workflow_builder.assert_called_once_with(
            "db-decommission",
            "mcp_config.json",
            description="Decommissioning of example_database database with pattern discovery, contextual rules, and comprehensive logging"
        )
        
        # Verify workflow steps are added
        assert mock_builder_instance.custom_step.call_count == 6  # 6 steps in the workflow
        mock_builder_instance.with_config.assert_called_once()
        mock_builder_instance.build.assert_called_once()
    
    @patch('concrete.db_decommission.utils.WorkflowBuilder')
    def test_create_workflow_with_custom_parameters(self, mock_workflow_builder):
        """Test creating workflow with custom parameters."""
        # Setup mocks
        mock_builder_instance = MagicMock()
        mock_workflow_builder.return_value = mock_builder_instance
        mock_builder_instance.custom_step.return_value = mock_builder_instance
        mock_builder_instance.with_config.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()
        
        # Execute
        workflow = create_db_decommission_workflow(
            database_name="custom_db",
            target_repos=["https://github.com/custom/repo"],
            slack_channel="C987654321",
            config_path="custom_config.json",
            workflow_id="custom-workflow-123"
        )
        
        # Verify
        mock_workflow_builder.assert_called_once_with(
            "db-decommission",
            "custom_config.json",
            description="Decommissioning of custom_db database with pattern discovery, contextual rules, and comprehensive logging"
        )
        
        # Verify custom parameters are passed to steps
        step_calls = mock_builder_instance.custom_step.call_args_list
        assert len(step_calls) == 6
        
        # Check that custom parameters are in the step calls
        for call_args in step_calls:
            parameters = call_args[1]["parameters"]
            if "database_name" in parameters:
                assert parameters["database_name"] == "custom_db"
            if "workflow_id" in parameters:
                assert parameters["workflow_id"] == "custom-workflow-123"
    
    @patch('concrete.db_decommission.utils.WorkflowBuilder')
    @patch('concrete.db_decommission.utils.extract_repo_details')
    def test_create_workflow_repo_extraction(self, mock_extract_repo, mock_workflow_builder):
        """Test workflow creation with repository details extraction."""
        # Setup mocks
        mock_extract_repo.return_value = ("test-owner", "test-repo")
        mock_builder_instance = MagicMock()
        mock_workflow_builder.return_value = mock_builder_instance
        mock_builder_instance.custom_step.return_value = mock_builder_instance
        mock_builder_instance.with_config.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()
        
        # Execute
        workflow = create_db_decommission_workflow(
            target_repos=["https://github.com/test-owner/test-repo"]
        )
        
        # Verify
        mock_extract_repo.assert_called_once_with("https://github.com/test-owner/test-repo")
        
        # Verify repo details are passed to relevant steps
        step_calls = mock_builder_instance.custom_step.call_args_list
        repo_specific_steps = [call for call in step_calls if "repo_owner" in call[1]["parameters"]]
        assert len(repo_specific_steps) > 0
        
        for call_args in repo_specific_steps:
            parameters = call_args[1]["parameters"]
            assert parameters["repo_owner"] == "test-owner"
            assert parameters["repo_name"] == "test-repo"


class TestRunDecommission:
    """Test run_decommission function."""
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.utils.create_db_decommission_workflow')
    @patch('concrete.db_decommission.utils.create_mcp_config')
    @patch('concrete.db_decommission.utils.get_logger')
    @patch('concrete.db_decommission.utils.LoggingConfig')
    @patch('builtins.open', new_callable=mock_open)
    async def test_run_decommission_success(self, mock_file, mock_logging_config, mock_get_logger, 
                                           mock_create_config, mock_create_workflow):
        """Test successful decommission run."""
        # Setup mocks
        mock_config = {"mcpServers": {"github": {}}}
        mock_create_config.return_value = mock_config
        
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        
        mock_workflow = MagicMock()
        mock_workflow.execute.return_value = AsyncMock()
        mock_workflow.stop.return_value = AsyncMock()
        mock_create_workflow.return_value = mock_workflow
        
        # Mock workflow result
        mock_result = MagicMock()
        mock_result.status = "completed"
        mock_result.success_rate = 100.0
        mock_result.duration_seconds = 120.5
        mock_result.get_step_result.return_value = {
            "database_name": "test_db",
            "repositories_processed": 1,
            "total_files_processed": 10,
            "total_files_modified": 5
        }
        mock_workflow.execute.return_value = mock_result
        
        # Execute
        result = await run_decommission(
            database_name="test_db",
            target_repos=["https://github.com/test/repo"],
            slack_channel="C123456789"
        )
        
        # Verify
        assert result == mock_result
        mock_create_config.assert_called_once()
        mock_create_workflow.assert_called_once()
        mock_workflow.execute.assert_called_once()
        mock_workflow.stop.assert_called_once()
        
        # Verify config file was written
        mock_file.assert_called_once_with("mcp_config.json", "w")
        handle = mock_file.return_value.__enter__.return_value
        handle.write.assert_called_once()
        
        # Verify logging calls
        mock_logger.log_info.assert_called()
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.utils.create_db_decommission_workflow')
    @patch('concrete.db_decommission.utils.create_mcp_config')
    @patch('concrete.db_decommission.utils.get_logger')
    @patch('concrete.db_decommission.utils.LoggingConfig')
    @patch('builtins.open', new_callable=mock_open)
    async def test_run_decommission_workflow_error(self, mock_file, mock_logging_config, mock_get_logger,
                                                  mock_create_config, mock_create_workflow):
        """Test decommission run with workflow error."""
        # Setup mocks
        mock_config = {"mcpServers": {"github": {}}}
        mock_create_config.return_value = mock_config
        
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        
        mock_workflow = MagicMock()
        mock_workflow.execute.side_effect = Exception("Workflow execution failed")
        mock_workflow.stop.return_value = AsyncMock()
        mock_create_workflow.return_value = mock_workflow
        
        # Execute and verify exception handling
        with pytest.raises(Exception, match="Workflow execution failed"):
            await run_decommission(database_name="test_db")
        
        # Verify cleanup still occurs
        mock_workflow.stop.assert_called_once()
        mock_logger.log_info.assert_called_with("Stopping workflow and cleaning up MCP servers...")


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('concrete.db_decommission.utils.get_parameter_service')
    def test_initialize_environment_with_centralized_secrets(self, mock_get_param_service):
        """Test environment initialization."""
        mock_service = MagicMock()
        mock_get_param_service.return_value = mock_service
        
        result = initialize_environment_with_centralized_secrets()
        
        assert result == mock_service
        mock_get_param_service.assert_called_once()
    
    def test_create_mcp_config(self):
        """Test MCP configuration creation."""
        config = create_mcp_config()
        
        assert isinstance(config, dict)
        assert "mcpServers" in config
        assert "ovr_github" in config["mcpServers"]
        assert "ovr_slack" in config["mcpServers"]
        assert "ovr_repomix" in config["mcpServers"]
        
        # Verify GitHub configuration
        github_config = config["mcpServers"]["ovr_github"]
        assert github_config["command"] == "npx"
        assert github_config["args"] == ["@modelcontextprotocol/server-github"]
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" in github_config["env"]
        
        # Verify Slack configuration
        slack_config = config["mcpServers"]["ovr_slack"]
        assert slack_config["command"] == "npx"
        assert slack_config["args"] == ["@modelcontextprotocol/server-slack"]
        assert "SLACK_BOT_TOKEN" in slack_config["env"]
        
        # Verify Repomix configuration
        repomix_config = config["mcpServers"]["ovr_repomix"]
        assert repomix_config["command"] == "npx"
        assert repomix_config["args"] == ["repomix", "--mcp"]
    
    def test_extract_repo_details_valid_url(self):
        """Test repository details extraction from valid GitHub URL."""
        test_cases = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("https://github.com/owner/repo.git", ("owner", "repo.git")),
            ("https://github.com/owner/repo/", ("owner", "repo")),
            ("https://github.com/owner/repo-with-dashes", ("owner", "repo-with-dashes")),
        ]
        
        for url, expected in test_cases:
            result = extract_repo_details(url)
            assert result == expected
    
    def test_extract_repo_details_invalid_url(self):
        """Test repository details extraction from invalid URLs."""
        test_cases = [
            "https://gitlab.com/owner/repo",
            "https://github.com/owner",
            "https://github.com/",
            "invalid-url",
            "",
        ]
        
        for url in test_cases:
            result = extract_repo_details(url)
            assert result == ("bprzybys-nc", "postgres-sample-dbs")  # Default fallback
    
    def test_generate_workflow_id(self):
        """Test workflow ID generation."""
        database_name = "test_db"
        workflow_id = generate_workflow_id(database_name)
        
        assert workflow_id.startswith("db-test_db-")
        assert len(workflow_id) > len("db-test_db-")
        
        # Verify timestamp component
        timestamp_part = workflow_id.split("-")[-1]
        assert timestamp_part.isdigit()
        assert int(timestamp_part) > 0
    
    def test_validate_workflow_parameters_valid(self):
        """Test workflow parameter validation with valid parameters."""
        result = validate_workflow_parameters(
            database_name="test_db",
            target_repos=["https://github.com/owner/repo"],
            slack_channel="C123456789"
        )
        
        assert result["valid"] is True
        assert result["errors"] == []
    
    def test_validate_workflow_parameters_invalid_database_name(self):
        """Test workflow parameter validation with invalid database name."""
        result = validate_workflow_parameters(
            database_name="",
            target_repos=["https://github.com/owner/repo"],
            slack_channel="C123456789"
        )
        
        assert result["valid"] is False
        assert "Database name cannot be empty" in result["errors"]
    
    def test_validate_workflow_parameters_invalid_repos(self):
        """Test workflow parameter validation with invalid repositories."""
        result = validate_workflow_parameters(
            database_name="test_db",
            target_repos=[],
            slack_channel="C123456789"
        )
        
        assert result["valid"] is False
        assert "At least one target repository must be specified" in result["errors"]
        
        # Test invalid repo URL
        result = validate_workflow_parameters(
            database_name="test_db",
            target_repos=["invalid-url"],
            slack_channel="C123456789"
        )
        
        assert result["valid"] is False
        assert any("Invalid repository URL format" in error for error in result["errors"])
    
    def test_validate_workflow_parameters_invalid_slack_channel(self):
        """Test workflow parameter validation with invalid Slack channel."""
        result = validate_workflow_parameters(
            database_name="test_db",
            target_repos=["https://github.com/owner/repo"],
            slack_channel=""
        )
        
        assert result["valid"] is False
        assert "Slack channel cannot be empty" in result["errors"]
    
    def test_create_workflow_config(self):
        """Test workflow configuration creation."""
        config = create_workflow_config(
            database_name="test_db",
            target_repos=["https://github.com/owner/repo"],
            slack_channel="C123456789",
            workflow_id="test-workflow-123"
        )
        
        assert config["workflow_id"] == "test-workflow-123"
        assert config["database_name"] == "test_db"
        assert config["target_repos"] == ["https://github.com/owner/repo"]
        assert config["slack_channel"] == "C123456789"
        assert config["workflow_version"] == "v2.0"
        assert "created_at" in config
        assert "features" in config
        
        # Test with generated workflow ID
        config_generated = create_workflow_config(
            database_name="test_db",
            target_repos=["https://github.com/owner/repo"],
            slack_channel="C123456789"
        )
        
        assert config_generated["workflow_id"].startswith("db-test_db-")
    
    def test_calculate_workflow_metrics(self):
        """Test workflow metrics calculation."""
        # Mock workflow result
        mock_result = MagicMock()
        mock_result.duration_seconds = 120.5
        mock_result.success_rate = 85.0
        mock_result.steps_completed = 5
        mock_result.total_steps = 6
        mock_result.status = "completed"
        
        # Mock step results
        mock_result.get_step_result.side_effect = lambda step_name, default: {
            "validate_environment": {"success": True, "duration": 10.0},
            "process_repositories": {"success": True, "duration": 60.0},
            "apply_refactoring": {"success": True, "duration": 30.0},
            "create_github_pr": {"success": True, "duration": 15.0},
            "quality_assurance": {"success": False, "duration": 5.0},
            "workflow_summary": {"success": True, "duration": 0.5}
        }.get(step_name, default)
        
        # Execute
        metrics = calculate_workflow_metrics(mock_result)
        
        # Verify
        assert metrics["execution_time"] == 120.5
        assert metrics["success_rate"] == 85.0
        assert metrics["steps_completed"] == 5
        assert metrics["total_steps"] == 6
        assert metrics["status"] == "completed"
        assert "step_metrics" in metrics
        assert len(metrics["step_metrics"]) == 6
    
    def test_format_workflow_summary(self):
        """Test workflow summary formatting."""
        # Mock workflow result
        mock_result = MagicMock()
        mock_result.duration_seconds = 120.5
        mock_result.success_rate = 85.0
        mock_result.steps_completed = 5
        mock_result.total_steps = 6
        mock_result.status = "completed"
        
        # Mock step results
        mock_result.get_step_result.side_effect = lambda step_name, default: {
            "process_repositories": {
                "repositories_processed": 1,
                "total_files_processed": 10,
                "total_files_modified": 5
            }
        }.get(step_name, default)
        
        # Execute
        summary = format_workflow_summary(mock_result, "test_db")
        
        # Verify
        assert isinstance(summary, str)
        assert "test_db" in summary
        assert "completed" in summary
        assert "85.0%" in summary
        assert "120.1s" in summary
        assert "5/6" in summary
        assert "Repositories Processed: 1" in summary
        assert "Files Discovered: 10" in summary
        assert "Files Modified: 5" in summary
    
    @patch('concrete.db_decommission.utils.get_logger')
    @patch('concrete.db_decommission.utils.LoggingConfig')
    def test_create_logger_adapter(self, mock_logging_config, mock_get_logger):
        """Test logger adapter creation."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config = MagicMock()
        mock_logging_config.from_env.return_value = mock_config
        
        # Execute
        logger = create_logger_adapter("test_db")
        
        # Verify
        assert logger == mock_logger
        mock_logging_config.from_env.assert_called_once()
        mock_get_logger.assert_called_once()
        
        # Verify workflow ID format
        call_args = mock_get_logger.call_args
        assert call_args[1]["workflow_id"].startswith("db-decommission-test_db-")
        assert call_args[1]["config"] == mock_config


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]