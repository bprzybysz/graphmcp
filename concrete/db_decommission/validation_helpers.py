"""
Database Decommissioning Validation Helpers.

This module contains validation functions for the database decommissioning workflow,
following async-first patterns and structured logging.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

# Import components for validation
from concrete.parameter_service import get_parameter_service, ParameterService
from concrete.database_reference_extractor import DatabaseReferenceExtractor
from concrete.file_decommission_processor import FileDecommissionProcessor
from concrete.source_type_classifier import SourceTypeClassifier, SourceType
from concrete.monitoring import get_monitoring_system, HealthStatus, AlertSeverity

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig

# Import data models
from .data_models import ValidationResult, QualityAssuranceResult, WorkflowStepResult


async def validate_environment_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate environment setup and initialize components with centralized secrets.
    
    Args:
        context: WorkflowContext for data sharing
        step: Step configuration object
        database_name: Name of the database to decommission
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing validation results and initialized components
    """
    start_time = time.time()
    
    # Initialize structured logger
    config = LoggingConfig.from_env()
    logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)
    
    # Initialize monitoring system
    monitoring = get_monitoring_system()
    
    logger.log_step_start(
        "validate_environment",
        "Validate environment setup and initialize components with centralized secrets",
        {"database_name": database_name}
    )
    
    try:
        # Perform comprehensive health checks
        health_results = await monitoring.perform_health_check()
        
        # Analyze health check results
        critical_issues = []
        warning_issues = []
        
        for check_name, result in health_results.items():
            if result.status == HealthStatus.CRITICAL:
                critical_issues.append(f"{check_name}: {result.message}")
            elif result.status == HealthStatus.WARNING:
                warning_issues.append(f"{check_name}: {result.message}")
        
        # Handle critical issues
        if critical_issues:
            await _handle_critical_issues(
                monitoring, critical_issues, database_name, logger
            )
        
        # Handle warning issues
        if warning_issues:
            await _handle_warning_issues(
                monitoring, warning_issues, database_name, logger
            )
        
        # Initialize parameter service
        param_service = await _initialize_parameter_service(
            monitoring, database_name, logger
        )
        
        # Initialize PRP-compliant components
        components = await _initialize_components(logger)
        
        # Generate and validate search patterns
        search_patterns, pattern_count = await _generate_search_patterns(
            database_name, logger
        )
        
        # Store components in context for other steps
        await _store_components_in_context(
            context, param_service, components, search_patterns
        )
        
        # Create validation result
        validation_result = _create_validation_result(
            database_name, param_service, pattern_count, health_results,
            critical_issues, warning_issues, start_time
        )
        
        logger.log_step_end("validate_environment", validation_result, success=True)
        
        # Update monitoring metrics
        monitoring.update_workflow_metrics(
            workflow_result=validation_result,
            duration_seconds=time.time() - start_time
        )
        
        return validation_result
        
    except Exception as e:
        return await _handle_validation_error(
            e, database_name, logger, monitoring, start_time
        )


async def perform_database_reference_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Check if database references were properly identified and handled.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing check results and confidence metrics
    """
    files = discovery_result.get("files", [])
    matched_files = discovery_result.get("matched_files", 0)
    total_files = discovery_result.get("total_files", 0)
    
    if total_files == 0:
        return {
            "status": ValidationResult.FAILED.value,
            "confidence": 0,
            "description": "No files were analyzed - repository may be empty or inaccessible",
            "details": {"total_files": 0, "matched_files": 0}
        }
    
    if matched_files == 0:
        return {
            "status": ValidationResult.WARNING.value,
            "confidence": 50,
            "description": f"No {database_name} references found - database may already be removed or not used",
            "details": {"total_files": total_files, "matched_files": 0}
        }
    
    # Check confidence distribution
    confidence_dist = discovery_result.get("confidence_distribution", {})
    high_confidence = confidence_dist.get("high_confidence", 0)
    total_matches = matched_files
    
    if total_matches > 0 and high_confidence / total_matches >= 0.8:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 95,
            "description": f"Database references properly identified with high confidence ({high_confidence}/{total_matches} files)",
            "details": {"total_files": total_files, "matched_files": matched_files, "high_confidence": high_confidence}
        }
    elif total_matches > 0:
        return {
            "status": ValidationResult.WARNING.value,
            "confidence": 70,
            "description": f"Database references found but some have low confidence ({high_confidence}/{total_matches} high confidence)",
            "details": {"total_files": total_files, "matched_files": matched_files, "high_confidence": high_confidence}
        }
    else:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 85,
            "description": f"Database references analysis completed ({matched_files} files processed)",
            "details": {"total_files": total_files, "matched_files": matched_files}
        }


async def perform_rule_compliance_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Check if pattern discovery followed proper rules and classification.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing rule compliance results
    """
    files_by_type = discovery_result.get("files_by_type", {})
    
    if not files_by_type:
        return {
            "status": ValidationResult.WARNING.value,
            "confidence": 40,
            "description": "No file type classification available for rule compliance validation",
            "details": {"file_types": 0}
        }
    
    # Check for proper file type diversity
    file_type_count = len(files_by_type)
    total_files = sum(len(files) for files in files_by_type.values())
    
    if file_type_count >= 3 and total_files >= 5:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 90,
            "description": f"Pattern discovery properly classified {file_type_count} file types across {total_files} files",
            "details": {"file_types": file_type_count, "total_classified": total_files, "types": list(files_by_type.keys())}
        }
    elif file_type_count >= 2:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 75,
            "description": f"Pattern discovery classified {file_type_count} file types with reasonable coverage",
            "details": {"file_types": file_type_count, "total_classified": total_files, "types": list(files_by_type.keys())}
        }
    else:
        return {
            "status": ValidationResult.WARNING.value,
            "confidence": 60,
            "description": f"Limited file type diversity found ({file_type_count} types) - may indicate narrow scope",
            "details": {"file_types": file_type_count, "total_classified": total_files, "types": list(files_by_type.keys())}
        }


