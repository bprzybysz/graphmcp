"""
Database Decommissioning Utilities.

This module contains shared utility functions for the database decommissioning workflow,
including workflow creation, configuration management, and helper functions.
"""

import json
import time
from typing import Any, Dict, List, Optional

# Import workflow components
from workflows.builder import WorkflowBuilder

# Import parameter service
from concrete.parameter_service import get_parameter_service

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig

# Import workflow steps
from .workflow_steps import (
    validate_environment_step,
    process_repositories_step,
    quality_assurance_step,
    apply_refactoring_step,
    create_github_pr_step,
    workflow_summary_step
)


# Removed create_structured_logger - using get_logger() directly


def initialize_environment_with_centralized_secrets():
    """
    Initialize environment with centralized parameter service.
    
    Returns:
        ParameterService: Initialized parameter service instance
    """
    return get_parameter_service()


def create_db_decommission_workflow(
    database_name: str = "example_database",
    target_repos: Optional[List[str]] = None,
    slack_channel: str = "C01234567",
    config_path: str = "mcp_config.json",
    workflow_id: Optional[str] = None
) -> "Workflow":
    """
    Create database decommissioning workflow with pattern discovery and contextual rules.
    
    This workflow includes:
    - Pattern discovery (replaces hardcoded files)
    - Source type classification for all file types
    - Contextual rules engine for intelligent processing
    - Comprehensive logging throughout
    
    Args:
        database_name: Name of the database to decommission (default: "example_database")
        target_repos: List of repository URLs to process (default: postgres-sample-dbs)
        slack_channel: Slack channel ID for notifications
        config_path: Path to MCP configuration file
        workflow_id: Unique workflow identifier
        
    Returns:
        Configured workflow ready for execution
    """
    # Set defaults
    if target_repos is None:
        target_repos = ["https://github.com/bprzybys-nc/postgres-sample-dbs"]
    
    # Create consistent workflow_id for visual logging
    if workflow_id is None:
        workflow_id = f"db-{database_name}-{int(time.time())}"
    
    # Extract repository owner and name from first target repo for branch/PR operations
    first_repo_url = target_repos[0] if target_repos else "https://github.com/bprzybys-nc/postgres-sample-dbs"
    repo_owner, repo_name = extract_repo_details(first_repo_url)
    
    workflow = (WorkflowBuilder(
        "db-decommission", 
        config_path,
        description=f"Decommissioning of {database_name} database with pattern discovery, contextual rules, and comprehensive logging"
    )
    
    .custom_step(
        "validate_environment", "Environment Validation & Setup",
        validate_environment_step,
        parameters={"database_name": database_name, "workflow_id": workflow_id},
        timeout_seconds=30
    )
    .custom_step(
        "process_repositories", "Repository Processing with Pattern Discovery",
        process_repositories_step,
        parameters={
            "target_repos": target_repos,
            "database_name": database_name,
            "slack_channel": slack_channel,
            "workflow_id": workflow_id
        },
        depends_on=["validate_environment"],
        timeout_seconds=600
    )
    .custom_step(
        "apply_refactoring", "Apply Contextual Refactoring Rules",
        apply_refactoring_step,
        parameters={
            "database_name": database_name,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "workflow_id": workflow_id
        },
        depends_on=["process_repositories"],
        timeout_seconds=300
    )
    .custom_step(
        "create_github_pr", "Create GitHub Pull Request",
        create_github_pr_step,
        parameters={
            "database_name": database_name,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "workflow_id": workflow_id
        },
        depends_on=["apply_refactoring"],
        timeout_seconds=180
    )
    .custom_step(
        "quality_assurance", "Quality Assurance & Validation",
        quality_assurance_step,
        parameters={
            "database_name": database_name,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "workflow_id": workflow_id
        },
        depends_on=["create_github_pr"],
        timeout_seconds=60
    )
    .custom_step(
        "workflow_summary", "Workflow Summary & Metrics",
        workflow_summary_step,
        parameters={"database_name": database_name, "workflow_id": workflow_id},
        depends_on=["quality_assurance"],
        timeout_seconds=30
    )
    .with_config(
        max_parallel_steps=4,
        default_timeout=120,
        stop_on_error=False,
        default_retry_count=3
    )
    .build())
    
    return workflow


