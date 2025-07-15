"""
Repomix MCP Client

Specialized client for Repomix MCP server operations.
Enables AI assistants to interact with code repositories efficiently
through repository packaging and analysis tools.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils import ensure_serializable
from .base import BaseMCPClient, MCPToolError

logger = logging.getLogger(__name__)

class RepomixMCPClient(BaseMCPClient):
    """
    Specialized MCP client for Repomix server operations.
    
    Repomix packages repositories into optimized single files
    for efficient AI analysis and processing.
    """
    SERVER_NAME = "ovr_repomix"
    
    def __init__(self, config_path: str | Path):
        """
        Initialize Repomix MCP client.
        
        Args:
            config_path: Path to MCP configuration file
        """
        super().__init__(config_path)

    async def list_available_tools(self) -> List[str]:
        """List available Repomix MCP tools."""
        try:
            result = await self._send_mcp_request("tools/list", {})
            return [tool.get("name") for tool in result.get("tools", [])]
        except Exception as e:
            logger.warning(f"Failed to list Repomix tools: {e}")
            return [
                "pack_codebase",
                "pack_remote_repository", 
                "grep_repomix_output"
            ]

    async def pack_codebase(self, directory_path: str, output_file: str = None,
                           include_patterns: List[str] = None,
                           exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Pack a local codebase directory into a single file.
        
        Args:
            directory_path: Local directory path to pack
            output_file: Optional output file path
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Packing result with file information
        """
        params = {
            "path": directory_path
        }
        
        if output_file:
            params["output"] = output_file
        if include_patterns:
            params["include"] = include_patterns
        if exclude_patterns:
            params["exclude"] = exclude_patterns
        
        try:
            result = await self.call_tool_with_retry("pack_codebase", params)
            
            pack_result = {
                "success": True,
                "directory_path": directory_path,
                "output_file": result.get("output_file"),
                "files_packed": result.get("files_packed", 0),
                "total_size": result.get("total_size", 0),
                "excluded_files": result.get("excluded_files", []),
                "summary": result.get("summary", "")
            }
            
            ensure_serializable(pack_result)
            logger.info(f"Packed codebase {directory_path}: {pack_result['files_packed']} files")
            return pack_result
            
        except Exception as e:
            logger.error(f"Failed to pack codebase {directory_path}: {e}")
            return {
                "success": False,
                "directory_path": directory_path,
                "error": str(e)
            }

    async def health_check(self) -> bool:
        """
        Perform a health check by listing available Repomix tools.
        """
        try:
            await self.list_available_tools()
            logger.debug(f"RepomixMCPClient ({self.server_name}) health check successful.")
            return True
        except Exception as e:
            logger.warning(f"RepomixMCPClient ({self.server_name}) health check failed: {e}")
            return False

    async def pack_remote_repository(self, repo_url: str, output_file: str = None,
                                   include_patterns: List[str] = None,
                                   exclude_patterns: List[str] = None,
                                   branch: str = None) -> Dict[str, Any]:
        """
        Pack a remote repository into a single file for AI analysis.
        
        Args:
            repo_url: GitHub repository URL to pack
            output_file: Optional output file path
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            branch: Specific branch to pack (defaults to default branch)
            
        Returns:
            Packed repository data with metadata
        """
        params = {
            "remote": repo_url # Changed 'url' to 'remote'
        }
        
        if output_file:
            params["output"] = output_file
        if include_patterns:
            params["include"] = include_patterns
        if exclude_patterns:
            params["exclude"] = exclude_patterns
        if branch:
            params["branch"] = branch
        
        try:
            logger.info(f"🔍 DEBUG: Calling pack_remote_repository with params: {params}")
            result = await self.call_tool_with_retry("pack_remote_repository", params)
            
            # Debug: Log the raw MCP response
            logger.info(f"🔍 DEBUG: Raw MCP response: {result}")
            
            # Check if the MCP response indicates success
            mcp_success = result.get("success", True)  # Default to True for backwards compatibility
            
            pack_result = {
                "success": mcp_success,
                "repository_url": repo_url,
                "output_file": result.get("output_file"),
                "files_packed": result.get("files_packed", 0),
                "total_size": result.get("total_size", 0),
                "branch": result.get("branch"),
                "commit_hash": result.get("commit_hash"),
                "excluded_files": result.get("excluded_files", []),
                "summary": result.get("summary", ""),
                "clone_time": result.get("clone_time"),
                "pack_time": result.get("pack_time")
            }
            
            ensure_serializable(pack_result)
            logger.info(f"Packed remote repository {repo_url}: {pack_result['files_packed']} files")
            return pack_result
            
        except Exception as e:
            logger.error(f"Failed to pack remote repository {repo_url}: {e}")
            return {
                "success": False,
                "repository_url": repo_url,
                "error": str(e)
            }

    async def grep_repomix_output(self, output_file: str, pattern: str,
                                context_lines: int = 2, case_sensitive: bool = True,
                                max_matches: int = 100) -> Dict[str, Any]:
        """
        Search for patterns in a repomix output file.
        
        Args:
            output_file: Path to repomix output file
            pattern: Regex pattern to search for
            context_lines: Number of context lines around matches
            case_sensitive: Whether search should be case sensitive
            max_matches: Maximum number of matches to return
            
        Returns:
            Search results with matches and context
        """
        params = {
            "file": output_file,
            "pattern": pattern,
            "context": context_lines,
            "case_sensitive": case_sensitive,
            "max_matches": max_matches
        }
        
        try:
            result = await self.call_tool_with_retry("grep_repomix_output", params)
            
            search_result = {
                "success": True,
                "output_file": output_file,
                "pattern": pattern,
                "total_matches": result.get("total_matches", 0),
                "matches": result.get("matches", []),
                "files_searched": result.get("files_searched", 0),
                "search_time": result.get("search_time")
            }
            
            ensure_serializable(search_result)
            logger.debug(f"Grep search found {search_result['total_matches']} matches for '{pattern}'")
            return search_result
            
        except Exception as e:
            logger.error(f"Failed to grep repomix output {output_file}: {e}")
            return {
                "success": False,
                "output_file": output_file,
                "pattern": pattern,
                "error": str(e)
            }

    # Legacy methods for backward compatibility
    async def pack_repository(self, repo_url: str, include_patterns: List[str] = None,
                            exclude_patterns: List[str] = None, 
                            output_file: str = None) -> Dict[str, Any]:
        """
        Legacy method: Pack a repository (maps to pack_remote_repository).
        
        Args:
            repo_url: Repository URL to pack
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            output_file: Optional output file path
            
        Returns:
            Packed repository data
        """
        logger.warning("pack_repository is deprecated, use pack_remote_repository instead")
        
        result = await self.pack_remote_repository(
            repo_url=repo_url,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            output_file=output_file
        )
        
        # Transform result to legacy format for compatibility
        if result.get("success"):
            return {
                "repository_url": repo_url,
                "packed_content": result.get("summary", ""),
                "file_count": result.get("files_packed", 0),
                "total_size": result.get("total_size", 0),
                "metadata": {
                    "output_file": result.get("output_file"),
                    "branch": result.get("branch"),
                    "commit_hash": result.get("commit_hash")
                }
            }
        else:
            return {
                "repository_url": repo_url,
                "error": result.get("error"),
                "packed_content": "",
                "file_count": 0
            }

    async def analyze_codebase_structure(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze codebase structure by packing and examining the repository.
        
        Args:
            repo_url: Repository URL to analyze
            
        Returns:
            Codebase structure analysis
        """
        try:
            # Pack the repository first
            pack_result = await self.pack_remote_repository(repo_url)
            
            if not pack_result.get("success"):
                return {
                    "repository_url": repo_url,
                    "error": pack_result.get("error", "Failed to pack repository")
                }
            
            # Extract structure information from pack result
            structure = {
                "repository_url": repo_url,
                "files_found": pack_result.get("files_packed", 0),
                "total_size": pack_result.get("total_size", 0),
                "branch": pack_result.get("branch"),
                "commit_hash": pack_result.get("commit_hash"),
                "excluded_files_count": len(pack_result.get("excluded_files", [])),
                "output_file": pack_result.get("output_file"),
                "pack_time": pack_result.get("pack_time"),
                "summary": pack_result.get("summary", "")
            }
            
            ensure_serializable(structure)
            logger.info(f"Analyzed codebase structure for {repo_url}")
            return structure
            
        except Exception as e:
            logger.error(f"Failed to analyze codebase structure for {repo_url}: {e}")
            return {
                "repository_url": repo_url,
                "error": str(e)
            }

    async def grep_content(self, repo_url: str, pattern: str, 
                          context_lines: int = 2) -> Dict[str, Any]:
        """
        Legacy method: Search for patterns in repository content.
        
        Args:
            repo_url: Repository URL to search
            pattern: Regex pattern to search for
            context_lines: Number of context lines around matches
            
        Returns:
            Search results with matches and context
        """
        logger.warning("grep_content is deprecated for URLs, use pack_remote_repository + grep_repomix_output")
        
        try:
            # First pack the repository
            pack_result = await self.pack_remote_repository(repo_url)
            
            if not pack_result.get("success"):
                return {
                    "repository_url": repo_url,
                    "pattern": pattern,
                    "error": pack_result.get("error"),
                    "matches": [],
                    "total_matches": 0
                }
            
            output_file = pack_result.get("output_file")
            if not output_file:
                return {
                    "repository_url": repo_url,
                    "pattern": pattern,
                    "error": "No output file from packing",
                    "matches": [],
                    "total_matches": 0
                }
            
            # Then search the packed output
            grep_result = await self.grep_repomix_output(
                output_file=output_file,
                pattern=pattern,
                context_lines=context_lines
            )
            
            # Transform to legacy format
            return {
                "repository_url": repo_url,
                "pattern": pattern,
                "matches": grep_result.get("matches", []),
                "total_matches": grep_result.get("total_matches", 0),
                "files_searched": grep_result.get("files_searched", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to grep content in {repo_url}: {e}")
            return {
                "repository_url": repo_url,
                "pattern": pattern,
                "error": str(e),
                "matches": [],
                "total_matches": 0
            } 