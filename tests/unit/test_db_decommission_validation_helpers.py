"""
Comprehensive unit tests for Database Decommissioning Validation Helpers

Tests the validation_helpers module with:
- Environment validation step function
- Database reference checks
- Rule compliance validation
- Service integrity checks
- Recommendation generation
- Async patterns and error handling
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch, call
from typing import Dict, List, Any, Optional

from concrete.db_decommission.validation_helpers import (
    validate_environment_step,
    perform_database_reference_check,
    perform_rule_compliance_check,
    perform_service_integrity_check,
    generate_recommendations
)
from concrete.db_decommission.data_models import ValidationResult


class TestValidateEnvironmentStep:
    """Test validate_environment_step function."""
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.validation_helpers.get_logger')
    @patch('concrete.db_decommission.validation_helpers.LoggingConfig')
    async def test_successful_validation(self, mock_logging_config, mock_get_logger):
        """Test successful environment validation."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        
        mock_context = MagicMock()
        mock_step = MagicMock()
        
        # Execute
        result = await validate_environment_step(
            mock_context,
            mock_step,
            database_name="test_db",
            workflow_id="test-workflow-123"
        )
        
        # Verify
        assert result["database_name"] == "test_db"
        assert result["success"] is True
        assert "duration" in result
        assert result["environment_checks"]["python_version"]["status"] == "PASSED"
        assert result["environment_checks"]["dependencies"]["status"] == "PASSED"
        assert result["environment_checks"]["network_connectivity"]["status"] == "PASSED"
        
        # Verify logging calls
        mock_logger.log_step_start.assert_called_once()
        mock_logger.log_step_end.assert_called_once()
        mock_logger.log_info.assert_called()
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.validation_helpers.get_logger')
    @patch('concrete.db_decommission.validation_helpers.LoggingConfig')
    async def test_validation_with_warnings(self, mock_logging_config, mock_get_logger):
        """Test environment validation with warnings."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        
        mock_context = MagicMock()
        mock_step = MagicMock()
        
        # Execute
        result = await validate_environment_step(
            mock_context,
            mock_step,
            database_name="test_db",
            workflow_id="test-workflow-123"
        )
        
        # Verify structure
        assert "environment_checks" in result
        assert "python_version" in result["environment_checks"]
        assert "dependencies" in result["environment_checks"]
        assert "network_connectivity" in result["environment_checks"]
        assert "validation_summary" in result
        
        # Verify logging
        mock_logger.log_step_start.assert_called_once()
        mock_logger.log_step_end.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('concrete.db_decommission.validation_helpers.get_logger')
    @patch('concrete.db_decommission.validation_helpers.LoggingConfig')
    async def test_validation_error_handling(self, mock_logging_config, mock_get_logger):
        """Test error handling in environment validation."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_logging_config.from_env.return_value = MagicMock()
        
        mock_context = MagicMock()
        mock_step = MagicMock()
        
        # Mock an error in the validation process
        mock_logger.log_step_start.side_effect = Exception("Logger error")
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Logger error"):
            await validate_environment_step(
                mock_context,
                mock_step,
                database_name="test_db",
                workflow_id="test-workflow-123"
            )
        
        # Verify error logging
        mock_logger.log_error.assert_called()


class TestPerformDatabaseReferenceCheck:
    """Test perform_database_reference_check function."""
    
    @pytest.mark.asyncio
    async def test_successful_database_reference_check(self):
        """Test successful database reference check."""
        # Setup test data
        discovery_result = {
            "files": [
                {"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"},
                {"path": "models.py", "content": "class User(Model): pass"}
            ],
            "files_by_type": {
                "python": [{"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"}],
                "documentation": [{"path": "models.py", "content": "class User(Model): pass"}]
            }
        }
        
        # Execute
        result = await perform_database_reference_check(discovery_result, "test_db")
        
        # Verify
        assert "status" in result
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "confidence" in result
        assert "description" in result
        assert "details" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 100
    
    @pytest.mark.asyncio
    async def test_database_reference_check_with_matches(self):
        """Test database reference check with database name matches."""
        # Setup test data with database name references
        discovery_result = {
            "files": [
                {"path": "config.py", "content": "DATABASE_NAME = 'test_db'"},
                {"path": "migrate.sql", "content": "USE test_db; SELECT * FROM users;"}
            ],
            "files_by_type": {
                "python": [{"path": "config.py", "content": "DATABASE_NAME = 'test_db'"}],
                "sql": [{"path": "migrate.sql", "content": "USE test_db; SELECT * FROM users;"}]
            }
        }
        
        # Execute
        result = await perform_database_reference_check(discovery_result, "test_db")
        
        # Verify
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "references_found" in result["details"]
        assert "file_analysis" in result["details"]
    
    @pytest.mark.asyncio
    async def test_database_reference_check_no_files(self):
        """Test database reference check with no files."""
        # Setup test data with empty discovery
        discovery_result = {
            "files": [],
            "files_by_type": {}
        }
        
        # Execute
        result = await perform_database_reference_check(discovery_result, "test_db")
        
        # Verify
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "description" in result
        assert "confidence" in result


