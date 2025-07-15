"""
Database Decommissioning Validation Helpers.

This module contains validation functions for the database decommissioning workflow,
following async-first patterns and structured logging.
"""

import time
from typing import Any, Dict, List, Optional

# Import components for validation
from concrete.parameter_service import get_parameter_service
from concrete.monitoring import get_monitoring_system

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig

# Import data models
from .data_models import ValidationResult

# Import extracted helper functions
from .environment_validation import perform_environment_validation


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
        # Perform comprehensive environment validation
        validation_results = await perform_environment_validation(database_name, logger)
        
        # Analyze validation results
        failed_validations = [v for v in validation_results if v["status"] == "FAILED"]
        warning_validations = [v for v in validation_results if v["status"] == "WARNING"]
        
        # Initialize parameter service
        param_service = get_parameter_service()
        
        # Generate search patterns
        search_patterns = [
            f"\\b{database_name}\\b",
            f"'{database_name}'",
            f'"{database_name}"',
            f"{database_name}\\."
        ]
        
        # Store components in context for other steps
        context.set_shared_value("parameter_service", param_service)
        context.set_shared_value("search_patterns", search_patterns)
        
        # Create validation result
        validation_result = {
            "database_name": database_name,
            "parameter_service_initialized": param_service is not None,
            "search_patterns": search_patterns,
            "validation_results": validation_results,
            "failed_validations": len(failed_validations),
            "warning_validations": len(warning_validations),
            "success": len(failed_validations) == 0,
            "duration": time.time() - start_time
        }
        
        # Log validation summary
        logger.log_table(
            "Environment Validation Results",
            [
                {
                    "component": v["component"],
                    "status": v["status"],
                    "message": v["message"]
                }
                for v in validation_results
            ]
        )
        
        logger.log_step_end("validate_environment", validation_result, success=True)
        
        return validation_result
        
    except Exception as e:
        logger.log_error("Environment validation step failed", e)
        raise


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

