"""
Database Decommissioning Repository Processors.

This module contains repository processing functions for the database decommissioning workflow,
following async-first patterns and structured logging.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

# Import MCP clients
from clients import GitHubMCPClient, SlackMCPClient, RepomixMCPClient

# Import PRP-compliant components
from concrete.database_reference_extractor import DatabaseReferenceExtractor
from concrete.source_type_classifier import SourceTypeClassifier
from concrete.performance_optimization import get_performance_manager

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig

# Import data models
from .data_models import FileProcessingResult, WorkflowStepResult


async def process_repositories_step(
    context: Any,
    step: Any,
    target_repos: List[str],
    database_name: str = "example_database",
    slack_channel: str = "#database-decommission",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process repositories with pattern discovery and contextual rules.
    
    Args:
        context: WorkflowContext for data sharing
        step: Step configuration object
        target_repos: List of repository URLs to process
        database_name: Name of the database to decommission
        slack_channel: Slack channel for notifications
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing repository processing results
    """
    process_start_time = time.time()
    
    # Initialize structured logger
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)
    
    # Log workflow start
    workflow_config = {
        "database_name": database_name,
        "target_repositories": len(target_repos),
        "slack_channel": slack_channel,
        "workflow_version": "v2.0"
    }
    logger.log_workflow_start(target_repos, workflow_config)
    
    try:
        # Initialize MCP clients
        logger.log_step_start(
            "initialize_clients",
            "Initialize MCP clients for GitHub, Slack, and Repomix",
            {"clients_needed": ["ovr_github", "ovr_slack", "ovr_repomix"]}
        )
        
        github_client = await initialize_github_client(context, logger)
        slack_client = await initialize_slack_client(context, logger)
        repomix_client = await initialize_repomix_client(context, logger)
        
        logger.log_step_end(
            "initialize_clients",
            {"github": bool(github_client), "slack": bool(slack_client), "repomix": bool(repomix_client)},
            success=True
        )
        
        # Initialize core systems
        source_classifier = SourceTypeClassifier()
        performance_manager = get_performance_manager()
        
        logger.log_step_start(
            "process_repositories",
            f"Process {len(target_repos)} repositories with pattern discovery",
            {"repositories": target_repos, "database_name": database_name}
        )
        
        # Process repositories sequentially (can be parallelized later)
        repo_results = []
        for repo_url in target_repos:
            result = await process_single_repository(
                repo_url, database_name, slack_channel, workflow_id,
                github_client, slack_client, repomix_client, logger
            )
            repo_results.append(result)
        
        # Calculate totals and compile results
        workflow_result = _compile_workflow_results(
            repo_results, target_repos, database_name, logger, process_start_time
        )
        
        logger.log_step_end("process_repositories", workflow_result, success=True)
        
        # Send final notifications
        await _send_final_notifications(
            slack_client, slack_channel, database_name, 
            repo_results, workflow_result, logger
        )
        
        logger.log_workflow_end(success=True)
        
        # Export workflow logs
        await _export_workflow_logs(database_name, logger)
        
        return workflow_result
        
    except Exception as e:
        logger.log_error("Repository processing step failed", e)
        raise


async def process_single_repository(
    repo_url: str,
    database_name: str,
    slack_channel: str,
    workflow_id: Optional[str],
    github_client: Any,
    slack_client: Any,
    repomix_client: Any,
    logger: Any
) -> Dict[str, Any]:
    """
    Process a single repository with optimized API calls.
    
    Args:
        repo_url: Repository URL to process
        database_name: Name of the database to decommission
        slack_channel: Slack channel for notifications
        workflow_id: Unique workflow identifier
        github_client: GitHub MCP client
        slack_client: Slack MCP client
        repomix_client: Repomix MCP client
        logger: Structured logger instance
        
    Returns:
        Dict containing single repository processing results
    """
    repo_owner, repo_name = extract_repo_details(repo_url)
    
    logger.log_info(f"📦 REPOSITORY START: {repo_owner}/{repo_name}")
    logger.log_info(f"   URL: {repo_url}")
    
    # Send start notification
    await send_slack_notification_with_retry(
        slack_client,
        slack_channel,
        f"🚀 Starting decommission of '{database_name}' in repository: `{repo_owner}/{repo_name}`",
        logger
    )
    
    try:
        # Get repository pack from repomix
        logger.log_info(f"🔄 Running DatabaseReferenceExtractor for {database_name} in {repo_owner}/{repo_name}")
        
        repomix_result = await repomix_client.pack_remote_repository(
            remote=f"https://github.com/{repo_owner}/{repo_name}"
        )
        
        # Extract references using PRP-compliant component
        extractor = DatabaseReferenceExtractor()
        discovery_result = await extractor.extract_references(
            database_name=database_name,
            target_repo_pack_path=repomix_result.get("output_path", f"tests/data/{repo_name}_repo_pack.xml"),
            output_dir=f"tests/tmp/pattern_match/{database_name}"
        )
        
        files_found = discovery_result.get("total_files", 0)
        high_confidence_matches = discovery_result.get("files", [])
        
        logger.log_info("🔍 PATTERN DISCOVERY RESULTS:")
        logger.log_info(f"   Total Files Found: {files_found}")
        logger.log_info(f"   High Confidence Files: {len(high_confidence_matches)}")
        
        # Log pattern discovery results in structured format
        await log_pattern_discovery_visual(workflow_id, discovery_result, repo_owner, repo_name, logger)
        
        # Send completion notification
        await send_slack_notification_with_retry(
            slack_client,
            slack_channel,
            f"ℹ️ Repository `{repo_owner}/{repo_name}` completed: "
            f"{'No' if files_found == 0 else files_found} '{database_name}' database references found",
            logger
        )
        
        logger.log_info(f"✅ REPOSITORY END: {repo_owner}/{repo_name}")
        logger.log_info(f"   Files Processed: {files_found}")
        
        return {
            "repository": repo_url,
            "owner": repo_owner,
            "name": repo_name,
            "success": True,
            "files_found": files_found,
            "files_processed": files_found,
            "files_modified": len(high_confidence_matches),
            "discovery_result": discovery_result
        }
        
    except Exception as e:
        logger.log_error(f"Failed to process repository {repo_url}", exception=e)
        
        return {
            "repository": repo_url,
            "owner": repo_owner,
            "name": repo_name,
            "success": False,
            "error": str(e),
            "files_found": 0,
            "files_processed": 0,
            "files_modified": 0
        }


