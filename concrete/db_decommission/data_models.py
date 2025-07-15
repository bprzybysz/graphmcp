"""
Database Decommissioning Workflow Data Models.

This module contains data models for the database decommissioning workflow,
following GraphMCP patterns:
- Use dataclasses with type hints
- Include timestamps for tracking
- Make models pickle-safe for state management
- Include proper serialization methods
- Add utility methods for state management
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

# Import source type from classifier
from concrete.source_type_classifier import SourceType


@dataclass
class FileProcessingResult:
    """
    Result from processing a file during decommissioning.
    
    Compatibility class for AgenticFileProcessor with enhanced tracking.
    """
    file_path: str
    source_type: SourceType
    success: bool
    total_changes: int
    rules_applied: Optional[List[str]] = None
    error_message: Optional[str] = None
    timestamp: Optional[float] = None
    processing_duration_ms: Optional[int] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.rules_applied is None:
            self.rules_applied = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "file_path": self.file_path,
            "source_type": self.source_type.value if self.source_type else None,
            "success": self.success,
            "total_changes": self.total_changes,
            "rules_applied": self.rules_applied,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "processing_duration_ms": self.processing_duration_ms
        }


@dataclass
class WorkflowConfig:
    """
    Configuration for database decommissioning workflow.
    
    Centralized configuration with environment variable support.
    """
    database_name: str
    repo_owner: str
    repo_name: str
    max_parallel_steps: int = 4
    default_timeout: int = 120
    log_file: str = "dbworkflow.log"
    enable_console_logging: bool = True
    enable_json_logging: bool = True
    enable_slack_notifications: bool = True
    dry_run: bool = False
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "database_name": self.database_name,
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "max_parallel_steps": self.max_parallel_steps,
            "default_timeout": self.default_timeout,
            "log_file": self.log_file,
            "enable_console_logging": self.enable_console_logging,
            "enable_json_logging": self.enable_json_logging,
            "enable_slack_notifications": self.enable_slack_notifications,
            "dry_run": self.dry_run,
            "timestamp": self.timestamp
        }


class ValidationResult(Enum):
    """Enumeration of validation results."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class QualityAssuranceResult:
    """
    Result from quality assurance checks.
    
    Comprehensive QA result with detailed metrics.
    """
    database_reference_check: ValidationResult
    rule_compliance_check: ValidationResult
    service_integrity_check: ValidationResult
    overall_status: ValidationResult
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.recommendations is None:
            self.recommendations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "database_reference_check": self.database_reference_check.value,
            "rule_compliance_check": self.rule_compliance_check.value,
            "service_integrity_check": self.service_integrity_check.value,
            "overall_status": self.overall_status.value,
            "details": self.details,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp
        }


@dataclass
class WorkflowStepResult:
    """
    Result from a single workflow step execution.
    
    Standardized step result with metrics and context.
    """
    step_name: str
    step_id: str
    success: bool
    duration_seconds: float
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.warnings is None:
            self.warnings = []
        if self.metrics is None:
            self.metrics = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "step_name": self.step_name,
            "step_id": self.step_id,
            "success": self.success,
            "duration_seconds": self.duration_seconds,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "timestamp": self.timestamp
        }


@dataclass
class DecommissioningSummary:
    """
    Summary of the entire decommissioning workflow.
    
    Comprehensive workflow summary with all key metrics.
    """
    workflow_id: str
    database_name: str
    total_files_processed: int
    successful_files: int
    failed_files: int
    total_changes: int
    rules_applied: List[str]
    execution_time_seconds: float
    quality_assurance: QualityAssuranceResult
    github_pr_url: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = time.time()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files_processed == 0:
            return 0.0
        return (self.successful_files / self.total_files_processed) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "database_name": self.database_name,
            "total_files_processed": self.total_files_processed,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "total_changes": self.total_changes,
            "rules_applied": self.rules_applied,
            "execution_time_seconds": self.execution_time_seconds,
            "quality_assurance": self.quality_assurance.to_dict() if self.quality_assurance else None,
            "github_pr_url": self.github_pr_url,
            "success_rate": self.success_rate,
            "timestamp": self.timestamp
        }