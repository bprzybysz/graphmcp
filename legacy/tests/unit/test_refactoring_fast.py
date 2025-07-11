"""
Fast Refactoring Tests

This module contains fast, focused tests for refactoring operations
during database decommissioning. Uses lightweight in-memory operations
for speed and comprehensive coverage.

Test Strategy:
- In-memory file content operations (no disk I/O)
- Sample code snippets for transformation testing  
- Pattern-based assertions for correctness
- Fast execution (<50ms per test)
- Comprehensive edge case coverage
"""

import pytest
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import re


@dataclass
class RefactoringTestCase:
    """A test case for refactoring operations."""
    name: str
    input_content: str
    expected_output: str
    database_name: str
    file_type: str
    transformation_type: str
    should_modify: bool = True
    
    
@dataclass 
class RefactoringResult:
    """Result of a refactoring operation."""
    success: bool
    modified: bool
    original_content: str
    new_content: str
    changes: List[Dict[str, Any]]
    confidence: float
    warnings: List[str] = None


class FastRefactoringEngine:
    """Lightweight refactoring engine for testing."""
    
    def __init__(self):
        self.supported_transformations = [
            "remove_database_references",
            "update_connection_strings", 
            "remove_schema_imports",
            "update_configuration_files",
            "comment_out_deprecated_code"
        ]
    
    def refactor_content(
        self, 
        content: str, 
        database_name: str, 
        file_type: str, 
        transformation_type: str
    ) -> RefactoringResult:
        """Perform refactoring on file content."""
        
        if transformation_type not in self.supported_transformations:
            return RefactoringResult(
                success=False, 
                modified=False,
                original_content=content,
                new_content=content,
                changes=[],
                confidence=0.0,
                warnings=[f"Unsupported transformation: {transformation_type}"]
            )
        
        # Apply transformation based on type
        if transformation_type == "remove_database_references":
            return self._remove_database_references(content, database_name, file_type)
        elif transformation_type == "update_connection_strings":
            return self._update_connection_strings(content, database_name, file_type)
        elif transformation_type == "remove_schema_imports":
            return self._remove_schema_imports(content, database_name, file_type)
        elif transformation_type == "update_configuration_files":
            return self._update_configuration_files(content, database_name, file_type)
        elif transformation_type == "comment_out_deprecated_code":
            return self._comment_out_deprecated_code(content, database_name, file_type)
    
    def _remove_database_references(self, content: str, database_name: str, file_type: str) -> RefactoringResult:
        """Remove direct database name references."""
        changes = []
        new_content = content
        
        # Pattern to find database name references
        db_pattern = re.compile(rf'\b{re.escape(database_name)}\b', re.IGNORECASE)
        matches = list(db_pattern.finditer(content))
        
        if not matches:
            return RefactoringResult(
                success=True,
                modified=False,
                original_content=content,
                new_content=content,
                changes=[],
                confidence=1.0
            )
        
        # Replace based on file type
        if file_type == "python":
            # Replace with placeholder or remove entirely
            new_content = db_pattern.sub("# REMOVED_DATABASE", content)
        elif file_type in ["yaml", "json"]:
            # Comment out or set to null
            new_content = db_pattern.sub("null  # was: " + database_name, content)
        elif file_type == "shell":
            # Comment out
            new_content = db_pattern.sub("# " + database_name, content)
        else:
            # Generic replacement
            new_content = db_pattern.sub("REMOVED_DB", content)
        
        for match in matches:
            changes.append({
                "type": "removal",
                "line": content[:match.start()].count('\n') + 1,
                "original": match.group(),
                "replacement": "# REMOVED_DATABASE" if file_type == "python" else "REMOVED_DB",
                "position": match.span()
            })
        
        confidence = 0.9 if len(matches) <= 5 else 0.7  # Lower confidence for many matches
        
        return RefactoringResult(
            success=True,
            modified=True,
            original_content=content,
            new_content=new_content,
            changes=changes,
            confidence=confidence
        )
    
    def _update_connection_strings(self, content: str, database_name: str, file_type: str) -> RefactoringResult:
        """Update database connection strings."""
        changes = []
        new_content = content
        
        # Patterns for different connection string formats
        patterns = [
            # PostgreSQL connection strings
            rf'postgresql://[^/]+/{database_name}',
            rf'postgres://[^/]+/{database_name}',
            # SQLAlchemy URLs
            rf'engine\s*=\s*create_engine\(["\'].*{database_name}.*["\']',
            # Django settings
            rf'["\']NAME["\']\s*:\s*["\'][^"\']*{database_name}[^"\']*["\']',
        ]
        
        total_matches = 0
        for pattern in patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            total_matches += len(matches)
            
            for match in matches:
                # Replace with placeholder connection
                replacement = match.group().replace(database_name, "PLACEHOLDER_DB")
                new_content = new_content.replace(match.group(), replacement)
                
                changes.append({
                    "type": "connection_update",
                    "line": content[:match.start()].count('\n') + 1,
                    "original": match.group(),
                    "replacement": replacement,
                    "position": match.span()
                })
        
        return RefactoringResult(
            success=True,
            modified=total_matches > 0,
            original_content=content,
            new_content=new_content,
            changes=changes,
            confidence=0.85 if total_matches > 0 else 1.0
        )
    
    def _remove_schema_imports(self, content: str, database_name: str, file_type: str) -> RefactoringResult:
        """Remove imports related to database schemas."""
        if file_type != "python":
            return RefactoringResult(
                success=True, modified=False, original_content=content,
                new_content=content, changes=[], confidence=1.0
            )
        
        changes = []
        lines = content.split('\n')
        new_lines = []
        
        import_patterns = [
            rf'from\s+{database_name}[._]\w+\s+import',
            rf'import\s+{database_name}[._]\w+',
            rf'from\s+.*{database_name}.*\s+import'
        ]
        
        for i, line in enumerate(lines):
            should_remove = False
            for pattern in import_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_remove = True
                    changes.append({
                        "type": "import_removal",
                        "line": i + 1,
                        "original": line,
                        "replacement": f"# REMOVED: {line}",
                        "position": (0, len(line))
                    })
                    break
            
            if should_remove:
                new_lines.append(f"# REMOVED: {line}")
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        return RefactoringResult(
            success=True,
            modified=len(changes) > 0,
            original_content=content,
            new_content=new_content,
            changes=changes,
            confidence=0.9
        )
    
    def _update_configuration_files(self, content: str, database_name: str, file_type: str) -> RefactoringResult:
        """Update configuration files to remove database references."""
        if file_type not in ["yaml", "json", "ini"]:
            return RefactoringResult(
                success=True, modified=False, original_content=content,
                new_content=content, changes=[], confidence=1.0
            )
        
        changes = []
        new_content = content
        
        # YAML-specific patterns
        if file_type == "yaml":
            patterns = [
                rf'database:\s*{database_name}',
                rf'db_name:\s*{database_name}',
                rf'name:\s*{database_name}'
            ]
        else:
            # Generic patterns
            patterns = [rf'{database_name}']
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                replacement = match.group().replace(database_name, "REMOVED_DB")
                new_content = new_content.replace(match.group(), replacement)
                
                changes.append({
                    "type": "config_update",
                    "line": content[:match.start()].count('\n') + 1,
                    "original": match.group(),
                    "replacement": replacement,
                    "position": match.span()
                })
        
        return RefactoringResult(
            success=True,
            modified=len(changes) > 0,
            original_content=content,
            new_content=new_content,
            changes=changes,
            confidence=0.8
        )
    
    def _comment_out_deprecated_code(self, content: str, database_name: str, file_type: str) -> RefactoringResult:
        """Comment out code blocks that use the deprecated database."""
        changes = []
        lines = content.split('\n')
        new_lines = []
        
        comment_prefix = "#" if file_type in ["python", "yaml", "shell"] else "//"
        
        for i, line in enumerate(lines):
            if database_name.lower() in line.lower() and not line.strip().startswith(comment_prefix):
                new_line = f"{comment_prefix} DEPRECATED: {line}"
                new_lines.append(new_line)
                changes.append({
                    "type": "deprecation_comment",
                    "line": i + 1,
                    "original": line,
                    "replacement": new_line,
                    "position": (0, len(line))
                })
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        return RefactoringResult(
            success=True,
            modified=len(changes) > 0,
            original_content=content,
            new_content=new_content,
            changes=changes,
            confidence=0.75
        )