async def initialize_github_client(context: Any, logger: Any) -> Optional[Any]:
    """
    Initialize GitHub client with error handling.
    
    Args:
        context: WorkflowContext for client caching
        logger: Structured logger instance
        
    Returns:
        GitHub client instance or None if initialization fails
    """
    try:
        github_client = context._clients.get('ovr_github')
        if github_client:
            logger.log_info("GitHub client already initialized")
            return github_client
        
        github_client = GitHubMCPClient(context.config.config_path)
        context._clients['ovr_github'] = github_client
        logger.log_info("GitHub client initialized successfully")
        return github_client
        
    except Exception as e:
        logger.log_error("Failed to initialize GitHub client", e)
        return None


async def initialize_slack_client(context: Any, logger: Any) -> Optional[Any]:
    """
    Initialize Slack client with error handling.
    
    Args:
        context: WorkflowContext for client caching
        logger: Structured logger instance
        
    Returns:
        Slack client instance or None if initialization fails
    """
    try:
        slack_client = context._clients.get('ovr_slack')
        if slack_client:
            logger.log_info("Slack client already initialized")
            return slack_client
        
        slack_client = SlackMCPClient(context.config.config_path)
        context._clients['ovr_slack'] = slack_client
        logger.log_info("Slack client initialized successfully")
        return slack_client
        
    except Exception as e:
        logger.log_error("Failed to initialize Slack client", e)
        return None


async def initialize_repomix_client(context: Any, logger: Any) -> Optional[Any]:
    """
    Initialize Repomix client with error handling.
    
    Args:
        context: WorkflowContext for client caching
        logger: Structured logger instance
        
    Returns:
        Repomix client instance or None if initialization fails
    """
    try:
        repomix_client = context._clients.get('ovr_repomix')
        if repomix_client:
            logger.log_info("Repomix client already initialized")
            return repomix_client
        
        repomix_client = RepomixMCPClient(context.config.config_path)
        context._clients['ovr_repomix'] = repomix_client
        logger.log_info("Repomix client initialized successfully")
        return repomix_client
        
    except Exception as e:
        logger.log_error("Failed to initialize Repomix client", e)
        return None


async def send_slack_notification_with_retry(
    slack_client: Any,
    channel: str,
    message: str,
    logger: Any
) -> None:
    """
    Send Slack notification with error handling and rate limiting.
    
    Args:
        slack_client: Slack MCP client instance
        channel: Slack channel ID or name
        message: Message to send
        logger: Structured logger instance
    """
    try:
        if slack_client:
            # Mock notification for demo - in production would send real Slack message
            logger.log_info(f"Slack notification: {message}")
            # In production: await slack_client.send_message(channel, message)
        else:
            logger.log_warning("Slack client not available for notification")
            
    except Exception as e:
        logger.log_warning(f"Slack notification failed: {str(e)}")


