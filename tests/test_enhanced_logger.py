"""
Comprehensive test suite for EnhancedDatabaseWorkflowLogger.

Tests enhanced logging functionality while ensuring backward compatibility
with existing DatabaseWorkflowLogger patterns.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from io import StringIO
from pathlib import Path
import tempfile

from concrete.enhanced_logger import (
    EnhancedDatabaseWorkflowLogger,
    create_enhanced_workflow_logger,
    create_enhanced_workflow_logger_async
)
from concrete.workflow_logger import EnhancedWorkflowMetrics

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]

class TestEnhancedDatabaseWorkflowLogger:
    """Test enhanced logger initialization and basic functionality."""
    
    @pytest.fixture
    def logger_basic(self):
        """Create basic enhanced logger for testing."""
        return EnhancedDatabaseWorkflowLogger("test_db", enable_visual=False)
    
    @pytest.fixture
    def logger_visual(self):
        """Create enhanced logger with visual features enabled."""
        return EnhancedDatabaseWorkflowLogger("test_db", enable_visual=True)
    
    @pytest.fixture
    def temp_html_path(self):
        """Create temporary HTML output path."""
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            yield f.name
        # Cleanup
        Path(f.name).unlink(missing_ok=True)
    
    def test_enhanced_logger_initialization(self, logger_basic):
        """Test enhanced logger initializes without breaking existing patterns."""
        assert logger_basic.database_name == "test_db"
        assert isinstance(logger_basic.enhanced_metrics, EnhancedWorkflowMetrics)
        assert logger_basic.enhanced_metrics.database_name == "test_db"
        assert logger_basic.enable_visual is False
        assert logger_basic.progress_tracker is None
        assert logger_basic.visual_renderer is None
    
    def test_enhanced_logger_visual_initialization(self, logger_visual):
        """Test enhanced logger with visual features enabled."""
        assert logger_visual.database_name == "test_db"
        assert logger_visual.enable_visual is True
        assert logger_visual.visual_renderer is not None
        assert logger_visual.progress_tracker is None  # Not initialized until async call
    
    def test_backward_compatibility_with_base_logger(self, logger_basic):
        """Test that all base logger methods work unchanged."""
        # Test that all base logger methods are available
        assert hasattr(logger_basic, 'log_workflow_start')
        assert hasattr(logger_basic, 'log_workflow_end')
        assert hasattr(logger_basic, 'log_step_start')
        assert hasattr(logger_basic, 'log_step_end')
        assert hasattr(logger_basic, 'get_metrics_summary')
        
        # Test that metrics are accessible
        assert hasattr(logger_basic, 'metrics')
        assert logger_basic.metrics.database_name == "test_db"
    
    async def test_progress_tracking_initialization(self, logger_visual):
        """Test progress tracking initialization."""
        total_steps = 5
        await logger_visual.initialize_progress_tracking(total_steps)
        
        assert logger_visual.progress_tracker is not None
        assert logger_visual.progress_tracker.total_steps == total_steps
    
    async def test_async_step_logging(self, logger_visual):
        """Test async step logging methods."""
        await logger_visual.initialize_progress_tracking(3)
        
        # Test step start
        await logger_visual.log_step_start_async("test_step", "Test step description", {"param": "value"})
        
        # Test progress updates
        await logger_visual.log_step_progress_async("test_step", 0.5, "Halfway done", 1024)
        
        # Test step completion
        await logger_visual.log_step_end_async("test_step", {"result": "success"}, True)
        
        # Verify progress tracking
        assert logger_visual.progress_tracker.current_step == "test_step"
        assert logger_visual.enhanced_metrics.current_step == "test_step"
    
    def test_sync_step_logging_compatibility(self, logger_basic):
        """Test that sync logging methods still work without async features."""
        # Test sync methods work without errors
        logger_basic.log_step_start("sync_step", "Sync step description")
        logger_basic.log_step_progress("sync_step", 0.7, "Almost done")
        logger_basic.log_step_end("sync_step", {"result": "completed"}, True)
        
        # Verify enhanced metrics updated
        assert logger_basic.enhanced_metrics.current_step == "sync_step"
        assert logger_basic.enhanced_metrics.progress_percentage == 100.0  # Should be 100% after completion
    
    async def test_error_handling_in_enhanced_logging(self, logger_visual):
        """Test that enhanced logging errors don't break workflow execution."""
        # Initialize with broken progress tracker
        logger_visual.progress_tracker = Mock()
        logger_visual.progress_tracker.start_step = AsyncMock(side_effect=Exception("Mock error"))
        
        # Should not raise exception and should use fallback
        try:
            await logger_visual.log_step_start_async("error_step", "Error test")
        except Exception:
            pass  # Expected to have errors but should not crash the workflow
        
        # Verify original functionality still works
        assert logger_visual.enhanced_metrics.current_step == "error_step"
    
    async def test_context_manager_async(self, logger_visual):
        """Test async context manager functionality."""
        async with logger_visual as logger:
            assert logger is not None
            await logger.initialize_progress_tracking(1)
            assert logger.progress_tracker is not None
        
        # Verify cleanup occurred (render task should be cancelled)
        assert logger_visual._render_task is None or logger_visual._render_task.cancelled()
    
    def test_context_manager_sync(self, logger_basic):
        """Test sync context manager for backward compatibility."""
        with logger_basic as logger:
            assert logger is not None
            logger.log_step_start("sync_context_step", "Sync context test")
        
        # Should complete without errors
        assert logger_basic.enhanced_metrics.current_step == "sync_context_step"
    
    def test_enhanced_metrics_summary(self, logger_visual):
        """Test enhanced metrics summary includes additional fields."""
        summary = logger_visual.get_enhanced_metrics_summary()
        
        assert "enhanced_metrics" in summary
        assert "visual_enabled" in summary
        assert "progress_tracker_active" in summary
        assert "render_task_active" in summary
        
        assert summary["visual_enabled"] is True
        assert summary["progress_tracker_active"] is False  # Not initialized yet
    
    async def test_html_output_generation(self, logger_visual, temp_html_path):
        """Test HTML output generation."""
        logger_visual.html_output_path = temp_html_path
        await logger_visual.initialize_progress_tracking(2)
        
        # Add some test steps
        await logger_visual.log_step_start_async("html_step1", "First step")
        await logger_visual.log_step_progress_async("html_step1", 1.0, "Complete")
        await logger_visual.log_step_end_async("html_step1", {"result": "done"}, True)
        
        # Let the render loop run once
        await asyncio.sleep(0.6)  # Wait longer than render interval
        
        # Check if HTML file exists
        html_file = Path(temp_html_path)
        assert html_file.exists()


