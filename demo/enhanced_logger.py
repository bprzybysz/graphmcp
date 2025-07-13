"""
Enhanced Visual Logger for GraphMCP Demo.

This module provides visually appealing logging utilities for the GraphMCP
workflow demo, including file hit tables, refactoring group displays,
agent parameter information, and formatted git diffs.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FileHit:
    """Represents a file with pattern hits."""
    file_path: str
    hit_count: int
    source_type: str
    confidence: float
    file_size: int = 0
    patterns: List[str] = None

    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []


@dataclass
class RefactoringGroup:
    """Represents a group of files for refactoring."""
    group_name: str
    files: List[str]
    patterns_count: int
    priority: str = "medium"  # high, medium, low
    estimated_effort: str = "1-2 hours"


@dataclass
class AgentParameters:
    """Represents agent/model parameters for logging."""
    mode: str  # mock or real
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    response_format: str = "json"
    prompt_type: str = "contextual"


class EnhancedDemoLogger:
    """
    Enhanced visual logger for GraphMCP demo workflow.
    
    Provides visually appealing logging with tables, formatting, and
    structured displays for workflow results using Rich library.
    """
    
    def __init__(self, workflow_name: str = "GraphMCP Demo"):
        self.workflow_name = workflow_name
        self.start_time = time.time()
        self.console = Console() if RICH_AVAILABLE else None
        
    def _get_confidence_emoji(self, confidence: float) -> str:
        """Get emoji indicator for confidence level."""
        if confidence >= 0.9:
            return "🟢"  # High confidence
        elif confidence >= 0.7:
            return "🟡"  # Medium confidence
        elif confidence >= 0.5:
            return "🟠"  # Low confidence
        else:
            return "🔴"  # Very low confidence
    
    def _get_priority_emoji(self, priority: str) -> str:
        """Get emoji indicator for priority level."""
        priority_map = {
            "high": "🔥",
            "medium": "⚡",
            "low": "📝"
        }
        return priority_map.get(priority.lower(), "📝")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0B"
        elif size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
    
    def _truncate_path(self, path: str, max_length: int = 50) -> str:
        """Truncate file path for display."""
        if len(path) <= max_length:
            return path
        
        # Try to keep the filename and some parent directories
        parts = Path(path).parts
        if len(parts) == 1:
            return f"...{path[-max_length+3:]}"
        
        filename = parts[-1]
        remaining_length = max_length - len(filename) - 4  # Account for ".../"
        
        if remaining_length <= 0:
            return f"...{filename}"
        
        # Build path backwards
        path_parts = []
        current_length = 0
        for part in reversed(parts[:-1]):
            if current_length + len(part) + 1 <= remaining_length:
                path_parts.insert(0, part)
                current_length += len(part) + 1
            else:
                break
        
        if path_parts:
            return f".../{'/'.join(path_parts)}/{filename}"
        else:
            return f".../{filename}"
    
    def print_section_header(self, title: str, emoji: str = "📋"):
        """Print a visually appealing section header."""
        print("\n" + "=" * 80)
        print(f"{emoji} {title.upper()}")
        print("=" * 80)
    
    def print_subsection_header(self, title: str, emoji: str = "📍"):
        """Print a subsection header."""
        print(f"\n{emoji} {title}")
        print("-" * 60)
    
    def log_file_hits_table(self, file_hits: List[FileHit], title: str = "Files with Pattern Hits"):
        """
        Log a visually appealing table of files with pattern hits using Rich.
        
        Args:
            file_hits: List of file hits to display
            title: Table title
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            self.print_subsection_header(title, "📁")
            if not file_hits:
                print("   No files with pattern hits found.")
                return
            for i, hit in enumerate(file_hits, 1):
                print(f"{i}. {hit.file_path} ({hit.hit_count} hits, {hit.confidence:.2f} confidence)")
            return
        
        if not file_hits:
            self.console.print(f"\n📁 {title}")
            self.console.print("   No files with pattern hits found.")
            return
        
        # Sort by hit count (descending) then by confidence
        sorted_hits = sorted(file_hits, key=lambda x: (x.hit_count, x.confidence), reverse=True)
        
        # Create Rich table
        table = Table(title=f"📁 {title}", show_header=True, header_style="bold blue")
        table.add_column("#", style="dim", width=3)
        table.add_column("File Path", style="cyan", min_width=30)
        table.add_column("Type", style="magenta")
        table.add_column("Hits", style="green", justify="right")
        table.add_column("Confidence", style="yellow")
        table.add_column("Size", style="blue", justify="right")
        
        # Add rows
        for i, hit in enumerate(sorted_hits, 1):
            truncated_path = self._truncate_path(hit.file_path, 40)
            confidence_display = f"{self._get_confidence_emoji(hit.confidence)} {hit.confidence:.2f}"
            size_display = self._format_file_size(hit.file_size)
            
            table.add_row(
                str(i),
                truncated_path,
                hit.source_type,
                str(hit.hit_count),
                confidence_display,
                size_display
            )
        
        self.console.print(table)
        
        # Show patterns in a tree structure for high-confidence files
        if any(hit.confidence >= 0.8 and hit.patterns for hit in sorted_hits):
            tree = Tree("🔍 Pattern Previews (High Confidence Files)")
            for hit in sorted_hits:
                if hit.confidence >= 0.8 and hit.patterns:
                    file_node = tree.add(f"[cyan]{self._truncate_path(hit.file_path, 50)}[/cyan]")
                    for pattern in hit.patterns[:2]:  # Show up to 2 patterns
                        pattern_preview = pattern[:60] + "..." if len(pattern) > 60 else pattern
                        file_node.add(f"[dim]{pattern_preview}[/dim]")
            self.console.print(tree)
        
        # Summary
        total_hits = sum(hit.hit_count for hit in file_hits)
        high_confidence = len([h for h in file_hits if h.confidence >= 0.8])
        self.console.print(f"\n📊 Summary: {len(file_hits)} files, {total_hits} total hits, {high_confidence} high-confidence matches")
    
    def log_refactoring_groups(self, groups: List[RefactoringGroup], title: str = "Refactoring Groups"):
        """
        Log refactoring groups with file listings using Rich Tree.
        
        Args:
            groups: List of refactoring groups
            title: Section title
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            self.print_subsection_header(title, "🔧")
            if not groups:
                print("   No refactoring groups identified.")
                return
            for i, group in enumerate(groups, 1):
                priority_emoji = self._get_priority_emoji(group.priority)
                print(f"{i}. {priority_emoji} {group.group_name} ({len(group.files)} files)")
                for file_path in group.files:
                    print(f"   • {file_path}")
            return
        
        if not groups:
            self.console.print(f"\n🔧 {title}")
            self.console.print("   No refactoring groups identified.")
            return
        
        # Create Rich tree for refactoring groups
        tree = Tree(f"🔧 {title}")
        
        for i, group in enumerate(groups, 1):
            priority_emoji = self._get_priority_emoji(group.priority)
            
            # Group node with metadata
            group_text = f"[bold]{priority_emoji} {group.group_name}[/bold]"
            group_node = tree.add(group_text)
            
            # Add metadata sub-node
            metadata_text = f"[dim]Priority: {group.priority.title()} | Patterns: {group.patterns_count} | Effort: {group.estimated_effort}[/dim]"
            group_node.add(metadata_text)
            
            # Add files sub-node
            files_text = f"[cyan]Files ({len(group.files)})[/cyan]"
            files_node = group_node.add(files_text)
            
            # Add individual files
            for file_path in group.files:
                truncated = self._truncate_path(file_path, 50)
                files_node.add(f"[green]✓[/green] {truncated}")
        
        self.console.print(tree)
        
        # Summary
        total_files = sum(len(group.files) for group in groups)
        total_patterns = sum(group.patterns_count for group in groups)
        self.console.print(f"\n📊 Summary: {len(groups)} groups, {total_files} files, {total_patterns} patterns to refactor")
    
    def log_agent_parameters(self, params: AgentParameters, title: str = "Agent Configuration"):
        """
        Log agent/model parameters and configuration using Rich panels.
        
        Args:
            params: Agent parameters to display
            title: Section title
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            self.print_subsection_header(title, "🤖")
            mode_emoji = "💾" if params.mode == "mock" else "🌐"
            print(f"   {mode_emoji} Execution Mode: {params.mode.upper()}")
            print(f"   🧠 Model: {params.model_name}")
            print(f"   🌡️ Temperature: {params.temperature}")
            return
        
        mode_emoji = "💾" if params.mode == "mock" else "🌐"
        mode_color = "blue" if params.mode == "mock" else "green"
        
        # Create content for the panel
        content = f"""[bold]{mode_emoji} Execution Mode:[/bold] [{mode_color}]{params.mode.upper()}[/{mode_color}]
[bold]🧠 Model:[/bold] [cyan]{params.model_name}[/cyan]
[bold]🌡️ Temperature:[/bold] [yellow]{params.temperature}[/yellow]
[bold]📝 Max Tokens:[/bold] [green]{params.max_tokens:,}[/green]
[bold]📋 Response Format:[/bold] [magenta]{params.response_format}[/magenta]
[bold]💭 Prompt Type:[/bold] [cyan]{params.prompt_type}[/cyan]

[bold]📁 Data Source:[/bold] {'[blue]Cached data for fast iteration[/blue]' if params.mode == 'mock' else '[green]Live MCP services[/green]'}"""
        
        panel = Panel(
            content,
            title=f"🤖 {title}",
            border_style=mode_color,
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def log_git_diff(self, file_path: str, diff_content: str, additions: int = 0, deletions: int = 0):
        """
        Log a nicely formatted git diff for a file with Rich styling.
        
        Args:
            file_path: Path to the file
            diff_content: Git diff content
            additions: Number of additions
            deletions: Number of deletions
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print without colors
            print(f"\nUpdated {self._truncate_path(file_path, 60)}")
            if additions > 0 or deletions > 0:
                print(f"   {additions} additions, {deletions} deletions")
            print("-" * 70)
            
            if diff_content.strip():
                lines = diff_content.split('\n')
                for line in lines:
                    if line.startswith('+++') or line.startswith('---'):
                        continue
                    elif line.startswith('@@'):
                        print(f"   {line}")
                    elif line.startswith('+'):
                        print(f"   + {line[1:]}")
                    elif line.startswith('-'):
                        print(f"   - {line[1:]}")
                    else:
                        print(f"      {line}")
            return
        
        # Rich formatting with background colors
        self.console.print(f"\nUpdated [cyan]{self._truncate_path(file_path, 60)}[/cyan]")
        if additions > 0 or deletions > 0:
            self.console.print(f"   [dim]{additions} additions, {deletions} deletions[/dim]")
        self.console.print("-" * 70)
        
        if diff_content.strip():
            lines = diff_content.split('\n')
            for line in lines:
                if line.startswith('+++') or line.startswith('---'):
                    continue  # Skip file headers
                elif line.startswith('@@'):
                    self.console.print(f"   [blue]{line}[/blue]")
                elif line.startswith('+'):
                    # Green background for additions
                    self.console.print(f"   [green on dark_green]{line}[/green on dark_green]")
                elif line.startswith('-'):
                    # Red background for deletions  
                    self.console.print(f"   [red on dark_red]{line}[/red on dark_red]")
                else:
                    self.console.print(f"      [dim]{line}[/dim]")
        else:
            self.console.print("   [dim](No changes to display)[/dim]")
    
    def log_batch_processing_status(self, batch_id: str, files_processed: int, total_files: int, 
                                    duration: float, errors: int = 0):
        """
        Log batch processing status with Rich progress bars.
        
        Args:
            batch_id: Batch identifier
            files_processed: Number of files processed
            total_files: Total files in batch
            duration: Processing duration in seconds
            errors: Number of errors encountered
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            progress_percent = (files_processed / total_files * 100) if total_files > 0 else 0
            progress_bar = "█" * int(progress_percent / 5) + "░" * (20 - int(progress_percent / 5))
            status_emoji = "✅" if errors == 0 else "⚠️" if errors < files_processed / 2 else "❌"
            print(f"\n{status_emoji} Batch {batch_id} Progress:")
            print(f"   📊 [{progress_bar}] {progress_percent:.1f}%")
            print(f"   📁 Files: {files_processed}/{total_files}")
            return
        
        progress_percent = (files_processed / total_files * 100) if total_files > 0 else 0
        status_emoji = "✅" if errors == 0 else "⚠️" if errors < files_processed / 2 else "❌"
        status_color = "green" if errors == 0 else "yellow" if errors < files_processed / 2 else "red"
        
        # Create a simple progress display using Rich
        content = f"""[bold]{status_emoji} Batch {batch_id} Progress[/bold]

[bold]📊 Progress:[/bold] [cyan]{progress_percent:.1f}%[/cyan] completed
[bold]📁 Files:[/bold] [green]{files_processed}[/green]/[blue]{total_files}[/blue] processed
[bold]⏱️ Duration:[/bold] [yellow]{duration:.1f}s[/yellow]"""
        
        if errors > 0:
            content += f"\n[bold]⚠️ Errors:[/bold] [red]{errors}[/red]"
        
        panel = Panel(
            content,
            title="⚙️ Batch Processing Status",
            border_style=status_color,
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def log_batch_file_results(self, files_processed: List[Dict[str, Any]], batch_name: str = "Batch Processing Results"):
        """
        Log detailed results for each file in a batch, including files with no changes.
        
        Args:
            files_processed: List of file processing results with status info
            batch_name: Name of the batch being processed
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            self.print_subsection_header(batch_name, "📊")
            if not files_processed:
                print("   No files processed.")
                return
            for i, file_result in enumerate(files_processed, 1):
                status = file_result.get('status', 'unknown')
                status_emoji = "✅" if status == "modified" else "➖" if status == "no_changes" else "❌" if status == "error" else "❓"
                print(f"{i}. {status_emoji} {file_result.get('file_path', 'Unknown')} - {status}")
            return
        
        if not files_processed:
            self.console.print(f"\n📊 {batch_name}")
            self.console.print("   No files processed.")
            return
        
        # Create Rich table for file results
        table = Table(title=f"📊 {batch_name}", show_header=True, header_style="bold blue")
        table.add_column("#", style="dim", width=3)
        table.add_column("File Path", style="cyan", min_width=30)
        table.add_column("Status", style="white", justify="center")
        table.add_column("Changes", style="yellow", justify="right")
        table.add_column("Duration", style="blue", justify="right")
        table.add_column("Details", style="dim")
        
        # Add rows for each file
        for i, file_result in enumerate(files_processed, 1):
            file_path = file_result.get('file_path', 'Unknown')
            status = file_result.get('status', 'unknown')
            changes_count = file_result.get('changes_count', 0)
            duration = file_result.get('duration_ms', 0)
            error_msg = file_result.get('error', '')
            
            # Status with color and emoji
            if status == "modified":
                status_display = "[green]✅ Modified[/green]"
            elif status == "no_changes":
                status_display = "[blue]➖ No changes[/blue]"
            elif status == "error":
                status_display = "[red]❌ Error[/red]"
            elif status == "skipped":
                status_display = "[yellow]⏭️ Skipped[/yellow]"
            else:
                status_display = "[dim]❓ Unknown[/dim]"
            
            # Format changes
            changes_display = str(changes_count) if changes_count > 0 else "-"
            
            # Format duration
            if duration > 1000:
                duration_display = f"{duration/1000:.1f}s"
            elif duration > 0:
                duration_display = f"{duration}ms"
            else:
                duration_display = "-"
            
            # Details (error message or file size)
            details = error_msg[:30] + "..." if error_msg and len(error_msg) > 30 else error_msg
            if not details and 'file_size' in file_result:
                details = self._format_file_size(file_result['file_size'])
            
            truncated_path = self._truncate_path(file_path, 40)
            
            table.add_row(
                str(i),
                truncated_path,
                status_display,
                changes_display,
                duration_display,
                details or "-"
            )
        
        self.console.print(table)
        
        # Summary statistics
        total_files = len(files_processed)
        modified_count = len([f for f in files_processed if f.get('status') == 'modified'])
        no_changes_count = len([f for f in files_processed if f.get('status') == 'no_changes'])
        error_count = len([f for f in files_processed if f.get('status') == 'error'])
        skipped_count = len([f for f in files_processed if f.get('status') == 'skipped'])
        total_changes = sum(f.get('changes_count', 0) for f in files_processed)
        
        summary_text = f"""[bold]📈 Summary:[/bold] [cyan]{total_files}[/cyan] files processed
[green]✅ Modified:[/green] {modified_count} ([yellow]{total_changes}[/yellow] total changes)
[blue]➖ No changes:[/blue] {no_changes_count}
[yellow]⏭️ Skipped:[/yellow] {skipped_count}"""
        
        if error_count > 0:
            summary_text += f"\n[red]❌ Errors:[/red] {error_count}"
        
        self.console.print(f"\n{summary_text}")

    def log_workflow_summary(self, total_duration: float, steps_completed: int, 
                            total_steps: int, success_rate: float):
        """
        Log final workflow summary.
        
        Args:
            total_duration: Total workflow duration
            steps_completed: Number of completed steps
            total_steps: Total number of steps
            success_rate: Success rate percentage
        """
        self.print_section_header("Workflow Summary", "🎉")
        
        status_emoji = "✅" if success_rate >= 95 else "⚠️" if success_rate >= 80 else "❌"
        
        print(f"{status_emoji} Workflow Status: {steps_completed}/{total_steps} steps completed")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Total Duration: {total_duration:.1f} seconds")
        print(f"🚀 Workflow: {self.workflow_name}")
        
        if success_rate >= 95:
            print("🎊 Excellent! All major components completed successfully.")
        elif success_rate >= 80:
            print("👍 Good! Most components completed with minor issues.")
        else:
            print("⚠️  Some issues encountered. Review logs for details.")


# Convenience functions for quick usage
def create_sample_file_hits() -> List[FileHit]:
    """Create sample file hits for demo purposes."""
    return [
        FileHit("src/config/database.py", 5, "python", 0.95, 2048, 
                ["DATABASE_URL = 'postgresql://...postgres_air'", "DB_NAME = 'postgres_air'"]),
        FileHit("sql/migrations/001_initial.sql", 12, "sql", 0.88, 4096,
                ["CREATE DATABASE postgres_air;", "USE postgres_air;"]),
        FileHit("docker-compose.yml", 3, "config", 0.75, 1024,
                ["POSTGRES_DB: postgres_air"]),
        FileHit("README.md", 2, "markdown", 0.65, 8192,
                ["## postgres_air Database Setup"]),
    ]


def create_sample_refactoring_groups() -> List[RefactoringGroup]:
    """Create sample refactoring groups for demo purposes."""
    return [
        RefactoringGroup("Database Configuration", 
                        ["src/config/database.py", "config/settings.yaml", ".env"], 
                        8, "high", "2-3 hours"),
        RefactoringGroup("SQL Scripts", 
                        ["sql/migrations/001_initial.sql", "sql/queries/reports.sql"], 
                        12, "high", "4-6 hours"),
        RefactoringGroup("Docker Configuration", 
                        ["docker-compose.yml", "Dockerfile"], 
                        3, "medium", "1-2 hours"),
        RefactoringGroup("Documentation", 
                        ["README.md", "docs/setup.md"], 
                        2, "low", "30 minutes"),
    ]


def create_sample_agent_params(mode: str = "mock") -> AgentParameters:
    """Create sample agent parameters optimized for database decommissioning refactoring."""
    return AgentParameters(
        mode=mode,
        model_name="gpt-4-nano" if mode == "real" else "mock-model",
        temperature=0.2,  # Slightly higher for creative refactoring solutions but still conservative
        max_tokens=8000,  # Increased for comprehensive database analysis and planning
        response_format="json_object",
        prompt_type="database_decommissioning_refactoring"
    )


def create_sample_batch_results() -> List[Dict[str, Any]]:
    """Create sample batch file processing results for demo purposes."""
    return [
        {
            "file_path": "src/config/database.py",
            "status": "modified",
            "changes_count": 3,
            "duration_ms": 1250,
            "file_size": 2048
        },
        {
            "file_path": "sql/migrations/001_initial.sql", 
            "status": "modified",
            "changes_count": 8,
            "duration_ms": 2100,
            "file_size": 4096
        },
        {
            "file_path": "tests/test_database.py",
            "status": "no_changes",
            "changes_count": 0,
            "duration_ms": 450,
            "file_size": 1536
        },
        {
            "file_path": "docker-compose.yml",
            "status": "modified", 
            "changes_count": 1,
            "duration_ms": 780,
            "file_size": 1024
        },
        {
            "file_path": "README.md",
            "status": "no_changes",
            "changes_count": 0,
            "duration_ms": 320,
            "file_size": 8192
        },
        {
            "file_path": "config/invalid_file.json",
            "status": "error",
            "changes_count": 0,
            "duration_ms": 150,
            "error": "File not found or invalid JSON format"
        },
        {
            "file_path": "docs/legacy_setup.md",
            "status": "skipped",
            "changes_count": 0,
            "duration_ms": 0,
            "file_size": 512
        }
    ]