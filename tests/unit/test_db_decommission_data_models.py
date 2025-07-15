"""
Comprehensive unit tests for Database Decommissioning Data Models

Tests the data models module with:
- Dataclass serialization/deserialization
- Validation of data model properties
- Type checking and error handling
- Pickle-safe serialization compliance
"""

import pytest
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional

from concrete.db_decommission.data_models import (
    FileProcessingResult,
    WorkflowConfig,
    QualityAssuranceResult,
    ValidationResult,
    DecommissioningSummary,
    WorkflowStepResult
)
from concrete.source_type_classifier import SourceType


class TestFileProcessingResult:
    """Test FileProcessingResult dataclass."""
    
    def test_creation_with_defaults(self):
        """Test creating FileProcessingResult with default values."""
        result = FileProcessingResult(
            file_path="test/file.py",
            source_type=SourceType.PYTHON,
            success=True,
            total_changes=5
        )
        
        assert result.file_path == "test/file.py"
        assert result.source_type == SourceType.PYTHON
        assert result.success is True
        assert result.total_changes == 5
        assert result.rules_applied is None
        assert result.error_message is None
    
    def test_creation_with_all_fields(self):
        """Test creating FileProcessingResult with all fields."""
        result = FileProcessingResult(
            file_path="test/file.py",
            source_type=SourceType.PYTHON,
            success=False,
            total_changes=0,
            rules_applied=["rule1", "rule2"],
            error_message="Processing failed"
        )
        
        assert result.file_path == "test/file.py"
        assert result.source_type == SourceType.PYTHON
        assert result.success is False
        assert result.total_changes == 0
        assert result.rules_applied == ["rule1", "rule2"]
        assert result.error_message == "Processing failed"
    
    def test_to_dict_method(self):
        """Test to_dict method serialization."""
        result = FileProcessingResult(
            file_path="test/file.py",
            source_type=SourceType.PYTHON,
            success=True,
            total_changes=3,
            rules_applied=["rule1"]
        )
        
        dict_result = result.to_dict()
        
        assert dict_result["file_path"] == "test/file.py"
        assert dict_result["source_type"] == "python"
        assert dict_result["success"] is True
        assert dict_result["total_changes"] == 3
        assert dict_result["rules_applied"] == ["rule1"]
        assert dict_result["error_message"] is None
    
    def test_from_dict_method(self):
        """Test from_dict method deserialization."""
        dict_data = {
            "file_path": "test/file.py",
            "source_type": "python",
            "success": True,
            "total_changes": 3,
            "rules_applied": ["rule1"],
            "error_message": None
        }
        
        result = FileProcessingResult.from_dict(dict_data)
        
        assert result.file_path == "test/file.py"
        assert result.source_type == SourceType.PYTHON
        assert result.success is True
        assert result.total_changes == 3
        assert result.rules_applied == ["rule1"]
        assert result.error_message is None
    
    def test_pickle_serialization(self):
        """Test pickle-safe serialization."""
        result = FileProcessingResult(
            file_path="test/file.py",
            source_type=SourceType.PYTHON,
            success=True,
            total_changes=5
        )
        
        # Serialize and deserialize
        serialized = pickle.dumps(result)
        deserialized = pickle.loads(serialized)
        
        assert deserialized.file_path == result.file_path
        assert deserialized.source_type == result.source_type
        assert deserialized.success == result.success
        assert deserialized.total_changes == result.total_changes


