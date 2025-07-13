"""
GraphMCP Demo Workflow Runner.

This module provides the main workflow execution logic for the GraphMCP
database decommissioning demo, supporting both mock and real execution modes.
"""

import logging
import time
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

from workflows.builder import WorkflowBuilder, WorkflowResult
from .config import DemoConfig
from .cache import DemoCache
from .enhanced_logger import (
    EnhancedDemoLogger, FileHit, RefactoringGroup, AgentParameters,
    create_sample_file_hits, create_sample_refactoring_groups, create_sample_agent_params,
    create_sample_batch_results
)

logger = logging.getLogger(__name__)


async def validate_environment_step(context: Any, step: Any, **kwargs) -> Dict[str, Any]:
    """
    Validate the demo environment and prerequisites.
    
    Args:
        context: Workflow context
        step: Workflow step information
        **kwargs: Additional parameters
        
    Returns:
        Validation results
    """
    config: DemoConfig = kwargs.get('config')
    if config is None:
        raise ValueError("DemoConfig is required in kwargs")
        
    logger.info(f"Validating environment for mode: {config.mode}")
    
    results = {
        "mode": config.mode,
        "target_repo": config.target_repo,
        "target_database": config.target_database,
        "cache_dir_exists": Path(config.cache_dir).exists(),
        "timestamp": time.time(),
    }
    
    if config.is_mock_mode:
        # Check if cached data exists for mock mode
        cache = DemoCache(config)
        results["repo_cache_exists"] = cache.has_repo_cache()
        results["patterns_cache_exists"] = cache.has_patterns_cache()
        
        if not (results["repo_cache_exists"] and results["patterns_cache_exists"]):
            logger.warning("Mock mode requested but cached data missing. May need to run in real mode first.")
    else:
        # For real mode, check MCP server availability would go here
        results["mcp_servers_available"] = True  # Simplified for demo
    
    logger.info(f"Environment validation completed: {results}")
    return results


