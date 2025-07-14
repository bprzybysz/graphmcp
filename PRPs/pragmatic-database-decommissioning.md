# PRP: Pragmatic Database Decommissioning (Essential)

**Status**: Planning Phase  
**Priority**: High  
**Target**: Minimal Viable Implementation  
**Version**: 1.0  
**Date**: 2025-07-14  

## 📋 Executive Summary

Essential database decommissioning: categorize extracted files and apply pragmatic strategies (remove infrastructure, comment configs, add exceptions). Goal: cluster works after redeployment.

## 🎯 Core Objectives

1. **Cluster Continuity**: Cluster functional after database removal
2. **Infrastructure Cleanup**: Remove Terraform resources, disable Helm charts
3. **Fail-Fast Strategy**: Replace connections with clear decommission exceptions

## 🔧 Implementation Requirements

### Essential Components Only

#### 1. FileDecommissionProcessor Class
```python
class FileDecommissionProcessor:
    """Processes extracted files using pragmatic decommission strategies."""
    
    async def process_files(
        self, 
        source_dir: str,
        database_name: str,
        ticket_id: str = "DB-DECOMM-001"
    ) -> Dict[str, Any]
```

#### 2. File Processing Strategies
```python
def process_terraform_file(content: str, db_name: str) -> str:
    """Comment out resources with decommission header."""
    
def process_config_file(content: str, db_name: str) -> str:
    """Comment out database configs."""
    
def process_code_file(content: str, db_name: str) -> str:
    """Add decommission exceptions."""
```

#### 3. Core Implementation
- [ ] **File categorization** by extension/content patterns
- [ ] **Strategy application** per file type
- [ ] **Decommission header generation**
- [ ] **Output to processed directory**

## 🧪 Testing Requirements

### Essential Tests Only
- [ ] **test_process_terraform_file**: Verify resource commenting
- [ ] **test_process_config_file**: Verify config commenting  
- [ ] **test_process_code_file**: Verify exception insertion

### E2E Test (Real Data)
- [ ] **test_process_extracted_files**: Process real extracted files
  - Source: `/Users/blaisem4/src/graphmcp/tests/tmp/pattern_match/postgres_air`
  - Database: `postgres_air`
  - Verify all file types handled correctly

## 📝 Implementation Blueprint

### `concrete/file_decommission_processor.py`
```python
"""
File Decommission Processor - Essential Implementation
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class FileDecommissionProcessor:
    
    def __init__(self):
        self.decommission_date = datetime.now().strftime("%Y-%m-%d")
    
    async def process_files(
        self, 
        source_dir: str,
        database_name: str,
        ticket_id: str = "DB-DECOMM-001"
    ) -> Dict[str, Any]:
        """
        Process all files in source directory with decommission strategies.
        
        Returns:
            Dict with processed_files, strategies_applied, output_directory
        """
        source_path = Path(source_dir)
        output_dir = source_path.parent / f"{database_name}_decommissioned"
        
        processed_files = []
        strategies_applied = {}
        
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                strategy = self._determine_strategy(file_path)
                processed_content = self._apply_strategy(
                    file_path, strategy, database_name, ticket_id
                )
                
                # Write to output directory
                output_file = output_dir / file_path.relative_to(source_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(processed_content)
                
                processed_files.append(str(file_path))
                strategies_applied[str(file_path)] = strategy
        
        return {
            "database_name": database_name,
            "source_directory": source_dir,
            "output_directory": str(output_dir),
            "processed_files": processed_files,
            "strategies_applied": strategies_applied,
            "success": True
        }
    
    def _determine_strategy(self, file_path: Path) -> str:
        """Determine decommission strategy based on file type."""
        if file_path.suffix in ['.tf']:
            return 'infrastructure'
        elif file_path.suffix in ['.yml', '.yaml'] and 'helm' in str(file_path):
            return 'infrastructure'
        elif file_path.suffix in ['.yml', '.yaml', '.json']:
            return 'configuration'
        elif file_path.suffix in ['.py', '.sh']:
            return 'code'
        else:
            return 'documentation'
    
    def _apply_strategy(
        self, 
        file_path: Path, 
        strategy: str, 
        database_name: str, 
        ticket_id: str
    ) -> str:
        """Apply decommission strategy to file content."""
        content = file_path.read_text()
        header = self._generate_header(database_name, ticket_id, strategy)
        
        if strategy == 'infrastructure':
            return self._process_infrastructure(content, database_name, header)
        elif strategy == 'configuration':
            return self._process_configuration(content, database_name, header)
        elif strategy == 'code':
            return self._process_code(content, database_name, header)
        else:
            return self._process_documentation(content, database_name, header)
    
    def _generate_header(self, db_name: str, ticket_id: str, strategy: str) -> str:
        """Generate decommission header."""
        return f"""# DECOMMISSIONED {self.decommission_date}: {db_name}
# Strategy: {strategy}
# Ticket: {ticket_id}
# Contact: ops-team@company.com
# Original content preserved below (commented)

"""
    
    def _process_infrastructure(self, content: str, db_name: str, header: str) -> str:
        """Comment out infrastructure resources."""
        lines = content.split('\n')
        processed_lines = []
        for line in lines:
            if db_name.lower() in line.lower():
                processed_lines.append(f"# {line}")
            else:
                processed_lines.append(line)
        return header + '\n'.join(processed_lines)
    
    def _process_configuration(self, content: str, db_name: str, header: str) -> str:
        """Comment out database configurations."""
        lines = content.split('\n')
        processed_lines = []
        for line in lines:
            if db_name.lower() in line.lower():
                processed_lines.append(f"# {line}")
            else:
                processed_lines.append(line)
        return header + '\n'.join(processed_lines)
    
    def _process_code(self, content: str, db_name: str, header: str) -> str:
        """Add decommission exceptions to code."""
        exception_code = f'''
def connect_to_{db_name}():
    raise Exception(
        "{db_name} database was decommissioned on {self.decommission_date}. "
        "Contact ops-team@company.com for migration guidance."
    )

'''
        return header + exception_code + f"\n# Original code:\n# " + content.replace('\n', '\n# ')
    
    def _process_documentation(self, content: str, db_name: str, header: str) -> str:
        """Add decommission notice to documentation."""
        notice = f"⚠️ **{db_name} DATABASE DECOMMISSIONED** - See header for details\n\n"
        return header + notice + content
```

