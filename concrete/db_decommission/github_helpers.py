"""
GitHub Helper Functions for Database Decommissioning.

This module contains GitHub-specific helper functions extracted from workflow_steps.py
to maintain the 500-line limit per module.
"""

import time
from typing import Any, Dict, List, Optional


async def _create_pr_body(
    database_name: str,
    modified_files: List[Dict[str, Any]],
    refactoring_result: Dict[str, Any],
    files_committed: int
) -> str:
    """
    Create comprehensive pull request body.
    
    Args:
        database_name: Name of the database being decommissioned
        modified_files: List of modified file results
        refactoring_result: Refactoring results from previous step
        files_committed: Number of files successfully committed
        
    Returns:
        Formatted PR body string
    """
    pr_body = f"""# Database Decommissioning: {database_name}

This pull request removes all references to the `{database_name}` database as part of the database decommissioning process.

## Summary
- **Database**: `{database_name}`
- **Files modified**: {files_committed}
- **Total changes**: {sum(f.get('changes_made', 0) for f in modified_files)}

## Changes by File Type
"""
    
    # Add summary by file type
    files_by_type = refactoring_result.get("files_by_type", {})
    for source_type, file_paths in files_by_type.items():
        modified_count = len([f for f in modified_files if f.get("source_type") == source_type])
        if modified_count > 0:
            pr_body += f"- **{source_type.upper()}**: {modified_count} files modified\n"
    
    pr_body += f"""
## Modified Files
"""
    for file_result in modified_files:
        pr_body += f"- `{file_result['path']}` ({file_result['changes_made']} changes)\n"
    
    pr_body += f"""
---
*This PR was generated automatically by the GraphMCP Database Decommissioning Workflow*
"""
    
    return pr_body


async def create_fork_and_branch(
    github_client: Any,
    repo_owner: str,
    repo_name: str,
    database_name: str,
    logger: Any
) -> Dict[str, Any]:
    """
    Create fork and branch for database decommissioning changes.
    
    Args:
        github_client: GitHub MCP client instance
        repo_owner: Repository owner name
        repo_name: Repository name
        database_name: Database name for branch naming
        logger: Structured logger instance
        
    Returns:
        Dict containing fork and branch information
    """
    logger.log_info(f"🍴 Creating fork of {repo_owner}/{repo_name}")
    
    # 1. Fork the repository
    fork_result = await github_client.fork_repository(repo_owner, repo_name)
    if not fork_result.get("success", False):
        raise RuntimeError(f"Failed to fork repository: {fork_result.get('error', 'Unknown error')}")
    
    fork_owner = fork_result["owner"]["login"]
    logger.log_info(f"✅ Forked to {fork_owner}/{repo_name}")
    
    # 2. Create feature branch
    branch_name = f"decommission-{database_name}-{int(time.time())}"
    logger.log_info(f"🌿 Creating branch: {branch_name}")
    
    # Wait for fork to be ready
    import asyncio
    await asyncio.sleep(3)
    
    branch_result = await github_client.create_branch(fork_owner, repo_name, branch_name)
    if not branch_result.get("success", False):
        raise RuntimeError(f"Failed to create branch: {branch_result.get('error', 'Unknown error')}")
    
    logger.log_info(f"✅ Created branch: {branch_name}")
    
    return {
        "fork_owner": fork_owner,
        "branch_name": branch_name,
        "fork_result": fork_result,
        "branch_result": branch_result
    }


async def commit_file_changes(
    github_client: Any,
    fork_owner: str,
    repo_name: str,
    branch_name: str,
    modified_files: List[Dict[str, Any]],
    database_name: str,
    logger: Any
) -> Dict[str, Any]:
    """
    Commit modified files to the feature branch.
    
    Args:
        github_client: GitHub MCP client instance
        fork_owner: Fork owner name
        repo_name: Repository name
        branch_name: Feature branch name
        modified_files: List of modified file results
        database_name: Database name for commit messages
        logger: Structured logger instance
        
    Returns:
        Dict containing commit results
    """
    files_committed = 0
    commit_messages = []
    
    for file_result in modified_files:
        file_path = file_result["path"]
        modified_content = file_result["modified_content"]
        changes_count = file_result["changes_made"]
        source_type = file_result.get("source_type", "unknown")
        
        commit_message = f"refactor({source_type}): remove {database_name} references from {file_path} ({changes_count} changes)"
        
        # Commit the file changes
        update_result = await github_client.create_or_update_file(
            fork_owner, repo_name, file_path, modified_content,
            commit_message, branch=branch_name
        )
        
        if update_result.get("success", False):
            files_committed += 1
            commit_messages.append(commit_message)
            logger.log_info(f"   ✅ Committed: {file_path}")
        else:
            logger.log_warning(f"Failed to commit: {file_path} - {update_result.get('error', 'Unknown error')}")
    
    return {
        "files_committed": files_committed,
        "commit_messages": commit_messages
    }


async def create_pull_request(
    github_client: Any,
    repo_owner: str,
    repo_name: str,
    fork_owner: str,
    branch_name: str,
    database_name: str,
    modified_files: List[Dict[str, Any]],
    refactoring_result: Dict[str, Any],
    files_committed: int,
    logger: Any
) -> Dict[str, Any]:
    """
    Create pull request for database decommissioning changes.
    
    Args:
        github_client: GitHub MCP client instance
        repo_owner: Repository owner name
        repo_name: Repository name
        fork_owner: Fork owner name
        branch_name: Feature branch name
        database_name: Database name for PR title
        modified_files: List of modified file results
        refactoring_result: Refactoring results from previous step
        files_committed: Number of files successfully committed
        logger: Structured logger instance
        
    Returns:
        Dict containing PR creation results
    """
    pr_title = f"Database Decommission: Remove {database_name} references"
    pr_body = await _create_pr_body(database_name, modified_files, refactoring_result, files_committed)
    
    logger.log_info(f"📝 Creating pull request: {pr_title}")
    
    pr_result = await github_client.create_pull_request(
        repo_owner, repo_name, pr_title,
        f"{fork_owner}:{branch_name}", "main", pr_body
    )
    
    if not pr_result.get("success", False):
        raise RuntimeError(f"Failed to create pull request: {pr_result.get('error', 'Unknown error')}")
    
    pr_number = pr_result.get("number", "Unknown")
    pr_url = pr_result.get("url") or pr_result.get("html_url") or f"https://github.com/{repo_owner}/{repo_name}/pulls"
    
    logger.log_info(f"✅ Created PR #{pr_number}: {pr_url}")
    
    return {
        "pr_number": pr_number,
        "pr_url": pr_url,
        "pr_title": pr_title,
        "pr_result": pr_result
    }