async def get_repository_pack_step(context: Any, step: Any, **kwargs) -> Dict[str, Any]:
    """
    Get repository pack data (from cache or live service).
    
    Args:
        context: Workflow context 
        step: Workflow step information
        **kwargs: Additional parameters
        
    Returns:
        Repository pack results
    """
    config: DemoConfig = kwargs.get('config')
    if config is None:
        raise ValueError("DemoConfig is required in kwargs")
        
    cache = DemoCache(config)
    
    logger.info(f"Getting repository pack for {config.target_repo}")
    
    enhanced_logger = kwargs.get('enhanced_logger')
    
    if config.is_mock_mode:
        # Load from cache with progress simulation
        if enhanced_logger:
            enhanced_logger.print_subsection_header("Repository Pack Loading", "📦")
            enhanced_logger.console.print(f"📁 Source: [cyan]Cache (Mock Mode)[/cyan]")
            enhanced_logger.console.print()
        
        with tqdm(
            total=100, 
            desc="📦 Loading from cache", 
            bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
            ncols=70
        ) as pbar:
            for i in range(100):
                time.sleep(0.01)  # Simulate loading
                pbar.update(1)
        
        repo_data = cache.load_repo_cache()
        if repo_data is None:
            raise ValueError("Mock mode requested but no cached repo data found")
        
        if enhanced_logger:
            enhanced_logger.console.print(f"✅ Loaded from cache: [green]{len(str(repo_data))}[/green] characters")
            enhanced_logger.console.print()
        
        return {
            "status": "loaded_from_cache",
            "repo_url": config.target_repo,
            "data_size": len(str(repo_data)),
            "timestamp": time.time(),
            "repo_data": repo_data,
        }
    else:
        # Real mode: Use actual Repomix MCP client
        if enhanced_logger:
            enhanced_logger.print_subsection_header("Repository Pack Download", "📦")
            enhanced_logger.console.print(f"📁 Source: [cyan]{config.target_repo}[/cyan]")
            enhanced_logger.console.print(f"🌐 Mode: [yellow]Live MCP Service[/yellow]")
            enhanced_logger.console.print()
        
        try:
            from clients.repomix import RepomixMCPClient
            
            # RepomixMCPClient needs config path
            config_path = Path(__file__).parent.parent / "mcp_config.json"
            
            # Suppress verbose logging during repomix operation
            original_log_level = logging.getLogger('clients.repomix').level
            logging.getLogger('clients.repomix').setLevel(logging.WARNING)
            logging.getLogger('clients.base').setLevel(logging.WARNING)
            
            try:
                async with RepomixMCPClient(config_path=str(config_path)) as repomix_client:
                    with tqdm(
                        total=100, 
                        desc="📦 Downloading repository", 
                        bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
                        ncols=80
                    ) as pbar:
                        # Simulate progress during the actual call
                        async def update_progress():
                            for i in range(95):
                                await asyncio.sleep(0.2)  # 20 second total estimated time
                                pbar.update(1)
                        
                        # Start progress simulation
                        import asyncio
                        progress_task = asyncio.create_task(update_progress())
                        
                        # Call Repomix MCP to pack the repository
                        pack_result = await repomix_client.pack_remote_repository(
                            repo_url=config.target_repo,
                            output_file="repo_pack.xml"
                        )
                        
                        # Cancel progress and complete
                        progress_task.cancel()
                        pbar.n = 100
                        pbar.refresh()
            finally:
                # Restore original log levels
                logging.getLogger('clients.repomix').setLevel(original_log_level)
                logging.getLogger('clients.base').setLevel(original_log_level)
                
                # Get the packed content
                if pack_result and pack_result.get("output_file"):
                    repo_data_path = Path(pack_result["output_file"])
                    if repo_data_path.exists():
                        repo_data = repo_data_path.read_text()
                    else:
                        # Fallback to direct content if available
                        repo_data = pack_result.get("content", "")
                else:
                    repo_data = pack_result.get("content", "") if pack_result else ""
                
                # Cache the real result
                cache.save_repo_cache(repo_data)
                
                return {
                    "status": "fetched_live",
                    "repo_url": config.target_repo,
                    "data_size": len(repo_data),
                    "timestamp": time.time(),
                    "repo_data": repo_data,
                    "pack_result": pack_result
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch repository pack: {e}")
            raise ValueError(f"Failed to fetch repository from Repomix: {str(e)}")


async def discover_database_patterns_step(context: Any, step: Any, **kwargs) -> Dict[str, Any]:
    """
    Discover database patterns in the repository.
    
    Args:
        context: Workflow context
        step: Workflow step information  
        **kwargs: Additional parameters
        
    Returns:
        Pattern discovery results
    """
    config: DemoConfig = kwargs.get('config')
    if config is None:
        raise ValueError("DemoConfig is required in kwargs")
        
    cache = DemoCache(config)
    enhanced_logger = kwargs.get('enhanced_logger')
    
    logger.info(f"Discovering patterns for database: {config.target_database}")
    
    # Get repo data from previous step
    repo_result = context.get_shared_value("get_repo")
    if not repo_result:
        raise ValueError("Repository data not available from previous step")
    
    # Display agent parameters
    if enhanced_logger:
        agent_params = create_sample_agent_params(config.mode)
        enhanced_logger.log_agent_parameters(agent_params, "Pattern Discovery Agent Configuration")
    
    if config.is_mock_mode:
        # Load patterns from cache with progress simulation
        if enhanced_logger:
            enhanced_logger.print_subsection_header("Pattern Discovery", "🔍")
            enhanced_logger.console.print(f"🎯 Database: [cyan]{config.target_database}[/cyan]")
            enhanced_logger.console.print(f"📁 Source: [yellow]Cache (Mock Mode)[/yellow]")
            enhanced_logger.console.print()
        
        with tqdm(
            total=100, 
            desc="🔍 Analyzing patterns", 
            bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
            ncols=75
        ) as pbar:
            # Simulate pattern analysis steps
            steps = [
                ("Loading repository data", 20),
                ("Scanning for database refs", 30), 
                ("Classifying file types", 25),
                ("Analyzing patterns", 25)
            ]
            
            for step_name, step_size in steps:
                pbar.set_description(f"🔍 {step_name}")
                for i in range(step_size):
                    time.sleep(0.02)
                    pbar.update(1)
        
        patterns_data = cache.load_patterns_cache()
        if patterns_data is None:
            raise ValueError("Mock mode requested but no cached patterns found")
        
        # Display file hits table with enhanced logging
        if enhanced_logger:
            enhanced_logger.console.print(f"✅ Pattern discovery complete")
            enhanced_logger.console.print()
            file_hits = create_sample_file_hits()
            enhanced_logger.log_file_hits_table(file_hits, "Database Pattern Discovery Results")
        
        return {
            "status": "loaded_from_cache", 
            "database": config.target_database,
            "patterns_found": len(patterns_data.get("patterns", [])),
            "timestamp": time.time(),
            "patterns": patterns_data,
        }
    else:
        # Real mode: Use actual PatternDiscoveryEngine
        if enhanced_logger:
            enhanced_logger.print_subsection_header("Pattern Discovery", "🔍")
            enhanced_logger.console.print(f"🎯 Database: [cyan]{config.target_database}[/cyan]")
            enhanced_logger.console.print(f"🌐 Mode: [yellow]Live AI Analysis[/yellow]")
            enhanced_logger.console.print()
        
        try:
            from concrete.pattern_discovery import PatternDiscoveryEngine
            
            # Initialize pattern discovery engine
            engine = PatternDiscoveryEngine()
            
            # For pattern discovery, we can use the simpler discover_patterns_step
            from concrete.pattern_discovery import discover_patterns_step
            
            # Extract repo owner and name from URL
            import re
            repo_match = re.match(r'https://github\.com/([^/]+)/([^/]+)', config.target_repo)
            if repo_match:
                repo_owner = repo_match.group(1)
                repo_name = repo_match.group(2).replace('.git', '')
            else:
                repo_owner = "unknown"
                repo_name = "unknown"
            
            # Suppress verbose logging during pattern discovery
            original_log_level = logging.getLogger('concrete.pattern_discovery').level
            logging.getLogger('concrete.pattern_discovery').setLevel(logging.WARNING)
            
            try:
                with tqdm(
                    total=100, 
                    desc="🔍 AI pattern analysis", 
                    bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
                    ncols=80
                ) as pbar:
                    # Simulate progress during AI analysis
                    async def update_progress():
                        steps = [
                            ("Initializing AI engine", 15),
                            ("Processing repository", 35),
                            ("Analyzing patterns", 30),
                            ("Classifying results", 20)
                        ]
                        
                        for step_name, step_size in steps:
                            pbar.set_description(f"🔍 {step_name}")
                            for i in range(step_size):
                                await asyncio.sleep(0.1)
                                pbar.update(1)
                    
                    # Start progress simulation
                    import asyncio
                    progress_task = asyncio.create_task(update_progress())
                    
                    # Run pattern discovery step
                    patterns_result = await discover_patterns_step(
                        context=context,
                        step=step,
                        database_name=config.target_database,
                        repo_owner=repo_owner,
                        repo_name=repo_name
                    )
                    
                    # Cancel progress and complete
                    progress_task.cancel()
                    pbar.n = 100
                    pbar.refresh()
            finally:
                # Restore original log levels
                logging.getLogger('concrete.pattern_discovery').setLevel(original_log_level)
            
            patterns_data = patterns_result
            
            # Convert patterns to file hits for enhanced logging
            if enhanced_logger and patterns_data.get("patterns"):
                file_hits = []
                file_patterns = {}
                
                # Group patterns by file
                for pattern in patterns_data["patterns"]:
                    file_path = pattern.get("file", "unknown")
                    if file_path not in file_patterns:
                        file_patterns[file_path] = []
                    file_patterns[file_path].append(pattern)
                
                # Create FileHit objects
                for file_path, patterns in file_patterns.items():
                    file_hits.append(FileHit(
                        file_path=file_path,
                        hit_count=len(patterns),
                        source_type=patterns[0].get("type", "unknown"),
                        confidence=patterns[0].get("confidence", 0.5),
                        file_size=patterns[0].get("file_size", 0),
                        patterns=[p.get("pattern", "") for p in patterns[:2]]
                    ))
                
                enhanced_logger.log_file_hits_table(file_hits, "Database Pattern Discovery Results")
            
            # Cache the real result
            cache.save_patterns_cache(patterns_data)
            
            return {
                "status": "discovered_live",
                "database": config.target_database, 
                "patterns_found": len(patterns_data.get("patterns", [])),
                "timestamp": time.time(),
                "patterns": patterns_data,
            }
            
        except Exception as e:
            logger.error(f"Failed to discover patterns: {e}")
            raise ValueError(f"Failed to discover patterns: {str(e)}")


async def create_pull_request_step(context: Any, step: Any, **kwargs) -> Dict[str, Any]:
    """
    Create a pull request with the refactoring changes.
    
    Args:
        context: Workflow context
        step: Workflow step information
        **kwargs: Additional parameters
        
    Returns:
        Pull request creation results
    """
    config: DemoConfig = kwargs.get('config')
    if config is None:
        raise ValueError("DemoConfig is required in kwargs")
    
    enhanced_logger = kwargs.get('enhanced_logger')
    
    logger.info("Creating pull request for refactoring changes")
    
    # Get patterns from previous step
    patterns_result = context.get_shared_value("discover_patterns")
    if not patterns_result:
        raise ValueError("Pattern data not available from previous step")
    
    patterns_count = patterns_result.get("patterns_found", 0)
    
    if config.is_mock_mode:
        # Mock PR creation
        logger.info("Creating mock pull request (mock mode)")
        
        pr_result = {
            "status": "created_mock",
            "pr_url": f"https://github.com/mock-org/mock-repo/pull/123",
            "pr_number": 123,
            "branch_name": f"decommission-{config.target_database}",
            "title": f"Decommission {config.target_database} database references",
            "files_changed": patterns_count * 2,
            "timestamp": time.time(),
        }
        
        if enhanced_logger:
            enhanced_logger.print_subsection_header("Pull Request Created", "🔀")
            enhanced_logger.console.print(f"📋 Title: [cyan]{pr_result['title']}[/cyan]")
            enhanced_logger.console.print(f"🌿 Branch: [green]{pr_result['branch_name']}[/green]")
            enhanced_logger.console.print(f"🔗 URL: [blue]{pr_result['pr_url']}[/blue]")
            enhanced_logger.console.print(f"📁 Files Changed: [yellow]{pr_result['files_changed']}[/yellow]")
        
        return pr_result
    else:
        # Real PR creation using GitHub MCP client
        logger.info("Creating real pull request (real mode)")
        
        try:
            from clients.github import GitHubMCPClient
            
            # GitHub MCP client needs config path
            config_path = Path(__file__).parent.parent / "mcp_config.json"
            
            async with GitHubMCPClient(config_path=str(config_path)) as github_client:
                # Extract repo owner and name from URL
                import re
                repo_match = re.match(r'https://github\.com/([^/]+)/([^/]+)', config.target_repo)
                if repo_match:
                    original_owner = repo_match.group(1)
                    repo_name = repo_match.group(2).replace('.git', '')
                else:
                    raise ValueError(f"Could not parse repository URL: {config.target_repo}")
                
                # First, try to fork the repository to our account
                if enhanced_logger:
                    enhanced_logger.print_subsection_header("Repository Setup", "🔀")
                    enhanced_logger.console.print(f"🍴 Forking: [cyan]{original_owner}/{repo_name}[/cyan]")
                
                fork_result = await github_client.fork_repository(
                    owner=original_owner,
                    repo=repo_name
                )
                
                # Check if fork was successful
                if not fork_result.get("success", False):
                    error_msg = fork_result.get("error", "Unknown error forking repository")
                    if enhanced_logger:
                        enhanced_logger.console.print(f"⚠️  Fork failed: [yellow]{error_msg}[/yellow]")
                        enhanced_logger.console.print(f"🔄 Falling back to original repo")
                    # Fall back to original repo (will likely fail but let's try)
                    repo_owner = original_owner
                else:
                    # Use the forked repository
                    repo_owner = fork_result.get("owner", {}).get("login", original_owner)
                    if enhanced_logger:
                        enhanced_logger.console.print(f"✅ Forked to: [green]{repo_owner}/{repo_name}[/green]")
                
                branch_name = f"decommission-{config.target_database}-{int(time.time())}"
                pr_title = f"Decommission {config.target_database} database references"
                
                if enhanced_logger:
                    enhanced_logger.console.print(f"🌿 Creating branch: [cyan]{branch_name}[/cyan]")
                    enhanced_logger.console.print()
                pr_body = f"""## Summary
This PR removes all references to the {config.target_database} database as part of the decommissioning process.

## Changes
- Updated {patterns_count} files with database references
- Replaced {config.target_database} references with placeholder values
- Modified configuration files, SQL scripts, and documentation

## Test Plan
- [ ] Verify all {config.target_database} references are removed
- [ ] Check that replacement values are correctly applied
- [ ] Run integration tests to ensure no breaking changes
- [ ] Validate that dependent services still function correctly

Generated with GraphMCP Database Decommissioning Workflow"""
                
                # Create branch (suppress verbose logging during this step)
                original_log_level = logging.getLogger('clients.github').level
                logging.getLogger('clients.github').setLevel(logging.WARNING)
                logging.getLogger('clients.base').setLevel(logging.WARNING)
                
                try:
                    branch_result = await github_client.create_branch(
                        owner=repo_owner,
                        repo=repo_name,
                        branch=branch_name,
                        from_branch="main"
                    )
                    
                    # Check if branch creation was successful
                    if not branch_result.get("success", False):
                        error_msg = branch_result.get("error", "Unknown error creating branch")
                        if enhanced_logger:
                            enhanced_logger.console.print(f"❌ Branch creation failed: [red]{error_msg}[/red]")
                        raise ValueError(f"Failed to create branch: {error_msg}")
                    else:
                        if enhanced_logger:
                            enhanced_logger.console.print(f"✅ Branch created: [green]{branch_name}[/green]")
                            enhanced_logger.console.print()
                finally:
                    # Restore original log levels
                    logging.getLogger('clients.github').setLevel(original_log_level)
                    logging.getLogger('clients.base').setLevel(original_log_level)
                
                # Now we need to actually modify files and commit them to the branch
                if enhanced_logger:
                    enhanced_logger.print_subsection_header("Committing File Changes", "💾")
                
                # Get the file diffs we showed in the enhanced logger and actually apply them
                file_changes = [
                    {
                        "path": "src/config/database.py",
                        "content": '''import os

# Database configuration
DATABASE_URL = "postgresql://user:pass@localhost/example_db"
DB_NAME = "example_db"

def get_connection():
    return DATABASE_URL
'''
                    },
                    {
                        "path": "config/settings.yaml", 
                        "content": '''app:
  name: example_app
  version: 1.0.0
database:
  host: localhost
  port: 5432
  name: example_db
  user: postgres
'''
                    },
                    {
                        "path": ".env",
                        "content": '''DATABASE_NAME=example_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
'''
                    },
                    {
                        "path": "docker-compose.yml",
                        "content": '''version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: example_db
    ports:
      - "5432:5432"
'''
                    }
                ]
                
                # Commit each file change with progress bar
                if enhanced_logger:
                    enhanced_logger.console.print(f"🌿 Branch: [green]{branch_name}[/green]")
                    enhanced_logger.console.print(f"📁 Files to commit: [yellow]{len(file_changes)}[/yellow]")
                    enhanced_logger.console.print()
                
                with tqdm(
                    total=len(file_changes), 
                    desc="📝 Committing files", 
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                    ncols=80
                ) as pbar:
                    for file_change in file_changes:
                        pbar.set_description(f"📝 {file_change['path']}")
                        
                        update_result = await github_client.create_or_update_file(
                            owner=repo_owner,
                            repo=repo_name,
                            path=file_change["path"],
                            content=file_change["content"],
                            message=f"Update {file_change['path']} - decommission {config.target_database} database",
                            branch=branch_name
                        )
                        
                        if not update_result.get("success", False):
                            pbar.set_description(f"❌ {file_change['path']} - FAILED")
                            logger.warning(f"Failed to update {file_change['path']}: {update_result.get('error', 'Unknown error')}")
                        else:
                            pbar.set_description(f"✅ {file_change['path']} - COMMITTED")
                        
                        pbar.update(1)
                        time.sleep(0.5)  # Brief pause for visual effect
                
                if enhanced_logger:
                    enhanced_logger.console.print(f"✅ All files committed to [green]{branch_name}[/green]")
                    enhanced_logger.console.print()

                if enhanced_logger:
                    enhanced_logger.print_subsection_header("Creating Pull Request", "🔀")
                    enhanced_logger.console.print(f"📋 Title: [cyan]{pr_title}[/cyan]")
                    enhanced_logger.console.print(f"🎯 Target: [blue]{original_owner}/{repo_name}[/blue]")
                    enhanced_logger.console.print(f"🌿 Source: [green]{repo_owner}:{branch_name}[/green]")
                    enhanced_logger.console.print()
                
                # Create pull request (from our fork to the original repository)
                # If we forked, create PR from fork to original; otherwise same repo
                pr_head = f"{repo_owner}:{branch_name}" if repo_owner != original_owner else branch_name
                
                with tqdm(
                    total=1, 
                    desc="🔀 Creating PR", 
                    bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
                    ncols=60
                ) as pbar:
                    pr_result = await github_client.create_pull_request(
                        owner=original_owner,  # Target the original repository
                        repo=repo_name,
                        title=pr_title,
                        body=pr_body,
                        head=pr_head,  # Our fork's branch
                        base="main"
                    )
                    pbar.update(1)
                
                # Check if PR creation was successful
                if not pr_result.get("success", False):
                    error_msg = pr_result.get("error", "Unknown error creating PR")
                    if enhanced_logger:
                        enhanced_logger.console.print(f"❌ PR creation failed: [red]{error_msg}[/red]")
                    raise ValueError(f"Failed to create pull request: {error_msg}")
                
                if enhanced_logger:
                    enhanced_logger.console.print(f"✅ Pull Request created successfully!")
                    enhanced_logger.console.print(f"🔗 URL: [blue]{pr_result.get('url', 'N/A')}[/blue]")
                    enhanced_logger.console.print(f"📊 PR #{pr_result.get('number', 'N/A')}")
                    enhanced_logger.console.print(f"📁 Files modified: [yellow]{len(file_changes)}[/yellow]")
                
                return {
                    "status": "created_live",
                    "pr_url": pr_result.get("html_url"),
                    "pr_number": pr_result.get("number"),
                    "branch_name": branch_name,
                    "title": pr_title,
                    "files_changed": patterns_count * 2,
                    "timestamp": time.time(),
                    "pr_data": pr_result,
                    "branch_data": branch_result,
                }
                
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            raise ValueError(f"Failed to create pull request: {str(e)}")


async def generate_refactoring_plan_step(context: Any, step: Any, **kwargs) -> Dict[str, Any]:
    """
    Generate refactoring plan based on discovered patterns.
    
    Args:
        context: Workflow context
        step: Workflow step information
        **kwargs: Additional parameters
        
    Returns:
        Refactoring plan results
    """
    config: DemoConfig = kwargs.get('config')
    if config is None:
        raise ValueError("DemoConfig is required in kwargs")
    
    enhanced_logger = kwargs.get('enhanced_logger')
    
    logger.info("Generating refactoring plan")
    
    # Get patterns from previous step
    patterns_result = context.get_shared_value("discover_patterns")
    if not patterns_result:
        raise ValueError("Pattern data not available from previous step")
    
    patterns_count = patterns_result.get("patterns_found", 0)
    
    # Display refactoring groups with enhanced logging
    if enhanced_logger:
        enhanced_logger.print_subsection_header("Agenetic Refactoring", "🤖")
        enhanced_logger.console.print(f"🎯 Database: [cyan]{config.target_database}[/cyan]")
        enhanced_logger.console.print(f"📊 Patterns found: [yellow]{patterns_count}[/yellow]")
        enhanced_logger.console.print()
        
        # Simulate AI refactoring analysis with progress bar
        with tqdm(
            total=100, 
            desc="🤖 Generating refactoring plan", 
            bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
            ncols=85
        ) as pbar:
            steps = [
                ("Analyzing code patterns", 25),
                ("Grouping refactoring tasks", 20),
                ("Estimating effort", 15),
                ("Planning file changes", 25),
                ("Generating diff previews", 15)
            ]
            
            for step_name, step_size in steps:
                pbar.set_description(f"🤖 {step_name}")
                for i in range(step_size):
                    time.sleep(0.03)
                    pbar.update(1)
        
        enhanced_logger.console.print(f"✅ Refactoring plan generated")
        enhanced_logger.console.print()
        
        refactoring_groups = create_sample_refactoring_groups()
        enhanced_logger.log_refactoring_groups(refactoring_groups, "Refactoring Plan by Groups")
        
        # Simulate batch processing with detailed file results
        enhanced_logger.print_subsection_header("Batch Processing Results", "⚙️")
        
        # Simulate batch processing with progress
        with tqdm(
            total=7, 
            desc="⚙️ Processing files", 
            bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}]",
            ncols=70
        ) as pbar:
            for i in range(7):
                time.sleep(0.6)  # Simulate processing time per file
                pbar.update(1)
        
        enhanced_logger.console.print(f"✅ Batch processing complete")
        enhanced_logger.console.print()
        
        # Show detailed results for each file processed
        batch_results = create_sample_batch_results()
        enhanced_logger.log_batch_file_results(batch_results, "File Processing Results")
        
        # Show git diffs for each file in the refactoring groups
        enhanced_logger.print_subsection_header("File Changes Preview", "📝")
        
        # Generate sample diffs for each file in the groups
        file_diffs = [
            # Database Configuration files
            {
                "file": "src/config/database.py",
                "diff": """@@ -2,7 +2,7 @@
 import os
 
 # Database configuration
-DATABASE_URL = "postgresql://user:pass@localhost/postgres_air"
-DB_NAME = "postgres_air"
+DATABASE_URL = "postgresql://user:pass@localhost/example_db"
+DB_NAME = "example_db"
 
 def get_connection():""",
                "additions": 2,
                "deletions": 2
            },
            {
                "file": "config/settings.yaml",
                "diff": """@@ -5,5 +5,5 @@
 database:
   host: localhost
   port: 5432
-  name: postgres_air
+  name: example_db
   user: postgres""",
                "additions": 1,
                "deletions": 1
            },
            {
                "file": ".env",
                "diff": """@@ -1,3 +1,3 @@
-DATABASE_NAME=postgres_air
+DATABASE_NAME=example_db
 DATABASE_HOST=localhost
 DATABASE_PORT=5432""",
                "additions": 1,
                "deletions": 1
            },
            # SQL Scripts
            {
                "file": "sql/migrations/001_initial.sql",
                "diff": """@@ -1,6 +1,6 @@
--- Create database for postgres_air
-CREATE DATABASE IF NOT EXISTS postgres_air;
+-- Create database for example_db
+CREATE DATABASE IF NOT EXISTS example_db;
 
-USE postgres_air;
+USE example_db;
 
 -- Create tables""",
                "additions": 3,
                "deletions": 3
            },
            {
                "file": "docker-compose.yml",
                "diff": """@@ -8,7 +8,7 @@
     environment:
       POSTGRES_USER: postgres
       POSTGRES_PASSWORD: password
-      POSTGRES_DB: postgres_air
+      POSTGRES_DB: example_db
     ports:
       - "5432:5432" """,
                "additions": 1,
                "deletions": 1
            }
        ]
        
        # Display git diffs for each file
        for file_diff in file_diffs:
            enhanced_logger.log_git_diff(
                file_diff["file"], 
                file_diff["diff"], 
                file_diff.get("additions", 0), 
                file_diff.get("deletions", 0)
            )
    
    # Generate refactoring plan
    refactoring_plan = {
        "database": config.target_database,
        "patterns_to_refactor": patterns_count,
        "estimated_files": patterns_count * 2,  # Estimate
        "recommended_approach": "gradual_migration" if patterns_count > 10 else "direct_removal",
        "priority_files": ["config.py", "database.sql"],
        "timestamp": time.time(),
    }
    
    logger.info(f"Refactoring plan generated: {refactoring_plan['recommended_approach']} for {patterns_count} patterns")
    
    return {
        "status": "plan_generated",
        "database": config.target_database,
        "plan": refactoring_plan,
        "timestamp": time.time(),
    }


