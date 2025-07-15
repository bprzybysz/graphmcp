"""
Database Reference Extractor - Essential Implementation

Extracts database references from packed repositories using normal grep,
preserving directory structure during file extraction.
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class MatchedFile:
    """File containing database references."""
    original_path: str
    extracted_path: str
    content: str
    match_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_path": self.original_path,
            "extracted_path": self.extracted_path,
            "content": self.content,
            "match_count": self.match_count
        }

class DatabaseReferenceExtractor:
    """Extracts database references preserving directory structure."""
    
    def __init__(self):
        self.logger = logger
    
    async def extract_references(
        self, 
        database_name: str, 
        target_repo_pack_path: str,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Extract database references using normal grep.
        
        Args:
            database_name: Name of database to search for (e.g., 'postgres_air')
            target_repo_pack_path: Path to repomix packed XML file
            output_dir: Output directory (defaults to tests/tmp/pattern_match/{database_name})
        
        Returns:
            Dict with matched_files, total_references, extraction_directory
        """
        start_time = time.time()
        
        try:
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
                "total_files": len(matched_files),  # Add this for repository processor compatibility
                "matched_files": [mf.to_dict() for mf in matched_files],  # Convert to dicts for JSON serialization
                "files": [{"path": mf.original_path, "matches": mf.match_count} for mf in matched_files],  # Add this for compatibility
                "extraction_directory": output_dir,
                "success": True,
                "duration_seconds": time.time() - start_time
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting references for {database_name}: {e}")
            return {
                "database_name": database_name,
                "source_file": target_repo_pack_path,
                "total_references": 0,
                "total_files": 0,
                "matched_files": [],
                "files": [],
                "extraction_directory": output_dir or f"tests/tmp/pattern_match/{database_name}",
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
    
    def _parse_repomix_file(self, file_path: str) -> List[Dict[str, str]]:
        """Parse repomix XML file to extract individual files."""
        files = []
        
        try:
            # Check if file exists first
            from pathlib import Path
            if not Path(file_path).exists():
                self.logger.warning(f"Repomix file does not exist: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse files using regex pattern: <file path="...">content</file>
            file_pattern = r'<file path="([^"]+)">\s*\n(.*?)\n</file>'
            matches = re.findall(file_pattern, content, re.DOTALL)
            
            self.logger.info(f"🔍 DEBUG: Found {len(matches)} file matches in XML")
            
            for file_path, file_content in matches:
                files.append({
                    "path": file_path,
                    "content": file_content.strip()
                })
                self.logger.info(f"🔍 DEBUG: Parsed file {file_path} with {len(file_content)} chars")
                
            self.logger.info(f"Parsed {len(files)} files from repomix file")
            return files
            
        except Exception as e:
            self.logger.error(f"Error parsing repomix file {file_path}: {e}")
            return []
        
    def _grep_file_content(self, content: str, database_name: str) -> List[str]:
        """Simple grep for database name in content using normal regex."""
        # Use normal grep approach - case insensitive search for database name
        # Look for word boundaries to avoid partial matches
        pattern = rf'\b{re.escape(database_name)}\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        self.logger.info(f"🔍 DEBUG: Searching for '{database_name}' in {len(content)} chars, found {len(matches)} matches")
        if matches:
            self.logger.info(f"🔍 DEBUG: Matches found: {matches[:5]}")  # Show first 5 matches
        
        return matches
        
    def _extract_file(self, file_info: Dict, output_dir: str, database_name: str) -> str:
        """Extract file preserving directory structure."""
        original_path = file_info['path']
        file_content = file_info['content']
        
        # Create full extraction path preserving directory structure
        extraction_path = Path(output_dir) / original_path
        
        # Create directories if they don't exist
        extraction_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        with open(extraction_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        self.logger.debug(f"Extracted file to: {extraction_path}")
        return str(extraction_path)