class TestFastRefactoring:
    """Fast refactoring test suite."""
    
    def setup_method(self):
        """Setup for each test."""
        self.engine = FastRefactoringEngine()
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self) -> List[RefactoringTestCase]:
        """Create comprehensive test cases for refactoring."""
        return [
            # Python code transformations
            RefactoringTestCase(
                name="python_remove_db_references",
                input_content='''
import psycopg2
connection = psycopg2.connect("postgresql://localhost/postgres_air")
cursor = connection.cursor()
cursor.execute("SELECT * FROM postgres_air.users")
''',
                expected_output='''
import psycopg2
connection = psycopg2.connect("postgresql://localhost/# REMOVED_DATABASE")
cursor = connection.cursor()
cursor.execute("SELECT * FROM # REMOVED_DATABASE.users")
''',
                database_name="postgres_air",
                file_type="python",
                transformation_type="remove_database_references"
            ),
            
            # YAML configuration transformation
            RefactoringTestCase(
                name="yaml_config_update",
                input_content='''
database:
  name: postgres_air
  host: localhost
  port: 5432
''',
                expected_output='''
database:
  name: REMOVED_DB
  host: localhost
  port: 5432
''',
                database_name="postgres_air",
                file_type="yaml",
                transformation_type="update_configuration_files"
            ),
            
            # Shell script transformation
            RefactoringTestCase(
                name="shell_script_update",
                input_content='''
#!/bin/bash
echo "Connecting to postgres_air"
psql -d postgres_air -c "SELECT version();"
''',
                expected_output='''
#!/bin/bash
echo "Connecting to # postgres_air"
psql -d # postgres_air -c "SELECT version();"
''',
                database_name="postgres_air",
                file_type="shell",
                transformation_type="remove_database_references"
            ),
            
            # Python import removal
            RefactoringTestCase(
                name="python_import_removal",
                input_content='''
from postgres_air.models import User, Order
from postgres_air.utils import connect
import postgres_air.schema as schema
from other_module import something
''',
                expected_output='''
# REMOVED: from postgres_air.models import User, Order
# REMOVED: from postgres_air.utils import connect
# REMOVED: import postgres_air.schema as schema
from other_module import something
''',
                database_name="postgres_air",
                file_type="python",
                transformation_type="remove_schema_imports"
            ),
            
            # Edge case: No references to remove
            RefactoringTestCase(
                name="no_references_found",
                input_content='''
# This file has no database references
def calculate_total(items):
    return sum(item.price for item in items)
''',
                expected_output='''
# This file has no database references
def calculate_total(items):
    return sum(item.price for item in items)
''',
                database_name="postgres_air",
                file_type="python",
                transformation_type="remove_database_references",
                should_modify=False
            ),
        ]
    
    def test_engine_initialization(self):
        """Test refactoring engine initializes correctly."""
        engine = FastRefactoringEngine()
        assert len(engine.supported_transformations) > 0
        assert "remove_database_references" in engine.supported_transformations
    
    @pytest.mark.parametrize("test_case", [
        case for case in [
            RefactoringTestCase(
                name="python_remove_db_references",
                input_content='connection = psycopg2.connect("postgresql://localhost/postgres_air")',
                expected_output='connection = psycopg2.connect("postgresql://localhost/# REMOVED_DATABASE")',
                database_name="postgres_air",
                file_type="python", 
                transformation_type="remove_database_references"
            )
        ]
    ])
    def test_specific_transformations(self, test_case):
        """Test specific transformation scenarios."""
        result = self.engine.refactor_content(
            test_case.input_content,
            test_case.database_name,
            test_case.file_type,
            test_case.transformation_type
        )
        
        assert result.success
        assert result.modified == test_case.should_modify
        assert result.confidence > 0.5
        
        if test_case.should_modify:
            assert result.new_content != result.original_content
            assert len(result.changes) > 0
        else:
            assert result.new_content == result.original_content
            assert len(result.changes) == 0
    
    def test_unsupported_transformation(self):
        """Test handling of unsupported transformation types."""
        result = self.engine.refactor_content(
            "some content",
            "test_db",
            "python",
            "unsupported_transformation"
        )
        
        assert not result.success
        assert not result.modified
        assert len(result.warnings) > 0
        assert "Unsupported transformation" in result.warnings[0]
    
    def test_remove_database_references_comprehensive(self):
        """Test comprehensive database reference removal."""
        test_cases = [
            ("python", 'db_name = "postgres_air"', True),
            ("yaml", "database: postgres_air", True),
            ("shell", "psql postgres_air", True),
            ("python", "# No database references here", False),
        ]
        
        for file_type, content, should_modify in test_cases:
            result = self.engine.refactor_content(
                content, "postgres_air", file_type, "remove_database_references"
            )
            
            assert result.success
            assert result.modified == should_modify
            
            if should_modify:
                # Check that transformation occurred properly based on file type
                if file_type == "yaml":
                    assert "null" in result.new_content and "was:" in result.new_content
                elif file_type == "shell":
                    assert "# postgres_air" in result.new_content  # Comments out with #
                elif file_type == "python":
                    assert "# REMOVED_DATABASE" in result.new_content or "postgres_air" not in result.new_content
                else:
                    # Generic case
                    assert "REMOVED_DB" in result.new_content or "postgres_air" not in result.new_content
    
    def test_connection_string_updates(self):
        """Test connection string transformation."""
        test_content = '''
DATABASE_URL = "postgresql://user:pass@localhost/postgres_air"
engine = create_engine("postgres://localhost/postgres_air")
'''
        
        result = self.engine.refactor_content(
            test_content, "postgres_air", "python", "update_connection_strings"
        )
        
        assert result.success
        assert result.modified
        assert "PLACEHOLDER_DB" in result.new_content
        assert len(result.changes) >= 1
    
    def test_schema_import_removal(self):
        """Test removal of schema-related imports."""
        test_content = '''
from postgres_air.models import User
from postgres_air.utils import connect
from other_module import something_else
import postgres_air.schema
'''
        
        result = self.engine.refactor_content(
            test_content, "postgres_air", "python", "remove_schema_imports"
        )
        
        assert result.success
        assert result.modified
        assert "from other_module import something_else" in result.new_content  # Should preserve non-DB imports
        assert "# REMOVED:" in result.new_content
        assert len(result.changes) >= 3  # Should remove 3 postgres_air imports
    
    def test_configuration_file_updates(self):
        """Test configuration file transformations."""
        yaml_content = '''
database:
  name: postgres_air
  host: localhost
services:
  - postgres_air_service
'''
        
        result = self.engine.refactor_content(
            yaml_content, "postgres_air", "yaml", "update_configuration_files"
        )
        
        assert result.success
        assert result.modified
        assert "REMOVED_DB" in result.new_content
    
    def test_deprecation_commenting(self):
        """Test commenting out deprecated code."""
        test_content = '''
def get_postgres_air_data():
    return query("SELECT * FROM postgres_air.table")

def other_function():
    return "not related"
'''
        
        result = self.engine.refactor_content(
            test_content, "postgres_air", "python", "comment_out_deprecated_code"
        )
        
        assert result.success
        assert result.modified
        assert "# DEPRECATED:" in result.new_content
        assert "def other_function():" in result.new_content  # Should not comment unrelated code
    
    def test_confidence_scoring(self):
        """Test confidence scoring accuracy."""
        # High confidence case: few, clear references
        simple_content = 'DATABASE = "postgres_air"'
        result1 = self.engine.refactor_content(
            simple_content, "postgres_air", "python", "remove_database_references"
        )
        
        # Lower confidence case: many references (might be risky)
        complex_content = "postgres_air " * 10  # Many references
        result2 = self.engine.refactor_content(
            complex_content, "postgres_air", "python", "remove_database_references"
        )
        
        assert result1.confidence > result2.confidence
        assert result1.confidence >= 0.8
        assert result2.confidence >= 0.5
    
    def test_change_tracking(self):
        """Test that changes are properly tracked."""
        test_content = '''
line 1: postgres_air reference
line 2: another postgres_air reference  
line 3: no reference
'''
        
        result = self.engine.refactor_content(
            test_content, "postgres_air", "python", "remove_database_references"
        )
        
        assert result.success
        assert len(result.changes) == 2  # Two references found
        
        for change in result.changes:
            assert "type" in change
            assert "line" in change
            assert "original" in change
            assert "replacement" in change
            assert "position" in change
    
    def test_performance_benchmark(self):
        """Test that refactoring operations are fast."""
        import time
        
        # Large content for performance testing
        large_content = "\n".join([
            f"line {i}: postgres_air reference here" for i in range(100)
        ])
        
        start_time = time.time()
        result = self.engine.refactor_content(
            large_content, "postgres_air", "python", "remove_database_references"
        )
        duration = time.time() - start_time
        
        assert result.success
        assert duration < 0.05  # Should complete in under 50ms
        assert len(result.changes) == 100  # Should find all 100 references


