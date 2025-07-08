"""
GitHub MCP Client

Specialized client for GitHub MCP server operations.
Implements currently used methods extracted from working db_decommission_workflow.
"""

import logging
from pathlib import Path
from typing import Any

from ..utils import GitHubSearchResult, ensure_serializable
from .base import BaseMCPClient

logger = logging.getLogger(__name__)


class GitHubMCPClient(BaseMCPClient):
    """
    Specialized MCP client for GitHub server operations.
    
    Implements the exact patterns and methods currently used in 
    db_decommission_workflow for maximum compatibility.
    """

    def __init__(self, config_path: str | Path, server_name: str = "ovr_github"):
        """
        Initialize GitHub MCP client.
        
        Args:
            config_path: Path to MCP configuration file
            server_name: Name of GitHub server in config (default: "ovr_github")
        """
        super().__init__(config_path, server_name)

    async def get_file_contents(self, owner: str, repo: str, path: str) -> str:
        """
        Get file contents from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path within repository
            
        Returns:
            File contents as string (guaranteed serializable)
        """
        params = {
            "owner": owner,
            "repo": repo,
            "path": path
        }
        
        try:
            result = await self.call_tool_with_retry("get_file_contents", params)
            
            # Extract content following exact pattern from DirectMCPClient
            if result and hasattr(result, 'content'):
                content = str(result.content)
                ensure_serializable(content)
                logger.debug(f"Retrieved file {path} from {owner}/{repo}: {len(content)} characters")
                return content
            else:
                logger.warning(f"No content returned for {path} in {owner}/{repo}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to get file contents for {owner}/{repo}/{path}: {e}")
            return ""  # Return empty string (serializable)

    async def search_code(self, query: str, sort: str = "indexed") -> str:
        """
        Search code in GitHub repositories.
        
        Args:
            query: Search query (e.g., "repo:owner/repo extension:py")
            sort: Sort order (default: "indexed")
            
        Returns:
            Search results as string (guaranteed serializable)
        """
        params = {
            "q": query,
            "sort": sort
        }
        
        try:
            result = await self.call_tool_with_retry("search_code", params)
            
            # Extract content following exact pattern from DirectMCPClient
            if result and hasattr(result, 'content'):
                content = str(result.content)
                if content and content != "null":
                    ensure_serializable(content)
                    logger.debug(f"Code search completed for query: {query}")
                    return content
                    
            logger.warning(f"No results returned for search query: {query}")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to search code with query '{query}': {e}")
            return ""  # Return empty string (serializable)

    async def analyze_repository(self, repo_url: str, max_retries: int = 3) -> GitHubSearchResult:
        """
        Analyze a GitHub repository using the exact pattern from DirectMCPClient.
        
        This method replicates DirectMCPClient.call_github_tools() exactly
        but returns a structured GitHubSearchResult object.
        
        Args:
            repo_url: Repository URL to analyze
            max_retries: Maximum retry attempts
            
        Returns:
            GitHubSearchResult with analysis data
        """
        # Extract repo owner and name from URL
        repo_parts = repo_url.rstrip('/').split('/')
        owner, repo = repo_parts[-2], repo_parts[-1]
        if repo.endswith('.git'):
            repo = repo[:-4]

        logger.info(f"Analyzing repository {owner}/{repo} from URL: {repo_url}")

        files_found = []
        matches = []

        try:
            # 1. Try to get repository files/structure (exact pattern from DirectMCPClient)
            for filename in ['README.md', 'package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml']:
                try:
                    content = await self.get_file_contents(owner, repo, filename)
                    if content and len(content) > 10:
                        files_found.append(filename)
                        matches.append({
                            "file": filename,
                            "content_preview": content[:500],
                            "type": "file_content"
                        })
                        logger.debug(f"Found useful file: {filename}")
                        break  # Found a useful file
                except Exception:
                    continue  # Try next file

            # 2. Try to search the repository (exact pattern from DirectMCPClient)
            try:
                search_query = f"repo:{owner}/{repo} extension:json OR extension:py OR extension:js OR extension:ts"
                search_results = await self.search_code(search_query)
                
                if search_results:
                    matches.append({
                        "query": search_query,
                        "results_preview": search_results[:500],
                        "type": "code_search"
                    })
                    logger.debug("Code search completed successfully")
                    
            except Exception as search_error:
                logger.debug(f"Code search failed: {search_error}")

            # Create result object
            result = GitHubSearchResult(
                repository_url=repo_url,
                files_found=files_found,
                matches=matches,
                search_query=f"analyze:{owner}/{repo}"
            )

            # Ensure result is serializable
            ensure_serializable(result)

            logger.info(f"Repository analysis completed for {repo_url}: {len(files_found)} files, {len(matches)} matches")
            return result

        except Exception as e:
            logger.error(f"Repository analysis failed for {repo_url}: {e}")
            
            # Return empty but valid result
            empty_result = GitHubSearchResult(
                repository_url=repo_url,
                files_found=[],
                matches=[],
                search_query=f"analyze:{owner}/{repo}"
            )
            ensure_serializable(empty_result)
            return empty_result

    async def extract_tech_stack(self, repo_url: str) -> list[str]:
        """
        Extract technology stack from repository analysis.
        
        Args:
            repo_url: Repository URL to analyze
            
        Returns:
            List of detected technologies (guaranteed serializable)
        """
        try:
            analysis = await self.analyze_repository(repo_url)
            
            tech_stack = []
            
            # Analyze found files to determine tech stack
            for file in analysis.files_found:
                if file == "package.json":
                    tech_stack.append("javascript")
                elif file == "requirements.txt" or file == "pyproject.toml":
                    tech_stack.append("python")
                elif file == "Cargo.toml":
                    tech_stack.append("rust")
                    
            # Look for patterns in matches
            for match in analysis.matches:
                if match.get("type") == "code_search":
                    content = match.get("results_preview", "").lower()
                    if "typescript" in content or ".ts" in content:
                        tech_stack.append("typescript")
                    if "react" in content:
                        tech_stack.append("react")
                    if "node" in content:
                        tech_stack.append("nodejs")

            # Remove duplicates and ensure serializable
            tech_stack = list(set(tech_stack))
            ensure_serializable(tech_stack)
            
            logger.info(f"Detected tech stack for {repo_url}: {tech_stack}")
            return tech_stack
            
        except Exception as e:
            logger.error(f"Failed to extract tech stack from {repo_url}: {e}")
            return []  # Return empty list (serializable)

    # Legacy compatibility method - maintains exact interface
    async def call_github_tools(self, repo_url: str, max_retries: int = 3) -> str:
        """
        Legacy compatibility method that maintains exact DirectMCPClient interface.
        
        This method exists for backward compatibility with existing code
        that expects the original call_github_tools() interface.
        
        Args:
            repo_url: Repository URL to analyze
            max_retries: Maximum retry attempts
            
        Returns:
            Analysis results as string (exact format as DirectMCPClient)
        """
        try:
            analysis = await self.analyze_repository(repo_url, max_retries)
            
            # Convert back to string format for compatibility
            results = []
            
            for match in analysis.matches:
                if match.get("type") == "file_content":
                    results.append(f"File {match['file']}: {match['content_preview']}...")
                elif match.get("type") == "code_search":
                    results.append(f"Code search results: {match['results_preview']}...")
                    
            if results:
                final_result = "\n\n".join(results)
            else:
                final_result = f"Repository {repo_url} accessed successfully via MCP GitHub tools"
                
            ensure_serializable(final_result)
            return final_result
            
        except Exception as e:
            logger.error(f"Legacy GitHub tools call failed for {repo_url}: {e}")
            raise RuntimeError(f"GitHub tools execution failed: {e}") 