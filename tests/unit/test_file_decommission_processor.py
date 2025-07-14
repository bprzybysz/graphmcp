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
        header = processor._generate_header("postgres_air", "DB-DECOMM-001", "infrastructure")
        
        result = processor._process_infrastructure(content, "postgres_air", header)
        
        assert "# resource" in result
        assert "postgres_air" in result
        assert "DECOMMISSIONED" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio  
    async def test_process_config_file(self):
        """Test configuration file processing."""
        processor = FileDecommissionProcessor()
        content = 'database: postgres_air\nhost: localhost'
        header = processor._generate_header("postgres_air", "DB-DECOMM-001", "configuration")
        
        result = processor._process_configuration(content, "postgres_air", header)
        
        assert "# database: postgres_air" in result
        assert "host: localhost" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_code_file(self):
        """Test code file processing."""
        processor = FileDecommissionProcessor()
        content = 'def connect():\n    return psycopg2.connect("postgres_air")'
        header = processor._generate_header("postgres_air", "DB-DECOMM-001", "code")
        
        result = processor._process_code(content, "postgres_air", header)
        
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