"""
Database Decommissioning Workflow Steps.

This module contains the main workflow step functions for the database decommissioning
workflow, following async-first patterns and structured logging.
"""

import time
from typing import Any, Dict, Optional

# Import PRP-compliant components
from concrete.file_decommission_processor import FileDecommissionProcessor

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig

# Import extracted helper modules
from .validation_checks import (
    perform_database_reference_check,
    perform_rule_compliance_check,
    perform_service_integrity_check,
    generate_recommendations
)
from .repository_processors import (
    initialize_github_client
)
from .github_helpers import (
    create_fork_and_branch,
    commit_file_changes,
    create_pull_request
)
from .data_models import (
    QualityAssuranceResult,
    ValidationResult,
    DecommissioningSummary
)


async def quality_assurance_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quality assurance checks for database decommissioning.
    
    Args:
        context: WorkflowContext for data sharing
        step: Step configuration object
        database_name: Name of the database to decommission
        repo_owner: Repository owner name
        repo_name: Repository name
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing quality assurance results
    """
    start_time = time.time()
    
    # Initialize structured logger
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)
    
    logger.log_step_start(
        "quality_assurance",
        "Perform comprehensive quality assurance checks",
        {"database_name": database_name, "repository": f"{repo_owner}/{repo_name}"}
    )
    
    try:
        qa_checks = []
        
        # Get discovery results from previous step
        discovery_result = context.get_shared_value("discovery", {})
        
        # CRITICAL: Ensure discovery results are properly structured
        if not discovery_result or "files" not in discovery_result:
            logger.log_warning("No discovery results found, creating empty structure for QA validation")
            discovery_result = {
                "files": [],
                "files_by_type": {},
                "extraction_directory": "",
                "total_files": 0,
                "database_name": database_name
            }
        
        # Validate discovery result structure
        files = discovery_result.get("files", [])
        total_files = discovery_result.get("total_files", len(files))
        
        logger.log_info(f"QA validation processing {total_files} files from discovery results")
        
        # Check 1: Verify database references have been properly identified
        reference_check = await perform_database_reference_check(discovery_result, database_name)
        logger.log_info(
            f"Database reference check: {reference_check['status']} - {reference_check['description']}"
        )
        qa_checks.append({"check": "database_reference_removal", **reference_check})
        
        # Check 2: Validate pattern discovery quality and confidence
        rule_check = await perform_rule_compliance_check(discovery_result, database_name)
        logger.log_info(
            f"Rule compliance check: {rule_check['status']} - {rule_check['description']}"
        )
        qa_checks.append({"check": "rule_compliance", **rule_check})
        
        # Check 3: Assess service integrity risk based on file types found
        integrity_check = await perform_service_integrity_check(discovery_result, database_name)
        logger.log_info(
            f"Service integrity check: {integrity_check['status']} - {integrity_check['description']}"
        )
        qa_checks.append({"check": "service_integrity", **integrity_check})
        
        # Calculate overall quality score
        passed_checks = sum(1 for check in qa_checks if check["status"] == ValidationResult.PASSED.value)
        quality_score = (passed_checks / len(qa_checks)) * 100
        
        # Generate recommendations
        recommendations = generate_recommendations(qa_checks, discovery_result)
        
        # Create QA result
        qa_result = QualityAssuranceResult(
            database_reference_check=ValidationResult(reference_check["status"]),
            rule_compliance_check=ValidationResult(rule_check["status"]),
            service_integrity_check=ValidationResult(integrity_check["status"]),
            overall_status=ValidationResult.PASSED if quality_score >= 80 else ValidationResult.WARNING,
            details={
                "quality_score": quality_score,
                "checks_passed": passed_checks,
                "total_checks": len(qa_checks)
            },
            recommendations=recommendations
        )
        
        # Create result dictionary
        result = {
            "database_name": database_name,
            "qa_checks": qa_checks,
            "all_checks_passed": all(check["status"] == ValidationResult.PASSED.value for check in qa_checks),
            "quality_score": quality_score,
            "recommendations": recommendations,
            "success": True,
            "duration": time.time() - start_time
        }
        
        # Log QA summary using enhanced logging
        qa_summary_data = []
        for check in qa_checks:
            qa_summary_data.append({
                "check_name": check["check"].replace("_", " ").title(),
                "status": "passed" if check["status"] == ValidationResult.PASSED.value else "failed",
                "confidence": check.get("confidence", 0),
                "description": check.get("description", "")
            })
        
        logger.log_quality_assurance_summary(qa_summary_data)
        
        # Log structured QA results
        logger.log_table(
            "Quality Assurance Results",
            [
                {
                    "check": check["check"].replace("_", " ").title(),
                    "status": check["status"],
                    "confidence": f"{check.get('confidence', 0):.0f}%",
                    "description": check.get("description", "")
                }
                for check in qa_checks
            ]
        )
        
        logger.log_step_end("quality_assurance", result, success=True)
        
        return result
        
    except Exception as e:
        logger.log_error("Quality assurance step failed", e)
        raise


async def apply_refactoring_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply contextual refactoring rules to discovered files.
    
    Args:
        context: WorkflowContext for data sharing
        step: Step configuration object
        database_name: Name of the database to decommission
        repo_owner: Repository owner name
        repo_name: Repository name
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing refactoring results
    """
    start_time = time.time()
    
    # Initialize structured logger
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)
    
    logger.log_step_start(
        "apply_refactoring",
        "Apply contextual refactoring rules to discovered files",
        {"database_name": database_name, "repository": f"{repo_owner}/{repo_name}"}
    )
    
    try:
        # Get discovery results from previous step
        discovery_result = context.get_shared_value("discovery", {})
        files_to_process = discovery_result.get("files", [])
        
        if not files_to_process:
            logger.log_warning("No files found to refactor")
            return {
                "success": True,
                "files_processed": 0,
                "files_modified": 0,
                "message": "No files found requiring refactoring"
            }
        
        # CRITICAL: Validate source directory exists
        source_dir = discovery_result.get("extraction_directory", f"tests/tmp/pattern_match/{database_name}")
        
        from pathlib import Path
        if not Path(source_dir).exists():
            logger.log_warning(f"Source directory not found: {source_dir}")
            return {
                "success": False,
                "files_processed": 0,
                "files_modified": 0,
                "message": f"Source directory not found: {source_dir}"
            }
        
        # Use PRP-compliant FileDecommissionProcessor
        processor = FileDecommissionProcessor()
        
        logger.log_info(f"Processing files in {source_dir} with FileDecommissionProcessor")
        
        # Start progress tracking for file processing
        total_files = len(files_to_process)
        step_id = logger.start_progress("File Processing", total_files)
        
        # Process files in chunks to show progress
        processing_start = time.time()
        
        # Use PRP-compliant processing
        processing_result = await processor.process_files(
            source_dir=source_dir,
            database_name=database_name,
            ticket_id="DB-DECOMM-001"
        )
        
        # Complete progress tracking
        logger.complete_progress(step_id, {"files_processed": total_files})
        
        # Log operation duration
        processing_duration = time.time() - processing_start
        logger.log_operation_duration(
            operation_name="File Refactoring",
            duration_seconds=processing_duration,
            items_processed=total_files
        )
        
        # Extract results in format expected by downstream steps
        processed_files = processing_result.get("processed_files", [])
        strategies_applied = processing_result.get("strategies_applied", {})
        
        total_files_processed = len(processed_files)
        total_files_modified = len([f for f in processed_files if strategies_applied.get(f) in ["infrastructure", "configuration", "code"]])
        
        # Create refactoring results for compatibility
        refactoring_results = []
        files_by_type = {}
        
        for file_path in processed_files:
            strategy = strategies_applied.get(file_path, "documentation")
            
            # Group by strategy type
            if strategy not in files_by_type:
                files_by_type[strategy] = []
            files_by_type[strategy].append(file_path)
            
            # Read modified content from output directory
            from pathlib import Path
            output_dir = Path(processing_result.get("output_directory", f"{source_dir}_decommissioned"))
            relative_path = Path(file_path).relative_to(source_dir) if source_dir in file_path else Path(file_path)
            modified_file = output_dir / relative_path
            
            if modified_file.exists():
                modified_content = modified_file.read_text()
                changes_made = 1 if strategy in ["infrastructure", "configuration", "code"] else 0
                
                # Map back to original repository path (remove extraction directory prefix)
                original_path = str(relative_path) if source_dir in file_path else file_path
                # Also check if we can find the original path from discovery results
                for discovered_file in discovery_result.get("matched_files", []):
                    if discovered_file.get("extracted_path") == file_path:
                        original_path = discovered_file.get("original_path", original_path)
                        break
                
                refactoring_results.append({
                    "path": original_path,
                    "source_type": strategy,
                    "changes_made": changes_made,
                    "modified_content": modified_content,
                    "success": True
                })
                
                if changes_made > 0:
                    logger.log_info(f"Modified {file_path} ({strategy}): {changes_made} changes")
        
        # Log summary by strategy type
        logger.log_table(
            "Refactoring Results by Strategy",
            [
                {
                    "strategy": strategy.upper(),
                    "total_files": len(file_paths),
                    "modified_files": len([r for r in refactoring_results 
                                         if r.get("source_type") == strategy and r.get("changes_made", 0) > 0])
                }
                for strategy, file_paths in files_by_type.items()
            ]
        )
        
        # Store refactoring results for next step
        refactoring_summary = {
            "database_name": database_name,
            "total_files_processed": total_files_processed,
            "total_files_modified": total_files_modified,
            "files_by_type": files_by_type,
            "refactoring_results": refactoring_results,
            "success": True,
            "duration": time.time() - start_time
        }
        
        context.set_shared_value("refactoring", refactoring_summary)
        
        logger.log_step_end("apply_refactoring", refactoring_summary, success=True)
        
        return refactoring_summary
        
    except Exception as e:
        logger.log_error("Refactoring step failed", e)
        raise


