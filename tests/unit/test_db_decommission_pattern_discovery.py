"""
Comprehensive unit tests for Database Decommissioning Pattern Discovery

Tests the pattern_discovery module with:
- AgenticFileProcessor class functionality
- Pattern discovery and file processing
- Batch processing with OpenAI integration
- File categorization by source type
- Processing metrics calculation
- Visual logging integration
- Error handling scenarios
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch, call
from typing import Dict, List, Any, Optional
from collections import defaultdict

from concrete.db_decommission.pattern_discovery import (
    AgenticFileProcessor,
    process_discovered_files_with_rules,
    log_pattern_discovery_visual,
    categorize_files_by_source_type,
    calculate_processing_metrics,
    extract_high_confidence_patterns,
    generate_pattern_discovery_summary
)
from concrete.db_decommission.data_models import FileProcessingResult
from concrete.source_type_classifier import SourceType, SourceTypeClassifier


class TestAgenticFileProcessor:
    """Test AgenticFileProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_source_classifier = MagicMock()
        self.mock_contextual_rules_engine = MagicMock()
        self.mock_contextual_rules_engine.database_name = "test_db"
        self.mock_github_client = MagicMock()
        self.repo_owner = "test-owner"
        self.repo_name = "test-repo"
        
        # Mock logger setup
        with patch('concrete.db_decommission.pattern_discovery.get_logger') as mock_get_logger:
            mock_get_logger.return_value = MagicMock()
            self.processor = AgenticFileProcessor(
                source_classifier=self.mock_source_classifier,
                contextual_rules_engine=self.mock_contextual_rules_engine,
                github_client=self.mock_github_client,
                repo_owner=self.repo_owner,
                repo_name=self.repo_name
            )
    
    def test_initialization(self):
        """Test AgenticFileProcessor initialization."""
        assert self.processor.source_classifier == self.mock_source_classifier
        assert self.processor.contextual_rules_engine == self.mock_contextual_rules_engine
        assert self.processor.github_client == self.mock_github_client
        assert self.processor.repo_owner == self.repo_owner
        assert self.processor.repo_name == self.repo_name
        assert self.processor.logger is not None
    
    def test_build_agent_prompt(self):
        """Test _build_agent_prompt method."""
        # Setup test data
        batch = [
            {
                "file_path": "test/file1.py",
                "file_content": "DATABASE_URL = 'postgres://test'"
            },
            {
                "file_path": "test/file2.py",
                "file_content": "import psycopg2"
            }
        ]
        
        rules = {
            "database_removal": {
                "patterns": ["DATABASE_URL", "psycopg2"],
                "replacements": ["# DATABASE_URL removed", "# psycopg2 removed"]
            }
        }
        
        source_type = SourceType.PYTHON
        
        # Execute
        prompt = self.processor._build_agent_prompt(batch, rules, source_type)
        
        # Verify
        assert isinstance(prompt, str)
        assert "test_db" in prompt
        assert "python" in prompt
        assert "test/file1.py" in prompt
        assert "test/file2.py" in prompt
        assert "DATABASE_URL" in prompt
        assert "psycopg2" in prompt
        assert "JSON object" in prompt
        assert "modified_content" in prompt
    
    @pytest.mark.asyncio
    @patch('openai.AsyncOpenAI')
    async def test_invoke_agent_on_batch_success(self, mock_openai):
        """Test successful _invoke_agent_on_batch execution."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_openai.return_value = mock_agent
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "test/file1.py": {
                "modified_content": "# DATABASE_URL removed"
            },
            "test/file2.py": {
                "modified_content": "# psycopg2 removed"
            }
        })
        
        mock_agent.chat.completions.create.return_value = mock_response
        
        # Setup source classifier mock
        mock_classification = MagicMock()
        mock_classification.source_type = SourceType.PYTHON
        self.mock_source_classifier.classify_file.return_value = mock_classification
        
        # Setup contextual rules engine mock
        self.mock_contextual_rules_engine._update_file_content.return_value = AsyncMock()
        
        # Test data
        batch = [
            {
                "file_path": "test/file1.py",
                "file_content": "DATABASE_URL = 'postgres://test'"
            },
            {
                "file_path": "test/file2.py",
                "file_content": "import psycopg2"
            }
        ]
        
        prompt = "test prompt"
        
        # Execute
        results = await self.processor._invoke_agent_on_batch(prompt, batch)
        
        # Verify
        assert len(results) == 2
        assert all(isinstance(result, FileProcessingResult) for result in results)
        assert results[0].file_path == "test/file1.py"
        assert results[0].success is True
        assert results[0].total_changes == 1
        assert results[1].file_path == "test/file2.py"
        assert results[1].success is True
        assert results[1].total_changes == 1
        
        # Verify OpenAI call
        mock_agent.chat.completions.create.assert_called_once()
        call_args = mock_agent.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4-turbo-preview"
        assert call_args[1]["response_format"] == {"type": "json_object"}
        
        # Verify file updates
        assert self.mock_contextual_rules_engine._update_file_content.call_count == 2
    
    @pytest.mark.asyncio
    @patch('openai.AsyncOpenAI')
    async def test_invoke_agent_on_batch_no_changes(self, mock_openai):
        """Test _invoke_agent_on_batch with no content changes."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_openai.return_value = mock_agent
        
        # Mock OpenAI response with no changes
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "test/file1.py": {
                "modified_content": "DATABASE_URL = 'postgres://test'"  # Same content
            }
        })
        
        mock_agent.chat.completions.create.return_value = mock_response
        
        # Setup source classifier mock
        mock_classification = MagicMock()
        mock_classification.source_type = SourceType.PYTHON
        self.mock_source_classifier.classify_file.return_value = mock_classification
        
        # Test data
        batch = [
            {
                "file_path": "test/file1.py",
                "file_content": "DATABASE_URL = 'postgres://test'"
            }
        ]
        
        prompt = "test prompt"
        
        # Execute
        results = await self.processor._invoke_agent_on_batch(prompt, batch)
        
        # Verify
        assert len(results) == 1
        assert results[0].file_path == "test/file1.py"
        assert results[0].success is True
        assert results[0].total_changes == 0
        
        # Verify no file update was called
        self.mock_contextual_rules_engine._update_file_content.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('openai.AsyncOpenAI')
    async def test_invoke_agent_on_batch_error(self, mock_openai):
        """Test _invoke_agent_on_batch with error handling."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_openai.return_value = mock_agent
        mock_agent.chat.completions.create.side_effect = Exception("OpenAI API error")
        
        # Setup source classifier mock
        mock_classification = MagicMock()
        mock_classification.source_type = SourceType.PYTHON
        self.mock_source_classifier.classify_file.return_value = mock_classification
        
        # Test data
        batch = [
            {
                "file_path": "test/file1.py",
                "file_content": "DATABASE_URL = 'postgres://test'"
            }
        ]
        
        prompt = "test prompt"
        
        # Execute
        results = await self.processor._invoke_agent_on_batch(prompt, batch)
        
        # Verify
        assert len(results) == 1
        assert results[0].file_path == "test/file1.py"
        assert results[0].success is False
        assert results[0].total_changes == 0
        assert "OpenAI API error" in results[0].error_message
        
        # Verify error was logged
        self.processor.logger.log_error.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_files_success(self):
        """Test successful process_files execution."""
        # Setup source classifier mock
        mock_classification = MagicMock()
        mock_classification.source_type = SourceType.PYTHON
        self.mock_source_classifier.classify_file.return_value = mock_classification
        
        # Setup contextual rules engine mock
        self.mock_contextual_rules_engine._get_applicable_rules.return_value = {
            "database_removal": ["rule1", "rule2"]
        }
        
        # Mock _invoke_agent_on_batch
        mock_result = FileProcessingResult(
            file_path="test/file1.py",
            source_type=SourceType.PYTHON,
            success=True,
            total_changes=1
        )
        
        with patch.object(self.processor, '_invoke_agent_on_batch', return_value=[mock_result]):
            # Test data
            files_to_process = [
                {
                    "file_path": "test/file1.py",
                    "file_content": "DATABASE_URL = 'postgres://test'"
                },
                {
                    "file_path": "test/file2.py",
                    "file_content": "import psycopg2"
                }
            ]
            
            # Execute
            results = await self.processor.process_files(files_to_process, batch_size=2)
            
            # Verify
            assert len(results) == 2  # One batch with 2 files
            assert all(isinstance(result, FileProcessingResult) for result in results)
            
            # Verify logging
            self.processor.logger.log_info.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_files_missing_content(self):
        """Test process_files with missing file content."""
        # Test data with missing content
        files_to_process = [
            {
                "file_path": "test/file1.py",
                "file_content": "DATABASE_URL = 'postgres://test'"
            },
            {
                "file_path": "test/file2.py",
                "file_content": None  # Missing content
            }
        ]
        
        # Setup source classifier mock
        mock_classification = MagicMock()
        mock_classification.source_type = SourceType.PYTHON
        self.mock_source_classifier.classify_file.return_value = mock_classification
        
        # Execute
        results = await self.processor.process_files(files_to_process)
        
        # Verify
        assert len(results) == 1  # Only one file processed
        
        # Verify warning was logged
        self.processor.logger.log_warning.assert_called()


class TestPatternDiscoveryFunctions:
    """Test pattern discovery utility functions."""
    
    @pytest.mark.asyncio
    async def test_process_discovered_files_with_rules_agentic(self):
        """Test process_discovered_files_with_rules with agentic processor."""
        # Setup mocks
        mock_context = MagicMock()
        mock_context.clients.get.return_value = MagicMock()
        
        mock_source_classifier = MagicMock()
        mock_contextual_rules_engine = MagicMock()
        mock_logger = MagicMock()
        
        discovery_result = {
            "files": [
                {"file_path": "test/file1.py", "file_content": "DATABASE_URL = 'test'"}
            ]
        }
        
        # Mock AgenticFileProcessor
        with patch('concrete.db_decommission.pattern_discovery.AgenticFileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = [
                FileProcessingResult(
                    file_path="test/file1.py",
                    source_type=SourceType.PYTHON,
                    success=True,
                    total_changes=1
                )
            ]
            mock_processor_class.return_value = mock_processor
            
            # Execute
            result = await process_discovered_files_with_rules(
                mock_context,
                discovery_result,
                "test_db",
                "test-owner",
                "test-repo",
                mock_contextual_rules_engine,
                mock_source_classifier,
                mock_logger
            )
            
            # Verify
            assert result["files_processed"] == 1
            assert result["files_modified"] == 1
            mock_processor.process_files.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_discovered_files_with_rules_sequential(self):
        """Test process_discovered_files_with_rules with sequential processor."""
        # Setup mocks
        mock_context = MagicMock()
        mock_context.clients.get.return_value = MagicMock()
        
        mock_source_classifier = MagicMock()
        mock_classification = MagicMock()
        mock_source_classifier.classify_file.return_value = mock_classification
        
        mock_contextual_rules_engine = MagicMock()
        mock_processing_result = FileProcessingResult(
            file_path="test/file1.py",
            source_type=SourceType.PYTHON,
            success=True,
            total_changes=1
        )
        mock_contextual_rules_engine.process_file_with_contextual_rules.return_value = mock_processing_result
        
        mock_logger = MagicMock()
        
        discovery_result = {
            "files": [
                {"path": "test/file1.py", "content": "DATABASE_URL = 'test'"}
            ]
        }
        
        # Patch to use sequential processor
        with patch('concrete.db_decommission.pattern_discovery.USE_AGENTIC_PROCESSOR', False):
            # Execute
            result = await process_discovered_files_with_rules(
                mock_context,
                discovery_result,
                "test_db",
                "test-owner",
                "test-repo",
                mock_contextual_rules_engine,
                mock_source_classifier,
                mock_logger
            )
            
            # Verify
            assert result["files_processed"] == 1
            assert result["files_modified"] == 1
    
    @pytest.mark.asyncio
    async def test_process_discovered_files_with_rules_error(self):
        """Test process_discovered_files_with_rules with error handling."""
        # Setup mocks
        mock_context = MagicMock()
        mock_source_classifier = MagicMock()
        mock_contextual_rules_engine = MagicMock()
        mock_logger = MagicMock()
        
        discovery_result = {
            "files": [
                {"file_path": "test/file1.py", "file_content": "DATABASE_URL = 'test'"}
            ]
        }
        
        # Mock AgenticFileProcessor to raise exception
        with patch('concrete.db_decommission.pattern_discovery.AgenticFileProcessor') as mock_processor_class:
            mock_processor_class.side_effect = Exception("Processor creation failed")
            
            # Execute
            result = await process_discovered_files_with_rules(
                mock_context,
                discovery_result,
                "test_db",
                "test-owner",
                "test-repo",
                mock_contextual_rules_engine,
                mock_source_classifier,
                mock_logger
            )
            
            # Verify
            assert result["files_processed"] == 0
            assert result["files_modified"] == 0
            mock_logger.log_error.assert_called()
    
    @pytest.mark.asyncio
    async def test_log_pattern_discovery_visual(self):
        """Test log_pattern_discovery_visual function."""
        # Setup mocks
        mock_logger = MagicMock()
        
        discovery_result = {
            "files_by_type": {
                "python": [{"path": "file1.py"}, {"path": "file2.py"}],
                "sql": [{"path": "migrate.sql"}],
                "documentation": [{"path": "README.md"}]
            }
        }
        
        # Execute
        await log_pattern_discovery_visual(
            "test-workflow-123",
            discovery_result,
            "test-owner",
            "test-repo",
            mock_logger
        )
        
        # Verify
        mock_logger.log_table.assert_called_once()
        mock_logger.log_tree.assert_called_once()
        mock_logger.log_info.assert_called()
        
        # Verify table data
        table_call = mock_logger.log_table.call_args
        assert "Pattern Discovery Results" in table_call[0][0]
        table_data = table_call[0][1]
        assert len(table_data) == 3
        assert any(row["file_type"] == "Python" for row in table_data)
        assert any(row["file_type"] == "Sql" for row in table_data)
        assert any(row["file_type"] == "Documentation" for row in table_data)
    
    @pytest.mark.asyncio
    async def test_log_pattern_discovery_visual_empty(self):
        """Test log_pattern_discovery_visual with empty results."""
        # Setup mocks
        mock_logger = MagicMock()
        
        discovery_result = {
            "files_by_type": {}
        }
        
        # Execute
        await log_pattern_discovery_visual(
            "test-workflow-123",
            discovery_result,
            "test-owner",
            "test-repo",
            mock_logger
        )
        
        # Verify no table or tree logging for empty results
        mock_logger.log_table.assert_not_called()
        mock_logger.log_tree.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_log_pattern_discovery_visual_error(self):
        """Test log_pattern_discovery_visual with error handling."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_logger.log_table.side_effect = Exception("Logging error")
        
        discovery_result = {
            "files_by_type": {
                "python": [{"path": "file1.py"}]
            }
        }
        
        # Execute
        await log_pattern_discovery_visual(
            "test-workflow-123",
            discovery_result,
            "test-owner",
            "test-repo",
            mock_logger
        )
        
        # Verify error is logged
        mock_logger.log_warning.assert_called()
    
    def test_categorize_files_by_source_type(self):
        """Test categorize_files_by_source_type function."""
        # Setup mocks
        mock_source_classifier = MagicMock()
        
        # Mock classifications
        python_classification = MagicMock()
        python_classification.source_type = SourceType.PYTHON
        sql_classification = MagicMock()
        sql_classification.source_type = SourceType.SQL
        
        mock_source_classifier.classify_file.side_effect = [
            python_classification,
            sql_classification,
            python_classification
        ]
        
        # Test data
        files = [
            {"path": "file1.py", "content": "import os"},
            {"path": "migrate.sql", "content": "CREATE TABLE users"},
            {"path": "file2.py", "content": "def main(): pass"}
        ]
        
        # Execute
        result = categorize_files_by_source_type(files, mock_source_classifier)
        
        # Verify
        assert len(result) == 2
        assert SourceType.PYTHON in result
        assert SourceType.SQL in result
        assert len(result[SourceType.PYTHON]) == 2
        assert len(result[SourceType.SQL]) == 1
        
        # Verify classifier was called for each file
        assert mock_source_classifier.classify_file.call_count == 3
    
    def test_categorize_files_by_source_type_empty(self):
        """Test categorize_files_by_source_type with empty files."""
        mock_source_classifier = MagicMock()
        
        result = categorize_files_by_source_type([], mock_source_classifier)
        
        assert result == {}
    
    def test_calculate_processing_metrics(self):
        """Test calculate_processing_metrics function."""
        # Test data
        results = [
            FileProcessingResult(
                file_path="file1.py",
                source_type=SourceType.PYTHON,
                success=True,
                total_changes=3
            ),
            FileProcessingResult(
                file_path="file2.py",
                source_type=SourceType.PYTHON,
                success=True,
                total_changes=1
            ),
            FileProcessingResult(
                file_path="migrate.sql",
                source_type=SourceType.SQL,
                success=False,
                total_changes=0
            )
        ]
        
        # Execute
        metrics = calculate_processing_metrics(results)
        
        # Verify
        assert metrics["total_files"] == 3
        assert metrics["successful_files"] == 2
        assert metrics["failed_files"] == 1
        assert metrics["total_changes"] == 4
        assert metrics["success_rate"] == 66.66666666666666
        
        # Verify by_source_type metrics
        assert "by_source_type" in metrics
        assert "python" in metrics["by_source_type"]
        assert "sql" in metrics["by_source_type"]
        
        python_metrics = metrics["by_source_type"]["python"]
        assert python_metrics["total_files"] == 2
        assert python_metrics["successful_files"] == 2
        assert python_metrics["total_changes"] == 4
        
        sql_metrics = metrics["by_source_type"]["sql"]
        assert sql_metrics["total_files"] == 1
        assert sql_metrics["successful_files"] == 0
        assert sql_metrics["total_changes"] == 0
    
    def test_calculate_processing_metrics_empty(self):
        """Test calculate_processing_metrics with empty results."""
        metrics = calculate_processing_metrics([])
        
        assert metrics["total_files"] == 0
        assert metrics["successful_files"] == 0
        assert metrics["failed_files"] == 0
        assert metrics["total_changes"] == 0
        assert metrics["success_rate"] == 0
        assert metrics["by_source_type"] == {}
    
    def test_extract_high_confidence_patterns(self):
        """Test extract_high_confidence_patterns function."""
        # Test data
        discovery_result = {
            "files": [
                {"path": "file1.py", "confidence": 0.9},
                {"path": "file2.py", "confidence": 0.7},
                {"path": "file3.py", "confidence": 0.85},
                {"path": "file4.py", "confidence": 0.6}
            ]
        }
        
        # Execute
        high_confidence_files = extract_high_confidence_patterns(discovery_result, 0.8)
        
        # Verify
        assert len(high_confidence_files) == 2
        assert high_confidence_files[0]["path"] == "file1.py"
        assert high_confidence_files[1]["path"] == "file3.py"
    
    def test_extract_high_confidence_patterns_empty(self):
        """Test extract_high_confidence_patterns with empty results."""
        discovery_result = {"files": []}
        
        high_confidence_files = extract_high_confidence_patterns(discovery_result)
        
        assert high_confidence_files == []
    
    def test_generate_pattern_discovery_summary(self):
        """Test generate_pattern_discovery_summary function."""
        # Test data
        discovery_result = {
            "files": [
                {"path": "file1.py", "confidence": 0.9},
                {"path": "file2.py", "confidence": 0.7},
                {"path": "file3.py", "confidence": 0.85}
            ],
            "files_by_type": {
                "python": [{"path": "file1.py"}, {"path": "file2.py"}],
                "sql": [{"path": "file3.py"}]
            },
            "confidence_distribution": {
                "high": 2,
                "medium": 1,
                "low": 0
            },
            "total_files": 100,
            "matched_files": 3
        }
        
        # Execute
        summary = generate_pattern_discovery_summary(discovery_result, "test_db")
        
        # Verify
        assert summary["database_name"] == "test_db"
        assert summary["total_files_scanned"] == 100
        assert summary["matched_files"] == 3
        assert summary["match_rate"] == 3.0
        assert summary["high_confidence_matches"] == 2
        assert summary["file_types_found"] == 2
        assert summary["confidence_distribution"]["high"] == 2
        assert summary["files_by_type"]["python"] == 2
        assert summary["files_by_type"]["sql"] == 1
    
    def test_generate_pattern_discovery_summary_empty(self):
        """Test generate_pattern_discovery_summary with empty results."""
        discovery_result = {
            "files": [],
            "files_by_type": {},
            "confidence_distribution": {},
            "total_files": 0,
            "matched_files": 0
        }
        
        summary = generate_pattern_discovery_summary(discovery_result, "test_db")
        
        assert summary["database_name"] == "test_db"
        assert summary["total_files_scanned"] == 0
        assert summary["matched_files"] == 0
        assert summary["match_rate"] == 0
        assert summary["high_confidence_matches"] == 0
        assert summary["file_types_found"] == 0


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]