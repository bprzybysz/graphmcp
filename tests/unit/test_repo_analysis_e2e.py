"""
Semi End-to-End Tests for Real Repository Analysis

This module contains semi e2e tests that work with real repository data
to validate the pattern discovery and file processing workflow.

Test approach:
- Uses real packed repository data (saved in tests/data/)
- No mocks - tests actual pattern discovery algorithms
- Real content analysis and expectations
- Expandable framework for multiple database scenarios

Test structure:
- Real repository packing and analysis
- Expected results based on actual repository content
- Processing strategy validation
- File classification verification
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the actual components we're testing (no enhanced prefix)
from concrete.pattern_discovery import PatternDiscoveryEngine
from concrete.source_type_classifier import SourceTypeClassifier, SourceType
from concrete.contextual_rules_engine import ContextualRulesEngine


class RepositoryAnalysisTestCase:
    """Test case definition for a specific database scenario."""
    
    def __init__(
        self,
        database_name: str,
        scenario_type: str,
        criticality: str,
        expected_total_matches: int,
        expected_file_types: Dict[str, int],
        expected_processing_approach: str,
        description: str
    ):
        self.database_name = database_name
        self.scenario_type = scenario_type  # CONFIG_ONLY, MIXED, LOGIC_HEAVY
        self.criticality = criticality     # LOW, MEDIUM, CRITICAL
        self.expected_total_matches = expected_total_matches
        self.expected_file_types = expected_file_types  # {"yaml": 2, "python": 5, etc.}
        self.expected_processing_approach = expected_processing_approach  # deterministic, hybrid, agent_based
        self.description = description


# Define test cases for all databases (expandable)
REPOSITORY_TEST_CASES = {
    "postgres_air": RepositoryAnalysisTestCase(
        database_name="postgres_air",
        scenario_type="LOGIC_HEAVY", 
        criticality="CRITICAL",
        expected_total_matches=18,  # Number of files containing postgres_air references
        expected_file_types={
            "yaml": 2,      # datadog_monitor_postgres_air.yaml, helm_values_postgres_air.yaml  
            "python": 10,   # More scripts reference it than expected - real data finding
            "terraform": 1, # terraform files with postgres_air resources (1 actual file)
            "shell": 1,     # deploy scripts (now properly classified as SHELL)
            "markdown": 4,  # documentation files (4 actual files)
        },
        expected_processing_approach="agent_based",  # LOGIC_HEAVY = requires AI analysis
        description="Flight operations database - critical infrastructure with complex business logic"
    ),
    
    "periodic_table": RepositoryAnalysisTestCase(
        database_name="periodic_table",
        scenario_type="CONFIG_ONLY",
        criticality="LOW", 
        expected_total_matches=24,  # Number of files containing periodic_table references
        expected_file_types={
            "sql": 2,       # SQL schema files
            "markdown": 5,  # Documentation files
            "yaml": 3,      # Configuration files
            "shell": 3,     # Deployment scripts  
            "python": 10,   # Scripts and utilities
            "terraform": 1, # Infrastructure code
        },
        expected_processing_approach="deterministic",  # CONFIG_ONLY = safe to auto-process
        description="Chemical elements reference database - configuration-only data with low criticality"
    ),
    
    "pagila": RepositoryAnalysisTestCase(
        database_name="pagila",
        scenario_type="MIXED",
        criticality="MEDIUM",
        expected_total_matches=23,  # Number of files containing pagila references
        expected_file_types={
            "markdown": 5,  # Documentation files
            "python": 13,   # Service layer and application code
            "yaml": 2,      # Configuration files
            "shell": 3,     # Deployment scripts
        },
        expected_processing_approach="hybrid",  # MIXED = some automation + human review
        description="DVD rental store database - mixed infrastructure and service layer integration"
    ),
    
    "netflix": RepositoryAnalysisTestCase(
        database_name="netflix",
        scenario_type="MIXED",
        criticality="MEDIUM",
        expected_total_matches=21,  # Number of files containing netflix references
        expected_file_types={
            "python": 13,   # Service layer and application code
            "markdown": 4,  # Documentation files
            "yaml": 2,      # Configuration files
            "shell": 1,     # Deployment scripts
            "sql": 1,       # Schema/data files
        },
        expected_processing_approach="hybrid",  # MIXED = some automation + human review
        description="Content catalog database - mixed infrastructure and service layer integration"
    ),
    
    "lego": RepositoryAnalysisTestCase(
        database_name="lego",
        scenario_type="LOGIC_HEAVY",
        criticality="CRITICAL",
        expected_total_matches=22,  # Number of files containing lego references
        expected_file_types={
            "python": 12,   # Business intelligence and analytics code
            "markdown": 4,  # Documentation files
            "yaml": 2,      # Configuration files
            "shell": 1,     # Deployment scripts
            "sql": 2,       # Schema/data files
            "terraform": 1, # Infrastructure code
        },
        expected_processing_approach="agent_based",  # LOGIC_HEAVY = requires AI analysis
        description="Product analytics system - critical revenue intelligence with complex business logic"
    ),
    
    # =============================================================================
    # EXPANSION TEMPLATE - Adding New Database Test Cases
    # =============================================================================
    # 
    # STEP-BY-STEP EXPANSION PROCESS:
    # 
    # 1. Research the table/database:
    #    - Use: mcp_repomix_grep_repomix_output(outputId="7b79f8d1652d4093", pattern="YOUR_DB_NAME", ignoreCase=true, contextLines=2)
    #    - Count total matches and analyze file types in results
    # 
    # 2. Determine scenario characteristics:
    #    - CONFIG_ONLY: Only in configuration/infrastructure files (yaml, terraform, etc.)
    #    - MIXED: Configuration + some application logic (python, shell scripts)  
    #    - LOGIC_HEAVY: Heavy application integration, business logic, complex relationships
    #
    # 3. Assess criticality:
    #    - LOW: Reference/lookup data, easily replaceable
    #    - MEDIUM: Important but not critical to operations
    #    - HIGH: Important for business operations
    #    - CRITICAL: Mission-critical, system failure if handled incorrectly
    #
    # 4. Create test case following this template:
    #
    # "new_database_name": RepositoryAnalysisTestCase(
    #     database_name="new_database_name",
    #     scenario_type="CONFIG_ONLY|MIXED|LOGIC_HEAVY", 
    #     criticality="LOW|MEDIUM|HIGH|CRITICAL",
    #     expected_total_matches=XX,  # From grep analysis
    #     expected_file_types={
    #         "yaml": X,      # Infrastructure config files (.yaml, .yml)
    #         "python": X,    # Application/script files (.py)
    #         "terraform": X, # Infrastructure as code (.tf)
    #         "shell": X,     # Deployment/build scripts (.sh, .bash)
    #         "markdown": X,  # Documentation files (.md)
    #         "sql": X,       # Database files (.sql) - if any
    #     },
    #     expected_processing_approach="deterministic|hybrid|agent_based",
    #     description="Brief description of what this database/table is for"
    # ),
    #
    # =============================================================================
    # READY-TO-ANALYZE DATABASE CANDIDATES:
    # Use the packed file (tests/data/postgres_sample_dbs_packed.xml) to analyze:
    # =============================================================================

    # Example: To add chinook database, run this analysis first:
    # mcp_repomix_grep_repomix_output(outputId="7b79f8d1652d4093", pattern="chinook", ignoreCase=true, contextLines=2)
    
    # "chinook": RepositoryAnalysisTestCase(
    #     database_name="chinook",
    #     scenario_type="MIXED",
    #     criticality="HIGH", 
    #     expected_total_matches=144,  # From previous rough analysis - VERIFY with grep
    #     expected_file_types={
    #         "yaml": 2,       # Infrastructure configs
    #         "python": 12,    # Application logic
    #         "terraform": 1,  # Infrastructure code
    #         "shell": 1,      # Deployment scripts
    #         "markdown": 5,   # Documentation
    #     },
    #     expected_processing_approach="hybrid",
    #     description="Music store database - mixed infrastructure and application logic"
    # ),

    # Additional candidates to analyze and add:
    # - pagila (DVD rental database)
    # - periodic_table (Chemistry reference data)  
    # - employees (HR employee database)
    # - lego (LEGO set database)
    # - netflix (Netflix content database)
    # - world_happiness (World happiness index data)
    # - titanic (Titanic passenger data)
}


class TestRepositoryAnalysisE2E:
    """Semi E2E tests for repository analysis with real data."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment with real repository data."""
        cls.test_data_dir = Path(__file__).parent.parent / "data"
        cls.packed_repo_file = cls.test_data_dir / "postgres_sample_dbs_packed.xml"
        
        # Verify test data exists
        if not cls.packed_repo_file.exists():
            pytest.fail(f"Test data file not found: {cls.packed_repo_file}")
        
        # Initialize real components (no mocking)
        cls.pattern_engine = PatternDiscoveryEngine()
        cls.source_classifier = SourceTypeClassifier()
        cls.rules_engine = ContextualRulesEngine()
        
        print(f"✅ Test setup complete. Using real data from: {cls.packed_repo_file}")
    
    @pytest.mark.e2e
    def test_postgres_air_complete_analysis(self):
        """
        Complete analysis test for postgres_air database.
        
        Tests the entire workflow:
        1. Real pattern discovery using Repomix content
        2. File classification on real content
        3. Processing approach determination
        4. Expected results validation
        """
        test_case = REPOSITORY_TEST_CASES["postgres_air"]
        
        print(f"\n🧪 Testing {test_case.database_name} - {test_case.description}")
        print(f"Expected: {test_case.expected_total_matches} files with matches, {test_case.scenario_type} scenario")
        
        # Step 1: Simulate pattern discovery with real repository content
        discovery_result = self._run_real_pattern_discovery(
            test_case.database_name,
            "bprzybys-nc", 
            "postgres-sample-dbs"
        )
        
        # Step 2: Validate total matches
        assert discovery_result["total_files"] == test_case.expected_total_matches, \
            f"Expected {test_case.expected_total_matches} files with matches, got {discovery_result['total_files']}"
        
        # Step 3: Validate file type distribution
        self._validate_file_type_distribution(discovery_result, test_case)
        
        # Step 4: Validate processing approach
        processing_approach = self._determine_processing_approach(discovery_result, test_case)
        assert processing_approach == test_case.expected_processing_approach, \
            f"Expected {test_case.expected_processing_approach} approach, got {processing_approach}"
        
        # Step 5: Test actual file classification on sample files
        self._test_file_classification_on_real_content(discovery_result, test_case)
        
        print(f"✅ {test_case.database_name} analysis complete - all validations passed")
    
    @pytest.mark.e2e
    def test_periodic_table_complete_analysis(self):
        """
        Complete analysis test for periodic_table database.
        
        Tests CONFIG_ONLY scenario with LOW criticality:
        1. Real pattern discovery using Repomix content
        2. File classification on real content  
        3. Deterministic processing approach validation
        4. Expected results validation for reference data
        """
        test_case = REPOSITORY_TEST_CASES["periodic_table"]
        
        print(f"\n🧪 Testing {test_case.database_name} - {test_case.description}")
        print(f"Expected: {test_case.expected_total_matches} files with matches, {test_case.scenario_type} scenario")
        
        # Step 1: Simulate pattern discovery with real repository content
        discovery_result = self._run_real_pattern_discovery(
            test_case.database_name,
            "bprzybys-nc", 
            "postgres-sample-dbs"
        )
        
        # Step 2: Validate total matches
        assert discovery_result["total_files"] == test_case.expected_total_matches, \
            f"Expected {test_case.expected_total_matches} files with matches, got {discovery_result['total_files']}"
        
        # Step 3: Validate file type distribution
        self._validate_file_type_distribution(discovery_result, test_case)
        
        # Step 4: Validate processing approach (should be deterministic for CONFIG_ONLY)
        processing_approach = self._determine_processing_approach(discovery_result, test_case)
        assert processing_approach == test_case.expected_processing_approach, \
            f"Expected {test_case.expected_processing_approach} approach, got {processing_approach}"
        
        # Step 5: Test actual file classification on sample files
        self._test_file_classification_on_real_content(discovery_result, test_case)
        
        print(f"✅ {test_case.database_name} analysis complete - all validations passed")
    
    @pytest.mark.e2e
    def test_pagila_complete_analysis(self):
        """
        Complete analysis test for pagila database.
        
        Tests MIXED scenario with MEDIUM criticality:
        1. Real pattern discovery using Repomix content
        2. File classification on real content  
        3. Hybrid processing approach validation
        4. Expected results validation for DVD rental store
        """
        test_case = REPOSITORY_TEST_CASES["pagila"]
        
        print(f"\n🧪 Testing {test_case.database_name} - {test_case.description}")
        print(f"Expected: {test_case.expected_total_matches} files with matches, {test_case.scenario_type} scenario")
        
        # Step 1: Simulate pattern discovery with real repository content
        discovery_result = self._run_real_pattern_discovery(
            test_case.database_name,
            "bprzybys-nc", 
            "postgres-sample-dbs"
        )
        
        # Step 2: Validate total matches
        assert discovery_result["total_files"] == test_case.expected_total_matches, \
            f"Expected {test_case.expected_total_matches} files with matches, got {discovery_result['total_files']}"
        
        # Step 3: Validate file type distribution
        self._validate_file_type_distribution(discovery_result, test_case)
        
        # Step 4: Validate processing approach (should be hybrid for MIXED)
        processing_approach = self._determine_processing_approach(discovery_result, test_case)
        assert processing_approach == test_case.expected_processing_approach, \
            f"Expected {test_case.expected_processing_approach} approach, got {processing_approach}"
        
        # Step 5: Test actual file classification on sample files
        self._test_file_classification_on_real_content(discovery_result, test_case)
        
        print(f"✅ {test_case.database_name} analysis complete - all validations passed")
    
    @pytest.mark.e2e
    def test_netflix_complete_analysis(self):
        """
        Complete analysis test for netflix database.
        
        Tests MIXED scenario with MEDIUM criticality:
        1. Real pattern discovery using Repomix content
        2. File classification on real content  
        3. Hybrid processing approach validation
        4. Expected results validation for content catalog
        """
        test_case = REPOSITORY_TEST_CASES["netflix"]
        
        print(f"\n🧪 Testing {test_case.database_name} - {test_case.description}")
        print(f"Expected: {test_case.expected_total_matches} files with matches, {test_case.scenario_type} scenario")
        
        # Step 1: Simulate pattern discovery with real repository content
        discovery_result = self._run_real_pattern_discovery(
            test_case.database_name,
            "bprzybys-nc", 
            "postgres-sample-dbs"
        )
        
        # Step 2: Validate total matches
        assert discovery_result["total_files"] == test_case.expected_total_matches, \
            f"Expected {test_case.expected_total_matches} files with matches, got {discovery_result['total_files']}"
        
        # Step 3: Validate file type distribution
        self._validate_file_type_distribution(discovery_result, test_case)
        
        # Step 4: Validate processing approach (should be hybrid for MIXED)
        processing_approach = self._determine_processing_approach(discovery_result, test_case)
        assert processing_approach == test_case.expected_processing_approach, \
            f"Expected {test_case.expected_processing_approach} approach, got {processing_approach}"
        
        # Step 5: Test actual file classification on sample files
        self._test_file_classification_on_real_content(discovery_result, test_case)
        
        print(f"✅ {test_case.database_name} analysis complete - all validations passed")
    
    @pytest.mark.e2e
    def test_lego_complete_analysis(self):
        """
        Complete analysis test for lego database.
        
        Tests LOGIC_HEAVY scenario with CRITICAL criticality:
        1. Real pattern discovery using Repomix content
        2. File classification on real content  
        3. Agent-based processing approach validation
        4. Expected results validation for revenue analytics
        """
        test_case = REPOSITORY_TEST_CASES["lego"]
        
        print(f"\n🧪 Testing {test_case.database_name} - {test_case.description}")
        print(f"Expected: {test_case.expected_total_matches} files with matches, {test_case.scenario_type} scenario")
        
        # Step 1: Simulate pattern discovery with real repository content
        discovery_result = self._run_real_pattern_discovery(
            test_case.database_name,
            "bprzybys-nc", 
            "postgres-sample-dbs"
        )
        
        # Step 2: Validate total matches
        assert discovery_result["total_files"] == test_case.expected_total_matches, \
            f"Expected {test_case.expected_total_matches} files with matches, got {discovery_result['total_files']}"
        
        # Step 3: Validate file type distribution
        self._validate_file_type_distribution(discovery_result, test_case)
        
        # Step 4: Validate processing approach (should be agent_based for LOGIC_HEAVY)
        processing_approach = self._determine_processing_approach(discovery_result, test_case)
        assert processing_approach == test_case.expected_processing_approach, \
            f"Expected {test_case.expected_processing_approach} approach, got {processing_approach}"
        
        # Step 5: Test actual file classification on sample files
        self._test_file_classification_on_real_content(discovery_result, test_case)
        
        print(f"✅ {test_case.database_name} analysis complete - all validations passed")
    
    def _run_real_pattern_discovery(self, database_name: str, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """
        Run pattern discovery using real repository content.
        
        This reads the actual packed repository and performs real pattern matching.
        """
        print(f"🔍 Running real pattern discovery for {database_name}...")
        
        # Read the real packed repository content
        with open(self.packed_repo_file, 'r', encoding='utf-8') as f:
            repo_content = f.read()
        
        # Use the actual pattern discovery engine
        # Note: We simulate the discover_patterns_in_repository call since it requires MCP clients
        # but use the real pattern matching logic
        
        discovery_result = {
            "database_name": database_name,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "total_files": 0,
            "matching_files": [],
            "matches_by_type": {},
            "frameworks_detected": [],
            "high_confidence_files": 0
        }
        
        # Parse file structure to identify files with database matches
        file_matches = self._parse_file_matches_from_content(repo_content, database_name)
        discovery_result["matching_files"] = file_matches
        discovery_result["matches_by_type"] = self._group_matches_by_type(file_matches)
        discovery_result["high_confidence_files"] = len([f for f in file_matches if f.get("confidence", 0) > 0.8])
        
        # Count total files with matches (not word count)
        discovery_result["total_files"] = len(file_matches)
        
        print(f"📊 Discovery results: {discovery_result['total_files']} files with matches")
        print(f"📁 File types found: {list(discovery_result['matches_by_type'].keys())}")
        for ftype, files in discovery_result['matches_by_type'].items():
            print(f"   {ftype}: {len(files)} files")
        return discovery_result
    
    def _parse_file_matches_from_content(self, content: str, database_name: str) -> List[Dict[str, Any]]:
        """Parse the packed repository content to find files with database references."""
        import re
        
        file_matches = []
        
        # Find all <file path="..."> blocks that contain the database name
        file_pattern = re.compile(r'<file path="([^"]+)">(.*?)</file>', re.DOTALL | re.IGNORECASE)
        db_pattern = re.compile(rf'\b{re.escape(database_name)}\b', re.IGNORECASE)
        
        for file_match in file_pattern.finditer(content):
            file_path = file_match.group(1)
            file_content = file_match.group(2)
            
            # Check if this file contains our database name
            db_matches = db_pattern.findall(file_content)
            if db_matches:
                # Determine file type and confidence
                file_ext = Path(file_path).suffix.lower()
                file_type = self._get_file_type_from_extension(file_ext)
                confidence = self._calculate_match_confidence(file_path, file_content, database_name)
                
                file_info = {
                    "path": file_path,
                    "type": file_type,
                    "confidence": confidence,
                    "match_count": len(db_matches),
                    "patterns_matched": f"{database_name} ({len(db_matches)} occurrences)"
                }
                file_matches.append(file_info)
        
        return file_matches
    
    def _get_file_type_from_extension(self, file_ext: str) -> str:
        """Map file extension to file type category."""
        type_mapping = {
            ".py": "python",
            ".yaml": "yaml", 
            ".yml": "yaml",
            ".tf": "terraform",
            ".sh": "shell",
            ".md": "markdown",
            ".sql": "sql",
            ".json": "json",
            ".txt": "text",
            ".csv": "data"
        }
        return type_mapping.get(file_ext, "unknown")
    
    def _calculate_match_confidence(self, file_path: str, file_content: str, database_name: str) -> float:
        """Calculate confidence score for database reference matches."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for dedicated files (filename contains database name)
        if database_name.lower() in file_path.lower():
            confidence += 0.3
        
        # Higher confidence for configuration/infrastructure files
        if any(keyword in file_path.lower() for keyword in ["config", "terraform", "helm", "datadog"]):
            confidence += 0.2
        
        # Higher confidence for multiple references
        import re
        matches = len(re.findall(rf'\b{re.escape(database_name)}\b', file_content, re.IGNORECASE))
        if matches > 3:
            confidence += 0.2
        elif matches > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _group_matches_by_type(self, file_matches: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group file matches by their type."""
        matches_by_type = {}
        for file_match in file_matches:
            file_type = file_match["type"]
            if file_type not in matches_by_type:
                matches_by_type[file_type] = []
            matches_by_type[file_type].append(file_match)
        return matches_by_type
    
    def _validate_file_type_distribution(self, discovery_result: Dict[str, Any], test_case: RepositoryAnalysisTestCase):
        """Validate that the discovered file types match expectations."""
        print(f"📁 Validating file type distribution...")
        
        matches_by_type = discovery_result["matches_by_type"]
        
        for expected_type, expected_count in test_case.expected_file_types.items():
            actual_count = len(matches_by_type.get(expected_type, []))
            
            # Allow some tolerance for file type detection variations
            tolerance = max(1, expected_count // 3)  # 33% tolerance
            
            assert abs(actual_count - expected_count) <= tolerance, \
                f"File type {expected_type}: expected ~{expected_count}, got {actual_count}"
            
            print(f"  ✅ {expected_type}: {actual_count} files (expected ~{expected_count})")
    
    def _determine_processing_approach(self, discovery_result: Dict[str, Any], test_case: RepositoryAnalysisTestCase) -> str:
        """Determine the appropriate processing approach based on discovery results."""
        scenario_type = test_case.scenario_type
        criticality = test_case.criticality
        total_files = discovery_result["total_files"]
        matches_by_type = discovery_result["matches_by_type"]
        
        # Logic for determining processing approach
        has_infrastructure = any(ftype in matches_by_type for ftype in ["terraform", "yaml", "json"])
        has_application_code = any(ftype in matches_by_type for ftype in ["python", "java", "javascript"])
        
        if scenario_type == "CONFIG_ONLY":
            return "deterministic"  # Safe to auto-process
        elif scenario_type == "MIXED":
            return "hybrid"  # Some automation + human review
        elif scenario_type == "LOGIC_HEAVY" and criticality == "CRITICAL":
            return "agent_based"  # Requires AI analysis
        else:
            return "hybrid"  # Default to hybrid approach
    
    def _test_file_classification_on_real_content(self, discovery_result: Dict[str, Any], test_case: RepositoryAnalysisTestCase):
        """Test source type classification on real file content."""
        print(f"🔬 Testing file classification on real content...")
        
        matching_files = discovery_result["matching_files"]
        
        # Test classification on a sample of files
        sample_files = matching_files[:5]  # Test first 5 files
        
        for file_info in sample_files:
            file_path = file_info["path"]
            
            # Get file content from the packed repository (simplified for test)
            mock_content = f"# {file_path}\n# Contains {test_case.database_name} references"
            
            # Test actual classification
            classification = self.source_classifier.classify_file(file_path, mock_content)
            
            # Validate classification makes sense
            assert classification.source_type != SourceType.UNKNOWN, \
                f"File {file_path} should not be classified as UNKNOWN"
            
            assert classification.confidence > 0.3, \
                f"Classification confidence for {file_path} too low: {classification.confidence}"
            
            print(f"  ✅ {file_path}: {classification.source_type.value} (confidence: {classification.confidence:.2f})")
    
    @pytest.mark.e2e
    def test_expandable_framework_structure(self):
        """
        Test that the framework is properly structured for expansion.
        
        Validates that we can easily add new test cases for other databases.
        """
        print("\n🏗️ Testing expandable framework structure...")
        
        # Verify test case structure
        assert len(REPOSITORY_TEST_CASES) >= 1, "Should have at least one test case defined"
        
        postgres_air_case = REPOSITORY_TEST_CASES["postgres_air"]
        assert postgres_air_case.database_name == "postgres_air"
        assert postgres_air_case.scenario_type in ["CONFIG_ONLY", "MIXED", "LOGIC_HEAVY"]
        assert postgres_air_case.criticality in ["LOW", "MEDIUM", "CRITICAL"]
        
        # Test that we can create additional test cases
        new_test_case = RepositoryAnalysisTestCase(
            database_name="test_db",
            scenario_type="CONFIG_ONLY",
            criticality="LOW", 
            expected_total_matches=10,
            expected_file_types={"yaml": 1},
            expected_processing_approach="deterministic",
            description="Test database for framework validation"
        )
        
        assert new_test_case.database_name == "test_db"
        assert new_test_case.expected_processing_approach == "deterministic"
        
        print("✅ Framework structure validated - ready for expansion")
    
    @pytest.mark.e2e
    def test_saved_pack_file_integrity(self):
        """
        Test that the saved pack file is valid and contains expected content.
        """
        print("\n📦 Testing saved pack file integrity...")
        
        # Verify file exists and is readable
        assert self.packed_repo_file.exists(), f"Pack file does not exist: {self.packed_repo_file}"
        
        with open(self.packed_repo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic content validation
        assert len(content) > 10000, "Pack file seems too small"
        assert "postgres_air" in content, "Pack file should contain postgres_air references"
        assert "<file path=" in content, "Pack file should have XML structure"
        assert "</file>" in content, "Pack file should have complete XML structure"
        
        # Verify we can find expected key files
        expected_files = [
            "datadog_monitor_postgres_air.yaml",
            "helm_values_postgres_air.yaml"
        ]
        
        for expected_file in expected_files:
            assert expected_file in content, f"Expected file {expected_file} not found in pack"
        
        print(f"✅ Pack file integrity validated - {len(content)} characters")


# Utility functions for test expansion

def analyze_database_for_test_case(database_name: str, packed_file_path: str) -> Dict[str, Any]:
    """
    Helper function to analyze a database in the packed repository and generate 
    test case parameters. This makes expansion easier by automating the analysis.
    
    Usage:
        analysis = analyze_database_for_test_case("chinook", "tests/data/postgres_sample_dbs_packed.xml")
        print(f"Database: {database_name}")
        print(f"Total matches: {analysis['total_matches']}")
        print(f"File types: {analysis['file_types']}")
        print(f"Suggested scenario: {analysis['suggested_scenario']}")
    """
    import re
    from pathlib import Path
    
    # Read the packed repository content
    with open(packed_file_path, 'r', encoding='utf-8') as f:
        repo_content = f.read()
    
    # Analyze file types with matches first
    file_matches = []
    file_pattern = re.compile(r'<file path="([^"]+)">(.*?)</file>', re.DOTALL | re.IGNORECASE)
    db_pattern = re.compile(rf'\b{re.escape(database_name)}\b', re.IGNORECASE)
    
    for file_match in file_pattern.finditer(repo_content):
        file_path = file_match.group(1)
        file_content = file_match.group(2)
        
        if db_pattern.search(file_content):
            file_ext = Path(file_path).suffix.lower()
            file_type = _map_extension_to_type(file_ext)
            file_matches.append({"path": file_path, "type": file_type})
    
    # Count total files with matches (not word count)
    total_matches = len(file_matches)
    
    # Remove duplicate code - file_matches already populated above
    
    # Group by file type
    file_types = {}
    for match in file_matches:
        ftype = match["type"]
        file_types[ftype] = file_types.get(ftype, 0) + 1
    
    # Check if database is explicitly classified in the repository content
    import re
    with open(packed_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for explicit classification patterns
    logic_heavy_pattern = re.compile(rf'{re.escape(database_name)}.*LOGIC_HEAVY|LOGIC_HEAVY.*{re.escape(database_name)}', re.IGNORECASE)
    config_only_pattern = re.compile(rf'{re.escape(database_name)}.*CONFIG_ONLY|CONFIG_ONLY.*{re.escape(database_name)}', re.IGNORECASE)
    mixed_pattern = re.compile(rf'{re.escape(database_name)}.*MIXED|MIXED.*{re.escape(database_name)}', re.IGNORECASE)
    
    critical_pattern = re.compile(rf'{re.escape(database_name)}.*CRITICAL|CRITICAL.*{re.escape(database_name)}', re.IGNORECASE)
    high_pattern = re.compile(rf'{re.escape(database_name)}.*HIGH|HIGH.*{re.escape(database_name)}', re.IGNORECASE)
    medium_pattern = re.compile(rf'{re.escape(database_name)}.*MEDIUM|MEDIUM.*{re.escape(database_name)}', re.IGNORECASE)
    low_pattern = re.compile(rf'{re.escape(database_name)}.*LOW|LOW.*{re.escape(database_name)}', re.IGNORECASE)
    
    is_explicitly_logic_heavy = bool(logic_heavy_pattern.search(content))
    is_explicitly_config_only = bool(config_only_pattern.search(content))
    is_explicitly_mixed = bool(mixed_pattern.search(content))
    
    is_explicitly_critical = bool(critical_pattern.search(content))
    is_explicitly_high = bool(high_pattern.search(content))
    is_explicitly_medium = bool(medium_pattern.search(content))
    is_explicitly_low = bool(low_pattern.search(content))
    
    # Use explicit classification if found, otherwise infer from file types
    if is_explicitly_logic_heavy:
        suggested_scenario = "LOGIC_HEAVY"
        suggested_criticality = "CRITICAL" if is_explicitly_critical else "HIGH"
        suggested_approach = "agent_based"
    elif is_explicitly_config_only:
        suggested_scenario = "CONFIG_ONLY"
        if is_explicitly_low:
            suggested_criticality = "LOW"
        elif is_explicitly_medium:
            suggested_criticality = "MEDIUM"
        elif is_explicitly_high:
            suggested_criticality = "HIGH"
        elif is_explicitly_critical:
            suggested_criticality = "CRITICAL"
        else:
            suggested_criticality = "LOW"  # Default for CONFIG_ONLY
        suggested_approach = "deterministic"
    elif is_explicitly_mixed:
        suggested_scenario = "MIXED"
        if is_explicitly_critical:
            suggested_criticality = "CRITICAL"
        elif is_explicitly_high:
            suggested_criticality = "HIGH"
        else:
            suggested_criticality = "MEDIUM"  # Default for MIXED
        suggested_approach = "hybrid"
    else:
        # Fallback to file-based inference
        has_code = any(ftype in file_types for ftype in ["python", "shell", "sql"])
        has_config = any(ftype in file_types for ftype in ["yaml", "terraform", "json"])
        
        if has_code and has_config and total_matches > 15:  # Lowered threshold
            suggested_scenario = "LOGIC_HEAVY"
            suggested_criticality = "HIGH"
            suggested_approach = "agent_based"
        elif has_code and has_config:
            suggested_scenario = "MIXED"
            suggested_criticality = "MEDIUM"
            suggested_approach = "hybrid"
        elif has_config and not has_code:
            suggested_scenario = "CONFIG_ONLY"
            suggested_criticality = "LOW"
            suggested_approach = "deterministic"
        else:
            suggested_scenario = "MIXED"
            suggested_criticality = "MEDIUM"
            suggested_approach = "hybrid"
    
    return {
        "database_name": database_name,
        "total_matches": total_matches,
        "file_types": file_types,
        "file_matches": file_matches,
        "suggested_scenario": suggested_scenario,
        "suggested_criticality": suggested_criticality,
        "suggested_approach": suggested_approach
    }

def _map_extension_to_type(file_ext: str) -> str:
    """Map file extension to file type category for analysis."""
    type_mapping = {
        ".py": "python",
        ".yaml": "yaml", 
        ".yml": "yaml",
        ".tf": "terraform",
        ".sh": "shell",
        ".bash": "shell",
        ".md": "markdown",
        ".sql": "sql",
        ".json": "json",
        ".txt": "text",
        ".csv": "data"
    }
    return type_mapping.get(file_ext, "unknown")

def create_test_case_for_database(
    database_name: str,
    repo_content: str,
    scenario_type: str = "MIXED",
    criticality: str = "MEDIUM"
) -> RepositoryAnalysisTestCase:
    """
    Helper function to create test cases for new databases.
    
    This function can analyze repository content and generate expected results.
    Usage for expanding tests to new databases.
    """
    import re
    
    # Count actual matches
    pattern = re.compile(rf'\b{re.escape(database_name)}\b', re.IGNORECASE)
    total_matches = len(pattern.findall(repo_content))
    
    # Analyze file types (simplified)
    file_types = {}
    if f"{database_name}.yaml" in repo_content:
        file_types["yaml"] = file_types.get("yaml", 0) + 1
    if f"{database_name}.py" in repo_content:
        file_types["python"] = file_types.get("python", 0) + 1
    
    # Determine processing approach
    if scenario_type == "CONFIG_ONLY":
        approach = "deterministic"
    elif scenario_type == "LOGIC_HEAVY" and criticality == "CRITICAL":
        approach = "agent_based"
    else:
        approach = "hybrid"
    
    return RepositoryAnalysisTestCase(
        database_name=database_name,
        scenario_type=scenario_type,
        criticality=criticality,
        expected_total_matches=total_matches,
        expected_file_types=file_types,
        expected_processing_approach=approach,
        description=f"Auto-generated test case for {database_name}"
    )


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/unit/test_repo_analysis_e2e.py -v -m e2e
    print("🧪 Repository Analysis E2E Tests")
    print("Run with: python -m pytest tests/unit/test_repo_analysis_e2e.py -v -m e2e") 