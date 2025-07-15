"""
Comprehensive unit tests for Database Decommissioning Workflow - Main Module

Tests the main workflow orchestration module with:
- Main entry point function
- Backward compatibility
- Module integration
- Error handling scenarios

Note: This test file focuses on the main module integration.
Individual modules have separate test files:
- test_db_decommission_data_models.py
- test_db_decommission_validation_helpers.py
- test_db_decommission_utils.py
- test_db_decommission_pattern_discovery.py
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch, call
from typing import Dict, List, Any

# Import the new modular structure
from concrete.db_decommission import (
    main,
    create_db_decommission_workflow,
    run_decommission,
    initialize_environment_with_centralized_secrets,
    FileProcessingResult,
    WorkflowConfig,
    QualityAssuranceResult,
    ValidationResult,
    DecommissioningSummary,
    WorkflowStepResult,
    validate_environment_step,
    process_repositories_step,
    quality_assurance_step,
    apply_refactoring_step,
    create_github_pr_step,
    workflow_summary_step,
    AgenticFileProcessor,
    create_mcp_config,
    extract_repo_details,
    generate_workflow_id
)


class TestMainModule:
    """Test main module integration and entry points."""
    
    def test_module_imports(self):
        """Test that all expected exports are available."""
        # Test that main function exists
        assert callable(main)
        
        # Test that workflow functions exist
        assert callable(create_db_decommission_workflow)
        assert callable(run_decommission)
        assert callable(initialize_environment_with_centralized_secrets)
        
        # Test that data models exist
        assert FileProcessingResult is not None
        assert WorkflowConfig is not None
        assert QualityAssuranceResult is not None
        assert ValidationResult is not None
        assert DecommissioningSummary is not None
        assert WorkflowStepResult is not None
        
        # Test that workflow steps exist
        assert callable(validate_environment_step)
        assert callable(process_repositories_step)
        assert callable(quality_assurance_step)
        assert callable(apply_refactoring_step)
        assert callable(create_github_pr_step)
        assert callable(workflow_summary_step)
        
        # Test that pattern discovery exists
        assert AgenticFileProcessor is not None
        
        # Test that utilities exist
        assert callable(create_mcp_config)
        assert callable(extract_repo_details)
        assert callable(generate_workflow_id)
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.run_decommission')
    @patch('concrete.db_decommission.format_workflow_summary')
    @patch('logging.basicConfig')
    async def test_main_function_success(self, mock_logging, mock_format_summary, mock_run_decommission):
        """Test successful main function execution."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.status = "completed"
        mock_result.success_rate = 100.0
        mock_run_decommission.return_value = mock_result
        
        mock_format_summary.return_value = "Workflow completed successfully"
        
        # Execute
        result = await main()
        
        # Verify
        assert result == mock_result
        mock_run_decommission.assert_called_once_with(
            database_name="postgres_air",
            target_repos=["https://github.com/bprzybys-nc/postgres-sample-dbs"],
            slack_channel="C01234567"
        )
        mock_format_summary.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.run_decommission')
    @patch('logging.basicConfig')
    async def test_main_function_error(self, mock_logging, mock_run_decommission):
        """Test main function with error handling."""
        # Setup mocks
        mock_run_decommission.side_effect = Exception("Workflow failed")
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Workflow failed"):
            await main()
        
        # Verify run_decommission was called
        mock_run_decommission.assert_called_once()
    
    @patch('concrete.db_decommission.get_parameter_service')
    def test_initialize_environment_with_centralized_secrets(self, mock_get_param_service):
        """Test environment initialization with parameter service."""
        mock_service = MagicMock()
        mock_get_param_service.return_value = mock_service
        
        result = initialize_environment_with_centralized_secrets()
        
        mock_get_param_service.assert_called_once()
        assert result == mock_service
    
    def test_create_mcp_config(self):
        """Test MCP configuration creation."""
        config = create_mcp_config()
        
        assert isinstance(config, dict)
        assert "mcpServers" in config
        assert "ovr_github" in config["mcpServers"]
        assert "ovr_slack" in config["mcpServers"]
        assert "ovr_repomix" in config["mcpServers"]
    
    def test_extract_repo_details(self):
        """Test repository details extraction."""
        # Test valid GitHub URL
        owner, repo = extract_repo_details("https://github.com/test/repo")
        assert owner == "test"
        assert repo == "repo"
        
        # Test invalid URL (should return default)
        owner, repo = extract_repo_details("invalid-url")
        assert owner == "bprzybys-nc"
        assert repo == "postgres-sample-dbs"
    
    def test_generate_workflow_id(self):
        """Test workflow ID generation."""
        workflow_id = generate_workflow_id("test_db")
        
        assert workflow_id.startswith("db-test_db-")
        assert len(workflow_id) > len("db-test_db-")
        
        # Should be unique
        workflow_id2 = generate_workflow_id("test_db")
        assert workflow_id != workflow_id2