async def perform_service_integrity_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Assess risk to service integrity based on types of files that reference the database.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing service integrity risk assessment
    """
    files_by_type = discovery_result.get("files_by_type", {})
    
    if not files_by_type:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 80,
            "description": "No classified files found - minimal service integrity risk",
            "details": {"risk_level": "low", "critical_files": 0}
        }
    
    # Assess risk based on file types
    critical_types = ["python", "java", "javascript", "typescript"]  # Application code
    infrastructure_types = ["yaml", "terraform", "shell"]  # Infrastructure
    config_types = ["json", "ini", "conf"]  # Configuration
    
    critical_files = sum(len(files_by_type.get(ftype, [])) for ftype in critical_types)
    infrastructure_files = sum(len(files_by_type.get(ftype, [])) for ftype in infrastructure_types)
    config_files = sum(len(files_by_type.get(ftype, [])) for ftype in config_types)
    
    if critical_files > 5:
        return {
            "status": ValidationResult.WARNING.value,
            "confidence": 85,
            "description": f"High service integrity risk - {critical_files} application code files reference database",
            "details": {"risk_level": "high", "critical_files": critical_files, "infrastructure_files": infrastructure_files}
        }
    elif critical_files > 0:
        return {
            "status": ValidationResult.WARNING.value,
            "confidence": 80,
            "description": f"Moderate service integrity risk - {critical_files} application files affected",
            "details": {"risk_level": "moderate", "critical_files": critical_files, "infrastructure_files": infrastructure_files}
        }
    elif infrastructure_files > 0:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 90,
            "description": f"Low service integrity risk - mainly infrastructure/config files ({infrastructure_files + config_files} files)",
            "details": {"risk_level": "low", "critical_files": 0, "infrastructure_files": infrastructure_files}
        }
    else:
        return {
            "status": ValidationResult.PASSED.value,
            "confidence": 95,
            "description": "Minimal service integrity risk - no critical application files affected",
            "details": {"risk_level": "minimal", "critical_files": 0, "infrastructure_files": 0}
        }


def generate_recommendations(
    qa_checks: List[Dict[str, Any]],
    discovery_result: Dict[str, Any]
) -> List[str]:
    """
    Generate actionable recommendations based on QA check results.
    
    Args:
        qa_checks: List of QA check results
        discovery_result: Results from pattern discovery
        
    Returns:
        List of actionable recommendations
    """
    recommendations = []
    
    # Base recommendations
    recommendations.append("Monitor application logs for any database connection errors")
    recommendations.append("Update documentation to reflect database decommissioning")
    
    # Risk-based recommendations
    for check in qa_checks:
        if check["check"] == "service_integrity":
            risk_level = check.get("details", {}).get("risk_level", "low")
            if risk_level == "high":
                recommendations.append("⚠️ HIGH RISK: Thoroughly test application functionality before deploying changes")
                recommendations.append("Consider phased rollout with rollback plan")
            elif risk_level == "moderate":
                recommendations.append("Test affected services in staging environment")
                
        elif check["check"] == "database_reference_removal":
            if check["status"] == "warning":
                recommendations.append("Review low-confidence matches manually for accuracy")
                
        elif check["check"] == "rule_compliance":
            if check["status"] == "warning":
                recommendations.append("Consider expanding search patterns for more comprehensive coverage")
    
    return recommendations


# Private helper functions

async def _handle_critical_issues(
    monitoring: Any,
    critical_issues: List[str],
    database_name: str,
    logger: Any
) -> None:
    """Handle critical environment issues."""
    await monitoring.send_alert(
        AlertSeverity.CRITICAL,
        "Environment Validation Failed",
        f"Critical health check failures: {'; '.join(critical_issues)}",
        {"database_name": database_name, "critical_issues": critical_issues}
    )
    logger.log_error("Critical environment issues detected", context={"issues": critical_issues})


async def _handle_warning_issues(
    monitoring: Any,
    warning_issues: List[str],
    database_name: str,
    logger: Any
) -> None:
    """Handle warning environment issues."""
    await monitoring.send_alert(
        AlertSeverity.WARNING,
        "Environment Validation Warnings",
        f"Health check warnings: {'; '.join(warning_issues)}",
        {"database_name": database_name, "warning_issues": warning_issues}
    )
    logger.log_warning("Environment warnings detected", context={"issues": warning_issues})


async def _initialize_parameter_service(
    monitoring: Any,
    database_name: str,
    logger: Any
) -> ParameterService:
    """Initialize centralized parameter service."""
    from concrete.db_decommission import initialize_environment_with_centralized_secrets
    
    logger.log_info("Initializing centralized parameter service...")
    param_service = initialize_environment_with_centralized_secrets()
    
    if not param_service:
        error_msg = "Failed to initialize parameter service"
        logger.log_error(error_msg)
        await monitoring.send_alert(
            AlertSeverity.CRITICAL,
            "Parameter Service Initialization Failed",
            error_msg,
            {"database_name": database_name}
        )
        raise RuntimeError(error_msg)
    
    return param_service


async def _initialize_components(logger: Any) -> Dict[str, Any]:
    """Initialize PRP-compliant components."""
    logger.log_info("Initializing PRP-compliant components...")
    
    return {
        "extractor": DatabaseReferenceExtractor(),
        "processor": FileDecommissionProcessor(),
        "source_classifier": SourceTypeClassifier()
    }


async def _generate_search_patterns(
    database_name: str,
    logger: Any
) -> tuple[Dict[str, Any], int]:
    """Generate database-specific search patterns."""
    logger.log_info(f"Validating pattern generation for database '{database_name}'...")
    
    try:
        search_patterns = {}
        
        # Generate patterns for each source type
        for source_type in SourceType:
            if source_type != SourceType.UNKNOWN:
                patterns = [
                    database_name,
                    f"'{database_name}'",
                    f'"{database_name}"',
                    f"{database_name}_",
                    f"_{database_name}"
                ]
                search_patterns[source_type.value] = patterns
        
        pattern_count = sum(len(patterns) for patterns in search_patterns.values())
        return search_patterns, pattern_count
        
    except Exception as e:
        logger.log_warning(f"Could not generate search patterns: {e}")
        return {}, 0


async def _store_components_in_context(
    context: Any,
    param_service: ParameterService,
    components: Dict[str, Any],
    search_patterns: Dict[str, Any]
) -> None:
    """Store initialized components in workflow context."""
    context.set_shared_value("parameter_service", param_service)
    context.set_shared_value("database_extractor", components["extractor"])
    context.set_shared_value("file_processor", components["processor"])
    context.set_shared_value("source_classifier", components["source_classifier"])
    context.set_shared_value("search_patterns", search_patterns)


def _create_validation_result(
    database_name: str,
    param_service: ParameterService,
    pattern_count: int,
    health_results: Dict[str, Any],
    critical_issues: List[str],
    warning_issues: List[str],
    start_time: float
) -> Dict[str, Any]:
    """Create validation result dictionary."""
    return {
        "database_name": database_name,
        "environment_status": "ready",
        "components_initialized": {
            "parameter_service": True,
            "database_extractor": True,
            "file_processor": True,
            "source_classifier": True
        },
        "validation_issues": param_service.validation_issues if param_service else [],
        "pattern_count": pattern_count,
        "config_loaded": True,
        "success": True,
        "duration": time.time() - start_time,
        "health_checks": {
            name: {
                "status": result.status.value,
                "message": result.message,
                "duration_ms": result.duration_ms
            }
            for name, result in health_results.items()
        },
        "critical_issues": critical_issues,
        "warning_issues": warning_issues
    }


async def _handle_validation_error(
    error: Exception,
    database_name: str,
    logger: Any,
    monitoring: Any,
    start_time: float
) -> Dict[str, Any]:
    """Handle validation errors with proper logging and alerts."""
    error_msg = f"Environment validation failed: {str(error)}"
    logger.log_error(error_msg, error)
    
    # Send critical alert
    await monitoring.send_alert(
        AlertSeverity.EMERGENCY,
        "Environment Validation Critical Failure",
        error_msg,
        {"database_name": database_name, "error": str(error)}
    )
    
    error_result = {
        "database_name": database_name,
        "environment_status": "failed",
        "error": error_msg,
        "success": False,
        "duration": time.time() - start_time
    }
    
    logger.log_step_end("validate_environment", error_result, success=False)
    
    # Update monitoring metrics with failure
    monitoring.update_workflow_metrics(
        workflow_result=error_result,
        duration_seconds=time.time() - start_time
    )
    
    raise