async def run_decommission(
    database_name: str = "postgres_air",
    target_repos: Optional[List[str]] = None,
    slack_channel: str = "C01234567",
    workflow_id: Optional[str] = None
) -> Any:
    """
    Execute the database decommissioning workflow.
    
    Args:
        database_name: Name of the database to decommission
        target_repos: List of repository URLs to process
        slack_channel: Slack channel ID for notifications
        workflow_id: Unique workflow identifier
        
    Returns:
        Workflow execution result
    """
    # Create MCP configuration
    config = create_mcp_config()
    
    # Write config to file
    with open("mcp_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Set default repositories
    if target_repos is None:
        target_repos = ["https://github.com/bprzybys-nc/postgres-sample-dbs"]
    
    # Create workflow
    workflow = create_db_decommission_workflow(
        database_name=database_name,
        target_repos=target_repos,
        slack_channel=slack_channel,
        config_path="mcp_config.json",
        workflow_id=workflow_id
    )
    
    # Initialize structured logger
    workflow_id = f"db-decommission-{database_name}-{int(time.time())}"
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=workflow_id, config=config)
    
    try:
        # Execute workflow
        result = await workflow.execute()
        
        # Log final results
        logger.log_info("Workflow Execution Complete!")
        logger.log_info(f"Status: {result.status}")
        logger.log_info(f"Success Rate: {result.success_rate:.1f}%")
        logger.log_info(f"Duration: {result.duration_seconds:.1f}s")
        
        # Log repository processing results
        repo_result = result.get_step_result('process_repositories', {})
        if repo_result:
            logger.log_info(f"Database: {repo_result.get('database_name')}")
            logger.log_info(f"Repositories Processed: {repo_result.get('repositories_processed', 0)}")
            logger.log_info(f"Files Discovered: {repo_result.get('total_files_processed', 0)}")
            logger.log_info(f"Files Modified: {repo_result.get('total_files_modified', 0)}")
        
        return result
        
    finally:
        # Clean up workflow and MCP servers
        logger.log_info("Stopping workflow and cleaning up MCP servers...")
        await workflow.stop()


def create_mcp_config() -> Dict[str, Any]:
    """
    Create MCP configuration for database decommissioning workflow.
    
    Returns:
        Dict containing MCP server configuration
    """
    return {
        "mcpServers": {
            "ovr_github": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_PERSONAL_ACCESS_TOKEN"
                }
            },
            "ovr_slack": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-slack"],
                "env": {
                    "SLACK_BOT_TOKEN": "$SLACK_BOT_TOKEN"
                }
            },
            "ovr_repomix": {
                "command": "npx",
                "args": ["repomix", "--mcp"]
            }
        }
    }


def extract_repo_details(repo_url: str) -> tuple[str, str]:
    """
    Extract repository owner and name from URL.
    
    Args:
        repo_url: Repository URL
        
    Returns:
        Tuple of (owner, name)
    """
    if repo_url.startswith("https://github.com/"):
        repo_path = repo_url.replace("https://github.com/", "").rstrip("/")
        if "/" in repo_path:
            repo_owner, repo_name = repo_path.split("/", 1)
            return repo_owner, repo_name
    
    # Default fallback
    return "bprzybys-nc", "postgres-sample-dbs"


def generate_workflow_id(database_name: str) -> str:
    """
    Generate a unique workflow identifier.
    
    Args:
        database_name: Name of the database being decommissioned
        
    Returns:
        Unique workflow identifier
    """
    return f"db-{database_name}-{int(time.time())}"


