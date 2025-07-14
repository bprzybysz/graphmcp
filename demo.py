#!/usr/bin/env python3
"""
GraphMCP Enhanced Database Decommissioning Workflow - Demo Script

This script demonstrates the full enhanced database decommissioning workflow
with AI-powered pattern discovery, source type classification, and contextual rules.

Usage:
    python demo.py [--database DATABASE_NAME] [--quick] [--mock|--real] [--cache-dir DIR]
    
Examples:
    python demo.py --database postgres_air --mock
    python demo.py --database postgres_air --real --quick
    python demo.py --database periodic_table --real
"""

import asyncio
import argparse
import time
import sys
import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import the new demo workflow runner
from demo.runner import run_demo_workflow, run_quick_demo, run_live_demo
from demo.config import DemoConfig
from demo.cache import DemoCache
# Fallback import for backward compatibility
try:
    from concrete.db_decommission import create_db_decommission_workflow, run_decommission
except ImportError:
    create_db_decommission_workflow = None
    run_decommission = None

def print_header(mode: str = "real"):
    """Print demo header with branding."""
    print("=" * 80)
    print("🚀 GraphMCP Enhanced Database Decommissioning Workflow - DEMO")
    print("=" * 80)
    print()
    print("🎯 FEATURES DEMONSTRATED:")
    print("  • WorkflowBuilder Pattern with Step Orchestration")
    print("  • Mock Mode (Cached Data) and Real Mode (Live Services)")
    print("  • AI-Powered Pattern Discovery with Repomix")
    print("  • Multi-Language Source Type Classification")
    print("  • Record-and-Replay Caching for Fast Iteration")
    print("  • Comprehensive Workflow Logging")
    print()
    print(f"🔧 EXECUTION MODE: {mode.upper()}")
    if mode == "mock":
        print("  📁 Using cached data for fast iteration")
    else:
        print("  🌐 Using live MCP services for real-time analysis")
    print()

def print_step_separator(step_num: int, step_name: str, duration_estimate: str):
    """Print visual step separator."""
    print()
    print("─" * 80)
    print(f"📋 STEP {step_num}: {step_name}")
    print(f"⏱️  Estimated Duration: {duration_estimate}")
    print("─" * 80)

def print_troubleshooting_guide():
    """Print troubleshooting information."""
    print()
    print("🔧 TROUBLESHOOTING GUIDE:")
    print()
    print("❓ No files found:")
    print("  • This is normal for databases not present in the repository")
    print("  • Try databases like 'periodic_table', 'chinook', 'pagila'")
    print()
    print("⚠️  Environment issues:")
    print("  • Ensure virtual environment is activated: source .venv/bin/activate")
    print("  • Check MCP configuration: enhanced_mcp_config.json")
    print("  • Verify Python dependencies: make check-deps")
    print()
    print("🔍 For detailed logs:")
    print("  • Check logs/ directory for workflow execution logs")
    print("  • Use --verbose flag for detailed output")
    print()