async def create_github_pr_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create GitHub fork, branch, apply changes, and create pull request.
    
    Args:
        context: WorkflowContext for data sharing
        step: Step configuration object
        database_name: Name of the database to decommission
        repo_owner: Repository owner name
        repo_name: Repository name
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing GitHub PR creation results
    """
    start_time = time.time()
    
    # Initialize structured logger
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)
    
    logger.log_step_start(
        "create_github_pr",
        "Create GitHub fork, branch, apply changes, and create pull request",
        {"database_name": database_name, "repository": f"{repo_owner}/{repo_name}"}
    )
    
    try:
        # Get refactoring results from previous step
        refactoring_result = context.get_shared_value("refactoring", {})
        refactoring_files = refactoring_result.get("refactoring_results", [])
        
        if not refactoring_files:
            logger.log_warning("No refactoring results found")
            return {
                "success": False,
                "message": "No refactoring results to commit"
            }
        
        # Get modified files only
        modified_files = [f for f in refactoring_files if f.get("changes_made", 0) > 0]
        
        if not modified_files:
            logger.log_info("No files were modified, skipping PR creation")
            return {
                "success": True,
                "message": "No changes to commit - database not found or already removed"
            }
        
        # Initialize GitHub client
        github_client = await initialize_github_client(context, logger)
        if not github_client:
            raise RuntimeError("Failed to initialize GitHub client")
        
        # Create fork and branch
        fork_info = await create_fork_and_branch(
            github_client, repo_owner, repo_name, database_name, logger
        )
        fork_owner = fork_info["fork_owner"]
        branch_name = fork_info["branch_name"]
        
        # Commit file changes
        commit_info = await commit_file_changes(
            github_client, fork_owner, repo_name, branch_name, 
            modified_files, database_name, logger
        )
        files_committed = commit_info["files_committed"]
        
        if files_committed == 0:
            raise RuntimeError("No files were successfully committed")
        
        # Create pull request
        pr_info = await create_pull_request(
            github_client, repo_owner, repo_name, fork_owner, branch_name,
            database_name, modified_files, refactoring_result, files_committed, logger
        )
        pr_number = pr_info["pr_number"]
        pr_url = pr_info["pr_url"]
        
        # Final result
        github_result = {
            "success": True,
            "fork_owner": fork_owner,
            "branch_name": branch_name,
            "files_committed": files_committed,
            "pr_number": pr_number,
            "pr_url": pr_url,
            "pr_title": pr_info["pr_title"],
            "duration": time.time() - start_time
        }
        
        context.set_shared_value("github_pr", github_result)
        
        logger.log_step_end("create_github_pr", github_result, success=True)
        
        return github_result
        
    except Exception as e:
        logger.log_error("GitHub PR creation step failed", e)
        raise


async def workflow_summary_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive workflow summary and metrics.
    
    Args:
        context: WorkflowContext for data sharing
        step: Step configuration object
        database_name: Name of the database to decommission
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing workflow summary and metrics
    """
    start_time = time.time()
    
    # Initialize structured logger
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)
    
    logger.log_step_start(
        "workflow_summary",
        "Generate comprehensive workflow summary and metrics",
        {"database_name": database_name}
    )
    
    try:
        # Get results from previous steps
        validation_result = context.get_step_result("validate_environment", {})
        repository_result = context.get_step_result("process_repositories", {})
        qa_result = context.get_step_result("quality_assurance", {})
        refactoring_result = context.get_step_result("apply_refactoring", {})
        github_result = context.get_step_result("create_github_pr", {})
        
        # Calculate summary metrics
        total_files_processed = refactoring_result.get("total_files_processed", 0)
        total_files_modified = refactoring_result.get("total_files_modified", 0)
        total_repositories = repository_result.get("total_repositories", 0)
        quality_score = qa_result.get("quality_score", 0)
        
        # Calculate success rate
        success_rate = 100.0 if qa_result.get("all_checks_passed", False) else quality_score
        
        # Create decommissioning summary
        decommissioning_summary = DecommissioningSummary(
            workflow_id=workflow_id or f"db_decommission_{int(time.time())}",
            database_name=database_name,
            total_files_processed=total_files_processed,
            successful_files=total_files_modified,
            failed_files=total_files_processed - total_files_modified,
            total_changes=sum(f.get("changes_made", 0) for f in refactoring_result.get("refactoring_results", [])),
            rules_applied=list(refactoring_result.get("files_by_type", {}).keys()),
            execution_time_seconds=time.time() - context.get_shared_value("workflow_start_time", start_time),
            quality_assurance=qa_result,
            github_pr_url=github_result.get("pr_url")
        )
        
        # Create comprehensive summary
        summary = {
            "database_name": database_name,
            "workflow_version": "v2.0",
            "summary": {
                "repositories_processed": total_repositories,
                "files_discovered": repository_result.get("total_files_processed", 0),
                "files_processed": total_files_processed,
                "files_modified": total_files_modified,
                "total_duration": decommissioning_summary.execution_time_seconds,
                "success_rate": success_rate
            },
            "features_used": {
                "pattern_discovery": True,
                "contextual_rules_engine": True,
                "comprehensive_logging": True,
                "source_type_classification": True,
                "graceful_error_handling": True
            },
            "quality_assurance": qa_result,
            "github_pr": github_result,
            "next_steps": [
                "Monitor applications for any connectivity issues",
                "Update database documentation",
                "Schedule infrastructure cleanup",
                "Notify stakeholders of completion"
            ],
            "success": True,
            "duration": time.time() - start_time
        }
        
        # Log final summary table
        logger.log_table(
            "Final Workflow Summary",
            [
                {"metric": "Repositories Processed", "value": str(total_repositories), "status": "✅"},
                {"metric": "Files Discovered", "value": str(repository_result.get("total_files_processed", 0)), "status": "✅"},
                {"metric": "Files Processed", "value": str(total_files_processed), "status": "✅"},
                {"metric": "Files Modified", "value": str(total_files_modified), "status": "✅"},
                {"metric": "Quality Score", "value": f"{quality_score:.1f}%", "status": "✅"},
                {"metric": "Success Rate", "value": f"{success_rate:.1f}%", "status": "✅"},
                {"metric": "Total Duration", "value": f"{decommissioning_summary.execution_time_seconds:.1f}s", "status": "✅"}
            ]
        )
        
        logger.log_step_end("workflow_summary", summary, success=True)
        
        return summary
        
    except Exception as e:
        logger.log_error("Workflow summary step failed", e)
        raise


# Helper functions extracted to github_helpers.py module