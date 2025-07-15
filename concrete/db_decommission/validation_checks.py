"""
Validation Check Functions for Database Decommissioning.

This module contains specific validation check functions extracted from validation_helpers.py
to maintain the 500-line limit per module.
"""

import re
from typing import Dict, List, Any, Optional


async def perform_database_reference_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Perform database reference check on discovered files.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing reference check results
    """
    try:
        files = discovery_result.get("files", [])
        files_by_type = discovery_result.get("files_by_type", {})
        
        total_files = len(files)
        references_found = 0
        file_analysis = []
        
        # Check for database name references in files
        for file_info in files:
            file_path = file_info.get("path", "")
            file_content = file_info.get("content", "")
            
            # Count references to the database name
            direct_references = len(re.findall(rf'\b{re.escape(database_name)}\b', file_content, re.IGNORECASE))
            
            if direct_references > 0:
                references_found += 1
                file_analysis.append({
                    "file_path": file_path,
                    "reference_count": direct_references,
                    "file_type": file_info.get("source_type", "unknown")
                })
        
        # Calculate confidence based on reference density
        if total_files == 0:
            confidence = 0
            status = "FAILED"
            description = "No files found to analyze"
        elif references_found == 0:
            confidence = 95
            status = "PASSED"
            description = f"No direct references to '{database_name}' found in {total_files} files"
        else:
            reference_density = references_found / total_files
            if reference_density < 0.1:  # Less than 10% of files have references
                confidence = 85
                status = "PASSED"
                description = f"Low reference density: {references_found}/{total_files} files contain references"
            elif reference_density < 0.3:  # Less than 30% of files have references
                confidence = 70
                status = "WARNING"
                description = f"Medium reference density: {references_found}/{total_files} files contain references"
            else:
                confidence = 40
                status = "FAILED"
                description = f"High reference density: {references_found}/{total_files} files contain references"
        
        return {
            "status": status,
            "confidence": confidence,
            "description": description,
            "details": {
                "total_files": total_files,
                "references_found": references_found,
                "file_analysis": file_analysis,
                "files_by_type": files_by_type
            }
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "confidence": 0,
            "description": f"Database reference check failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def perform_rule_compliance_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Perform rule compliance check on pattern discovery results.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing compliance check results
    """
    try:
        files = discovery_result.get("files", [])
        files_by_type = discovery_result.get("files_by_type", {})
        confidence_dist = discovery_result.get("confidence_distribution", {})
        
        # Analyze pattern discovery quality
        total_files = len(files)
        file_types_count = len(files_by_type)
        
        # Check confidence distribution
        high_confidence = confidence_dist.get("high", 0)
        medium_confidence = confidence_dist.get("medium", 0)
        low_confidence = confidence_dist.get("low", 0)
        
        total_confidence_files = high_confidence + medium_confidence + low_confidence
        
        if total_confidence_files == 0:
            confidence = 50
            status = "WARNING"
            description = "No confidence data available for pattern discovery"
        else:
            # Calculate weighted confidence score
            weighted_confidence = (
                (high_confidence * 1.0) +
                (medium_confidence * 0.7) +
                (low_confidence * 0.4)
            ) / total_confidence_files
            
            confidence = int(weighted_confidence * 100)
            
            if confidence >= 80:
                status = "PASSED"
                description = f"High quality pattern discovery: {confidence}% confidence"
            elif confidence >= 60:
                status = "WARNING"
                description = f"Medium quality pattern discovery: {confidence}% confidence"
            else:
                status = "FAILED"
                description = f"Low quality pattern discovery: {confidence}% confidence"
        
        return {
            "status": status,
            "confidence": confidence,
            "description": description,
            "details": {
                "total_files": total_files,
                "file_types_count": file_types_count,
                "pattern_quality": {
                    "high_confidence": high_confidence,
                    "medium_confidence": medium_confidence,
                    "low_confidence": low_confidence
                },
                "confidence_analysis": {
                    "weighted_score": confidence,
                    "coverage": f"{total_confidence_files}/{total_files} files analyzed"
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "confidence": 0,
            "description": f"Rule compliance check failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def perform_service_integrity_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Perform service integrity check based on file types and patterns.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing integrity check results
    """
    try:
        files_by_type = discovery_result.get("files_by_type", {})
        
        # Define critical file types that could impact service integrity
        critical_types = {
            "python": "Application code",
            "sql": "Database schema",
            "infrastructure": "Infrastructure configuration",
            "config": "Configuration files"
        }
        
        critical_files = []
        total_critical_files = 0
        
        for file_type, description in critical_types.items():
            if file_type in files_by_type:
                file_count = len(files_by_type[file_type])
                if file_count > 0:
                    critical_files.append({
                        "type": file_type,
                        "description": description,
                        "file_count": file_count
                    })
                    total_critical_files += file_count
        
        # Calculate risk assessment
        total_files = sum(len(files) for files in files_by_type.values())
        
        if total_files == 0:
            confidence = 0
            status = "FAILED"
            description = "No files found to analyze"
            risk_level = "UNKNOWN"
        elif total_critical_files == 0:
            confidence = 90
            status = "PASSED"
            description = "No critical file types found"
            risk_level = "LOW"
        else:
            critical_ratio = total_critical_files / total_files
            
            if critical_ratio < 0.2:  # Less than 20% critical files
                confidence = 80
                status = "PASSED"
                description = f"Low impact: {total_critical_files}/{total_files} critical files"
                risk_level = "LOW"
            elif critical_ratio < 0.5:  # Less than 50% critical files
                confidence = 60
                status = "WARNING"
                description = f"Medium impact: {total_critical_files}/{total_files} critical files"
                risk_level = "MEDIUM"
            else:
                confidence = 30
                status = "FAILED"
                description = f"High impact: {total_critical_files}/{total_files} critical files"
                risk_level = "HIGH"
        
        return {
            "status": status,
            "confidence": confidence,
            "description": description,
            "details": {
                "total_files": total_files,
                "critical_files": critical_files,
                "total_critical_files": total_critical_files,
                "risk_assessment": {
                    "level": risk_level,
                    "critical_ratio": round(total_critical_files / total_files * 100, 1) if total_files > 0 else 0,
                    "recommendations": _generate_integrity_recommendations(critical_files, risk_level)
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "confidence": 0,
            "description": f"Service integrity check failed: {str(e)}",
            "details": {"error": str(e)}
        }


def _generate_integrity_recommendations(
    critical_files: List[Dict[str, Any]],
    risk_level: str
) -> List[str]:
    """
    Generate recommendations based on service integrity assessment.
    
    Args:
        critical_files: List of critical file information
        risk_level: Assessed risk level
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    if risk_level == "HIGH":
        recommendations.extend([
            "Perform thorough testing before deployment",
            "Create rollback plan with database restore procedures",
            "Coordinate with application teams for deployment window",
            "Monitor application logs closely after deployment"
        ])
    elif risk_level == "MEDIUM":
        recommendations.extend([
            "Review critical file changes with application team",
            "Test application functionality in staging environment",
            "Prepare monitoring alerts for potential issues"
        ])
    elif risk_level == "LOW":
        recommendations.extend([
            "Standard deployment procedures should be sufficient",
            "Monitor application health metrics after deployment"
        ])
    
    # Add file-type specific recommendations
    file_types = {f["type"] for f in critical_files}
    
    if "sql" in file_types:
        recommendations.append("Review database schema changes with DBA team")
    
    if "infrastructure" in file_types:
        recommendations.append("Validate infrastructure configuration changes")
    
    if "config" in file_types:
        recommendations.append("Update configuration management documentation")
    
    return recommendations


def generate_recommendations(
    qa_checks: List[Dict[str, Any]],
    discovery_result: Dict[str, Any]
) -> List[str]:
    """
    Generate comprehensive recommendations based on QA check results.
    
    Args:
        qa_checks: List of QA check results
        discovery_result: Results from pattern discovery
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Analyze failed checks
    failed_checks = [check for check in qa_checks if check.get("status") == "FAILED"]
    warning_checks = [check for check in qa_checks if check.get("status") == "WARNING"]
    
    if failed_checks:
        recommendations.extend([
            "Review failed quality checks before proceeding",
            "Address critical issues identified in validation",
            "Consider manual verification of high-risk changes"
        ])
    
    if warning_checks:
        recommendations.extend([
            "Monitor applications closely after deployment",
            "Have rollback procedures ready",
            "Consider phased deployment approach"
        ])
    
    # Add general recommendations
    recommendations.extend([
        "Notify stakeholders of database decommissioning completion",
        "Update database documentation and inventory",
        "Schedule infrastructure cleanup tasks",
        "Archive database backups according to retention policy"
    ])
    
    # Add discovery-specific recommendations
    files_by_type = discovery_result.get("files_by_type", {})
    
    if "sql" in files_by_type:
        recommendations.append("Review database schema changes with DBA team")
    
    if "infrastructure" in files_by_type:
        recommendations.append("Update infrastructure monitoring and alerting")
    
    if "config" in files_by_type:
        recommendations.append("Validate configuration changes in staging environment")
    
    return recommendations