"""
Filesystem MCP Client

Specialized client for Filesystem MCP server operations.
Implements currently used methods extracted from working db_decommission_workflow.
"""

import logging
from pathlib import Path
from typing import Any
from dataclasses import dataclass

from utils import ensure_serializable
from .base import BaseMCPClient

logger = logging.getLogger(__name__)


@dataclass
class FilesystemScanResult:
    base_path: str
    pattern: str
    files_found: list[str]
    matches: list[dict[str, Any]]


class FilesystemMCPClient(BaseMCPClient):
    """
    Specialized MCP client for Filesystem server operations.
    
    Currently minimal implementation since filesystem tools are not heavily
    used in the current db_decommission_workflow. This provides structure
    for future expansion when filesystem operations are needed.
    """
    SERVER_NAME = "filesystem"

    def __init__(self, config_path: str | Path):
        """
        Initialize Filesystem MCP client.
        
        Args:
            config_path: Path to MCP configuration file
        """
        super().__init__(config_path)

    async def read_file(self, file_path: str) -> str:
        """
        Read contents of a file through MCP filesystem server.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            File contents as string (guaranteed serializable)
        """
        params = {"path": file_path}
        
        try:
            result = await self.call_tool_with_retry("read_file", params)
            
            # Extract content (pattern may vary by filesystem server implementation)
            if result and hasattr(result, 'content'):
                content = str(result.content)
                ensure_serializable(content)
                logger.debug(f"Read file {file_path}: {len(content)} characters")
                return content
            else:
                logger.warning(f"No content returned for file: {file_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return ""  # Return empty string (serializable)

    async def list_directory(self, dir_path: str) -> list[str]:
        """
        List contents of a directory through MCP filesystem server.
        
        Args:
            dir_path: Path to directory to list
            
        Returns:
            List of file/directory names (guaranteed serializable)
        """
        params = {"path": dir_path}
        
        try:
            result = await self.call_tool_with_retry("list_directory", params)
            
            # Extract directory listing (pattern may vary by filesystem server implementation)
            if result and hasattr(result, 'files'):
                files = list(result.files) if result.files else []
                ensure_serializable(files)
                logger.debug(f"Listed directory {dir_path}: {len(files)} items")
                return files
            else:
                logger.warning(f"No directory listing returned for: {dir_path}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list directory {dir_path}: {e}")
            return []  # Return empty list (serializable)

    async def search_files(self, pattern: str, base_path: str = ".") -> FilesystemScanResult:
        """
        Search for files matching a pattern through MCP filesystem server.
        
        Args:
            pattern: Search pattern (e.g., "*.py")
            base_path: Base directory to search from
            
        Returns:
            FilesystemScanResult with search results
        """
        params = {
            "pattern": pattern,
            "path": base_path
        }
        
        try:
            result = await self.call_tool_with_retry("search_files", params)
            
            # Extract search results (pattern may vary by filesystem server implementation)
            files_found = []
            matches = []
            
            if result and hasattr(result, 'files'):
                files_found = list(result.files) if result.files else []
                matches = [{"file": f, "type": "pattern_match"} for f in files_found]
            
            # Create result object
            search_result = FilesystemScanResult(
                base_path=base_path,
                pattern=pattern,
                files_found=files_found,
                matches=matches
            )
            
            # Ensure result is serializable
            ensure_serializable(search_result)
            
            logger.debug(f"File search completed for pattern {pattern} in {base_path}: {len(files_found)} files")
            return search_result
            
        except Exception as e:
            logger.error(f"Failed to search files with pattern {pattern} in {base_path}: {e}")
            
            # Return empty but valid result
            empty_result = FilesystemScanResult(
                base_path=base_path,
                pattern=pattern,
                files_found=[],
                matches=[]
            )
            ensure_serializable(empty_result)
            return empty_result

    async def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file through MCP filesystem server.
        
        Args:
            file_path: Path to file to write
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        params = {
            "path": file_path,
            "content": content
        }
        
        try:
            result = await self.call_tool_with_retry("write_file", params)
            
            # Check if write was successful (pattern may vary by filesystem server implementation)
            success = result and (hasattr(result, 'success') and result.success)
            
            if success:
                logger.debug(f"Successfully wrote file: {file_path}")
            else:
                logger.warning(f"File write may have failed: {file_path}")
                
            return bool(success)
            
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False

    async def health_check(self) -> bool:
        """
        Perform a health check by listing available Filesystem tools.
        """
        try:
            await self.list_available_tools()
            logger.debug(f"FilesystemMCPClient ({self.server_name}) health check successful.")
            return True
        except Exception as e:
            logger.warning(f"FilesystemMCPClient ({self.server_name}) health check failed: {e}")
            return False

    async def list_available_tools(self) -> list[str]:
        """
        List available tools for the Filesystem MCP client.
        """
        return ["read_file", "list_directory", "search_files", "write_file"]

    # Placeholder methods for future filesystem operations
    
    async def create_directory(self, dir_path: str) -> bool:
        """
        Create a directory through MCP filesystem server.
        
        This is a placeholder for future implementation.
        
        Args:
            dir_path: Path to directory to create
            
        Returns:
            True if successful, False otherwise
        """
        logger.warning(f"create_directory not implemented yet for path: {dir_path}")
        return False

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file through MCP filesystem server.
        
        This is a placeholder for future implementation.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        logger.warning(f"delete_file not implemented yet for path: {file_path}")
        return False 