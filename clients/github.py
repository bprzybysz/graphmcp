"""
GitHub MCP Client

Specialized client for GitHub MCP server operations.
Provides comprehensive GitHub repository management through MCP tools.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import BaseMCPClient, MCPToolError
from utils import ensure_serializable

logger = logging.getLogger(__name__)

class GitHubMCPClient(BaseMCPClient):
    """
    Specialized MCP client for GitHub server operations.
    
    Provides tools for repository analysis, file management,
    pull request creation, and code search.
    """
    SERVER_NAME = "ovr_github"
    
    def __init__(self, config_path: str | Path):
        """
        Initialize GitHub MCP client.
        
        Args:
            config_path: Path to MCP configuration file
        """
        super().__init__(config_path)

    async def list_available_tools(self) -> List[str]:
        """List available GitHub MCP tools."""
        try:
            result = await self._send_mcp_request("tools/list", {})
            return [tool.get("name") for tool in result.get("tools", [])]
        except Exception as e:
            logger.warning(f"Failed to list GitHub tools: {e}")
            return [
                "search_repositories",
                "get_file_contents", 
                "create_or_update_file",
                "create_pull_request",
                "search_code",
                "list_issues",
                "create_issue",
                "fork_repository",
                "create_branch"
            ]

    async def health_check(self) -> bool:
        """
        Perform a health check by listing available GitHub tools.
        """
        try:
            await self.list_available_tools()
            logger.debug(f"GitHubMCPClient ({self.server_name}) health check successful.")
            return True
        except Exception as e:
            logger.warning(f"GitHubMCPClient ({self.server_name}) health check failed: {e}")
            return False

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information and metadata using search_repositories.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            
        Returns:
            Repository information dictionary
        """
        try:
            # Use search_repositories to find the specific repository
            search_query = f"repo:{owner}/{repo}"
            result = await self.call_tool_with_retry("search_repositories", {
                "query": search_query,
                "perPage": 1
            })
            
            # Extract repository info from search results
            items = result.get("items", [])
            if items and len(items) > 0:
                repo_data = items[0]
                repo_info = {
                    "owner": owner,
                    "repo": repo,
                    "full_name": repo_data.get("full_name", f"{owner}/{repo}"),
                    "default_branch": repo_data.get("default_branch", "main"),
                    "language": repo_data.get("language"),
                    "languages": {},  # Not available in search results
                    "description": repo_data.get("description"),
                    "topics": repo_data.get("topics", []),
                    "size": repo_data.get("size", 0),
                    "stargazers_count": repo_data.get("stargazers_count", 0),
                    "forks_count": repo_data.get("forks_count", 0)
                }
            else:
                # Fallback with basic info if search doesn't find the repo
                repo_info = {
                    "owner": owner,
                    "repo": repo,
                    "full_name": f"{owner}/{repo}",
                    "default_branch": "main",
                    "language": None,
                    "languages": {},
                    "description": None,
                    "topics": [],
                    "size": 0,
                    "stargazers_count": 0,
                    "forks_count": 0
                }
            
            ensure_serializable(repo_info)
            logger.debug(f"Retrieved repository info for {owner}/{repo}")
            return repo_info
            
        except Exception as e:
            logger.error(f"Failed to get repository {owner}/{repo}: {e}")
            return {"owner": owner, "repo": repo, "error": str(e)}

    async def analyze_repo_structure(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze the structure of a repository using multiple GitHub tools.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Repository structure analysis
        """
        try:
            # Parse repository URL
            if repo_url.startswith("https://github.com/"):
                repo_path = repo_url.replace("https://github.com/", "").rstrip("/")
                owner, repo = repo_path.split("/")
            else:
                raise ValueError(f"Invalid GitHub URL: {repo_url}")
            
            # Get repository information
            repo_info = await self.get_repository(owner, repo)
            
            # Search for common configuration files
            config_files = await self.search_code(
                query=f"repo:{owner}/{repo} filename:*.yaml OR filename:*.yml OR filename:Chart.yaml",
                per_page=100
            )
            
            structure = {
                "repository_url": repo_url,
                "owner": owner,
                "repo": repo,
                "default_branch": repo_info.get("default_branch", "main"),
                "languages": repo_info.get("languages", {}),
                "primary_language": repo_info.get("language"),
                "file_count": len(config_files.get("items", [])),
                "config_files": [
                    {
                        "path": item.get("path"),
                        "name": item.get("name"),
                        "size": item.get("size", 0)
                    }
                    for item in config_files.get("items", [])
                ],
                "topics": repo_info.get("topics", []),
                "description": repo_info.get("description")
            }
            
            ensure_serializable(structure)
            logger.info(f"Analyzed structure for {repo_url}: {structure['file_count']} config files found")
            return structure
            
        except Exception as e:
            logger.error(f"Failed to analyze repo structure for {repo_url}: {e}")
            return {"repository_url": repo_url, "error": str(e)}

    async def get_file_contents(self, owner: str, repo: str, path: str, ref: str = None) -> str:
        """
        Get the contents of a file from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name  
            path: File path in repository
            ref: Git reference (branch, tag, commit), defaults to default branch
            
        Returns:
            File content as string
        """
        params = {
            "owner": owner,
            "repo": repo,
            "path": path
        }
        
        if ref:
            params["ref"] = ref
        
        try:
            result = await self.call_tool_with_retry("get_file_contents", params)
            
            # Handle different response formats
            if isinstance(result, str):
                content = result
            elif isinstance(result, dict):
                content = result.get("content", "")
                # Handle base64 encoded content
                if result.get("encoding") == "base64":
                    import base64
                    content = base64.b64decode(content).decode("utf-8")
            else:
                content = str(result)
            
            logger.debug(f"Retrieved file contents for {owner}/{repo}/{path}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to get file contents {owner}/{repo}/{path}: {e}")
            raise MCPToolError(f"Failed to get file contents: {e}")

    async def create_or_update_file(self, owner: str, repo: str, path: str, 
                                  content: str, message: str, branch: str = None,
                                  sha: str = None) -> Dict[str, Any]:
        """
        Create or update a file in the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            content: New file content
            message: Commit message
            branch: Target branch (optional)
            sha: Current file SHA for updates (optional)
            
        Returns:
            Result of file operation
        """
        params = {
            "owner": owner,
            "repo": repo,
            "path": path,
            "content": content,
            "message": message
        }
        
        if branch:
            params["branch"] = branch
        if sha:
            params["sha"] = sha
        
        try:
            result = await self.call_tool_with_retry("create_or_update_file", params)
            
            update_result = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "path": path,
                "branch": branch or "main",
                "commit_sha": result.get("commit", {}).get("sha"),
                "commit_url": result.get("commit", {}).get("html_url")
            }
            
            ensure_serializable(update_result)
            logger.info(f"Updated file {path} in {owner}/{repo}")
            return update_result
            
        except Exception as e:
            logger.error(f"Failed to update file {owner}/{repo}/{path}: {e}")
            return {
                "success": False,
                "owner": owner,
                "repo": repo,
                "path": path,
                "error": str(e)
            }

    async def create_pull_request(self, owner: str, repo: str, title: str, 
                                head: str, base: str, body: str = "",
                                draft: bool = False) -> Dict[str, Any]:
        """
        Create a pull request in the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Pull request title
            head: Branch containing changes
            base: Target branch for merge
            body: Pull request description
            draft: Whether to create as draft PR
            
        Returns:
            Pull request creation result
        """
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        
        if draft:
            params["draft"] = draft
        
        try:
            result = await self.call_tool_with_retry("create_pull_request", params)
            
            pr_result = {
                "success": True,
                "owner": owner,
                "repo": repo,
                "number": result.get("number"),
                "url": result.get("html_url"),
                "title": title,
                "head": head,
                "base": base,
                "state": result.get("state", "open"),
                "draft": result.get("draft", False)
            }
            
            ensure_serializable(pr_result)
            logger.info(f"Created PR #{pr_result['number']} in {owner}/{repo}: {title}")
            return pr_result
            
        except Exception as e:
            logger.error(f"Failed to create PR in {owner}/{repo}: {e}")
            return {
                "success": False,
                "owner": owner,
                "repo": repo,
                "title": title,
                "error": str(e)
            }

    async def search_code(self, query: str, sort: str = "indexed", 
                         order: str = "desc", per_page: int = 30,
                         page: int = 1) -> Dict[str, Any]:
        """
        Search for code across repositories.
        
        Args:
            query: Search query string
            sort: Sort field (indexed, created, updated)
            order: Sort order (asc, desc)
            per_page: Results per page (max 100)
            page: Page number
            
        Returns:
            Search results dictionary
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),
            "page": page
        }
        
        try:
            result = await self.call_tool_with_retry("search_code", params)
            
            search_result = {
                "total_count": result.get("total_count", 0),
                "incomplete_results": result.get("incomplete_results", False),
                "items": result.get("items", []),
                "query": query
            }
            
            ensure_serializable(search_result)
            logger.debug(f"Code search completed: {search_result['total_count']} results for '{query}'")
            return search_result
            
        except Exception as e:
            logger.error(f"Failed to search code: {e}")
            return {"total_count": 0, "items": [], "query": query, "error": str(e)}

    async def list_issues(self, owner: str, repo: str, state: str = "open",
                         labels: List[str] = None, sort: str = "created",
                         direction: str = "desc", per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List issues in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            labels: Filter by labels
            sort: Sort field (created, updated, comments)
            direction: Sort direction (asc, desc)
            per_page: Results per page
            
        Returns:
            List of issue dictionaries
        """
        params = {
            "owner": owner,
            "repo": repo,
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": per_page
        }
        
        if labels:
            params["labels"] = ",".join(labels)
        
        try:
            result = await self.call_tool_with_retry("list_issues", params)
            
            issues = [
                {
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "state": issue.get("state"),
                    "labels": [label.get("name") for label in issue.get("labels", [])],
                    "created_at": issue.get("created_at"),
                    "updated_at": issue.get("updated_at"),
                    "html_url": issue.get("html_url")
                }
                for issue in (result if isinstance(result, list) else result.get("issues", []))
            ]
            
            ensure_serializable(issues)
            logger.debug(f"Listed {len(issues)} issues for {owner}/{repo}")
            return issues
            
        except Exception as e:
            logger.error(f"Failed to list issues for {owner}/{repo}: {e}")
            return []

    async def create_issue(self, owner: str, repo: str, title: str, 
                          body: str = "", labels: List[str] = None,
                          assignees: List[str] = None) -> Dict[str, Any]:
        """
        Create a new issue in the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: Issue labels
            assignees: Issue assignees
            
        Returns:
            Created issue information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body
        }
        
        if labels:
            params["labels"] = labels
        if assignees:
            params["assignees"] = assignees
        
        try:
            result = await self.call_tool_with_retry("create_issue", params)
            
            issue_result = {
                "success": True,
                "number": result.get("number"),
                "title": title,
                "html_url": result.get("html_url"),
                "state": result.get("state", "open"),
                "created_at": result.get("created_at")
            }
            
            ensure_serializable(issue_result)
            logger.info(f"Created issue #{issue_result['number']} in {owner}/{repo}: {title}")
            return issue_result
            
        except Exception as e:
            logger.error(f"Failed to create issue in {owner}/{repo}: {e}")
            return {"success": False, "title": title, "error": str(e)}

    def _extract_json_from_mcp_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract JSON data from MCP response content field.
        
        Args:
            result: MCP response with content field
            
        Returns:
            Parsed JSON data or empty dict if parsing fails
        """
        try:
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                first_content = result["content"][0]
                if isinstance(first_content, dict) and "text" in first_content:
                    import json
                    return json.loads(first_content["text"])
            return {}
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Failed to parse MCP response content: {e}")
            return {}

    async def fork_repository(self, owner: str, repo: str, organization: str = None) -> Dict[str, Any]:
        """
        Fork a repository to the authenticated user's account or specified organization.
        
        Args:
            owner: Repository owner
            repo: Repository name
            organization: Optional organization to fork to (defaults to user account)
            
        Returns:
            Fork information dictionary
        """
        params = {
            "owner": owner,
            "repo": repo
        }
        
        if organization:
            params["organization"] = organization
        
        try:
            result = await self.call_tool_with_retry("fork_repository", params)
            
            # Extract JSON data from MCP response content
            fork_data = self._extract_json_from_mcp_response(result)
            
            fork_result = {
                "success": True,
                "name": fork_data.get("name"),
                "full_name": fork_data.get("full_name"),
                "owner": fork_data.get("owner", {}),
                "html_url": fork_data.get("html_url"),
                "clone_url": fork_data.get("clone_url"),
                "default_branch": fork_data.get("default_branch", "main"),
                "fork": fork_data.get("fork", True),
                "created_at": fork_data.get("created_at")
            }
            
            ensure_serializable(fork_result)
            logger.info(f"Forked repository {owner}/{repo} to {fork_result.get('full_name')}")
            return fork_result
            
        except Exception as e:
            logger.error(f"Failed to fork repository {owner}/{repo}: {e}")
            return {
                "success": False,
                "owner": owner,
                "repo": repo,
                "error": str(e)
            }

    async def create_branch(self, owner: str, repo: str, branch: str, 
                           from_branch: str = None) -> Dict[str, Any]:
        """
        Create a new branch in the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Name for the new branch
            from_branch: Source branch to create from (defaults to default branch)
            
        Returns:
            Branch creation result
        """
        params = {
            "owner": owner,
            "repo": repo,
            "branch": branch
        }
        
        if from_branch:
            params["from_branch"] = from_branch
        
        try:
            result = await self.call_tool_with_retry("create_branch", params)
            
            # Extract JSON data from MCP response content
            branch_data = self._extract_json_from_mcp_response(result)
            
            branch_result = {
                "success": True,
                "ref": branch_data.get("ref"),
                "node_id": branch_data.get("node_id"),
                "url": branch_data.get("url"),
                "object": branch_data.get("object", {}),
                "owner": owner,
                "repo": repo,
                "branch": branch
            }
            
            ensure_serializable(branch_result)
            logger.info(f"Created branch '{branch}' in {owner}/{repo}")
            return branch_result
            
        except Exception as e:
            logger.error(f"Failed to create branch '{branch}' in {owner}/{repo}: {e}")
            return {
                "success": False,
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "error": str(e)
            } 