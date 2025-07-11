"""
Enhanced Logging System for Database Decommissioning Workflow.

This module provides comprehensive logging functionality to track all aspects
of the database decommissioning process with proper formatting and context.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import asyncio

@dataclass
class WorkflowMetrics:
    """Metrics tracking for workflow execution."""
    start_time: float
    end_time: Optional[float] = None
    repositories_processed: int = 0
    files_discovered: int = 0
    files_processed: int = 0
    files_modified: int = 0
    errors_encountered: int = 0
    warnings_generated: int = 0
    database_name: str = ""
    
    @property
    def duration(self) -> float:
        """Calculate workflow duration."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        result = asdict(self)
        # Include the duration property since asdict() doesn't include @property methods
        result['duration'] = self.duration
        return result

class DatabaseWorkflowLogger:
    """Enhanced logger for database decommissioning workflows."""
    
    def __init__(self, database_name: str, log_level: str = "INFO"):
        self.database_name = database_name
        self.metrics = WorkflowMetrics(
            start_time=time.time(),
            database_name=database_name
        )
        
        # Set up logger
        self.logger = logging.getLogger(f"db_decommission.{database_name}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Track workflow state
        self.current_step = ""
        self.current_repository = ""
        self.step_metrics = {}
        
    def log_workflow_start(self, target_repos: List[str], config: Dict[str, Any]):
        """Log workflow initialization."""
        self.logger.info("=" * 80)
        self.logger.info(f"DATABASE DECOMMISSIONING WORKFLOW STARTED")
        self.logger.info(f"Database: {self.database_name}")
        self.logger.info(f"Target Repositories: {len(target_repos)}")
        self.logger.info(f"Workflow Configuration: {json.dumps(config, indent=2)}")
        self.logger.info("=" * 80)
        
        for i, repo in enumerate(target_repos, 1):
            self.logger.info(f"Repository {i}: {repo}")
    
    def log_workflow_end(self, success: bool = True):
        """Log workflow completion."""
        self.metrics.end_time = time.time()
        
        self.logger.info("=" * 80)
        if success:
            self.logger.info(f"DATABASE DECOMMISSIONING WORKFLOW COMPLETED SUCCESSFULLY")
        else:
            self.logger.error(f"DATABASE DECOMMISSIONING WORKFLOW FAILED")
        
        self.logger.info(f"Total Duration: {self.metrics.duration:.2f} seconds")
        self.logger.info(f"Repositories Processed: {self.metrics.repositories_processed}")
        self.logger.info(f"Files Discovered: {self.metrics.files_discovered}")
        self.logger.info(f"Files Processed: {self.metrics.files_processed}")
        self.logger.info(f"Files Modified: {self.metrics.files_modified}")
        self.logger.info(f"Errors Encountered: {self.metrics.errors_encountered}")
        self.logger.info(f"Warnings Generated: {self.metrics.warnings_generated}")
        self.logger.info("=" * 80)
        
    def log_step_start(self, step_name: str, step_description: str, parameters: Dict[str, Any] = None):
        """Log the start of a workflow step."""
        self.current_step = step_name
        self.step_metrics[step_name] = {
            "start_time": time.time(),
            "description": step_description,
            "parameters": parameters or {}
        }
        
        self.logger.info(f"🚀 STEP START: {step_name}")
        self.logger.info(f"   Description: {step_description}")
        if parameters:
            self.logger.info(f"   Parameters: {json.dumps(parameters, indent=4)}")
    
    def log_step_end(self, step_name: str, result: Dict[str, Any], success: bool = True):
        """Log the end of a workflow step."""
        if step_name in self.step_metrics:
            self.step_metrics[step_name]["end_time"] = time.time()
            self.step_metrics[step_name]["duration"] = (
                self.step_metrics[step_name]["end_time"] - 
                self.step_metrics[step_name]["start_time"]
            )
            self.step_metrics[step_name]["success"] = success
            self.step_metrics[step_name]["result"] = result
        
        status_icon = "✅" if success else "❌"
        duration = self.step_metrics.get(step_name, {}).get("duration", 0)
        
        self.logger.info(f"{status_icon} STEP END: {step_name} (Duration: {duration:.2f}s)")
        
        if not success and "error" in result:
            self.logger.error(f"   Error: {result['error']}")
            self.metrics.errors_encountered += 1
        elif result:
            # Log key result metrics
            if "total_files" in result:
                self.logger.info(f"   Files Found: {result['total_files']}")
            if "files_processed" in result:
                self.logger.info(f"   Files Processed: {result['files_processed']}")
            if "files_modified" in result:
                self.logger.info(f"   Files Modified: {result['files_modified']}")
    
    def log_repository_start(self, repo_url: str, repo_owner: str, repo_name: str):
        """Log the start of repository processing."""
        self.current_repository = f"{repo_owner}/{repo_name}"
        self.logger.info(f"📦 REPOSITORY START: {self.current_repository}")
        self.logger.info(f"   URL: {repo_url}")
        
    def log_repository_end(self, repo_owner: str, repo_name: str, result: Dict[str, Any]):
        """Log the end of repository processing."""
        repo_name_full = f"{repo_owner}/{repo_name}"
        files_processed = result.get("files_processed", 0)
        success = result.get("success", True)
        
        status_icon = "✅" if success else "❌"
        self.logger.info(f"{status_icon} REPOSITORY END: {repo_name_full}")
        self.logger.info(f"   Files Processed: {files_processed}")
        
        if success:
            self.metrics.repositories_processed += 1
            self.metrics.files_processed += files_processed
        else:
            self.logger.error(f"   Error: {result.get('error', 'Unknown error')}")
    
    def log_pattern_discovery(self, discovery_result: Dict[str, Any]):
        """Log pattern discovery results."""
        total_files = discovery_result.get("total_files", 0)
        matched_files = discovery_result.get("matched_files", 0)
        confidence_dist = discovery_result.get("confidence_distribution", {})
        high_confidence = confidence_dist.get("high_confidence", 0)
        matches_by_type = discovery_result.get("files_by_type", {})
        
        self.logger.info(f"🔍 PATTERN DISCOVERY RESULTS:")
        self.logger.info(f"   Total Files Found: {total_files}")
        self.logger.info(f"   Files Matched: {matched_files}")
        self.logger.info(f"   High Confidence Files: {high_confidence}")
        
        self.metrics.files_discovered += total_files
        
        # Log detailed files table if files were found (show all files, not just matched ones)
        matched_files_data = discovery_result.get("files", [])
        repo_analysis = discovery_result.get("repository_analysis", {})
        all_files_data = repo_analysis.get("files", [])
        
        # If we have matched files, show those with full details
        if matched_files_data:
            self.log_files_table(matched_files_data, show_pattern_matches=True)
        # If we have files but no matches, show all files without pattern match details
        elif all_files_data:
            # Convert all files to display format for the table
            display_files = []
            for file_info in all_files_data:
                display_file = {
                    "path": file_info.get("path", ""),
                    "source_type": file_info.get("type", "unknown"),
                    "confidence": 0.0,  # No matches found
                    "match_count": 0,
                    "size": file_info.get("size", len(file_info.get("content", ""))),
                    "content": file_info.get("content", "")
                }
                display_files.append(display_file)
            self.log_files_table(display_files, show_pattern_matches=False)
        
        if matches_by_type:
            self.logger.info(f"   Files by Source Type:")
            for source_type, files in matches_by_type.items():
                self.logger.info(f"     {source_type}: {len(files)} files")
                
        frameworks = discovery_result.get("frameworks_detected", [])
        if frameworks:
            self.logger.info(f"   Detected Frameworks: {', '.join(frameworks)}")
    
    def log_files_table(self, files_data: List[Dict[str, Any]], show_pattern_matches: bool = True):
        """Log files found in a nicely formatted table."""
        if not files_data:
            return
            
        self.logger.info(f"")
        self.logger.info(f"📁 FILES DISCOVERED:")
        self.logger.info(f"{'='*120}")
        
        # Table header
        header = f"{'#':<3} {'File Path':<50} {'Type':<15} {'Matches':<8} {'Confidence':<12} {'Size':<8}"
        self.logger.info(header)
        self.logger.info(f"{'-'*120}")
        
        # Sort files by confidence score (descending), then by file path for consistent display
        sorted_files = sorted(files_data, key=lambda f: (f.get('confidence', 0), f.get('path', '')), reverse=True)
        
        for idx, file_info in enumerate(sorted_files, 1):
            file_path = file_info.get('path', 'Unknown')
            source_type = file_info.get('source_type', 'unknown')
            confidence = file_info.get('confidence', 0.0)
            match_count = file_info.get('match_count', 0)
            
            # Truncate long file paths for display
            display_path = file_path if len(file_path) <= 47 else f"...{file_path[-44:]}"
            
            # Get file size if available
            file_size = file_info.get('size', len(file_info.get('content', '')))
            size_str = self._format_file_size(file_size)
            
            # Format confidence with color indicators
            confidence_str = f"{confidence:.2f}"
            if confidence >= 0.8:
                confidence_indicator = "🟢"
            elif confidence >= 0.5:
                confidence_indicator = "🟡"
            elif confidence > 0.0:
                confidence_indicator = "🔴"
            else:
                confidence_indicator = "⚪"  # No matches found
            
            row = f"{idx:<3} {display_path:<50} {source_type:<15} {match_count:<8} {confidence_indicator} {confidence_str:<9} {size_str:<8}"
            self.logger.info(row)
        
        self.logger.info(f"{'='*120}")
        self.logger.info(f"")
        
        # Log pattern matches summary for high-confidence files (only if requested)
        if show_pattern_matches:
            high_conf_files = [f for f in files_data if f.get('confidence', 0) >= 0.8]
            if high_conf_files:
                self.logger.info(f"🎯 HIGH CONFIDENCE PATTERN MATCHES:")
                for file_info in high_conf_files[:5]:  # Show top 5
                    file_path = file_info.get('path', 'Unknown')
                    matches = file_info.get('pattern_matches', [])
                    if matches:
                        self.logger.info(f"   📄 {file_path}:")
                        for match in matches[:3]:  # Show top 3 matches per file
                            pattern = match.get('pattern', 'unknown')
                            context = match.get('context', '')[:100]  # First 100 chars
                            self.logger.info(f"      • Pattern: '{pattern}' → {context}...")
                self.logger.info(f"")
        else:
            # Show a note about no pattern matches
            self.logger.info(f"📝 NOTE: Files discovered but no database pattern matches found for the specified database name.")
            self.logger.info(f"")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.1f}MB"
    
    def log_file_processing(self, file_path: str, operation: str, result: str, 
                          source_type: str = "", changes_made: int = 0):
        """Log individual file processing."""
        status_icons = {
            "success": "✅",
            "modified": "🔧", 
            "skipped": "⏭️",
            "error": "❌",
            "warning": "⚠️"
        }
        
        icon = status_icons.get(result, "ℹ️")
        
        self.logger.info(f"  {icon} File: {file_path}")
        self.logger.info(f"     Operation: {operation}")
        self.logger.info(f"     Result: {result}")
        
        if source_type:
            self.logger.info(f"     Source Type: {source_type}")
        
        if changes_made > 0:
            self.logger.info(f"     Changes Made: {changes_made}")
            self.metrics.files_modified += 1
        
        if result == "error":
            self.metrics.errors_encountered += 1
        elif result == "warning":
            self.metrics.warnings_generated += 1
    
    def log_batch_processing(self, batch_number: int, total_batches: int, 
                           files_in_batch: int, batch_result: Dict[str, Any]):
        """Log batch processing results."""
        self.logger.info(f"📁 BATCH {batch_number}/{total_batches} PROCESSING:")
        self.logger.info(f"   Files in Batch: {files_in_batch}")
        
        if "files_processed" in batch_result:
            self.logger.info(f"   Files Processed: {batch_result['files_processed']}")
        
        if "files_modified" in batch_result:
            self.logger.info(f"   Files Modified: {batch_result['files_modified']}")
        
        if "errors" in batch_result and batch_result["errors"]:
            self.logger.warning(f"   Errors in Batch: {len(batch_result['errors'])}")
            for error in batch_result["errors"]:
                self.logger.error(f"     - {error}")
    
    def log_mcp_operation(self, client_name: str, operation: str, 
                         parameters: Dict[str, Any], result: Any, 
                         duration: float, success: bool = True):
        """Log MCP client operations."""
        status_icon = "✅" if success else "❌"
        
        self.logger.debug(f"🔌 MCP OPERATION: {client_name}.{operation}")
        self.logger.debug(f"   Parameters: {json.dumps(parameters, indent=4)}")
        self.logger.debug(f"   Duration: {duration:.3f}s")
        self.logger.debug(f"   Status: {status_icon}")
        
        if not success:
            self.logger.error(f"   Error: {result}")
            self.metrics.errors_encountered += 1
    
    def log_rule_application(self, rule_file: str, rules_applied: List[str], 
                           file_path: str, changes_made: int):
        """Log application of decommissioning rules."""
        self.logger.info(f"📋 RULES APPLIED:")
        self.logger.info(f"   Rule File: {rule_file}")
        self.logger.info(f"   Target File: {file_path}")
        self.logger.info(f"   Rules Applied: {len(rules_applied)}")
        self.logger.info(f"   Changes Made: {changes_made}")
        
        for rule in rules_applied:
            self.logger.debug(f"     - {rule}")
    
    def log_quality_check(self, check_name: str, result: str, details: Dict[str, Any]):
        """Log quality assurance checks."""
        status_icons = {
            "pass": "✅",
            "fail": "❌", 
            "warning": "⚠️",
            "skip": "⏭️"
        }
        
        icon = status_icons.get(result, "ℹ️")
        
        self.logger.info(f"🔍 QUALITY CHECK: {check_name}")
        self.logger.info(f"   Result: {icon} {result.upper()}")
        
        if details:
            for key, value in details.items():
                self.logger.info(f"   {key}: {value}")
        
        if result == "fail":
            self.metrics.errors_encountered += 1
        elif result == "warning":
            self.metrics.warnings_generated += 1
    
    def log_slack_notification(self, channel: str, message: str, success: bool = True):
        """Log Slack notifications."""
        status_icon = "✅" if success else "❌"
        
        self.logger.info(f"💬 SLACK NOTIFICATION: {status_icon}")
        self.logger.info(f"   Channel: {channel}")
        self.logger.info(f"   Message Preview: {message[:100]}...")
        
        if not success:
            self.metrics.errors_encountered += 1
    
    def log_pull_request_creation(self, pr_title: str, pr_url: str, success: bool = True):
        """Log pull request creation."""
        status_icon = "✅" if success else "❌"
        
        self.logger.info(f"🔀 PULL REQUEST CREATION: {status_icon}")
        self.logger.info(f"   Title: {pr_title}")
        
        if success:
            self.logger.info(f"   URL: {pr_url}")
        else:
            self.metrics.errors_encountered += 1
    
    def log_warning(self, message: str, context: Dict[str, Any] = None):
        """Log a warning message."""
        self.logger.warning(f"⚠️ WARNING: {message}")
        if context:
            self.logger.warning(f"   Context: {json.dumps(context, indent=4)}")
        self.metrics.warnings_generated += 1
    
    def log_error(self, message: str, exception: Exception = None, context: Dict[str, Any] = None):
        """Log an error message."""
        self.logger.error(f"❌ ERROR: {message}")
        
        if exception:
            self.logger.error(f"   Exception: {type(exception).__name__}: {str(exception)}")
        
        if context:
            self.logger.error(f"   Context: {json.dumps(context, indent=4)}")
        
        self.metrics.errors_encountered += 1
    
    def log_info(self, message: str, context: Dict[str, Any] = None):
        """Log an info message."""
        self.logger.info(f"ℹ️ INFO: {message}")
        if context:
            self.logger.info(f"   Context: {json.dumps(context, indent=4)}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive workflow metrics."""
        return {
            "workflow_metrics": self.metrics.to_dict(),
            "step_metrics": self.step_metrics,
            "performance_summary": {
                "total_duration": self.metrics.duration,
                "avg_time_per_repo": (
                    self.metrics.duration / max(self.metrics.repositories_processed, 1)
                ),
                "files_per_second": (
                    self.metrics.files_processed / max(self.metrics.duration, 1)
                ),
                "success_rate": (
                    1 - (self.metrics.errors_encountered / 
                         max(self.metrics.files_processed, 1))
                ) if self.metrics.files_processed > 0 else 0
            }
        }
    
    def export_logs(self, output_path: str):
        """Export workflow logs and metrics to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Clean step metrics to avoid circular references
            cleaned_step_metrics = {}
            for step_name, step_data in self.step_metrics.items():
                cleaned_step_data = {
                    "start_time": step_data.get("start_time"),
                    "end_time": step_data.get("end_time"),
                    "duration": step_data.get("duration"),
                    "description": step_data.get("description"),
                    "parameters": step_data.get("parameters", {}),
                    "success": step_data.get("success", True)
                }
                
                # Safely include result data, excluding potential circular refs
                if "result" in step_data:
                    result = step_data["result"]
                    if isinstance(result, dict):
                        # Create a clean copy excluding potential circular references
                        cleaned_result = {}
                        safe_keys = ["database_name", "total_repositories", "repositories_processed", 
                                   "repositories_failed", "total_files_processed", "total_files_modified",
                                   "workflow_version", "success", "duration", "components_initialized",
                                   "environment_status", "validation_issues", "pattern_count", 
                                   "config_loaded", "qa_checks", "all_checks_passed", "quality_score",
                                   "recommendations", "summary", "features_used", "next_steps"]
                        
                        for key in safe_keys:
                            if key in result:
                                cleaned_result[key] = result[key]
                        
                        cleaned_step_data["result"] = cleaned_result
                    else:
                        cleaned_step_data["result"] = str(result)
                
                cleaned_step_metrics[step_name] = cleaned_step_data
            
            # Create export data with cleaned metrics
            export_data = {
                "workflow_info": {
                    "database_name": self.database_name,
                    "timestamp": datetime.now().isoformat(),
                    "current_step": self.current_step,
                    "current_repository": self.current_repository
                },
                "metrics": {
                    "workflow_metrics": self.metrics.to_dict(),
                    "step_metrics": cleaned_step_metrics,
                    "performance_summary": {
                        "total_duration": self.metrics.duration,
                        "avg_time_per_repo": (
                            self.metrics.duration / max(self.metrics.repositories_processed, 1)
                        ),
                        "files_per_second": (
                            self.metrics.files_processed / max(self.metrics.duration, 1)
                        ),
                        "success_rate": (
                            1 - (self.metrics.errors_encountered / 
                                 max(self.metrics.files_processed, 1))
                        ) if self.metrics.files_processed > 0 else 0
                    }
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"📄 Workflow logs exported to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")

def create_workflow_logger(database_name: str, log_level: str = "INFO") -> DatabaseWorkflowLogger:
    """Factory function to create a configured workflow logger."""
    return DatabaseWorkflowLogger(database_name, log_level) 