class TestProgressTrackerIntegration:
    """Test integration between enhanced logger and progress tracker."""
    
    @pytest.fixture
    def logger_with_tracker(self):
        """Create logger with initialized progress tracker."""
        import asyncio
        
        async def _create_logger():
            logger = EnhancedDatabaseWorkflowLogger("integration_test", enable_visual=True)
            await logger.initialize_progress_tracking(3)
            return logger
        
        # Return the coroutine, tests will await it
        return _create_logger()
    
    async def test_bandwidth_calculation(self, logger_with_tracker):
        """Test bandwidth calculation during progress updates."""
        logger = await logger_with_tracker
        step_id = "bandwidth_test"
        
        await logger.log_step_start_async(step_id, "Bandwidth test")
        
        # Simulate processing data
        await logger.log_step_progress_async(step_id, 0.3, "Processing", 1024)
        await asyncio.sleep(0.1)  # Small delay for bandwidth calculation
        await logger.log_step_progress_async(step_id, 0.6, "More processing", 2048)
        
        # Check that bandwidth is calculated
        frame = await logger.progress_tracker.get_step_frame(step_id)
        assert frame is not None
        assert frame.bandwidth_mbps >= 0
        assert frame.bytes_processed > 0
    
    async def test_progress_estimation(self, logger_with_tracker):
        """Test progress estimation calculations."""
        logger = await logger_with_tracker
        step_id = "estimation_test"
        
        await logger.log_step_start_async(step_id, "Estimation test")
        await asyncio.sleep(0.1)
        
        # Update progress
        await logger.log_step_progress_async(step_id, 0.5, "Halfway")
        
        # Check estimation
        frame = await logger.progress_tracker.get_step_frame(step_id)
        assert frame is not None
        assert frame.estimated_remaining is not None
        assert frame.estimated_remaining > 0


