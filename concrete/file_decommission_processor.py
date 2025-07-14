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