def validate_workflow_parameters(
    database_name: str,
    target_repos: List[str],
    slack_channel: str
) -> Dict[str, Any]:
    """
    Validate workflow parameters before execution.
    
    Args:
        database_name: Name of the database to decommission
        target_repos: List of repository URLs to process
        slack_channel: Slack channel ID for notifications
        
    Returns:
        Dict containing validation results
    """
    validation_errors = []
    
    # Validate database name
    if not database_name or not database_name.strip():
        validation_errors.append("Database name cannot be empty")
    
    # Validate target repositories
    if not target_repos or len(target_repos) == 0:
        validation_errors.append("At least one target repository must be specified")
    
    for repo_url in target_repos:
        if not repo_url.startswith("https://github.com/"):
            validation_errors.append(f"Invalid repository URL format: {repo_url}")
    
    # Validate slack channel
    if not slack_channel or not slack_channel.strip():
        validation_errors.append("Slack channel cannot be empty")
    
    return {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors
    }


def create_workflow_config(
    database_name: str,
    target_repos: List[str],
    slack_channel: str,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create workflow configuration dictionary.
    
    Args:
        database_name: Name of the database to decommission
        target_repos: List of repository URLs to process
        slack_channel: Slack channel ID for notifications
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing workflow configuration
    """
    if workflow_id is None:
        workflow_id = generate_workflow_id(database_name)
    
    return {
        "workflow_id": workflow_id,
        "database_name": database_name,
        "target_repos": target_repos,
        "slack_channel": slack_channel,
        "workflow_version": "v2.0",
        "created_at": time.time(),
        "features": {
            "pattern_discovery": True,
            "contextual_rules_engine": True,
            "comprehensive_logging": True,
            "source_type_classification": True,
            "graceful_error_handling": True
        }
    }


def calculate_workflow_metrics(workflow_result: Any) -> Dict[str, Any]:
    """
    Calculate comprehensive workflow metrics from execution results.
    
    Args:
        workflow_result: Workflow execution result
        
    Returns:
        Dict containing calculated metrics
    """
    metrics = {
        "execution_time": workflow_result.duration_seconds,
        "success_rate": workflow_result.success_rate,
        "steps_completed": workflow_result.steps_completed,
        "total_steps": workflow_result.total_steps,
        "status": workflow_result.status
    }
    
    # Extract step-specific metrics
    step_metrics = {}
    for step_name in ["validate_environment", "process_repositories", "apply_refactoring", "create_github_pr", "quality_assurance", "workflow_summary"]:
        step_result = workflow_result.get_step_result(step_name, {})
        if step_result:
            step_metrics[step_name] = {
                "success": step_result.get("success", False),
                "duration": step_result.get("duration", 0)
            }
    
    metrics["step_metrics"] = step_metrics
    
    return metrics


def format_workflow_summary(
    workflow_result: Any,
    database_name: str
) -> str:
    """
    Format a human-readable workflow summary.
    
    Args:
        workflow_result: Workflow execution result
        database_name: Name of the database being decommissioned
        
    Returns:
        Formatted summary string
    """
    metrics = calculate_workflow_metrics(workflow_result)
    
    summary = f"""
🎉 Database Decommissioning Workflow Complete!

Database: {database_name}
Status: {metrics['status']}
Success Rate: {metrics['success_rate']:.1f}%
Duration: {metrics['execution_time']:.1f}s
Steps Completed: {metrics['steps_completed']}/{metrics['total_steps']}

Repository Processing Results:
"""
    
    repo_result = workflow_result.get_step_result('process_repositories', {})
    if repo_result:
        summary += f"""- Repositories Processed: {repo_result.get('repositories_processed', 0)}
- Files Discovered: {repo_result.get('total_files_processed', 0)}
- Files Modified: {repo_result.get('total_files_modified', 0)}
"""
    
    return summary.strip()


# Legacy compatibility functions (to be removed in Phase 2)
def create_logger_adapter(database_name: str) -> Any:
    """
    Create logger adapter for backward compatibility.
    
    Args:
        database_name: Name of database being decommissioned
        
    Returns:
        Logger adapter instance
    """
    workflow_id = f"db-decommission-{database_name}-{int(time.time())}"
    config = LoggingConfig.from_env()
    return get_logger(workflow_id=workflow_id, config=config)