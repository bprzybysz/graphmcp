"""
Database Decommissioning Workflow Module.

This module provides the main orchestration for database decommissioning workflow
with modular architecture for improved maintainability and testability.

Following the PRP principles:
- Single responsibility per module
- <500 lines per file
- Proper separation of concerns
- Structured logging integration
- Async-first design patterns
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

# Import main workflow components
from .workflow_steps import (
    quality_assurance_step,
    apply_refactoring_step,
    create_github_pr_step,
    workflow_summary_step
)

from .validation_helpers import validate_environment_step
from .repository_processors import process_repositories_step

from .data_models import (
    FileProcessingResult,
    WorkflowConfig,
    QualityAssuranceResult,
    ValidationResult,
    DecommissioningSummary,
    WorkflowStepResult
)

from .utils import (
    create_db_decommission_workflow,
    run_decommission,
    initialize_environment_with_centralized_secrets,
    create_mcp_config,
    extract_repo_details,
    generate_workflow_id,
    validate_workflow_parameters,
    create_workflow_config,
    calculate_workflow_metrics,
    format_workflow_summary
)

from .validation_checks import (
    perform_database_reference_check,
    perform_rule_compliance_check,
    perform_service_integrity_check,
    generate_recommendations
)

from .environment_validation import perform_environment_validation

from .repository_processors import (
    initialize_github_client,
    initialize_slack_client,
    initialize_repomix_client,
    send_slack_notification_with_retry
)

from .pattern_discovery import (
    AgenticFileProcessor,
    process_discovered_files_with_rules,
    log_pattern_discovery_visual,
    categorize_files_by_source_type,
    calculate_processing_metrics
)

# Set up module logger
logger = logging.getLogger(__name__)

# Version and metadata
__version__ = "2.0.0"
__author__ = "GraphMCP Database Decommissioning Team"

# Export main workflow functions
__all__ = [
    # Main workflow functions
    "create_db_decommission_workflow",
    "run_decommission",
    
    # Workflow steps
    "validate_environment_step",
    "process_repositories_step",
    "quality_assurance_step",
    "apply_refactoring_step",
    "create_github_pr_step",
    "workflow_summary_step",
    
    # Data models
    "FileProcessingResult",
    "WorkflowConfig",
    "QualityAssuranceResult",
    "ValidationResult",
    "DecommissioningSummary",
    "WorkflowStepResult",
    
    # Validation helpers
    "perform_database_reference_check",
    "perform_rule_compliance_check",
    "perform_service_integrity_check",
    "generate_recommendations",
    
    # Repository processors
    "initialize_github_client",
    "initialize_slack_client",
    "initialize_repomix_client",
    
    # Pattern discovery
    "AgenticFileProcessor",
    "process_discovered_files_with_rules",
    "log_pattern_discovery_visual",
    
    # Utilities
    "initialize_environment_with_centralized_secrets",
    "extract_repo_details",
    "generate_workflow_id",
    "validate_workflow_parameters",
    "create_workflow_config",
    "calculate_workflow_metrics",
    "format_workflow_summary",
]


# Main execution function for backward compatibility
async def main():
    """
    Main execution function for database decommissioning workflow.
    
    This function provides backward compatibility with the original db_decommission.py
    while using the new modular architecture.
    """
    # Default configuration
    database_name = "postgres_air"
    target_repos = ["https://github.com/bprzybys-nc/postgres-sample-dbs"]
    slack_channel = "C01234567"
    
    try:
        # Execute workflow
        result = await run_decommission(
            database_name=database_name,
            target_repos=target_repos,
            slack_channel=slack_channel
        )
        
        # Log final summary
        summary = format_workflow_summary(result, database_name)
        logger.info(summary)
        
        return result
        
    except Exception as e:
        logger.error(f"Database decommissioning workflow failed: {e}")
        raise


# Command-line interface
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the main workflow
    asyncio.run(main())