### `tests/unit/test_file_decommission_processor.py`
```python
"""
Essential tests for FileDecommissionProcessor.
"""

import pytest
import tempfile
from pathlib import Path
from concrete.file_decommission_processor import FileDecommissionProcessor

class TestFileDecommissionProcessor:
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_terraform_file(self):
        """Test Terraform file processing."""
        processor = FileDecommissionProcessor()
        content = 'resource "azurerm_postgresql" "postgres_air" {\n  name = "postgres_air"\n}'
        
        result = processor._process_infrastructure(content, "postgres_air", "# Header\n")
        
        assert "# resource" in result
        assert "postgres_air" in result
        assert "DECOMMISSIONED" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio  
    async def test_process_config_file(self):
        """Test configuration file processing."""
        processor = FileDecommissionProcessor()
        content = 'database: postgres_air\nhost: localhost'
        
        result = processor._process_configuration(content, "postgres_air", "# Header\n")
        
        assert "# database: postgres_air" in result
        assert "host: localhost" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_code_file(self):
        """Test code file processing."""
        processor = FileDecommissionProcessor()
        content = 'def connect():\n    return psycopg2.connect("postgres_air")'
        
        result = processor._process_code(content, "postgres_air", "# Header\n")
        
        assert "def connect_to_postgres_air():" in result
        assert "raise Exception" in result
        assert "decommissioned" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_extracted_files(self):
        """E2E test with real extracted files."""
        source_dir = "/Users/blaisem4/src/graphmcp/tests/tmp/pattern_match/postgres_air"
        database_name = "postgres_air"
        
        # Skip if test data doesn't exist
        if not Path(source_dir).exists():
            pytest.skip(f"Test data directory not found: {source_dir}")
        
        processor = FileDecommissionProcessor()
        result = await processor.process_files(source_dir, database_name)
        
        assert result["success"] is True
        assert result["database_name"] == database_name
        assert len(result["processed_files"]) > 0
        
        # Verify output directory created
        output_dir = Path(result["output_directory"])
        assert output_dir.exists()
        
        # Verify files processed with strategies
        assert len(result["strategies_applied"]) > 0
        strategies = set(result["strategies_applied"].values())
        assert len(strategies) > 1  # Multiple strategies applied
```

## ✅ Acceptance Criteria (Minimal)

### Must Have
1. ✅ Process extracted files with appropriate strategies
2. ✅ Generate decommission headers with contact info
3. ✅ Unit tests for core processing functions
4. ✅ One e2e test with real extracted data

### Out of Scope
- Complex dependency analysis
- Terraform syntax validation
- Pull request automation
- Monitoring integration
- Advanced rollback mechanisms

---

**Next Steps**: Implement essential processor with real file testing