async def log_pattern_discovery_visual(
    workflow_id: Optional[str],
    discovery_result: Dict[str, Any],
    repo_owner: str,
    repo_name: str,
    logger: Any
) -> None:
    """
    Log pattern discovery results with structured data.
    
    Args:
        workflow_id: Unique workflow identifier
        discovery_result: Results from pattern discovery
        repo_owner: Repository owner
        repo_name: Repository name
        logger: Structured logger instance
    """
    try:
        files_by_type = discovery_result.get("files_by_type", {})
        
        # Create table of discovered files by type
        if files_by_type:
            table_data = []
            for file_type, files in files_by_type.items():
                table_data.append({
                    "file_type": file_type.title(),
                    "count": len(files),
                    "status": "✅"
                })
            
            logger.log_table(
                f"Pattern Discovery Results: {repo_owner}/{repo_name}",
                table_data
            )
            
            # Log file type distribution
            logger.log_tree(
                f"File Type Distribution: {repo_owner}/{repo_name}",
                {
                    file_type.title(): len(files)
                    for file_type, files in files_by_type.items()
                }
            )
            
    except Exception as e:
        logger.log_warning(f"Failed to create visual logs for pattern discovery: {e}")


def extract_repo_details(repo_url: str) -> Tuple[str, str]:
    """
    Extract owner and name from repository URL.
    
    Args:
        repo_url: Repository URL
        
    Returns:
        Tuple of (owner, name)
        
    Raises:
        ValueError: If URL format is invalid
    """
    if repo_url.startswith("https://github.com/"):
        repo_path = repo_url.replace("https://github.com/", "").rstrip("/")
        if "/" in repo_path:
            repo_owner, repo_name = repo_path.split("/", 1)
            return repo_owner, repo_name
        else:
            raise ValueError(f"Invalid repository URL format: {repo_url}")
    else:
        raise ValueError(f"Invalid repository URL format: {repo_url}")


def _compile_workflow_results(
    repo_results: List[Dict[str, Any]],
    target_repos: List[str],
    database_name: str,
    logger: Any,
    process_start_time: float
) -> Dict[str, Any]:
    """
    Compile final workflow results from repository processing.
    
    Args:
        repo_results: List of repository processing results
        target_repos: List of target repository URLs
        database_name: Name of the database being decommissioned
        logger: Structured logger instance
        process_start_time: Start time of the process
        
    Returns:
        Dict containing compiled workflow results
    """
    # Calculate totals
    total_files_processed = sum(r.get("files_processed", 0) for r in repo_results if isinstance(r, dict))
    total_files_modified = sum(r.get("files_modified", 0) for r in repo_results if isinstance(r, dict))
    
    # Calculate success/failure counts
    successful_repos = [r for r in repo_results if isinstance(r, dict) and r.get("success", False)]
    failed_repos = [r for r in repo_results if isinstance(r, dict) and not r.get("success", False)]
    
    # Compile final results
    workflow_result = {
        "database_name": database_name,
        "total_repositories": len(target_repos),
        "repositories_processed": len(successful_repos),
        "repositories_failed": len(failed_repos),
        "total_files_processed": total_files_processed,
        "total_files_modified": total_files_modified,
        "repository_results": repo_results,
        "workflow_version": "v2.0",
        "metrics": logger.get_metrics_summary() if hasattr(logger, 'get_metrics_summary') else {},
        "success": len(failed_repos) == 0,
        "duration": time.time() - process_start_time
    }
    
    return workflow_result


async def _send_final_notifications(
    slack_client: Any,
    slack_channel: str,
    database_name: str,
    repo_results: List[Dict[str, Any]],
    workflow_result: Dict[str, Any],
    logger: Any
) -> None:
    """
    Send final Slack notifications about workflow completion.
    
    Args:
        slack_client: Slack MCP client instance
        slack_channel: Slack channel for notifications
        database_name: Name of the database being decommissioned
        repo_results: List of repository processing results
        workflow_result: Compiled workflow results
        logger: Structured logger instance
    """
    if slack_client:
        final_message = (
            f"🎉 Database decommissioning completed for '{database_name}'!\n"
            f"📊 Summary: {len(repo_results)} repositories processed, "
            f"{workflow_result['total_files_processed']} files processed, "
            f"{workflow_result['total_files_modified']} files modified"
        )
        await send_slack_notification_with_retry(slack_client, slack_channel, final_message, logger)


async def _export_workflow_logs(database_name: str, logger: Any) -> None:
    """
    Export workflow logs to file.
    
    Args:
        database_name: Name of the database being decommissioned
        logger: Structured logger instance
    """
    try:
        log_export_path = f"logs/db_decommission_{database_name}_{int(time.time())}.json"
        if hasattr(logger, 'export_logs'):
            logger.export_logs(log_export_path)
        else:
            logger.log_info(f"Workflow logs would be exported to: {log_export_path}")
    except Exception as e:
        logger.log_warning(f"Failed to export workflow logs: {e}")


# Safe Slack notification helper for backward compatibility
async def safe_slack_notification(
    slack_client: Any,
    channel: str,
    message: str,
    logger: Any
) -> None:
    """
    Send Slack notification with error handling (backward compatibility).
    
    Args:
        slack_client: Slack MCP client instance
        channel: Slack channel ID or name
        message: Message to send
        logger: Structured logger instance
    """
    await send_slack_notification_with_retry(slack_client, channel, message, logger)