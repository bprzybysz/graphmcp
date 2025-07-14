# PRP: Database Reference Extractor (Essential Implementation)

**Status**: Planning Phase  
**Priority**: High  
**Target**: Minimal Viable Implementation  
**Version**: 1.0  
**Date**: 2025-07-14  

## 📋 Executive Summary

Minimal implementation of Database Reference Extractor: finds database references in packed repository files using normal grep, extracts matching files while preserving directory structure. Focus on essential functionality with unit and e2e tests.

## 🎯 Core Objectives

1. **Database Reference Discovery**: Find all references using normal grep
2. **File Extraction**: Extract matched files preserving directory structure  
3. **Basic Testing**: Unit tests + 1 e2e test with configurable target repo/database_name

## 🔧 Implementation Requirements

### Essential Components Only

#### 1. DatabaseReferenceExtractor Class
```python
class DatabaseReferenceExtractor:
    """Extracts database references using normal grep, preserves directory structure."""
    
    async def extract_references(
        self, 
        database_name: str, 
        target_repo_pack_path: str,
        output_dir: str = None
    ) -> Dict[str, Any]
```

#### 2. Basic Data Models
```python
@dataclass
class MatchedFile:
    """File containing database references."""
    original_path: str
    extracted_path: str
    content: str
    match_count: int
```

#### 3. Core Implementation
- [ ] **Normal grep search** (not contextual rules)
- [ ] **Directory structure preservation** 
- [ ] **File content parsing** from repomix XML
- [ ] **Basic error handling**

## 🧪 Testing Requirements

### Unit Tests
- [ ] **test_extract_references_basic**: Test with simple mock data
- [ ] **test_directory_preservation**: Verify paths preserved correctly
- [ ] **test_no_matches_found**: Handle case with no database references

### E2E Test (Parameterized)
- [ ] **test_real_extraction**: Test with real data
  - Parameters: `target_repo_pack_path`, `database_name`
  - Default: `tests/data/postgres_air_real_repo_pack.xml`, `postgres_air`

## 📝 Implementation Blueprint

### `concrete/database_reference_extractor.py`
```python
"""
Database Reference Extractor - Essential Implementation
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class MatchedFile:
    original_path: str
    extracted_path: str
    content: str
    match_count: int

class DatabaseReferenceExtractor:
    
    async def extract_references(
        self, 
        database_name: str, 
        target_repo_pack_path: str,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Extract database references using normal grep.
        
        Returns:
            Dict with matched_files, total_references, extraction_directory
        """
        start_time = time.time()
        
        # Default output directory
        if not output_dir:
            output_dir = f"tests/tmp/pattern_match/{database_name}"
        
        # Read and parse packed repository
        files = self._parse_repomix_file(target_repo_pack_path)
        
        # Find matches using normal grep
        matched_files = []
        total_references = 0
        
        for file_info in files:
            matches = self._grep_file_content(file_info['content'], database_name)
            if matches:
                extracted_path = self._extract_file(
                    file_info, output_dir, database_name
                )
                
                matched_file = MatchedFile(
                    original_path=file_info['path'],
                    extracted_path=extracted_path,
                    content=file_info['content'],
                    match_count=len(matches)
                )
                matched_files.append(matched_file)
                total_references += len(matches)
        
        return {
            "database_name": database_name,
            "source_file": target_repo_pack_path,
            "total_references": total_references,
            "matched_files": matched_files,
            "extraction_directory": output_dir,
            "success": True,
            "duration_seconds": time.time() - start_time
        }
    
    def _parse_repomix_file(self, file_path: str) -> List[Dict[str, str]]:
        """Parse repomix XML file to extract individual files."""
        # Implementation
        
    def _grep_file_content(self, content: str, database_name: str) -> List[str]:
        """Simple grep for database name in content."""
        # Implementation using re.findall
        
    def _extract_file(self, file_info: Dict, output_dir: str, database_name: str) -> str:
        """Extract file preserving directory structure."""
        # Implementation
```

### `tests/test_database_reference_extractor.py`
```python
"""
Essential tests for DatabaseReferenceExtractor.
"""

import pytest
import tempfile
from pathlib import Path
from concrete.database_reference_extractor import DatabaseReferenceExtractor

class TestDatabaseReferenceExtractor:
    
    @pytest.mark.unit
    async def test_extract_references_basic(self):
        """Test basic extraction with mock data."""
        # Create mock repomix file
        # Test extraction
        # Assert results
    
    @pytest.mark.unit  
    async def test_directory_preservation(self):
        """Test directory structure is preserved."""
        # Test nested paths preserved correctly
    
    @pytest.mark.unit
    async def test_no_matches_found(self):
        """Test behavior when no database references found."""
        # Assert graceful handling of no matches
    
    @pytest.mark.integration
    @pytest.mark.parametrize("target_repo_pack_path,database_name", [
        ("tests/data/postgres_air_real_repo_pack.xml", "postgres_air")
    ])
    async def test_real_extraction(self, target_repo_pack_path, database_name):
        """E2E test with real data - configurable via parameters."""
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
```

## ✅ Acceptance Criteria (Minimal)

### Must Have
1. ✅ Extract database references using normal grep
2. ✅ Preserve directory structure in extracted files
3. ✅ Unit tests for basic functionality
4. ✅ One parameterized e2e test

### Out of Scope
- Enhanced logging integration
- Progress tracking/visualization  
- Performance optimization
- HTML reports
- Complex error handling
- Comprehensive documentation

---

**Next Steps**: Execute minimal implementation in TASK.md