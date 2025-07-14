"""
Essential tests for FileDecommissionProcessor.
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
from concrete.file_decommission_processor import FileDecommissionProcessor


def log_file_diff(file_path: str, original_content: str, modified_content: str):
    """Log file changes in git diff style with colors and dark theme styling."""
    if original_content == modified_content:
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "original"
        modified_file = temp_path / "modified"
        
        original_file.write_text(original_content)
        modified_file.write_text(modified_content)
        
        # Generate diff
        result = subprocess.run([
            'diff', '-u', '--label', f'a/{file_path}', '--label', f'b/{file_path}',
            str(original_file), str(modified_file)
        ], capture_output=True, text=True)
        
        if result.stdout:
            lines = result.stdout.split('\n')
            additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
            removals = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
            
            # Dark theme header with file path
            print(f"\n\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")
            print(f"\033[1;33m📝 DIFF: {file_path}\033[0m")
            print(f"\033[1;32m+{additions} additions\033[0m \033[1;31m-{removals} removals\033[0m")
            print(f"\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")
            
            for i, line in enumerate(lines):
                if line.startswith('---'):
                    # Dark theme file header - original
                    print(f"\033[1;31m--- {line[4:]}\033[0m")
                elif line.startswith('+++'):
                    # Dark theme file header - modified
                    print(f"\033[1;32m+++ {line[4:]}\033[0m")
                elif line.startswith('@@'):
                    # Dark theme line numbers context
                    print(f"\033[1;34m{line}\033[0m")
                elif line.startswith('+') and not line.startswith('+++'):
                    # Bright green for additions (dark theme)
                    line_content = line[1:]  # Remove the + prefix
                    print(f"\033[1;32m+{line_content}\033[0m")
                elif line.startswith('-') and not line.startswith('---'):
                    # Bright red for removals (dark theme)
                    line_content = line[1:]  # Remove the - prefix
                    print(f"\033[1;31m-{line_content}\033[0m")
                elif line.strip():
                    # Context lines (unchanged) - dim white for dark theme
                    print(f"\033[0;37m {line}\033[0m")
            
            print(f"\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")
            print()

class TestFileDecommissionProcessor:
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_terraform_file(self):
        """Test Terraform file processing."""
        processor = FileDecommissionProcessor()
        original_content = 'resource "azurerm_postgresql" "postgres_air" {\n  name = "postgres_air"\n}'
        header = processor._generate_header("postgres_air", "DB-DECOMM-001", "infrastructure")
        
        result = processor._process_infrastructure(original_content, "postgres_air", header)
        
        # Log diff for visualization
        log_file_diff("terraform_prod_critical_databases.tf", original_content, result)
        
        assert "# resource" in result
        assert "postgres_air" in result
        assert "DECOMMISSIONED" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio  
    async def test_process_config_file(self):
        """Test configuration file processing."""
        processor = FileDecommissionProcessor()
        original_content = 'database: postgres_air\nhost: localhost'
        header = processor._generate_header("postgres_air", "DB-DECOMM-001", "configuration")
        
        result = processor._process_configuration(original_content, "postgres_air", header)
        
        # Log diff for visualization
        log_file_diff("config/database.yml", original_content, result)
        
        assert "# database: postgres_air" in result
        assert "host: localhost" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_code_file(self):
        """Test code file processing."""
        processor = FileDecommissionProcessor()
        original_content = 'def connect():\n    return psycopg2.connect("postgres_air")'
        header = processor._generate_header("postgres_air", "DB-DECOMM-001", "code")
        
        result = processor._process_code(original_content, "postgres_air", header)
        
        # Log diff for visualization
        log_file_diff("scripts/migrate.py", original_content, result)
        
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
        
        # Store original content for diff comparison
        source_path = Path(source_dir)
        original_contents = {}
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                try:
                    original_contents[str(file_path)] = file_path.read_text()
                except:
                    pass  # Skip binary files
        
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
        
        # Show diff for sample files from each strategy
        print(f"\n🔍 DATABASE DECOMMISSIONING RESULTS - {database_name}")
        print(f"📊 Processed {len(result['processed_files'])} files")
        print(f"🛠️  Applied {len(strategies)} different strategies")
        
        strategy_samples = {}
        for file_path, strategy in result["strategies_applied"].items():
            if strategy not in strategy_samples:
                strategy_samples[strategy] = file_path
        
        # Show diff for one sample file per strategy
        for strategy, sample_file in strategy_samples.items():
            if sample_file in original_contents:
                processed_file = output_dir / Path(sample_file).relative_to(source_path)
                if processed_file.exists():
                    try:
                        processed_content = processed_file.read_text()
                        relative_path = str(Path(sample_file).relative_to(source_path))
                        print(f"\n📝 Strategy: {strategy.upper()}")
                        log_file_diff(relative_path, original_contents[sample_file], processed_content)
                    except:
                        pass  # Skip if file can't be read