class TestBackwardCompatibility:
    """Test backward compatibility with legacy interfaces."""
    
    def test_legacy_imports_available(self):
        """Test that legacy imports are still available."""
        # These should still work for backward compatibility
        from concrete.db_decommission import (
            create_db_decommission_workflow,
            run_decommission,
            initialize_environment_with_centralized_secrets
        )
        
        assert callable(create_db_decommission_workflow)
        assert callable(run_decommission)
        assert callable(initialize_environment_with_centralized_secrets)
    
    @patch('concrete.db_decommission.utils.WorkflowBuilder')
    def test_create_db_decommission_workflow_compatibility(self, mock_workflow_builder):
        """Test workflow creation maintains backward compatibility."""
        # Setup mocks
        mock_builder_instance = MagicMock()
        mock_workflow_builder.return_value = mock_builder_instance
        mock_builder_instance.custom_step.return_value = mock_builder_instance
        mock_builder_instance.with_config.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()
        
        # Execute with legacy-style call
        workflow = create_db_decommission_workflow(
            database_name="test_db",
            target_repos=["https://github.com/test/repo"]
        )
        
        # Verify workflow was created
        mock_workflow_builder.assert_called_once()
        mock_builder_instance.build.assert_called_once()


class TestModuleIntegration:
    """Test integration between modules."""
    
    def test_data_models_integration(self):
        """Test that data models can be created and used."""
        # Test FileProcessingResult
        from concrete.source_type_classifier import SourceType
        
        result = FileProcessingResult(
            file_path="test.py",
            source_type=SourceType.PYTHON,
            success=True,
            total_changes=5
        )
        
        assert result.file_path == "test.py"
        assert result.source_type == SourceType.PYTHON
        assert result.success is True
        assert result.total_changes == 5
        
        # Test serialization
        dict_result = result.to_dict()
        assert isinstance(dict_result, dict)
        assert dict_result["file_path"] == "test.py"
        
        # Test deserialization
        restored = FileProcessingResult.from_dict(dict_result)
        assert restored.file_path == result.file_path
        assert restored.source_type == result.source_type
    
    def test_validation_result_enum(self):
        """Test ValidationResult enum integration."""
        assert ValidationResult.PASSED.value == "PASSED"
        assert ValidationResult.WARNING.value == "WARNING"
        assert ValidationResult.FAILED.value == "FAILED"
    
    @patch('concrete.db_decommission.pattern_discovery.get_logger')
    def test_agentic_file_processor_integration(self, mock_get_logger):
        """Test AgenticFileProcessor can be instantiated."""
        from concrete.source_type_classifier import SourceTypeClassifier
        
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Create processor
        processor = AgenticFileProcessor(
            source_classifier=SourceTypeClassifier(),
            contextual_rules_engine=MagicMock(),
            github_client=MagicMock(),
            repo_owner="test",
            repo_name="repo"
        )
        
        assert processor.repo_owner == "test"
        assert processor.repo_name == "repo"
        assert processor.logger is not None


class TestWorkflowStepFunctions:
    """Test workflow step functions are accessible."""
    
    def test_workflow_step_functions_callable(self):
        """Test that all workflow step functions are callable."""
        step_functions = [
            validate_environment_step,
            process_repositories_step,
            quality_assurance_step,
            apply_refactoring_step,
            create_github_pr_step,
            workflow_summary_step
        ]
        
        for func in step_functions:
            assert callable(func)
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.validation_helpers.get_logger')
    @patch('concrete.db_decommission.validation_helpers.LoggingConfig')
    async def test_validate_environment_step_callable(self, mock_logging_config, mock_get_logger):
        """Test that validate_environment_step can be called."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        
        mock_context = MagicMock()
        mock_step = MagicMock()
        
        # Execute
        result = await validate_environment_step(
            mock_context,
            mock_step,
            database_name="test_db"
        )
        
        # Verify
        assert isinstance(result, dict)
        assert "database_name" in result
        assert result["database_name"] == "test_db"
        assert "success" in result
        assert "duration" in result


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.utils.create_db_decommission_workflow')
    @patch('concrete.db_decommission.utils.create_mcp_config')
    @patch('concrete.db_decommission.utils.get_logger')
    @patch('concrete.db_decommission.utils.LoggingConfig')
    async def test_run_decommission_with_workflow_error(self, mock_logging_config, mock_get_logger, 
                                                        mock_create_config, mock_create_workflow):
        """Test run_decommission with workflow execution error."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        mock_create_config.return_value = {}
        
        mock_workflow = MagicMock()
        mock_workflow.execute.side_effect = Exception("Workflow execution failed")
        mock_workflow.stop.return_value = AsyncMock()
        mock_create_workflow.return_value = mock_workflow
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Workflow execution failed"):
            await run_decommission(database_name="test_db")
        
        # Verify cleanup was called
        mock_workflow.stop.assert_called_once()


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]