"""
Progress Tracking System for GraphMCP Workflows.

This module provides real-time progress tracking with bandwidth monitoring,
animation state management, and cached frame buffering for smooth visualization.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path

from concrete.performance_optimization import AsyncCache, CacheStrategy

logger = logging.getLogger(__name__)

@dataclass
class ProgressFrame:
    """Individual progress frame for tracking workflow step execution."""
    step_id: str
    step_name: str
    status: str  # pending, running, completed, error
    progress: float  # 0.0 to 1.0
    elapsed_time: float
    estimated_remaining: Optional[float]
    bandwidth_mbps: float
    bytes_processed: int = 0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status,
            "progress": self.progress,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining": self.estimated_remaining,
            "bandwidth_mbps": self.bandwidth_mbps,
            "bytes_processed": self.bytes_processed,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressFrame':
        """Create ProgressFrame from dictionary."""
        return cls(
            step_id=data.get("step_id", ""),
            step_name=data.get("step_name", ""),
            status=data.get("status", "pending"),
            progress=data.get("progress", 0.0),
            elapsed_time=data.get("elapsed_time", 0.0),
            estimated_remaining=data.get("estimated_remaining"),
            bandwidth_mbps=data.get("bandwidth_mbps", 0.0),
            bytes_processed=data.get("bytes_processed", 0),
            timestamp=data.get("timestamp", time.time())
        )

@dataclass
class WorkflowProgress:
    """Overall workflow progress aggregating all steps."""
    total_steps: int
    completed_steps: int
    current_step_index: int
    overall_progress: float  # 0.0 to 1.0
    total_elapsed: float
    estimated_total_duration: Optional[float]
    average_bandwidth_mbps: float
    total_bytes_processed: int = 0
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage (0-100)."""
        return self.overall_progress * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "current_step_index": self.current_step_index,
            "overall_progress": self.overall_progress,
            "completion_percentage": self.completion_percentage,
            "total_elapsed": self.total_elapsed,
            "estimated_total_duration": self.estimated_total_duration,
            "average_bandwidth_mbps": self.average_bandwidth_mbps,
            "total_bytes_processed": self.total_bytes_processed
        }