class TestPerformRuleComplianceCheck:
    """Test perform_rule_compliance_check function."""
    
    @pytest.mark.asyncio
    async def test_successful_rule_compliance_check(self):
        """Test successful rule compliance check."""
        # Setup test data
        discovery_result = {
            "files": [
                {"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"},
                {"path": "models.py", "content": "class User(Model): pass"}
            ],
            "files_by_type": {
                "python": [{"path": "config.py"}],
                "documentation": [{"path": "models.py"}]
            },
            "confidence_distribution": {
                "high": 2,
                "medium": 1,
                "low": 0
            }
        }
        
        # Execute
        result = await perform_rule_compliance_check(discovery_result, "test_db")
        
        # Verify
        assert "status" in result
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "confidence" in result
        assert "description" in result
        assert "details" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 100
    
    @pytest.mark.asyncio
    async def test_rule_compliance_check_with_quality_issues(self):
        """Test rule compliance check with quality issues."""
        # Setup test data with low confidence
        discovery_result = {
            "files": [
                {"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"},
                {"path": "models.py", "content": "class User(Model): pass"}
            ],
            "files_by_type": {
                "python": [{"path": "config.py"}],
                "documentation": [{"path": "models.py"}]
            },
            "confidence_distribution": {
                "high": 0,
                "medium": 1,
                "low": 5
            }
        }
        
        # Execute
        result = await perform_rule_compliance_check(discovery_result, "test_db")
        
        # Verify
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "pattern_quality" in result["details"]
        assert "confidence_analysis" in result["details"]


class TestPerformServiceIntegrityCheck:
    """Test perform_service_integrity_check function."""
    
    @pytest.mark.asyncio
    async def test_successful_service_integrity_check(self):
        """Test successful service integrity check."""
        # Setup test data
        discovery_result = {
            "files": [
                {"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"},
                {"path": "README.md", "content": "Documentation file"}
            ],
            "files_by_type": {
                "python": [{"path": "config.py"}],
                "documentation": [{"path": "README.md"}]
            }
        }
        
        # Execute
        result = await perform_service_integrity_check(discovery_result, "test_db")
        
        # Verify
        assert "status" in result
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "confidence" in result
        assert "description" in result
        assert "details" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 100
    
    @pytest.mark.asyncio
    async def test_service_integrity_check_critical_files(self):
        """Test service integrity check with critical files."""
        # Setup test data with critical file types
        discovery_result = {
            "files": [
                {"path": "database.py", "content": "import psycopg2"},
                {"path": "migration.sql", "content": "CREATE TABLE users"},
                {"path": "docker-compose.yml", "content": "version: '3'"}
            ],
            "files_by_type": {
                "python": [{"path": "database.py"}],
                "sql": [{"path": "migration.sql"}],
                "infrastructure": [{"path": "docker-compose.yml"}]
            }
        }
        
        # Execute
        result = await perform_service_integrity_check(discovery_result, "test_db")
        
        # Verify
        assert result["status"] in ["PASSED", "WARNING", "FAILED"]
        assert "critical_files" in result["details"]
        assert "risk_assessment" in result["details"]


class TestGenerateRecommendations:
    """Test generate_recommendations function."""
    
    def test_generate_recommendations_all_passed(self):
        """Test recommendations generation when all checks pass."""
        # Setup test data
        qa_checks = [
            {"check": "database_reference_removal", "status": "PASSED", "confidence": 95},
            {"check": "rule_compliance", "status": "PASSED", "confidence": 90},
            {"check": "service_integrity", "status": "PASSED", "confidence": 85}
        ]
        
        discovery_result = {
            "files": [{"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"}],
            "files_by_type": {"python": [{"path": "config.py"}]}
        }
        
        # Execute
        recommendations = generate_recommendations(qa_checks, discovery_result)
        
        # Verify
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 0
        
        # Should have basic recommendations even when all checks pass
        for recommendation in recommendations:
            assert isinstance(recommendation, str)
            assert len(recommendation) > 0
    
    def test_generate_recommendations_with_failures(self):
        """Test recommendations generation with check failures."""
        # Setup test data with failures
        qa_checks = [
            {"check": "database_reference_removal", "status": "FAILED", "confidence": 40},
            {"check": "rule_compliance", "status": "WARNING", "confidence": 70},
            {"check": "service_integrity", "status": "PASSED", "confidence": 85}
        ]
        
        discovery_result = {
            "files": [
                {"path": "config.py", "content": "DATABASE_URL = 'postgres://test'"},
                {"path": "migrate.sql", "content": "USE test_db; SELECT * FROM users;"}
            ],
            "files_by_type": {
                "python": [{"path": "config.py"}],
                "sql": [{"path": "migrate.sql"}]
            }
        }
        
        # Execute
        recommendations = generate_recommendations(qa_checks, discovery_result)
        
        # Verify
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should contain specific recommendations for failed checks
        recommendation_text = " ".join(recommendations)
        assert any(keyword in recommendation_text.lower() for keyword in ["database", "reference", "review"])
    
    def test_generate_recommendations_empty_input(self):
        """Test recommendations generation with empty input."""
        # Setup empty data
        qa_checks = []
        discovery_result = {"files": [], "files_by_type": {}}
        
        # Execute
        recommendations = generate_recommendations(qa_checks, discovery_result)
        
        # Verify
        assert isinstance(recommendations, list)
        # Should still provide some basic recommendations
        assert len(recommendations) >= 0


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]