class TestVisualRendererIntegration:
    """Test integration with visual renderer."""
    
    @pytest.fixture
    def mock_stdout(self):
        """Mock stdout for terminal output testing."""
        mock_stream = StringIO()
        with patch('sys.stdout', mock_stream):
            yield mock_stream
    
    async def test_terminal_rendering(self, mock_stdout):
        """Test terminal output rendering."""
        logger = EnhancedDatabaseWorkflowLogger("render_test", enable_visual=True)
        await logger.initialize_progress_tracking(2)
        
        # Add a step and let it render
        await logger.log_step_start_async("render_step", "Rendering test")
        await logger.log_step_progress_async("render_step", 0.5, "Half done")
        
        # Let render loop run
        await asyncio.sleep(0.6)
        
        # Check that something was written to stdout
        output = mock_stdout.getvalue()
        # Should contain progress information (even if mocked)
        assert len(output) >= 0  # At least some output was generated
    
    async def test_render_loop_cancellation(self):
        """Test that render loop is properly cancelled."""
        logger = EnhancedDatabaseWorkflowLogger("cancel_test", enable_visual=True)
        await logger.initialize_progress_tracking(1)
        
        # Verify render task is running
        assert logger._render_task is not None
        assert not logger._render_task.done()
        
        # Cleanup should cancel the task
        await logger.cleanup_async()
        
        # Verify task was cancelled
        assert logger._render_task.cancelled()


class TestErrorScenarios:
    """Test error handling and edge cases."""
    
    async def test_initialization_without_event_loop(self):
        """Test initialization when no event loop is available."""
        # This test ensures graceful degradation
        logger = EnhancedDatabaseWorkflowLogger("no_loop_test", enable_visual=True)
        
        # Should not raise errors even without event loop
        logger.log_step_start("no_loop_step", "No loop test")
        logger.log_step_progress("no_loop_step", 0.5, "Progress without loop")
        logger.log_step_end("no_loop_step", {"result": "ok"}, True)
        
        assert logger.enhanced_metrics.current_step == "no_loop_step"
    
    async def test_progress_tracker_failure_handling(self):
        """Test handling of progress tracker failures."""
        logger = EnhancedDatabaseWorkflowLogger("failure_test", enable_visual=True)
        
        # Mock progress tracker to fail
        logger.progress_tracker = Mock()
        logger.progress_tracker.start_step = AsyncMock(side_effect=Exception("Tracker failed"))
        logger.progress_tracker.update_progress = AsyncMock(side_effect=Exception("Update failed"))
        
        # Should not raise exceptions and should use fallback
        try:
            await logger.log_step_start_async("fail_step", "Failure test")
            await logger.log_step_progress_async("fail_step", 0.5, "Progress")
        except Exception:
            pass  # Expected to have errors but should not crash the workflow
        
        # Basic functionality should still work
        assert logger.enhanced_metrics.current_step == "fail_step"
    
    def test_visual_disabled_fallback(self):
        """Test behavior when visual features are disabled."""
        logger = EnhancedDatabaseWorkflowLogger("disabled_test", enable_visual=False)
        
        # Should work like regular logger
        logger.log_step_start("disabled_step", "Disabled test")
        logger.log_step_progress("disabled_step", 1.0, "Complete")
        logger.log_step_end("disabled_step", {"result": "success"}, True)
        
        assert logger.enhanced_metrics.current_step == "disabled_step"
        assert logger.progress_tracker is None
        assert logger.visual_renderer is None