class ProgressTracker:
    """
    Real-time progress tracker with bandwidth monitoring and caching.
    
    Provides smooth progress tracking using AsyncCache for frame buffering
    and real-time bandwidth calculation following GraphMCP patterns.
    """
    
    def __init__(self, 
                 total_steps: int,
                 cache_dir: str = "cache/progress"):
        self.total_steps = total_steps
        self.completed_steps = 0
        self.current_step = ""
        self.current_step_index = 0
        self.start_time = time.time()
        
        # Progress tracking
        self.step_frames: Dict[str, ProgressFrame] = {}
        self.step_start_times: Dict[str, float] = {}
        self.step_bytes: Dict[str, int] = {}
        
        # Performance metrics
        self.total_bytes_processed = 0
        self.bandwidth_history: List[float] = []
        
        # Cache for smooth animation frames
        self.metrics_cache = AsyncCache(
            strategy=CacheStrategy.MEMORY,
            max_size=1000,
            default_ttl=60,  # 1 minute TTL for progress frames
            cache_dir=cache_dir
        )
        
        logger.debug(f"ProgressTracker initialized with {total_steps} steps")
    
    def calculate_step_bandwidth(self, step_id: str, bytes_delta: int, duration: float) -> float:
        """Calculate bandwidth for a specific step with safe division."""
        if duration <= 0:
            return 0.0
        
        # Update step bytes tracking
        if step_id not in self.step_bytes:
            self.step_bytes[step_id] = 0
        self.step_bytes[step_id] += bytes_delta
        
        # Calculate bandwidth in MB/s
        bandwidth_mbps = (self.step_bytes[step_id] / duration) / (1024 * 1024)
        
        # Update bandwidth history for rolling average
        self.bandwidth_history.append(bandwidth_mbps)
        if len(self.bandwidth_history) > 10:  # Keep last 10 measurements
            self.bandwidth_history.pop(0)
        
        return bandwidth_mbps
    
    def calculate_average_bandwidth(self) -> float:
        """Calculate rolling average bandwidth."""
        if not self.bandwidth_history:
            return 0.0
        return sum(self.bandwidth_history) / len(self.bandwidth_history)
    
    def estimate_remaining_time(self, step_id: str, progress: float) -> Optional[float]:
        """Estimate remaining time for current step."""
        if step_id not in self.step_start_times or progress <= 0:
            return None
        
        step_elapsed = time.time() - self.step_start_times[step_id]
        if step_elapsed <= 0:
            return None
        
        # Calculate time per progress unit
        time_per_progress = step_elapsed / progress
        remaining_progress = 1.0 - progress
        
        return remaining_progress * time_per_progress
    
    def estimate_total_completion(self) -> Optional[float]:
        """Estimate total workflow completion time."""
        if self.completed_steps == 0:
            return None
        
        total_elapsed = time.time() - self.start_time
        avg_time_per_step = total_elapsed / self.completed_steps
        remaining_steps = self.total_steps - self.completed_steps
        
        return time.time() + (remaining_steps * avg_time_per_step)
    
    async def start_step(self, step_id: str, step_name: str) -> None:
        """Start tracking a new workflow step."""
        self.current_step = step_id
        self.current_step_index = len(self.step_start_times)
        self.step_start_times[step_id] = time.time()
        self.step_bytes[step_id] = 0
        
        # Create initial progress frame
        frame = ProgressFrame(
            step_id=step_id,
            step_name=step_name,
            status="running",
            progress=0.0,
            elapsed_time=0.0,
            estimated_remaining=None,
            bandwidth_mbps=0.0,
            bytes_processed=0
        )
        
        self.step_frames[step_id] = frame
        
        # Cache the frame for smooth updates
        await self.metrics_cache.set(f"progress_{step_id}", frame)
        
        logger.debug(f"Started tracking step: {step_id} ({step_name})")
    
    async def update_progress(self, 
                            step_id: str, 
                            progress: float, 
                            bytes_delta: int = 0,
                            status: str = "running") -> None:
        """Update progress for a specific step with bandwidth tracking."""
        if step_id not in self.step_frames:
            logger.warning(f"Step {step_id} not found in tracking. Starting new step.")
            await self.start_step(step_id, step_id)
        
        # Ensure progress is within bounds
        progress = max(0.0, min(1.0, progress))
        
        # Calculate timing and bandwidth
        now = time.time()
        step_start = self.step_start_times.get(step_id, now)
        elapsed = now - step_start
        
        bandwidth = 0.0
        if bytes_delta > 0:
            self.total_bytes_processed += bytes_delta
            bandwidth = self.calculate_step_bandwidth(step_id, bytes_delta, elapsed)
        
        # Estimate remaining time
        estimated_remaining = self.estimate_remaining_time(step_id, progress)
        
        # Update frame
        frame = self.step_frames[step_id]
        frame.progress = progress
        frame.status = status
        frame.elapsed_time = elapsed
        frame.estimated_remaining = estimated_remaining
        frame.bandwidth_mbps = bandwidth
        frame.bytes_processed = self.step_bytes.get(step_id, 0)
        frame.timestamp = now
        
        # Cache updated frame for animation
        await self.metrics_cache.set(f"progress_{step_id}", frame)
        
        logger.debug(f"Updated progress for {step_id}: {progress:.1%} ({bandwidth:.2f} MB/s)")
    
    async def complete_step(self, step_id: str, success: bool = True) -> None:
        """Mark a step as completed."""
        if step_id not in self.step_frames:
            logger.warning(f"Cannot complete unknown step: {step_id}")
            return
        
        # Update step status
        status = "completed" if success else "error"
        await self.update_progress(step_id, 1.0, status=status)
        
        if success:
            self.completed_steps += 1
        
        logger.info(f"Step completed: {step_id} ({'success' if success else 'error'})")
    
    async def get_step_frame(self, step_id: str) -> Optional[ProgressFrame]:
        """Get current progress frame for a step."""
        # Try cache first for smooth animation
        cached_frame = await self.metrics_cache.get(f"progress_{step_id}")
        if cached_frame:
            return cached_frame
        
        # Fallback to direct lookup
        return self.step_frames.get(step_id)
    
    async def get_all_frames(self) -> Dict[str, ProgressFrame]:
        """Get all current progress frames."""
        frames = {}
        
        for step_id in self.step_frames.keys():
            frame = await self.get_step_frame(step_id)
            if frame:
                frames[step_id] = frame
        
        return frames
    
    async def get_workflow_progress(self) -> WorkflowProgress:
        """Get overall workflow progress summary."""
        total_elapsed = time.time() - self.start_time
        
        # Calculate overall progress
        if self.total_steps == 0:
            overall_progress = 0.0
        else:
            # Weight completed steps + current step progress
            current_step_progress = 0.0
            if self.current_step and self.current_step in self.step_frames:
                current_step_progress = self.step_frames[self.current_step].progress
            
            overall_progress = (self.completed_steps + current_step_progress) / self.total_steps
        
        # Estimate total duration
        estimated_total = self.estimate_total_completion()
        
        # Calculate average bandwidth
        avg_bandwidth = self.calculate_average_bandwidth()
        
        return WorkflowProgress(
            total_steps=self.total_steps,
            completed_steps=self.completed_steps,
            current_step_index=self.current_step_index,
            overall_progress=overall_progress,
            total_elapsed=total_elapsed,
            estimated_total_duration=estimated_total,
            average_bandwidth_mbps=avg_bandwidth,
            total_bytes_processed=self.total_bytes_processed
        )
    
    async def export_progress_data(self, output_path: str) -> None:
        """Export progress data to JSON file for analysis."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Gather all data
            workflow_progress = await self.get_workflow_progress()
            all_frames = await self.get_all_frames()
            
            export_data = {
                "workflow_progress": workflow_progress.to_dict(),
                "step_frames": {
                    step_id: frame.to_dict() 
                    for step_id, frame in all_frames.items()
                },
                "bandwidth_history": self.bandwidth_history,
                "export_timestamp": time.time()
            }
            
            import json
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Progress data exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export progress data: {e}")
    
    async def cleanup(self) -> None:
        """Clean up resources and clear cache."""
        try:
            await self.metrics_cache.clear()
            logger.debug("ProgressTracker cleanup completed")
        except Exception as e:
            logger.warning(f"Error during ProgressTracker cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup()

# Convenience factory function
async def create_progress_tracker(total_steps: int, cache_dir: str = "cache/progress") -> ProgressTracker:
    """Factory function to create a ProgressTracker with proper initialization."""
    return ProgressTracker(total_steps, cache_dir)