class TestWorkflowConfig:
    """Test WorkflowConfig dataclass."""
    
    def test_creation_with_defaults(self):
        """Test creating WorkflowConfig with default values."""
        config = WorkflowConfig(
            workflow_id="test-workflow-123",
            database_name="test_db",
            target_repos=["https://github.com/test/repo"],
            slack_channel="C123456"
        )
        
        assert config.workflow_id == "test-workflow-123"
        assert config.database_name == "test_db"
        assert config.target_repos == ["https://github.com/test/repo"]
        assert config.slack_channel == "C123456"
        assert config.config_path == "mcp_config.json"
    
    def test_to_dict_method(self):
        """Test to_dict method serialization."""
        config = WorkflowConfig(
            workflow_id="test-workflow-123",
            database_name="test_db",
            target_repos=["https://github.com/test/repo"],
            slack_channel="C123456",
            config_path="custom_config.json"
        )
        
        dict_result = config.to_dict()
        
        assert dict_result["workflow_id"] == "test-workflow-123"
        assert dict_result["database_name"] == "test_db"
        assert dict_result["target_repos"] == ["https://github.com/test/repo"]
        assert dict_result["slack_channel"] == "C123456"
        assert dict_result["config_path"] == "custom_config.json"
    
    def test_from_dict_method(self):
        """Test from_dict method deserialization."""
        dict_data = {
            "workflow_id": "test-workflow-123",
            "database_name": "test_db",
            "target_repos": ["https://github.com/test/repo"],
            "slack_channel": "C123456",
            "config_path": "custom_config.json"
        }
        
        config = WorkflowConfig.from_dict(dict_data)
        
        assert config.workflow_id == "test-workflow-123"
        assert config.database_name == "test_db"
        assert config.target_repos == ["https://github.com/test/repo"]
        assert config.slack_channel == "C123456"
        assert config.config_path == "custom_config.json"


class TestQualityAssuranceResult:
    """Test QualityAssuranceResult dataclass."""
    
    def test_creation_with_all_fields(self):
        """Test creating QualityAssuranceResult with all fields."""
        qa_result = QualityAssuranceResult(
            database_reference_check=ValidationResult.PASSED,
            rule_compliance_check=ValidationResult.WARNING,
            service_integrity_check=ValidationResult.FAILED,
            overall_status=ValidationResult.WARNING,
            details={"score": 85.5},
            recommendations=["Fix issue 1", "Review issue 2"]
        )
        
        assert qa_result.database_reference_check == ValidationResult.PASSED
        assert qa_result.rule_compliance_check == ValidationResult.WARNING
        assert qa_result.service_integrity_check == ValidationResult.FAILED
        assert qa_result.overall_status == ValidationResult.WARNING
        assert qa_result.details == {"score": 85.5}
        assert qa_result.recommendations == ["Fix issue 1", "Review issue 2"]
    
    def test_to_dict_method(self):
        """Test to_dict method serialization."""
        qa_result = QualityAssuranceResult(
            database_reference_check=ValidationResult.PASSED,
            rule_compliance_check=ValidationResult.WARNING,
            service_integrity_check=ValidationResult.FAILED,
            overall_status=ValidationResult.WARNING,
            details={"score": 85.5},
            recommendations=["Fix issue 1"]
        )
        
        dict_result = qa_result.to_dict()
        
        assert dict_result["database_reference_check"] == "PASSED"
        assert dict_result["rule_compliance_check"] == "WARNING"
        assert dict_result["service_integrity_check"] == "FAILED"
        assert dict_result["overall_status"] == "WARNING"
        assert dict_result["details"] == {"score": 85.5}
        assert dict_result["recommendations"] == ["Fix issue 1"]