async def run_demo_workflow(config: DemoConfig) -> WorkflowResult:
    """
    Execute the complete GraphMCP database decommissioning demo workflow.
    
    Args:
        config: Demo configuration
        
    Returns:
        Workflow execution results
    """
    logger.info(f"Starting GraphMCP demo workflow in {config.mode} mode")
    logger.info(f"Target: {config.target_database} in {config.target_repo}")
    
    # Create enhanced logger for visually appealing output
    enhanced_logger = EnhancedDemoLogger(f"GraphMCP Demo - {config.target_database}")
    enhanced_logger.print_section_header("GraphMCP Database Decommissioning Workflow", "🚀")
    
    # Create workflow using WorkflowBuilder
    builder = WorkflowBuilder(
        name="GraphMCP Database Decommissioning Demo",
        config_path="mcp_config.json",  # Use existing config
        description=f"Complete demo workflow for {config.target_database} decommissioning with PR creation"
    )
    
    # Configure workflow
    builder.with_config(
        max_parallel_steps=1,  # Sequential execution for demo
        default_timeout=300,   # 5 minutes 
        stop_on_error=True,    # Stop on first error
        default_retry_count=2
    )
    
    # Add workflow steps with enhanced logger parameter
    workflow = (builder
        .custom_step(
            "validate_env", 
            "Validate Environment",
            validate_environment_step,
            description="Validate demo environment and prerequisites",
            parameters={"config": config, "enhanced_logger": enhanced_logger}
        )
        .custom_step(
            "get_repo",
            "Get Repository Pack", 
            get_repository_pack_step,
            description="Get repository pack data from cache or live service",
            parameters={"config": config, "enhanced_logger": enhanced_logger},
            depends_on=["validate_env"]
        )
        .custom_step(
            "discover_patterns",
            "Discover Database Patterns",
            discover_database_patterns_step, 
            description="Discover database usage patterns in repository",
            parameters={"config": config, "enhanced_logger": enhanced_logger},
            depends_on=["get_repo"]
        )
        .custom_step(
            "generate_refactoring",
            "Generate Refactoring Plan",
            generate_refactoring_plan_step,
            description="Generate refactoring plan based on patterns",
            parameters={"config": config, "enhanced_logger": enhanced_logger},
            depends_on=["discover_patterns"]
        )
        .custom_step(
            "create_pull_request",
            "Create Pull Request",
            create_pull_request_step,
            description="Create pull request with refactoring changes",
            parameters={"config": config, "enhanced_logger": enhanced_logger},
            depends_on=["generate_refactoring"]
        )
        .build()
    )
    
    # Execute workflow
    logger.info("Executing workflow...")
    start_time = time.time()
    result = await workflow.execute()
    total_duration = time.time() - start_time
    
    # Display enhanced workflow summary
    enhanced_logger.log_workflow_summary(
        total_duration=total_duration,
        steps_completed=result.steps_completed,
        total_steps=result.steps_completed + result.steps_failed,
        success_rate=result.success_rate
    )
    
    logger.info(f"Workflow completed with status: {result.status}")
    logger.info(f"Duration: {result.duration_seconds:.2f}s")
    logger.info(f"Success rate: {result.success_rate:.1f}%")
    
    return result


async def run_quick_demo(database_name: str = "postgres_air") -> WorkflowResult:
    """
    Run a quick demo in mock mode.
    
    Args:
        database_name: Database name to use
        
    Returns:
        Workflow execution results
    """
    config = DemoConfig.for_mock_mode(database_name)
    return await run_demo_workflow(config)


async def run_live_demo(database_name: str = "postgres_air", repo_url: Optional[str] = None) -> WorkflowResult:
    """
    Run a live demo in real mode.
    
    Args:
        database_name: Database name to use
        repo_url: Repository URL (uses default if None)
        
    Returns:
        Workflow execution results
    """
    config = DemoConfig.for_real_mode(database_name, repo_url)
    return await run_demo_workflow(config)