"""
Unit tests for Demo Runner.

Tests the demo workflow execution, configuration management,
and mock/real mode functionality.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from demo.runner import (
    run_demo_workflow, 
    run_quick_demo, 
    run_live_demo,
    validate_environment_step,
    get_repository_pack_step,
    discover_database_patterns_step,
    generate_refactoring_plan_step
)
from demo.config import DemoConfig
from demo.cache import DemoCache


class TestDemoConfig:
    """Test suite for DemoConfig functionality."""
    
    def test_config_initialization(self):
        """Test DemoConfig initializes correctly."""
        config = DemoConfig(
            mode="mock",
            target_repo="https://github.com/test/repo",
            target_database="test_db"
        )
        
        assert config.mode == "mock"
        assert config.target_repo == "https://github.com/test/repo"
        assert config.target_database == "test_db"
        assert config.cache_dir == "tests/data"
        assert config.is_mock_mode is True
        assert config.is_real_mode is False
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid modes should work
        config = DemoConfig(mode="mock", target_repo="test", target_database="test")
        assert config.mode == "mock"
        
        config = DemoConfig(mode="real", target_repo="test", target_database="test")
        assert config.mode == "real"
        
        # Invalid mode should raise error
        with pytest.raises(ValueError, match="Invalid mode"):
            DemoConfig(mode="invalid", target_repo="test", target_database="test")
    
    def test_config_from_env(self):
        """DemoConfig loads from environment variables."""
        with patch.dict(os.environ, {
            "DEMO_MODE": "real",
            "TARGET_DATABASE": "custom_db",
            "CACHE_TTL": "7200"
        }):
            config = DemoConfig.from_env()
            assert config.mode == "real"
            assert config.target_database == "custom_db"
            assert config.cache_ttl == 7200
    
    def test_config_for_mock_mode(self):
        """Test mock mode configuration factory."""
        config = DemoConfig.for_mock_mode("test_db")
        
        assert config.mode == "mock"
        assert config.target_database == "test_db"
        assert config.quick_mode is True
        assert config.is_mock_mode is True
    
    def test_config_for_real_mode(self):
        """Test real mode configuration factory."""
        config = DemoConfig.for_real_mode("test_db", "https://github.com/test/repo")
        
        assert config.mode == "real"
        assert config.target_database == "test_db"
        assert config.target_repo == "https://github.com/test/repo"
        assert config.quick_mode is False
        assert config.is_real_mode is True
    
    def test_cache_paths(self):
        """Test cache path generation."""
        config = DemoConfig(mode="mock", target_repo="test", target_database="test_db")
        
        repo_path = config.get_repo_cache_path()
        patterns_path = config.get_patterns_cache_path()
        
        assert str(repo_path).endswith("test_db_mock_repo_pack.xml")
        assert str(patterns_path).endswith("test_db_mock_patterns.json")


class TestWorkflowSteps:
    """Test suite for individual workflow steps."""
    
    @pytest.mark.asyncio
    async def test_validate_environment_step(self):
        """Test environment validation step."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        step = Mock()
        
        result = await validate_environment_step(context, step, config=config)
        
        assert result["mode"] == "mock"
        assert result["target_database"] == "test_db"
        assert "cache_dir_exists" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_validate_environment_step_missing_config(self):
        """Test environment validation with missing config."""
        context = Mock()
        step = Mock()
        
        with pytest.raises(ValueError, match="DemoConfig is required"):
            await validate_environment_step(context, step)
    
    @pytest.mark.asyncio
    async def test_get_repository_pack_step_mock(self):
        """Test repository pack step in mock mode."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        step = Mock()
        
        # Mock the cache to return data
        with patch("demo.runner.DemoCache") as mock_cache_class:
            mock_cache = Mock()
            mock_cache.load_repo_cache.return_value = "<xml>mock data</xml>"
            mock_cache_class.return_value = mock_cache
            
            result = await get_repository_pack_step(context, step, config=config)
            
            assert result["status"] == "loaded_from_cache"
            assert result["repo_data"] == "<xml>mock data</xml>"
            assert "data_size" in result
    
    @pytest.mark.asyncio
    async def test_get_repository_pack_step_real(self):
        """Test repository pack step in real mode."""
        config = DemoConfig.for_real_mode("test_db")
        context = Mock()
        step = Mock()
        
        # Mock the cache save operation
        with patch("demo.runner.DemoCache") as mock_cache_class:
            mock_cache = Mock()
            mock_cache.save_repo_cache.return_value = True
            mock_cache_class.return_value = mock_cache
            
            result = await get_repository_pack_step(context, step, config=config)
            
            assert result["status"] == "fetched_live"
            assert "repo_data" in result
            assert "data_size" in result
    
    @pytest.mark.asyncio
    async def test_discover_patterns_step_mock(self):
        """Test pattern discovery step in mock mode."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        context.get_shared_value.return_value = {"status": "loaded_from_cache"}
        step = Mock()
        
        # Mock the cache to return patterns
        with patch("demo.runner.DemoCache") as mock_cache_class:
            mock_cache = Mock()
            mock_cache.load_patterns_cache.return_value = {
                "patterns": [{"type": "test", "file": "test.py"}]
            }
            mock_cache_class.return_value = mock_cache
            
            result = await discover_database_patterns_step(context, step, config=config)
            
            assert result["status"] == "loaded_from_cache"
            assert result["patterns_found"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_refactoring_plan_step(self):
        """Test refactoring plan generation."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        context.get_shared_value.return_value = {"patterns_found": 5}
        step = Mock()
        
        result = await generate_refactoring_plan_step(context, step, config=config)
        
        assert result["status"] == "plan_generated"
        assert result["plan"]["patterns_to_refactor"] == 5
        assert result["plan"]["recommended_approach"] in ["gradual_migration", "direct_removal"]


class TestDemoWorkflowExecution:
    """Test suite for complete demo workflow execution."""
    
    @pytest.mark.asyncio
    async def test_run_quick_demo(self):
        """Demo runs successfully in mock mode."""
        # Mock WorkflowBuilder and execution
        with patch("demo.runner.WorkflowBuilder") as mock_builder_class:
            mock_builder = Mock()
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.status = "completed"
            mock_result.duration_seconds = 1.5
            mock_result.success_rate = 100.0
            
            mock_workflow.execute = AsyncMock(return_value=mock_result)
            mock_builder.custom_step.return_value = mock_builder
            mock_builder.with_config.return_value = mock_builder
            mock_builder.build.return_value = mock_workflow
            mock_builder_class.return_value = mock_builder
            
            # Mock cache operations
            with patch("demo.runner.DemoCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.has_repo_cache.return_value = True
                mock_cache.has_patterns_cache.return_value = True
                mock_cache_class.return_value = mock_cache
                
                result = await run_quick_demo("test_db")
                
                assert result.status == "completed"
                assert result.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_run_demo_workflow_mock_mode(self):
        """Test demo workflow in mock mode."""
        config = DemoConfig.for_mock_mode("test_db")
        
        with patch("demo.runner.WorkflowBuilder") as mock_builder_class:
            # Setup mock workflow execution
            mock_builder = Mock()
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.status = "completed"
            mock_result.steps_completed = 4
            mock_result.steps_failed = 0
            
            mock_workflow.execute = AsyncMock(return_value=mock_result)
            mock_builder.custom_step.return_value = mock_builder
            mock_builder.with_config.return_value = mock_builder
            mock_builder.build.return_value = mock_workflow
            mock_builder_class.return_value = mock_builder
            
            # Mock cache with existing data
            with patch("demo.runner.DemoCache") as mock_cache_class:
                mock_cache = Mock()
                mock_cache.has_repo_cache.return_value = True
                mock_cache.has_patterns_cache.return_value = True
                mock_cache_class.return_value = mock_cache
                
                result = await run_demo_workflow(config)
                
                assert result.status == "completed"
                assert result.steps_completed == 4
    
    @pytest.mark.asyncio
    async def test_run_demo_workflow_real_mode(self):
        """Test demo workflow in real mode."""
        config = DemoConfig.for_real_mode("test_db")
        
        with patch("demo.runner.WorkflowBuilder") as mock_builder_class:
            # Setup mock workflow execution
            mock_builder = Mock()
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.status = "completed"
            mock_result.duration_seconds = 120.0
            
            mock_workflow.execute = AsyncMock(return_value=mock_result)
            mock_builder.custom_step.return_value = mock_builder
            mock_builder.with_config.return_value = mock_builder
            mock_builder.build.return_value = mock_workflow
            mock_builder_class.return_value = mock_builder
            
            result = await run_demo_workflow(config)
            
            assert result.status == "completed"
    
    @pytest.mark.asyncio
    async def test_run_live_demo(self):
        """Test live demo execution."""
        with patch("demo.runner.run_demo_workflow") as mock_run:
            mock_result = Mock()
            mock_result.status = "completed"
            mock_run.return_value = mock_result
            
            result = await run_live_demo("test_db", "https://github.com/test/repo")
            
            assert result.status == "completed"
            # Verify config was created correctly
            call_args = mock_run.call_args[0][0]  # First argument (config)
            assert call_args.mode == "real"
            assert call_args.target_database == "test_db"
            assert call_args.target_repo == "https://github.com/test/repo"


class TestErrorHandling:
    """Test suite for error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_missing_repo_data_in_patterns_step(self):
        """Test pattern discovery when repo data is missing."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        context.get_shared_value.return_value = None  # No repo data
        step = Mock()
        
        with pytest.raises(ValueError, match="Repository data not available"):
            await discover_database_patterns_step(context, step, config=config)
    
    @pytest.mark.asyncio
    async def test_missing_patterns_in_refactoring_step(self):
        """Test refactoring plan generation when patterns are missing."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        context.get_shared_value.return_value = None  # No patterns
        step = Mock()
        
        with pytest.raises(ValueError, match="Pattern data not available"):
            await generate_refactoring_plan_step(context, step, config=config)
    
    @pytest.mark.asyncio
    async def test_mock_mode_missing_cache(self):
        """Test mock mode when cache data is missing."""
        config = DemoConfig.for_mock_mode("test_db")
        context = Mock()
        step = Mock()
        
        # Mock cache to return None (no data)
        with patch("demo.runner.DemoCache") as mock_cache_class:
            mock_cache = Mock()
            mock_cache.load_repo_cache.return_value = None
            mock_cache_class.return_value = mock_cache
            
            with pytest.raises(ValueError, match="Mock mode requested but no cached repo data found"):
                await get_repository_pack_step(context, step, config=config)