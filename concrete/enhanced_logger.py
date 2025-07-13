"""
Enhanced Logger Integration for GraphMCP Workflows.

This module integrates DatabaseWorkflowLogger with ProgressTracker and VisualRenderer
to provide real-time animated logging with visual feedback while maintaining
full backward compatibility with existing logging patterns.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from concrete.workflow_logger import DatabaseWorkflowLogger, EnhancedWorkflowMetrics
from concrete.progress_tracker import ProgressTracker
from concrete.visual_renderer import VisualRenderer, RenderConfig

logger = logging.getLogger(__name__)

class EnhancedDatabaseWorkflowLogger(DatabaseWorkflowLogger):
    """
    Enhanced logger extending DatabaseWorkflowLogger with visual progress tracking.
    
    Provides real-time visual feedback with animated progress bars, bandwidth metrics,
    and responsive terminal/HTML output while preserving all existing method signatures
    for full backward compatibility.
    """
    
    def __init__(self, 
                 database_name: str, 
                 log_level: str = "INFO",
                 enable_visual: bool = True,
                 enable_animations: bool = True,
                 output_mode: str = "terminal",
                 html_output_path: Optional[str] = None):
        
        # Initialize parent logger (preserves all existing functionality)
        super().__init__(database_name, log_level)
        
        # Replace base metrics with enhanced metrics
        self.enhanced_metrics = EnhancedWorkflowMetrics(
            start_time=self.metrics.start_time,
            database_name=database_name
        )
        
        # Enhanced components
        self.enable_visual = enable_visual
        self.progress_tracker: Optional[ProgressTracker] = None
        self.visual_renderer: Optional[VisualRenderer] = None
        self.html_output_path = html_output_path
        
        # Visual rendering configuration
        if self.enable_visual:
            render_config = RenderConfig(
                output_mode=output_mode,
                use_animations=enable_animations,
                html_template_path=None
            )
            self.visual_renderer = VisualRenderer(render_config)
        
        # Async cleanup tracking
        self._cleanup_tasks: List[asyncio.Task] = []
        self._render_task: Optional[asyncio.Task] = None
        self._render_interval = 0.5  # Update every 500ms
        
        logger.debug(f"EnhancedDatabaseWorkflowLogger initialized (visual={enable_visual})")
    
    async def initialize_progress_tracking(self, total_steps: int) -> None:
        """Initialize progress tracking for the workflow."""
        if not self.enable_visual:
            return
        
        try:
            self.progress_tracker = ProgressTracker(total_steps)
            
            # Start background rendering task for live updates
            if self.visual_renderer:
                self._render_task = asyncio.create_task(self._render_loop())
            
            logger.debug(f"Progress tracking initialized for {total_steps} steps")
            
        except Exception as e:
            logger.warning(f"Failed to initialize progress tracking: {e}")
            self.enable_visual = False
    
    async def _render_loop(self) -> None:
        """Background task for continuous visual rendering."""
        try:
            while True:
                if self.progress_tracker and self.visual_renderer:
                    workflow_progress = await self.progress_tracker.get_workflow_progress()
                    step_frames = await self.progress_tracker.get_all_frames()
                    
                    # Render to terminal
                    self.visual_renderer.render_progress(workflow_progress, step_frames)
                    
                    # Generate HTML report if path provided
                    if self.html_output_path:
                        self.visual_renderer.render_html_report(
                            workflow_progress, step_frames, self.html_output_path
                        )
                
                await asyncio.sleep(self._render_interval)
        
        except asyncio.CancelledError:
            logger.debug("Render loop cancelled")
        except Exception as e:
            logger.error(f"Error in render loop: {e}")
    
    def log_workflow_start(self, target_repos: List[str], config: Dict[str, Any]):
        """Enhanced workflow start logging with progress initialization."""
        # Call parent method to preserve existing functionality
        super().log_workflow_start(target_repos, config)
        
        # Initialize progress tracking if visual mode enabled
        if self.enable_visual:
            # Estimate total steps based on configuration
            estimated_steps = len(target_repos) * 3 + 5  # Rough estimate
            
            # Schedule async initialization
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.initialize_progress_tracking(estimated_steps))
            except RuntimeError:
                logger.warning("No event loop available for progress tracking initialization")
    
    async def log_step_start_async(self, step_name: str, step_description: str, parameters: Dict[str, Any] = None):
        """Async version of log_step_start with progress tracking."""
        # Call synchronous version first
        self.log_step_start(step_name, step_description, parameters)
        
        # Update enhanced metrics
        self.enhanced_metrics.update_progress(step_name, 0.0)
        
        # Start progress tracking
        if self.progress_tracker:
            await self.progress_tracker.start_step(step_name, step_description)
    
    def log_step_start(self, step_name: str, step_description: str, parameters: Dict[str, Any] = None):
        """Enhanced step start logging (preserves parent signature)."""
        # Call parent method to preserve existing functionality
        super().log_step_start(step_name, step_description, parameters)
        
        # Update enhanced metrics
        self.enhanced_metrics.update_progress(step_name, 0.0)
        
        # Schedule async progress tracking if available
        if self.progress_tracker:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.progress_tracker.start_step(step_name, step_description))
            except RuntimeError:
                pass  # No event loop available, continue with sync logging
    
    async def log_step_progress_async(self, 
                                    step_name: str, 
                                    progress: float, 
                                    message: str = "",
                                    bytes_processed: int = 0):
        """Log step progress with visual updates."""
        # Update enhanced metrics
        self.enhanced_metrics.update_progress(step_name, progress, bytes_processed)
        
        # Log message if provided
        if message:
            self.logger.info(f"🔄 {step_name}: {message} ({progress:.1%})")
        
        # Update progress tracker
        if self.progress_tracker:
            await self.progress_tracker.update_progress(step_name, progress, bytes_processed)
    
    def log_step_progress(self, 
                         step_name: str, 
                         progress: float, 
                         message: str = "",
                         bytes_processed: int = 0):
        """Synchronous step progress logging with visual updates."""
        # Update enhanced metrics
        self.enhanced_metrics.update_progress(step_name, progress, bytes_processed)
        
        # Log message if provided
        if message:
            self.logger.info(f"🔄 {step_name}: {message} ({progress:.1%})")
        
        # Schedule async progress tracking if available
        if self.progress_tracker:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.progress_tracker.update_progress(step_name, progress, bytes_processed))
            except RuntimeError:
                pass  # No event loop available, continue with sync logging
    
    async def log_step_end_async(self, step_name: str, result: Dict[str, Any], success: bool = True):
        """Async version of log_step_end with progress completion."""
        # Call synchronous version first
        self.log_step_end(step_name, result, success)
        
        # Complete progress tracking
        if self.progress_tracker:
            await self.progress_tracker.complete_step(step_name, success)
        
        # Update enhanced metrics to completed state
        self.enhanced_metrics.update_progress(step_name, 1.0)
        if success:
            self.enhanced_metrics.animation_state = "completed"
        else:
            self.enhanced_metrics.animation_state = "error"
    
    def log_step_end(self, step_name: str, result: Dict[str, Any], success: bool = True):
        """Enhanced step end logging (preserves parent signature)."""
        # Call parent method to preserve existing functionality
        super().log_step_end(step_name, result, success)
        
        # Update enhanced metrics to completed state
        self.enhanced_metrics.update_progress(step_name, 1.0)
        if success:
            self.enhanced_metrics.animation_state = "completed"
        else:
            self.enhanced_metrics.animation_state = "error"
        
        # Schedule async progress completion if available
        if self.progress_tracker:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.progress_tracker.complete_step(step_name, success))
            except RuntimeError:
                pass  # No event loop available, continue with sync logging
    
    def log_workflow_end(self, success: bool = True):
        """Enhanced workflow end logging with final summary."""
        # Update enhanced metrics end time
        self.enhanced_metrics.end_time = time.time()
        
        # Call parent method to preserve existing functionality
        super().log_workflow_end(success)
        
        # Stop background rendering
        if self._render_task and not self._render_task.done():
            self._render_task.cancel()
        
        # Render final summary if visual mode enabled
        if self.enable_visual and self.visual_renderer and self.progress_tracker:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._render_final_summary(success))
            except RuntimeError:
                # No event loop, render sync
                self._render_final_summary_sync(success)
    
    async def _render_final_summary(self, success: bool):
        """Render final workflow summary with visual elements."""
        if not (self.progress_tracker and self.visual_renderer):
            return
        
        try:
            workflow_progress = await self.progress_tracker.get_workflow_progress()
            step_frames = await self.progress_tracker.get_all_frames()
            
            # Render final summary
            self.visual_renderer.render_final_summary(workflow_progress, step_frames, success)
            
            # Generate final HTML report
            if self.html_output_path:
                final_html_path = str(Path(self.html_output_path).with_suffix('.final.html'))
                self.visual_renderer.render_html_report(workflow_progress, step_frames, final_html_path)
                self.logger.info(f"📄 Final HTML report: {final_html_path}")
        
        except Exception as e:
            logger.error(f"Error rendering final summary: {e}")
    
    def _render_final_summary_sync(self, success: bool):
        """Synchronous fallback for final summary rendering."""
        if not self.visual_renderer:
            return
        
        # Create minimal progress data for sync rendering
        try:
            from concrete.progress_tracker import WorkflowProgress
            
            total_steps = getattr(self.progress_tracker, 'total_steps', 1) if self.progress_tracker else 1
            completed_steps = getattr(self.progress_tracker, 'completed_steps', 1) if self.progress_tracker else 1
            
            workflow_progress = WorkflowProgress(
                total_steps=total_steps,
                completed_steps=completed_steps,
                current_step_index=completed_steps,
                overall_progress=1.0,
                total_elapsed=self.enhanced_metrics.duration,
                estimated_total_duration=None,
                average_bandwidth_mbps=self.enhanced_metrics.bandwidth_mbps
            )
            
            self.visual_renderer.render_final_summary(workflow_progress, {}, success)
        
        except Exception as e:
            logger.error(f"Error in sync final summary: {e}")
    
    def get_enhanced_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive enhanced workflow metrics."""
        base_summary = self.get_metrics_summary()
        
        enhanced_summary = {
            "enhanced_metrics": self.enhanced_metrics.to_dict(),
            "visual_enabled": self.enable_visual,
            "progress_tracker_active": self.progress_tracker is not None,
            "render_task_active": self._render_task is not None and not self._render_task.done()
        }
        
        # Add progress tracker metrics if available
        if self.progress_tracker:
            try:
                loop = asyncio.get_event_loop()
                workflow_progress = loop.run_until_complete(self.progress_tracker.get_workflow_progress())
                enhanced_summary["workflow_progress"] = workflow_progress.to_dict()
            except RuntimeError:
                enhanced_summary["workflow_progress"] = "Not available (no event loop)"
        
        # Merge with base summary
        base_summary.update(enhanced_summary)
        return base_summary
    
    async def cleanup_async(self) -> None:
        """Async cleanup of enhanced logger resources."""
        try:
            # Cancel render task
            if self._render_task and not self._render_task.done():
                self._render_task.cancel()
                try:
                    await self._render_task
                except asyncio.CancelledError:
                    pass
            
            # Cleanup progress tracker
            if self.progress_tracker:
                await self.progress_tracker.cleanup()
            
            # Cancel any pending cleanup tasks
            for task in self._cleanup_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for cleanup tasks to complete
            if self._cleanup_tasks:
                await asyncio.gather(*self._cleanup_tasks, return_exceptions=True)
            
            logger.debug("Enhanced logger cleanup completed")
        
        except Exception as e:
            logger.error(f"Error during enhanced logger cleanup: {e}")
    
    def cleanup_sync(self) -> None:
        """Synchronous cleanup fallback."""
        try:
            # Cancel render task if possible
            if self._render_task and not self._render_task.done():
                self._render_task.cancel()
            
            logger.debug("Enhanced logger sync cleanup completed")
        
        except Exception as e:
            logger.error(f"Error during sync cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup_async()
    
    def __enter__(self):
        """Sync context manager entry for backward compatibility."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit with cleanup."""
        # Try async cleanup first
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.cleanup_async())
        except RuntimeError:
            # Fallback to sync cleanup
            self.cleanup_sync()

# Convenience factory functions
def create_enhanced_workflow_logger(database_name: str, 
                                   log_level: str = "INFO",
                                   enable_visual: bool = True,
                                   enable_animations: bool = True,
                                   html_output_path: Optional[str] = None) -> EnhancedDatabaseWorkflowLogger:
    """Factory function to create an enhanced workflow logger with common settings."""
    return EnhancedDatabaseWorkflowLogger(
        database_name=database_name,
        log_level=log_level,
        enable_visual=enable_visual,
        enable_animations=enable_animations,
        html_output_path=html_output_path
    )

async def create_enhanced_workflow_logger_async(database_name: str,
                                               total_steps: int,
                                               log_level: str = "INFO",
                                               enable_visual: bool = True,
                                               enable_animations: bool = True,
                                               html_output_path: Optional[str] = None) -> EnhancedDatabaseWorkflowLogger:
    """Async factory function with automatic progress tracking initialization."""
    logger = EnhancedDatabaseWorkflowLogger(
        database_name=database_name,
        log_level=log_level,
        enable_visual=enable_visual,
        enable_animations=enable_animations,
        html_output_path=html_output_path
    )
    
    if enable_visual:
        await logger.initialize_progress_tracking(total_steps)
    
    return logger