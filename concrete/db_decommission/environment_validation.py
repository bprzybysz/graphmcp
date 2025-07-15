"""
Environment Validation Functions.

This module contains environment validation functions extracted from validation_helpers.py
to maintain the 500-line limit per module.
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


async def _validate_parameter_service(logger: Any) -> Dict[str, Any]:
    """
    Validate parameter service connectivity and credentials.
    
    Args:
        logger: Structured logger instance
        
    Returns:
        Dict containing validation results
    """
    try:
        param_service = get_parameter_service()
        
        # Test connection
        test_result = param_service.validate_mcp_configuration()
        
        return {
            "status": "PASSED" if test_result else "FAILED",
            "component": "parameter_service",
            "message": "Parameter service connection validated" if test_result else "Parameter service connection failed",
            "details": {"connected": test_result}
        }
    except Exception as e:
        logger.log_error("Parameter service validation failed", e)
        return {
            "status": "FAILED",
            "component": "parameter_service",
            "message": f"Parameter service error: {str(e)}",
            "details": {"error": str(e)}
        }


async def _validate_monitoring_system(logger: Any) -> Dict[str, Any]:
    """
    Validate monitoring system connectivity and configuration.
    
    Args:
        logger: Structured logger instance
        
    Returns:
        Dict containing validation results
    """
    try:
        monitoring = get_monitoring_system()
        
        # Test monitoring health
        health_checks = await monitoring.perform_health_check()
        
        # Get overall status from all checks
        overall_status = "PASSED"
        if isinstance(health_checks, dict):
            # Check if any health check failed
            for check_result in health_checks.values():
                if hasattr(check_result, 'status') and check_result.status != HealthStatus.HEALTHY:
                    overall_status = "WARNING"
                    break
        
        return {
            "status": overall_status,
            "component": "monitoring_system",
            "message": f"Monitoring system health checks completed",
            "details": {
                "checks_run": len(health_checks) if isinstance(health_checks, dict) else 1,
                "status": overall_status
            }
        }
    except Exception as e:
        logger.log_error("Monitoring system validation failed", e)
        return {
            "status": "WARNING",
            "component": "monitoring_system",
            "message": f"Monitoring system error: {str(e)}",
            "details": {"error": str(e)}
        }


async def _validate_database_reference_extractor(database_name: str, logger: Any) -> Dict[str, Any]:
    """
    Validate database reference extractor functionality.
    
    Args:
        database_name: Name of the database to validate
        logger: Structured logger instance
        
    Returns:
        Dict containing validation results
    """
    try:
        extractor = DatabaseReferenceExtractor()
        
        # Test basic functionality - create a simple test
        references = await extractor.extract_references(
            database_name=database_name,
            target_repo_pack_path="test_path",
            output_dir="test_output"
        )
        
        return {
            "status": "PASSED",
            "component": "database_reference_extractor",
            "message": f"Database reference extractor initialized for {database_name}",
            "details": {
                "database_name": database_name,
                "test_references_found": len(references)
            }
        }
    except Exception as e:
        logger.log_error("Database reference extractor validation failed", e)
        return {
            "status": "FAILED",
            "component": "database_reference_extractor",
            "message": f"Database reference extractor error: {str(e)}",
            "details": {"error": str(e)}
        }


async def _validate_file_decommission_processor(logger: Any, database_name: str = "test_db") -> Dict[str, Any]:
    """
    Validate file decommission processor functionality.
    
    Args:
        logger: Structured logger instance
        database_name: Name of database for testing
        
    Returns:
        Dict containing validation results
    """
    try:
        processor = FileDecommissionProcessor()
        
        # Test basic functionality - this will validate the processor can be instantiated
        # and basic configuration is valid
        # Test basic functionality with empty directory (create temporary test dir)
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as temp_dir:
            test_result = await processor.process_files(temp_dir, database_name, "test_output")
        
        return {
            "status": "PASSED" if test_result else "FAILED",
            "component": "file_decommission_processor",
            "message": "File decommission processor validated" if test_result else "File decommission processor validation failed",
            "details": {"configuration_valid": test_result}
        }
    except Exception as e:
        logger.log_error("File decommission processor validation failed", e)
        return {
            "status": "FAILED",
            "component": "file_decommission_processor",
            "message": f"File decommission processor error: {str(e)}",
            "details": {"error": str(e)}
        }


async def _validate_source_type_classifier(logger: Any) -> Dict[str, Any]:
    """
    Validate source type classifier functionality.
    
    Args:
        logger: Structured logger instance
        
    Returns:
        Dict containing validation results
    """
    try:
        classifier = SourceTypeClassifier()
        
        # Test classification with a simple example
        test_classification = classifier.classify_file("example.py", "print('hello')")
        
        return {
            "status": "PASSED",
            "component": "source_type_classifier",
            "message": "Source type classifier validated",
            "details": {
                "test_classification": test_classification.source_type.value if test_classification else "unknown"
            }
        }
    except Exception as e:
        logger.log_error("Source type classifier validation failed", e)
        return {
            "status": "FAILED",
            "component": "source_type_classifier",
            "message": f"Source type classifier error: {str(e)}",
            "details": {"error": str(e)}
        }


async def perform_environment_validation(
    database_name: str,
    logger: Any
) -> List[Dict[str, Any]]:
    """
    Perform comprehensive environment validation.
    
    Args:
        database_name: Name of the database being decommissioned
        logger: Structured logger instance
        
    Returns:
        List of validation results
    """
    validation_tasks = [
        _validate_parameter_service(logger),
        _validate_monitoring_system(logger),
        _validate_database_reference_extractor(database_name, logger),
        _validate_file_decommission_processor(logger, database_name),
        _validate_source_type_classifier(logger)
    ]
    
    # Run all validations concurrently
    validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
    
    # Process results and handle exceptions
    processed_results = []
    for i, result in enumerate(validation_results):
        if isinstance(result, Exception):
            processed_results.append({
                "status": "FAILED",
                "component": f"validation_task_{i}",
                "message": f"Validation task failed: {str(result)}",
                "details": {"error": str(result)}
            })
        else:
            processed_results.append(result)
    
    return processed_results
