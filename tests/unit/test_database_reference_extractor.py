"""
Essential tests for DatabaseReferenceExtractor.
"""

import pytest
import tempfile
import os
from pathlib import Path
from concrete.database_reference_extractor import DatabaseReferenceExtractor, MatchedFile

class TestDatabaseReferenceExtractor:
    """Test suite for database reference extraction."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_references_basic(self):
        """Test basic extraction with mock data."""
        # Create mock repomix file content
        mock_content = '''This file is a merged representation of the entire codebase.

<file path="config/database.yml">
production:
  adapter: postgresql
  database: postgres_air
  username: postgres
  password: secret
  host: localhost
  port: 5432
</file>

<file path="scripts/migrate.py">
#!/usr/bin/env python3
"""Migration script for postgres_air database."""

import os
import psycopg2

DATABASE_URL = "postgresql://user:pass@localhost:5432/postgres_air"

def connect_to_postgres_air():
    """Connect to the postgres_air database."""
    return psycopg2.connect(DATABASE_URL)
</file>'''
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_content)
            temp_file = f.name
        
        try:
            # Test extraction
            extractor = DatabaseReferenceExtractor()
            result = await extractor.extract_references(
                database_name="postgres_air",
                target_repo_pack_path=temp_file
            )
            
            # Assert results
            assert result["success"] is True
            assert result["database_name"] == "postgres_air"
            assert result["total_references"] > 0
            assert len(result["matched_files"]) == 2  # Both files have references
            
            # Check that files were extracted
            extraction_dir = Path(result["extraction_directory"])
            assert extraction_dir.exists()
            assert (extraction_dir / "config" / "database.yml").exists()
            assert (extraction_dir / "scripts" / "migrate.py").exists()
            
        finally:
            # Cleanup
            os.unlink(temp_file)
    
    @pytest.mark.unit  
    @pytest.mark.asyncio
    async def test_directory_preservation(self):
        """Test directory structure is preserved."""
        # Create mock content with nested directories
        mock_content = '''<file path="deep/nested/path/config.json">
{
  "database": "postgres_air",
  "host": "localhost"
}
</file>

<file path="another/very/deep/path/settings.py">
DATABASE_NAME = "postgres_air"
DATABASE_HOST = "localhost"
</file>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_content)
            temp_file = f.name
        
        try:
            extractor = DatabaseReferenceExtractor()
            result = await extractor.extract_references(
                database_name="postgres_air",
                target_repo_pack_path=temp_file
            )
            
            # Verify nested directory structure is preserved
            extraction_dir = Path(result["extraction_directory"])
            assert (extraction_dir / "deep" / "nested" / "path" / "config.json").exists()
            assert (extraction_dir / "another" / "very" / "deep" / "path" / "settings.py").exists()
            
            # Verify file contents are preserved
            with open(extraction_dir / "deep" / "nested" / "path" / "config.json") as f:
                content = f.read()
                assert "postgres_air" in content
                assert '"database": "postgres_air"' in content
                
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_matches_found(self):
        """Test behavior when no database references found."""
        # Create mock content with no database references
        mock_content = '''<file path="README.md">
# Project Documentation

This is a sample project without any database references.
</file>

<file path="utils/helpers.py">
def helper_function():
    return "no database references here"
</file>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_content)
            temp_file = f.name
        
        try:
            extractor = DatabaseReferenceExtractor()
            result = await extractor.extract_references(
                database_name="postgres_air",
                target_repo_pack_path=temp_file
            )
            
            # Assert graceful handling of no matches
            assert result["success"] is True
            assert result["total_references"] == 0
            assert len(result["matched_files"]) == 0
            
            # Directory should still be created but empty
            extraction_dir = Path(result["extraction_directory"])
            assert extraction_dir.exists()
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.parametrize("target_repo_pack_path,database_name", [
        ("tests/data/postgres_air_real_repo_pack.xml", "postgres_air")
    ])
    async def test_real_extraction(self, target_repo_pack_path, database_name):
        """E2E test with real data - configurable via parameters."""
        # Check if test data file exists
        if not os.path.exists(target_repo_pack_path):
            pytest.skip(f"Test data file not found: {target_repo_pack_path}")
        
        extractor = DatabaseReferenceExtractor()
        
        result = await extractor.extract_references(
            database_name=database_name,
            target_repo_pack_path=target_repo_pack_path
        )
        
        assert result["success"] is True
        assert result["total_references"] > 0
        assert len(result["matched_files"]) > 0
        
        # Verify files were actually extracted
        extraction_dir = Path(result["extraction_directory"])
        assert extraction_dir.exists()
        
        # Verify at least one extracted file exists and contains the database name
        extracted_files = list(extraction_dir.rglob("*"))
        text_files = [f for f in extracted_files if f.is_file() and f.suffix in ['.yaml', '.yml', '.py', '.sql', '.md', '.txt']]
        assert len(text_files) > 0
        
        # Check that extracted files actually contain the database name
        found_reference = False
        for file_path in text_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if database_name.lower() in content.lower():
                        found_reference = True
                        break
            except Exception:
                # Skip files that can't be read
                continue
        
        assert found_reference, f"No references to {database_name} found in extracted files"
        
        # Verify the MatchedFile objects are properly structured
        for matched_file in result["matched_files"]:
            assert isinstance(matched_file, MatchedFile)
            assert matched_file.original_path
            assert matched_file.extracted_path
            assert matched_file.content
            assert matched_file.match_count > 0