"""
Unit tests for Enhanced Database Decommissioning Workflow

Tests the enhanced components that replace the basic workflow with:
- AI-powered pattern discovery
- Source type classification
- Contextual rules engine
- Performance optimization
- Comprehensive logging
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, call
from datetime import datetime

from concrete.enhanced_db_decommission import (
    validate_environment_step,
    process_repositories_step, 
    quality_assurance_step,
    workflow_summary_step,
    run_decommission
)
from concrete.parameter_service import ParameterService
from concrete.workflow_logger import DatabaseWorkflowLogger
from concrete.monitoring import MonitoringSystem
from concrete.error_handling import ErrorHandler
from concrete.performance_optimization import PerformanceManager


class MockContext:
    """Mock workflow context for testing."""
    
    def __init__(self):
        self.shared_values = {}
        self._step_results = {}
        self.config = MagicMock()
        self.config.config_path = "test_config.json"
    
    def set_shared_value(self, key: str, value):
        self.shared_values[key] = value
    
    def get_shared_value(self, key: str, default=None):
        return self.shared_values.get(key, default)
    
    def get_step_result(self, step_name: str):
        return self._step_results.get(step_name)
    
    def set_step_result(self, step_name: str, result):
        self._step_results[step_name] = result


class TestValidateEnvironmentStep:
    """Test the enhanced environment validation step."""
    
    @pytest.fixture
    def mock_context(self):
        return MockContext()
    
    @pytest.fixture  
    def mock_step(self):
        step = MagicMock()
        step.parameters = {
            'database_name': 'test_database',
            'repository_owner': 'test_owner',
            'repository_name': 'test_repo'
        }
        return step
    
    @pytest.mark.asyncio
    async def test_validate_environment_success(self, mock_context, mock_step):
        """Test successful environment validation."""
        with patch('concrete.enhanced_db_decommission.ParameterService') as mock_param_service, \
             patch('concrete.enhanced_db_decommission.MonitoringSystem') as mock_monitoring, \
             patch('concrete.enhanced_db_decommission.ErrorHandler') as mock_error_handler:
            
            # Configure mocks
            mock_param_service.return_value.validate_environment.return_value = True
            mock_param_service.return_value.get_parameter.side_effect = lambda key, default=None: {
                'GITHUB_TOKEN': 'test_token',
                'DATABASE_NAME': 'test_database'
            }.get(key, default)
            
            mock_monitoring.return_value.perform_health_checks.return_value = {
                'overall_health': 'HEALTHY',
                'checks': {'memory': 'PASS', 'cpu': 'PASS'}
            }
            
            # Execute the step
            result = await validate_environment_step(mock_context, mock_step)
            
            # Verify results
            assert result['success'] is True
            assert result['validation_status'] == 'PASSED'
            assert 'health_check' in result
            assert 'duration' in result
            assert 'start_time' in result
            
            # Verify parameter service was called
            mock_param_service.return_value.validate_environment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_environment_validation_failure(self, mock_context, mock_step):
        """Test environment validation failure."""
        with patch('concrete.enhanced_db_decommission.ParameterService') as mock_param_service:
            mock_param_service.return_value.validate_environment.return_value = False
            
            result = await validate_environment_step(mock_context, mock_step)
            
            assert result['success'] is False
            assert result['validation_status'] == 'FAILED'
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_validate_environment_exception_handling(self, mock_context, mock_step):
        """Test exception handling in environment validation."""
        with patch('concrete.enhanced_db_decommission.ParameterService') as mock_param_service:
            mock_param_service.side_effect = Exception("Configuration error")
            
            result = await validate_environment_step(mock_context, mock_step)
            
            assert result['success'] is False
            assert 'Configuration error' in result['error']


class TestProcessRepositoriesStep:
    """Test the enhanced repository processing step."""
    
    @pytest.fixture
    def mock_context(self):
        context = MockContext()
        context.set_shared_value('database_name', 'test_database')
        context.set_shared_value('repository_owner', 'test_owner')
        context.set_shared_value('repository_name', 'test_repo')
        return context
    
    @pytest.fixture
    def mock_step(self):
        step = MagicMock()
        step.parameters = {'parallel_processing': True}
        return step
    
    @pytest.mark.asyncio
    async def test_process_repositories_success(self, mock_context, mock_step):
        """Test successful repository processing."""
        with patch('concrete.enhanced_db_decommission.enhanced_discover_patterns_step') as mock_patterns, \
             patch('concrete.enhanced_db_decommission.PerformanceManager') as mock_perf:
            
            # Mock pattern discovery
            mock_patterns.return_value = {
                'success': True,
                'files_found': ['file1.py', 'file2.sql'],
                'patterns_discovered': ['pattern1', 'pattern2'],
                'processing_approach': 'hybrid'
            }
            
            # Mock performance manager
            mock_perf.return_value.process_repositories_parallel.return_value = {
                'processed_repositories': 1,
                'total_files': 2,
                'performance_score': 0.95
            }
            
            result = await process_repositories_step(mock_context, mock_step)
            
            assert result['success'] is True
            assert result['files_found'] == ['file1.py', 'file2.sql']
            assert result['patterns_discovered'] == ['pattern1', 'pattern2']
            assert 'duration' in result
            
            # Verify pattern discovery was called
            mock_patterns.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_repositories_pattern_failure(self, mock_context, mock_step):
        """Test handling of pattern discovery failure."""
        with patch('concrete.enhanced_db_decommission.enhanced_discover_patterns_step') as mock_patterns:
            mock_patterns.return_value = {
                'success': False,
                'error': 'Pattern discovery failed'
            }
            
            result = await process_repositories_step(mock_context, mock_step)
            
            assert result['success'] is False
            assert 'Pattern discovery failed' in result['error']


class TestQualityAssuranceStep:
    """Test the enhanced quality assurance step."""
    
    @pytest.fixture
    def mock_context(self):
        context = MockContext()
        context.set_step_result('process_repositories', {
            'files_found': ['file1.py', 'file2.sql'],
            'patterns_discovered': ['pattern1', 'pattern2'],
            'processing_approach': 'hybrid'
        })
        return context
    
    @pytest.fixture
    def mock_step(self):
        return MagicMock()
    
    @pytest.mark.asyncio
    async def test_quality_assurance_success(self, mock_context, mock_step):
        """Test successful quality assurance."""
        with patch('concrete.enhanced_db_decommission.ContextualRulesEngine') as mock_rules:
            mock_rules.return_value.validate_processing_results.return_value = {
                'validation_passed': True,
                'quality_score': 0.92,
                'recommendations': ['recommendation1']
            }
            
            result = await quality_assurance_step(mock_context, mock_step)
            
            assert result['success'] is True
            assert result['validation_passed'] is True
            assert result['quality_score'] == 0.92
            assert 'duration' in result
    
    @pytest.mark.asyncio
    async def test_quality_assurance_validation_failure(self, mock_context, mock_step):
        """Test quality assurance validation failure."""
        with patch('concrete.enhanced_db_decommission.ContextualRulesEngine') as mock_rules:
            mock_rules.return_value.validate_processing_results.return_value = {
                'validation_passed': False,
                'quality_score': 0.45,
                'issues': ['Low pattern coverage']
            }
            
            result = await quality_assurance_step(mock_context, mock_step)
            
            assert result['success'] is True  # Step succeeds but validation fails
            assert result['validation_passed'] is False
            assert result['quality_score'] == 0.45


class TestWorkflowSummaryStep:
    """Test the enhanced workflow summary step."""
    
    @pytest.fixture
    def mock_context(self):
        context = MockContext()
        context.set_step_result('validate_environment', {'success': True})
        context.set_step_result('process_repositories', {
            'success': True,
            'files_found': ['file1.py', 'file2.sql']
        })
        context.set_step_result('quality_assurance', {
            'success': True,
            'validation_passed': True,
            'quality_score': 0.92
        })
        return context
    
    @pytest.fixture
    def mock_step(self):
        return MagicMock()
    
    @pytest.mark.asyncio
    async def test_workflow_summary_success(self, mock_context, mock_step):
        """Test successful workflow summary generation."""
        result = await workflow_summary_step(mock_context, mock_step)
        
        assert result['success'] is True
        assert result['total_steps_completed'] == 3
        assert result['overall_success'] is True
        assert result['files_processed'] == 2
        assert 'execution_summary' in result
        assert 'duration' in result
    
    @pytest.mark.asyncio
    async def test_workflow_summary_with_failures(self, mock_context, mock_step):
        """Test workflow summary with step failures."""
        # Add a failed step
        mock_context.set_step_result('process_repositories', {
            'success': False,
            'error': 'Processing failed'
        })
        
        result = await workflow_summary_step(mock_context, mock_step)
        
        assert result['success'] is True  # Summary step itself succeeds
        assert result['overall_success'] is False  # But overall workflow failed
        assert 'failures' in result
        assert len(result['failures']) > 0


class TestRunDecommission:
    """Test the main run_decommission function."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            "mcpServers": {
                "test_server": {
                    "command": "echo",
                    "args": ["test"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_run_decommission_success(self, temp_config_file):
        """Test successful execution of the decommission workflow."""
        with patch('concrete.enhanced_db_decommission.WorkflowBuilder') as mock_builder, \
             patch('concrete.enhanced_db_decommission.DatabaseWorkflowLogger') as mock_logger:
            
            # Mock workflow execution
            mock_workflow = MagicMock()
            mock_workflow.execute.return_value = {
                'success': True,
                'results': {
                    'validate_environment': {'success': True},
                    'process_repositories': {'success': True, 'files_found': ['test.py']},
                    'quality_assurance': {'success': True},
                    'workflow_summary': {'success': True}
                }
            }
            
            mock_builder.return_value.add_step.return_value = mock_builder.return_value
            mock_builder.return_value.build.return_value = mock_workflow
            
            # Execute
            result = await run_decommission(
                config_path=temp_config_file,
                database_name='test_db',
                repository_owner='test_owner',
                repository_name='test_repo'
            )
            
            assert result['success'] is True
            assert 'workflow_results' in result
            
            # Verify workflow was built and executed
            mock_builder.assert_called_once()
            mock_workflow.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_decommission_with_custom_params(self, temp_config_file):
        """Test decommission with custom parameters."""
        with patch('concrete.enhanced_db_decommission.WorkflowBuilder') as mock_builder:
            mock_workflow = MagicMock()
            mock_workflow.execute.return_value = {'success': True, 'results': {}}
            mock_builder.return_value.add_step.return_value = mock_builder.return_value
            mock_builder.return_value.build.return_value = mock_workflow
            
            result = await run_decommission(
                config_path=temp_config_file,
                database_name='custom_db',
                repository_owner='custom_owner',
                repository_name='custom_repo',
                enable_notifications=True,
                parallel_processing=False,
                timeout_minutes=30
            )
            
            # Verify parameters were passed to workflow steps
            call_args = mock_builder.return_value.add_step.call_args_list
            
            # Check that custom parameters were used
            assert any('custom_db' in str(args) for args, kwargs in call_args)
            
    @pytest.mark.asyncio
    async def test_run_decommission_workflow_failure(self, temp_config_file):
        """Test handling of workflow execution failure."""
        with patch('concrete.enhanced_db_decommission.WorkflowBuilder') as mock_builder:
            mock_workflow = MagicMock()
            mock_workflow.execute.side_effect = Exception("Workflow execution failed")
            mock_builder.return_value.add_step.return_value = mock_builder.return_value
            mock_builder.return_value.build.return_value = mock_workflow
            
            result = await run_decommission(
                config_path=temp_config_file,
                database_name='test_db',
                repository_owner='test_owner',
                repository_name='test_repo'
            )
            
            assert result['success'] is False
            assert 'Workflow execution failed' in result['error']


class TestIntegrationScenarios:
    """Test integration scenarios between enhanced components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_enhanced_workflow(self):
        """Test end-to-end enhanced workflow integration."""
        with patch('concrete.enhanced_db_decommission.ParameterService') as mock_params, \
             patch('concrete.enhanced_db_decommission.MonitoringSystem') as mock_monitoring, \
             patch('concrete.enhanced_db_decommission.enhanced_discover_patterns_step') as mock_patterns, \
             patch('concrete.enhanced_db_decommission.ContextualRulesEngine') as mock_rules:
            
            # Setup mocks for full workflow
            mock_params.return_value.validate_environment.return_value = True
            mock_params.return_value.get_parameter.return_value = 'test_value'
            
            mock_monitoring.return_value.perform_health_checks.return_value = {
                'overall_health': 'HEALTHY'
            }
            
            mock_patterns.return_value = {
                'success': True,
                'files_found': ['test.py'],
                'patterns_discovered': ['test_pattern']
            }
            
            mock_rules.return_value.validate_processing_results.return_value = {
                'validation_passed': True,
                'quality_score': 0.9
            }
            
            # Create context and execute all steps
            context = MockContext()
            context.set_shared_value('database_name', 'test_db')
            
            # Execute workflow steps in sequence
            env_result = await validate_environment_step(context, MagicMock())
            context.set_step_result('validate_environment', env_result)
            
            repo_result = await process_repositories_step(context, MagicMock())
            context.set_step_result('process_repositories', repo_result)
            
            qa_result = await quality_assurance_step(context, MagicMock())
            context.set_step_result('quality_assurance', qa_result)
            
            summary_result = await workflow_summary_step(context, MagicMock())
            
            # Verify all steps succeeded
            assert env_result['success'] is True
            assert repo_result['success'] is True
            assert qa_result['success'] is True
            assert summary_result['success'] is True
            assert summary_result['overall_success'] is True 