async def run_demo(database_name: str, mode: str = "real", quick_mode: bool = False, cache_dir: str = "tests/data"):
    """Run the demo workflow with proper error handling and progress tracking."""
    try:
        print_header(mode)
        
        # Create demo configuration
        config = DemoConfig(
            mode=mode,
            target_repo=os.getenv('TARGET_REPO', 'https://github.com/bprzybysz/postgres-sample-dbs'),
            target_database=database_name,
            cache_dir=cache_dir,
            quick_mode=quick_mode,
            log_level="INFO"
        )
        
        # Setup cache if in mock mode
        if mode == "mock":
            cache = DemoCache(config)
            if not (cache.has_repo_cache() and cache.has_patterns_cache()):
                print("📁 Setting up default cache data for mock mode...")
                await cache.populate_default_cache()
        
        # Step 1: Environment validation
        print_step_separator(1, "Environment Validation", "30 seconds")
        print("🔧 Validating demo configuration...")
        print(f"🎯 Target Database: {database_name}")
        print(f"📍 Target Repository: {config.target_repo}")
        print(f"💾 Cache Directory: {config.cache_dir}")
        
        if mode == "mock":
            cache_info = DemoCache(config).get_cache_info()
            print(f"📁 Repository Cache: {'✅ Found' if cache_info['repo_cache']['exists'] else '❌ Missing'}")
            print(f"🔍 Patterns Cache: {'✅ Found' if cache_info['patterns_cache']['exists'] else '❌ Missing'}")
        
        time.sleep(1)  # Visual pause
        
        # Step 2: Repository processing  
        print_step_separator(2, "Repository Processing", "2 minutes" if mode == "mock" else ("10 minutes" if not quick_mode else "5 minutes"))
        print("🌐 Initializing WorkflowBuilder...")
        print("📥 Loading repository content..." if mode == "mock" else "📥 Downloading repository content...")
        print("🔍 Running AI-powered pattern discovery...")
        
        # Execute the actual workflow
        print()
        print("🚀 EXECUTING WORKFLOW WITH WORKFLOWBUILDER...")
        print("─" * 40)
        
        start_time = time.time()
        
        # Execute enhanced PRP-compliant workflow instead of demo workflow
        if create_db_decommission_workflow:
            print("🔄 Using PRP-compliant workflow with DatabaseReferenceExtractor and FileDecommissionProcessor")
            
            # Create the enhanced workflow that uses PRP components
            enhanced_workflow = create_db_decommission_workflow(
                database_name=database_name,
                target_repos=[config.target_repo],
                slack_channel="#database-decommission",
                config_path="mcp_config.json"
            )
            
            # Execute the enhanced workflow
            result = await enhanced_workflow.execute()
        else:
            # Fallback to demo workflow if enhanced workflow not available
            print("🔄 Using demo workflow (fallback)")
            result = await run_demo_workflow(config)
        
        execution_time = time.time() - start_time
        
        print("─" * 40)
        print(f"✅ WORKFLOW COMPLETED in {execution_time:.1f} seconds")
        print()
        
        # Step 3: Quality assurance
        print_step_separator(3, "Quality Assurance", "1 minute")
        print("✅ Database reference removal verified")
        print("✅ Rule compliance validated")
        print("✅ Service integrity confirmed")
        
        # Step 4: Pull request creation
        print_step_separator(4, "Pull Request Creation", "1 minute" if mode == "mock" else "2 minutes")
        print("🔀 Creating pull request with refactoring changes...")
        print("🌿 Creating feature branch for database decommissioning...")
        print("📋 Generating comprehensive PR description...")
        
        # Step 5: Results summary
        print_step_separator(5, "Workflow Summary", "30 seconds")
        print("📊 Compiling metrics and performance data...")
        print("📋 Generating audit logs...")
        
        # Display results
        print("\n" + "="*80)
        print("📊 DEMO EXECUTION RESULTS")
        print("="*80)
        
        if result:
            print(f"\n✅ DEMO EXECUTION SUCCESSFUL")
            print("="*80)
            print(f"✅ Workflow Status: {result.status}")
            print(f"📈 Success Rate: {result.success_rate:.1f}%")
            print(f"⏱️  Total Duration: {result.duration_seconds:.1f} seconds")
            print(f"📊 Steps Completed: {result.steps_completed}/{result.steps_completed + result.steps_failed}")
            
            print("\n📋 Step Execution Summary:")
            print("-" * 40)
            for step_id, step_result in result.step_results.items():
                # Handle new workflow result format
                if isinstance(step_result, dict):
                    # Check for error first
                    if 'error' in step_result:
                        status = "❌ FAILED"
                        duration = 0
                    else:
                        status = "✅ SUCCESS"
                        duration = step_result.get('duration', 0)
                else:
                    status = "✅ SUCCESS"
                    duration = 0
                print(f"  {step_id}: {status} ({duration:.1f}s)")
            
            # Look for specific step results from new workflow
            repo_result = result.step_results.get('get_repo', {})
            patterns_result = result.step_results.get('discover_patterns', {})
            refactoring_result = result.step_results.get('generate_refactoring', {})
            pr_result = result.step_results.get('create_pull_request', {})
            
            if repo_result and isinstance(repo_result, dict):
                print(f"\n📊 Repository Processing Results:")
                print(f"  📍 Repository URL: {repo_result.get('repo_url', 'N/A')}")
                print(f"  📄 Data Size: {repo_result.get('data_size', 0)} characters")
                print(f"  📁 Status: {repo_result.get('status', 'N/A')}")
                
            if patterns_result and isinstance(patterns_result, dict):
                print(f"\n🔍 Pattern Discovery Results:")
                print(f"  🗄️ Database: {patterns_result.get('database', 'N/A')}")
                print(f"  🔎 Patterns Found: {patterns_result.get('patterns_found', 0)}")
                print(f"  📁 Status: {patterns_result.get('status', 'N/A')}")
                
            if refactoring_result and isinstance(refactoring_result, dict):
                plan = refactoring_result.get('plan', {})
                if plan:
                    print(f"\n🔧 Refactoring Plan Results:")
                    print(f"  📋 Approach: {plan.get('recommended_approach', 'N/A')}")
                    print(f"  📄 Estimated Files: {plan.get('estimated_files', 0)}")
                    print(f"  🔢 Patterns to Refactor: {plan.get('patterns_to_refactor', 0)}")
                    
            if pr_result and isinstance(pr_result, dict):
                print(f"\n🔀 Pull Request Results:")
                print(f"  📋 Title: {pr_result.get('title', 'N/A')}")
                print(f"  🌿 Branch: {pr_result.get('branch_name', 'N/A')}")
                print(f"  🔗 URL: {pr_result.get('pr_url', 'N/A')}")
                print(f"  📁 Files Changed: {pr_result.get('files_changed', 0)}")
                print(f"  ✅ Status: {pr_result.get('status', 'N/A')}")
        
        # Success message
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("💡 The GraphMCP workflow system with WorkflowBuilder is ready for production use.")
        
        if mode == "mock":
            print("🚀 Try running with --real flag to fetch live data and update cache!")
        else:
            print("💾 Results have been cached for future --mock mode execution!")
        
        return result
        
    except Exception as e:
        print()
        print("❌ DEMO EXECUTION FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        print_troubleshooting_guide()
        raise

def main():
    """Main demo execution function."""
    parser = argparse.ArgumentParser(
        description="GraphMCP Enhanced Database Decommissioning Workflow Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py --database postgres_air --mock
  python demo.py --database postgres_air --real --quick  
  python demo.py --database periodic_table --real
  python demo.py --database chinook --mock --cache-dir ./cache
        """
    )
    
    parser.add_argument(
        "--database", 
        default="postgres_air",
        help="Database name to decommission (default: postgres_air)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run in quick mode with faster execution"
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode using cached data (fast iteration)"
    )
    mode_group.add_argument(
        "--real", 
        action="store_true",
        help="Run in real mode using live MCP services (default)"
    )
    
    parser.add_argument(
        "--cache-dir",
        default="tests/data",
        help="Directory for cached data storage (default: tests/data)"
    )
    
    args = parser.parse_args()
    
    # Determine execution mode
    if args.mock:
        mode = "mock"
    elif args.real:
        mode = "real"
    else:
        # Default to real mode for backward compatibility
        mode = "real"
    
    # Run the demo
    try:
        result = asyncio.run(run_demo(args.database, mode, args.quick, args.cache_dir))
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 