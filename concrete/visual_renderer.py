"""
Visual Rendering Engine for GraphMCP Workflow Progress.

This module provides terminal and HTML rendering capabilities for real-time
workflow progress with animated indicators, progress bars, and responsive layouts.
"""

import sys
import time
import shutil
import logging
from typing import Dict, Any, Optional, TextIO
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from concrete.progress_tracker import ProgressFrame, WorkflowProgress

logger = logging.getLogger(__name__)

@dataclass
class RenderConfig:
    """Configuration for visual rendering."""
    output_mode: str = "terminal"  # terminal, html, both
    terminal_width: int = 80
    use_colors: bool = True
    use_animations: bool = True
    refresh_rate: float = 0.1  # seconds
    html_template_path: Optional[str] = None

class TerminalRenderer:
    """Terminal-based progress renderer with ANSI codes and animations."""
    
    # ANSI Color codes following Makefile patterns
    COLORS = {
        'RED': '\033[0;31m',
        'GREEN': '\033[0;32m',
        'YELLOW': '\033[0;33m',
        'BLUE': '\033[0;34m',
        'MAGENTA': '\033[0;35m',
        'CYAN': '\033[0;36m',
        'NC': '\033[0m'  # No Color
    }
    
    # Animation frames for spinner
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __init__(self, config: RenderConfig):
        self.config = config
        self.terminal_width = self._detect_terminal_width()
        self.is_tty = self._is_tty()
        self.spinner_index = 0
        self.last_render_time = 0.0
        
        # Disable colors and animations if not TTY
        if not self.is_tty:
            self.config.use_colors = False
            self.config.use_animations = False
    
    def _detect_terminal_width(self) -> int:
        """Detect terminal width with fallback."""
        try:
            return shutil.get_terminal_size().columns
        except (AttributeError, OSError):
            return self.config.terminal_width
    
    def _is_tty(self) -> bool:
        """Check if output is a TTY (supports colors/animations)."""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.config.use_colors:
            return text
        
        color_code = self.COLORS.get(color.upper(), '')
        reset_code = self.COLORS['NC']
        return f"{color_code}{text}{reset_code}"
    
    def _get_spinner_frame(self) -> str:
        """Get next spinner animation frame."""
        if not self.config.use_animations:
            return "•"
        
        frame = self.SPINNER_FRAMES[self.spinner_index]
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_FRAMES)
        return frame
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m{secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h{minutes}m"
    
    def _format_bandwidth(self, mbps: float) -> str:
        """Format bandwidth with appropriate units."""
        if mbps < 0.1:
            return f"{mbps * 1000:.0f} KB/s"
        elif mbps < 100:
            return f"{mbps:.1f} MB/s"
        else:
            return f"{mbps:.0f} MB/s"
    
    def render_progress_bar(self, 
                          progress: float, 
                          step_name: str,
                          status: str = "running",
                          bandwidth_mbps: float = 0.0,
                          elapsed_time: float = 0.0,
                          estimated_remaining: Optional[float] = None) -> str:
        """Render a progress bar with status indicators."""
        
        # Calculate responsive bar width
        name_width = min(30, len(step_name))
        info_width = 40  # Space for percentage, time, bandwidth
        available_width = max(20, self.terminal_width - name_width - info_width - 10)
        bar_width = min(40, available_width)
        
        # Calculate filled portion
        filled_chars = int(progress * bar_width)
        
        # Choose status icon and color based on status
        if status == "completed":
            status_icon = "✅"
            color = "GREEN"
            bar_char = "█"
        elif status == "error":
            status_icon = "❌"
            color = "RED"
            bar_char = "█"
        elif status == "running":
            status_icon = self._get_spinner_frame()
            color = "BLUE"
            bar_char = "█"
        else:  # pending
            status_icon = "⏳"
            color = "YELLOW"
            bar_char = "█"
        
        # Build progress bar
        filled_bar = bar_char * filled_chars
        empty_bar = "░" * (bar_width - filled_chars)
        progress_bar = f"[{filled_bar}{empty_bar}]"
        
        # Format percentage
        percentage = f"{progress * 100:5.1f}%"
        
        # Format timing info
        time_info = self._format_duration(elapsed_time)
        if estimated_remaining:
            time_info += f" / ~{self._format_duration(estimated_remaining)}"
        
        # Format bandwidth
        bandwidth_info = ""
        if bandwidth_mbps > 0:
            bandwidth_info = f" @ {self._format_bandwidth(bandwidth_mbps)}"
        
        # Truncate step name if needed
        display_name = step_name[:name_width]
        if len(step_name) > name_width:
            display_name = display_name[:-3] + "..."
        
        # Assemble the complete line
        line = f"{status_icon} {display_name:<{name_width}} {progress_bar} {percentage} {time_info}{bandwidth_info}"
        
        return self._colorize(line, color)
    
    def render_workflow_summary(self, workflow_progress: WorkflowProgress) -> str:
        """Render overall workflow progress summary."""
        
        # Overall progress bar
        overall_bar = self.render_progress_bar(
            workflow_progress.overall_progress,
            "Overall Progress",
            "running" if workflow_progress.completed_steps < workflow_progress.total_steps else "completed",
            workflow_progress.average_bandwidth_mbps,
            workflow_progress.total_elapsed,
            workflow_progress.estimated_total_duration
        )
        
        # Summary stats
        steps_info = f"Steps: {workflow_progress.completed_steps}/{workflow_progress.total_steps}"
        duration_info = f"Duration: {self._format_duration(workflow_progress.total_elapsed)}"
        
        if workflow_progress.estimated_total_duration:
            eta = workflow_progress.estimated_total_duration - time.time()
            if eta > 0:
                duration_info += f" (ETA: {self._format_duration(eta)})"
        
        bandwidth_info = ""
        if workflow_progress.average_bandwidth_mbps > 0:
            bandwidth_info = f"Avg Speed: {self._format_bandwidth(workflow_progress.average_bandwidth_mbps)}"
        
        # Build summary lines
        summary_lines = [
            self._colorize("─" * min(80, self.terminal_width), "CYAN"),
            overall_bar,
            f"  {steps_info}  |  {duration_info}  |  {bandwidth_info}",
            self._colorize("─" * min(80, self.terminal_width), "CYAN")
        ]
        
        return "\n".join(summary_lines)
    
    def render_step_list(self, frames: Dict[str, ProgressFrame], max_visible: int = 10) -> str:
        """Render a list of workflow steps with their progress."""
        if not frames:
            return self._colorize("No active steps", "YELLOW")
        
        lines = []
        
        # Sort frames by status and progress
        sorted_frames = sorted(
            frames.values(),
            key=lambda f: (
                0 if f.status == "running" else 1 if f.status == "completed" else 2,
                -f.progress
            )
        )
        
        # Show up to max_visible steps
        visible_frames = sorted_frames[:max_visible]
        
        for frame in visible_frames:
            line = self.render_progress_bar(
                frame.progress,
                frame.step_name,
                frame.status,
                frame.bandwidth_mbps,
                frame.elapsed_time,
                frame.estimated_remaining
            )
            lines.append(line)
        
        # Show count if there are more steps
        if len(sorted_frames) > max_visible:
            remaining = len(sorted_frames) - max_visible
            lines.append(self._colorize(f"... and {remaining} more steps", "YELLOW"))
        
        return "\n".join(lines)
    
    def clear_screen(self) -> None:
        """Clear the terminal screen if supported."""
        if self.is_tty:
            print("\033[2J\033[H", end="")
    
    def move_cursor_up(self, lines: int) -> None:
        """Move cursor up by specified number of lines."""
        if self.is_tty and lines > 0:
            print(f"\033[{lines}A", end="")
    
    def should_render(self) -> bool:
        """Check if enough time has passed for next render."""
        now = time.time()
        if now - self.last_render_time >= self.config.refresh_rate:
            self.last_render_time = now
            return True
        return False

class HTMLRenderer:
    """HTML-based progress renderer inspired by claude-code-log patterns."""
    
    def __init__(self, config: RenderConfig):
        self.config = config
        self.template_cache = {}
    
    def _load_template(self, template_name: str) -> str:
        """Load HTML template from file or use default."""
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        # Try to load custom template
        if self.config.html_template_path:
            template_path = Path(self.config.html_template_path) / f"{template_name}.html"
            if template_path.exists():
                with open(template_path) as f:
                    template = f.read()
                    self.template_cache[template_name] = template
                    return template
        
        # Use default template
        template = self._get_default_template(template_name)
        self.template_cache[template_name] = template
        return template
    
    def _get_default_template(self, template_name: str) -> str:
        """Get default HTML template."""
        if template_name == "workflow_progress":
            return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GraphMCP Workflow Progress</title>
    <style>
        body { font-family: 'Monaco', 'Consolas', monospace; margin: 20px; background: #1e1e1e; color: #d4d4d4; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { border-bottom: 2px solid #007acc; padding-bottom: 10px; margin-bottom: 20px; }
        .workflow-summary { background: #252526; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .progress-bar { background: #3c3c3c; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; transition: width 0.3s ease; }
        .progress-running { background: linear-gradient(90deg, #007acc, #0099ff); }
        .progress-completed { background: linear-gradient(90deg, #22bb33, #44dd55); }
        .progress-error { background: linear-gradient(90deg, #dd3333, #ff4444); }
        .step-list { margin-top: 20px; }
        .step-item { background: #2d2d30; padding: 10px; margin: 5px 0; border-radius: 3px; border-left: 3px solid #007acc; }
        .step-running { border-left-color: #007acc; animation: pulse 2s infinite; }
        .step-completed { border-left-color: #22bb33; }
        .step-error { border-left-color: #dd3333; }
        .metrics { display: flex; gap: 20px; margin: 10px 0; }
        .metric { background: #3c3c3c; padding: 8px 12px; border-radius: 3px; }
        .timestamp { color: #808080; font-size: 0.9em; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .spinner { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 GraphMCP Workflow Progress</h1>
            <div class="timestamp">Last updated: {{timestamp}}</div>
        </div>
        
        <div class="workflow-summary">
            <h2>Overall Progress</h2>
            <div class="progress-bar">
                <div class="progress-fill progress-{{overall_status}}" style="width: {{overall_percentage}}%"></div>
            </div>
            <div class="metrics">
                <div class="metric">Steps: {{completed_steps}}/{{total_steps}}</div>
                <div class="metric">Duration: {{duration}}</div>
                <div class="metric">Speed: {{bandwidth}}</div>
                {{#eta}}<div class="metric">ETA: {{eta}}</div>{{/eta}}
            </div>
        </div>
        
        <div class="step-list">
            <h2>Workflow Steps</h2>
            {{#steps}}
            <div class="step-item step-{{status}}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>{{icon}} {{step_name}}</span>
                    <span>{{percentage}}%</span>
                </div>
                <div class="progress-bar" style="height: 10px; margin: 5px 0;">
                    <div class="progress-fill progress-{{status}}" style="width: {{percentage}}%"></div>
                </div>
                <div class="metrics">
                    <div class="metric">{{elapsed_time}}</div>
                    {{#bandwidth}}<div class="metric">{{bandwidth}}</div>{{/bandwidth}}
                    {{#estimated_remaining}}<div class="metric">~{{estimated_remaining}} remaining</div>{{/estimated_remaining}}
                </div>
            </div>
            {{/steps}}
        </div>
    </div>
    
    <script>
        // Auto-refresh every 2 seconds
        setTimeout(() => location.reload(), 2000);
    </script>
</body>
</html>
            """
        
        return "<html><body><h1>Template not found</h1></body></html>"
    
    def _format_duration_html(self, seconds: float) -> str:
        """Format duration for HTML display."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _get_status_icon(self, status: str) -> str:
        """Get appropriate icon for status."""
        icons = {
            "pending": "⏳",
            "running": "<span class='spinner'>🔄</span>",
            "completed": "✅",
            "error": "❌"
        }
        return icons.get(status, "❓")
    
    def render_workflow_html(self, 
                           workflow_progress: WorkflowProgress,
                           step_frames: Dict[str, ProgressFrame],
                           output_path: str) -> None:
        """Render complete workflow progress as HTML file."""
        
        template = self._load_template("workflow_progress")
        
        # Prepare template data
        template_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_percentage": workflow_progress.completion_percentage,
            "overall_status": "running" if workflow_progress.completed_steps < workflow_progress.total_steps else "completed",
            "completed_steps": workflow_progress.completed_steps,
            "total_steps": workflow_progress.total_steps,
            "duration": self._format_duration_html(workflow_progress.total_elapsed),
            "bandwidth": f"{workflow_progress.average_bandwidth_mbps:.1f} MB/s" if workflow_progress.average_bandwidth_mbps > 0 else "N/A"
        }
        
        # Add ETA if available
        if workflow_progress.estimated_total_duration:
            eta = workflow_progress.estimated_total_duration - time.time()
            if eta > 0:
                template_data["eta"] = self._format_duration_html(eta)
        
        # Prepare step data
        steps_data = []
        for frame in step_frames.values():
            step_data = {
                "step_name": frame.step_name,
                "status": frame.status,
                "icon": self._get_status_icon(frame.status),
                "percentage": f"{frame.progress * 100:.1f}",
                "elapsed_time": self._format_duration_html(frame.elapsed_time)
            }
            
            if frame.bandwidth_mbps > 0:
                step_data["bandwidth"] = f"{frame.bandwidth_mbps:.1f} MB/s"
            
            if frame.estimated_remaining:
                step_data["estimated_remaining"] = self._format_duration_html(frame.estimated_remaining)
            
            steps_data.append(step_data)
        
        template_data["steps"] = steps_data
        
        # Simple template substitution (would use Jinja2 in production)
        html_content = self._substitute_template(template, template_data)
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML progress report saved to: {output_path}")
    
    def _substitute_template(self, template: str, data: Dict[str, Any]) -> str:
        """Simple template substitution (basic implementation)."""
        result = template
        
        for key, value in data.items():
            if isinstance(value, list):
                continue  # Handle lists separately
            result = result.replace(f"{{{{{key}}}}}", str(value))
        
        # Handle steps list (simple loop)
        if "{{#steps}}" in result and "steps" in data:
            start_marker = "{{#steps}}"
            end_marker = "{{/steps}}"
            
            start_idx = result.find(start_marker)
            end_idx = result.find(end_marker) + len(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                step_template = result[start_idx + len(start_marker):end_idx - len(end_marker)]
                
                steps_html = ""
                for step in data["steps"]:
                    step_html = step_template
                    for key, value in step.items():
                        step_html = step_html.replace(f"{{{{{key}}}}}", str(value))
                    
                    # Handle conditionals
                    for key in step.keys():
                        step_html = step_html.replace(f"{{#{key}}}", "")
                        step_html = step_html.replace(f"{{/{key}}}", "")
                    
                    steps_html += step_html
                
                result = result[:start_idx] + steps_html + result[end_idx:]
        
        return result

class VisualRenderer:
    """Main visual renderer supporting both terminal and HTML output."""
    
    def __init__(self, config: RenderConfig = None):
        self.config = config or RenderConfig()
        self.terminal_renderer = TerminalRenderer(self.config)
        self.html_renderer = HTMLRenderer(self.config)
        self.last_line_count = 0
    
    def render_progress(self, 
                       workflow_progress: WorkflowProgress,
                       step_frames: Dict[str, ProgressFrame],
                       output_stream: TextIO = None) -> None:
        """Render progress to terminal with live updates."""
        
        if not self.terminal_renderer.should_render():
            return
        
        stream = output_stream or sys.stdout
        
        # Clear previous output if in TTY mode
        if self.terminal_renderer.is_tty and self.last_line_count > 0:
            self.terminal_renderer.move_cursor_up(self.last_line_count)
        
        # Render workflow summary
        summary = self.terminal_renderer.render_workflow_summary(workflow_progress)
        
        # Render step list
        steps_display = self.terminal_renderer.render_step_list(step_frames, max_visible=8)
        
        # Combine output
        output_lines = [
            summary,
            "",  # Blank line
            steps_display,
            ""  # Final blank line
        ]
        
        output = "\n".join(output_lines)
        
        # Count lines for next clear
        self.last_line_count = len(output.split('\n'))
        
        # Print to stream
        print(output, file=stream, flush=True)
    
    def render_html_report(self, 
                          workflow_progress: WorkflowProgress,
                          step_frames: Dict[str, ProgressFrame],
                          output_path: str) -> None:
        """Generate HTML progress report."""
        self.html_renderer.render_workflow_html(
            workflow_progress, 
            step_frames, 
            output_path
        )
    
    def render_final_summary(self, 
                           workflow_progress: WorkflowProgress,
                           step_frames: Dict[str, ProgressFrame],
                           success: bool = True) -> None:
        """Render final workflow completion summary."""
        
        # Clear any ongoing animation
        if self.terminal_renderer.is_tty and self.last_line_count > 0:
            self.terminal_renderer.move_cursor_up(self.last_line_count)
        
        # Final summary
        status_icon = "✅" if success else "❌"
        status_text = "COMPLETED" if success else "FAILED"
        color = "GREEN" if success else "RED"
        
        summary_lines = [
            "",
            self.terminal_renderer._colorize("=" * 60, "CYAN"),
            self.terminal_renderer._colorize(f"{status_icon} WORKFLOW {status_text}", color),
            self.terminal_renderer._colorize("=" * 60, "CYAN"),
            "",
            f"Total Steps: {workflow_progress.completed_steps}/{workflow_progress.total_steps}",
            f"Duration: {self.terminal_renderer._format_duration(workflow_progress.total_elapsed)}",
            f"Average Speed: {self.terminal_renderer._format_bandwidth(workflow_progress.average_bandwidth_mbps)}" if workflow_progress.average_bandwidth_mbps > 0 else "",
            ""
        ]
        
        print("\n".join(filter(None, summary_lines)), flush=True)
        self.last_line_count = 0  # Reset for any future renders

# Convenience factory function
def create_visual_renderer(output_mode: str = "terminal", 
                         use_colors: bool = True,
                         use_animations: bool = True) -> VisualRenderer:
    """Factory function to create a VisualRenderer with common configurations."""
    config = RenderConfig(
        output_mode=output_mode,
        use_colors=use_colors,
        use_animations=use_animations
    )
    return VisualRenderer(config)