class TestDecommissioningSummary:
    """Test DecommissioningSummary dataclass."""
    
    def test_creation_with_defaults(self):
        """Test creating DecommissioningSummary with default values."""
        summary = DecommissioningSummary(
            workflow_id="test-workflow-123",
            database_name="test_db",
            total_files_processed=10,
            successful_files=8,
            failed_files=2,
            total_changes=25,
            rules_applied=["rule1", "rule2"],
            execution_time_seconds=120.5
        )
        
        assert summary.workflow_id == "test-workflow-123"
        assert summary.database_name == "test_db"
        assert summary.total_files_processed == 10
        assert summary.successful_files == 8
        assert summary.failed_files == 2
        assert summary.total_changes == 25
        assert summary.rules_applied == ["rule1", "rule2"]
        assert summary.execution_time_seconds == 120.5
        assert summary.quality_assurance is None
        assert summary.github_pr_url is None
    
    def test_to_dict_method(self):
        """Test to_dict method serialization."""
        qa_result = QualityAssuranceResult(
            database_reference_check=ValidationResult.PASSED,
            rule_compliance_check=ValidationResult.PASSED,
            service_integrity_check=ValidationResult.PASSED,
            overall_status=ValidationResult.PASSED,
            details={},
            recommendations=[]
        )
        
        summary = DecommissioningSummary(
            workflow_id="test-workflow-123",
            database_name="test_db",
            total_files_processed=10,
            successful_files=8,
            failed_files=2,
            total_changes=25,
            rules_applied=["rule1", "rule2"],
            execution_time_seconds=120.5,
            quality_assurance=qa_result,
            github_pr_url="https://github.com/test/repo/pull/123"
        )
        
        dict_result = summary.to_dict()
        
        assert dict_result["workflow_id"] == "test-workflow-123"
        assert dict_result["database_name"] == "test_db"
        assert dict_result["total_files_processed"] == 10
        assert dict_result["successful_files"] == 8
        assert dict_result["failed_files"] == 2
        assert dict_result["total_changes"] == 25
        assert dict_result["rules_applied"] == ["rule1", "rule2"]
        assert dict_result["execution_time_seconds"] == 120.5
        assert isinstance(dict_result["quality_assurance"], dict)
        assert dict_result["github_pr_url"] == "https://github.com/test/repo/pull/123"
    
    def test_from_dict_method(self):
        """Test from_dict method deserialization."""
        dict_data = {
            "workflow_id": "test-workflow-123",
            "database_name": "test_db",
            "total_files_processed": 10,
            "successful_files": 8,
            "failed_files": 2,
            "total_changes": 25,
            "rules_applied": ["rule1", "rule2"],
            "execution_time_seconds": 120.5,
            "quality_assurance": {
                "database_reference_check": "PASSED",
                "rule_compliance_check": "PASSED",
                "service_integrity_check": "PASSED",
                "overall_status": "PASSED",
                "details": {},
                "recommendations": []
            },
            "github_pr_url": "https://github.com/test/repo/pull/123"
        }
        
        summary = DecommissioningSummary.from_dict(dict_data)
        
        assert summary.workflow_id == "test-workflow-123"
        assert summary.database_name == "test_db"
        assert summary.total_files_processed == 10
        assert summary.successful_files == 8
        assert summary.failed_files == 2
        assert summary.total_changes == 25
        assert summary.rules_applied == ["rule1", "rule2"]
        assert summary.execution_time_seconds == 120.5
        assert isinstance(summary.quality_assurance, QualityAssuranceResult)
        assert summary.github_pr_url == "https://github.com/test/repo/pull/123"


class TestWorkflowStepResult:
    """Test WorkflowStepResult dataclass."""
    
    def test_creation_with_defaults(self):
        """Test creating WorkflowStepResult with default values."""
        step_result = WorkflowStepResult(
            step_name="test_step",
            success=True,
            duration_seconds=45.2,
            output_data={"processed": 5, "modified": 3}
        )
        
        assert step_result.step_name == "test_step"
        assert step_result.success is True
        assert step_result.duration_seconds == 45.2
        assert step_result.output_data == {"processed": 5, "modified": 3}
        assert step_result.error_message is None
    
    def test_creation_with_error(self):
        """Test creating WorkflowStepResult with error."""
        step_result = WorkflowStepResult(
            step_name="test_step",
            success=False,
            duration_seconds=10.5,
            output_data={},
            error_message="Step failed due to network error"
        )
        
        assert step_result.step_name == "test_step"
        assert step_result.success is False
        assert step_result.duration_seconds == 10.5
        assert step_result.output_data == {}
        assert step_result.error_message == "Step failed due to network error"
    
    def test_to_dict_method(self):
        """Test to_dict method serialization."""
        step_result = WorkflowStepResult(
            step_name="test_step",
            success=True,
            duration_seconds=45.2,
            output_data={"processed": 5, "modified": 3},
            error_message=None
        )
        
        dict_result = step_result.to_dict()
        
        assert dict_result["step_name"] == "test_step"
        assert dict_result["success"] is True
        assert dict_result["duration_seconds"] == 45.2
        assert dict_result["output_data"] == {"processed": 5, "modified": 3}
        assert dict_result["error_message"] is None
    
    def test_from_dict_method(self):
        """Test from_dict method deserialization."""
        dict_data = {
            "step_name": "test_step",
            "success": True,
            "duration_seconds": 45.2,
            "output_data": {"processed": 5, "modified": 3},
            "error_message": None
        }
        
        step_result = WorkflowStepResult.from_dict(dict_data)
        
        assert step_result.step_name == "test_step"
        assert step_result.success is True
        assert step_result.duration_seconds == 45.2
        assert step_result.output_data == {"processed": 5, "modified": 3}
        assert step_result.error_message is None


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]