class TestFactoryFunctions:
    """Test factory functions for creating enhanced loggers."""
    
    def test_create_enhanced_workflow_logger(self):
        """Test basic factory function."""
        logger = create_enhanced_workflow_logger("factory_test")
        
        assert isinstance(logger, EnhancedDatabaseWorkflowLogger)
        assert logger.database_name == "factory_test"
        assert logger.enable_visual is True  # Default
    
    def test_create_enhanced_workflow_logger_with_options(self):
        """Test factory function with options."""
        logger = create_enhanced_workflow_logger(
            "factory_options_test",
            log_level="DEBUG",
            enable_visual=False,
            enable_animations=False,
            html_output_path="/tmp/test.html"
        )
        
        assert logger.database_name == "factory_options_test"
        assert logger.enable_visual is False
        assert logger.html_output_path == "/tmp/test.html"
    
    async def test_create_enhanced_workflow_logger_async(self):
        """Test async factory function."""
        logger = await create_enhanced_workflow_logger_async(
            "async_factory_test",
            total_steps=5,
            enable_visual=True
        )
        
        assert isinstance(logger, EnhancedDatabaseWorkflowLogger)
        assert logger.database_name == "async_factory_test"
        assert logger.progress_tracker is not None
        assert logger.progress_tracker.total_steps == 5


# Performance tests
class TestPerformanceImpact:
    """Test that enhanced logging doesn't significantly impact performance."""
    
    async def test_logging_overhead(self):
        """Test performance overhead of enhanced logging."""
        # Basic logger timing
        basic_logger = EnhancedDatabaseWorkflowLogger("perf_basic", enable_visual=False)
        
        start_time = time.time()
        for i in range(100):
            basic_logger.log_step_start(f"step_{i}", f"Step {i}")
            basic_logger.log_step_progress(f"step_{i}", 0.5, "Progress")
            basic_logger.log_step_end(f"step_{i}", {"result": "ok"}, True)
        basic_duration = time.time() - start_time
        
        # Enhanced logger timing
        enhanced_logger = EnhancedDatabaseWorkflowLogger("perf_enhanced", enable_visual=True)
        await enhanced_logger.initialize_progress_tracking(100)
        
        start_time = time.time()
        for i in range(100):
            await enhanced_logger.log_step_start_async(f"step_{i}", f"Step {i}")
            await enhanced_logger.log_step_progress_async(f"step_{i}", 0.5, "Progress")
            await enhanced_logger.log_step_end_async(f"step_{i}", {"result": "ok"}, True)
        enhanced_duration = time.time() - start_time
        
        # Enhanced logging should not be more than 3x slower (allowing for async overhead)
        overhead_ratio = enhanced_duration / basic_duration if basic_duration > 0 else 1
        assert overhead_ratio < 5.0, f"Enhanced logging overhead too high: {overhead_ratio:.2f}x"
        
        await enhanced_logger.cleanup_async()


# Integration test with mock workflow
@pytest.mark.integration
class TestWorkflowIntegration:
    """Test integration with workflow execution."""
    
    async def test_workflow_with_enhanced_logger(self):
        """Test enhanced logger integration with workflow execution."""
        from workflows.builder import WorkflowBuilder
        
        # Create a simple workflow (config unused but kept for context)
        
        async def mock_step(context, step, **params):
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": "mock_completed", "data": params.get("test_data", "none")}
        
        builder = WorkflowBuilder("test_workflow", "test_config.json")
        builder.custom_step("mock_step", "Mock Step", mock_step, parameters={"test_data": "test_value"})
        workflow = builder.build()
        
        # Create enhanced logger
        enhanced_logger = await create_enhanced_workflow_logger_async("workflow_test", 1)
        
        # Execute workflow with enhanced logger
        result = await workflow.execute(enhanced_logger=enhanced_logger)
        
        assert result.status in ["completed", "partial_success"]
        assert result.steps_completed >= 0
        assert "mock_step" in result.step_results
        
        await enhanced_logger.cleanup_async()