# Helper functions for integration with existing test suite

def create_fast_refactoring_test_data() -> Dict[str, Any]:
    """Create test data for integration testing."""
    return {
        "sample_files": {
            "python": '''
from postgres_air.models import User
connection = psycopg2.connect("postgresql://localhost/postgres_air")
result = db.query("SELECT * FROM postgres_air.users")
''',
            "yaml": '''
database:
  name: postgres_air
  host: localhost
monitoring:
  - postgres_air_metrics
''',
            "shell": '''
#!/bin/bash
psql -d postgres_air -c "VACUUM ANALYZE;"
echo "postgres_air maintenance complete"
'''
        },
        "expected_transformations": {
            "remove_references": 3,
            "update_connections": 1,
            "remove_imports": 1
        }
    }


def benchmark_refactoring_performance(engine: FastRefactoringEngine, iterations: int = 100) -> Dict[str, float]:
    """Benchmark refactoring performance."""
    import time
    
    test_content = '''
def connect_to_postgres_air():
    return psycopg2.connect("postgresql://localhost/postgres_air")
    
def query_postgres_air_users():
    return db.query("SELECT * FROM postgres_air.users")
'''
    
    times = []
    for _ in range(iterations):
        start = time.time()
        result = engine.refactor_content(
            test_content, "postgres_air", "python", "remove_database_references"
        )
        times.append(time.time() - start)
    
    return {
        "avg_time": sum(times) / len(times),
        "max_time": max(times),
        "min_time": min(times),
        "total_time": sum(times)
    } 