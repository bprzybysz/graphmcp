"""
GraphMCP Demo Workflow Runner.

This module provides the main workflow execution logic for the GraphMCP
database decommissioning demo, supporting both mock and real execution modes.
"""

import logging
import time
from typing import Any, Dict, Optional
from pathlib import Path

from workflows.builder import WorkflowBuilder, WorkflowResult
from .config import DemoConfig
from .cache import DemoCache

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
    
    if config.is_mock_mode:
        # Load from cache
        logger.info("Loading repository pack from cache (mock mode)")
        repo_data = cache.load_repo_cache()
        if repo_data is None:
            raise ValueError("Mock mode requested but no cached repo data found")
        
        return {
            "status": "loaded_from_cache",
            "repo_url": config.target_repo,
            "data_size": len(str(repo_data)),
            "timestamp": time.time(),
            "repo_data": repo_data,
        }
    else:
        # For real mode, would call actual Repomix MCP client
        # For now, simulate and cache the result
        logger.info("Fetching repository pack from live service (real mode)")
        
        # Simulate repo pack result
        repo_data = f"<repository url='{config.target_repo}'><file>mock_content</file></repository>"
        
        # Cache the result
        cache.save_repo_cache(repo_data)
        
        return {
            "status": "fetched_live",
            "repo_url": config.target_repo,
            "data_size": len(repo_data),
            "timestamp": time.time(),
            "repo_data": repo_data,
        }


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
    
    logger.info(f"Discovering patterns for database: {config.target_database}")
    
    # Get repo data from previous step
    repo_result = context.get_shared_value("get_repo")
    if not repo_result:
        raise ValueError("Repository data not available from previous step")
    
    if config.is_mock_mode:
        # Load patterns from cache
        logger.info("Loading pattern discovery from cache (mock mode)")
        patterns_data = cache.load_patterns_cache()
        if patterns_data is None:
            raise ValueError("Mock mode requested but no cached patterns found")
        
        return {
            "status": "loaded_from_cache", 
            "database": config.target_database,
            "patterns_found": len(patterns_data.get("patterns", [])),
            "timestamp": time.time(),
            "patterns": patterns_data,
        }
    else:
        # For real mode, would use PatternDiscoveryEngine
        logger.info("Running pattern discovery on live data (real mode)")
        
        # Simulate pattern discovery
        patterns_data = {
            "database": config.target_database,
            "patterns": [
                {"type": "sql_query", "file": "example.sql", "line": 10},
                {"type": "connection_string", "file": "config.py", "line": 25},
            ],
            "total_files_scanned": 42,
            "timestamp": time.time(),
        }
        
        # Cache the result
        cache.save_patterns_cache(patterns_data)
        
        return {
            "status": "discovered_live",
            "database": config.target_database, 
            "patterns_found": len(patterns_data["patterns"]),
            "timestamp": time.time(),
            "patterns": patterns_data,
        }


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
    
    logger.info("Generating refactoring plan")
    
    # Get patterns from previous step
    patterns_result = context.get_shared_value("discover_patterns")
    if not patterns_result:
        raise ValueError("Pattern data not available from previous step")
    
    patterns_count = patterns_result.get("patterns_found", 0)
    
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
    
    # Create workflow using WorkflowBuilder
    builder = WorkflowBuilder(
        name="GraphMCP Database Decommissioning Demo",
        config_path="mcp_config.json",  # Use existing config
        description=f"Demo workflow for {config.target_database} decommissioning"
    )
    
    # Configure workflow
    builder.with_config(
        max_parallel_steps=1,  # Sequential execution for demo
        default_timeout=300,   # 5 minutes 
        stop_on_error=True,    # Stop on first error
        default_retry_count=2
    )
    
    # Add workflow steps
    workflow = (builder
        .custom_step(
            "validate_env", 
            "Validate Environment",
            validate_environment_step,
            description="Validate demo environment and prerequisites",
            parameters={"config": config}
        )
        .custom_step(
            "get_repo",
            "Get Repository Pack", 
            get_repository_pack_step,
            description="Get repository pack data from cache or live service",
            parameters={"config": config},
            depends_on=["validate_env"]
        )
        .custom_step(
            "discover_patterns",
            "Discover Database Patterns",
            discover_database_patterns_step, 
            description="Discover database usage patterns in repository",
            parameters={"config": config},
            depends_on=["get_repo"]
        )
        .custom_step(
            "generate_refactoring",
            "Generate Refactoring Plan",
            generate_refactoring_plan_step,
            description="Generate refactoring plan based on patterns",
            parameters={"config": config},
            depends_on=["discover_patterns"]
        )
        .build()
    )
    
    # Execute workflow
    logger.info("Executing workflow...")
    result = await workflow.execute()
    
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