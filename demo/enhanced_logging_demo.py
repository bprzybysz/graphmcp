#!/usr/bin/env python3
"""
Enhanced Logging Demo for GraphMCP Workflows.

This demo showcases the enhanced logging system with animated progress indicators,
bandwidth tracking, and visual feedback elements integrated with WorkflowBuilder.

Usage:
    python demo/enhanced_logging_demo.py [--mode MODE] [--database DB] [--html-output PATH]
    
Examples:
    python demo/enhanced_logging_demo.py --mode mock --database demo_db
    python demo/enhanced_logging_demo.py --mode real --html-output progress.html
    python demo/enhanced_logging_demo.py --database test_db --html-output /tmp/demo.html
"""

import asyncio
import argparse
import time
import sys
import logging
import random
from pathlib import Path

# Import enhanced logging components
from concrete.enhanced_logger import create_enhanced_workflow_logger_async
from workflows.builder import WorkflowBuilder

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def print_demo_header():
    """Print demo header with branding."""
    print("=" * 80)
    print("🚀 GraphMCP Enhanced Logging System - DEMO")
    print("=" * 80)
    print()
    print("🎯 FEATURES DEMONSTRATED:")
    print("  • Real-time Animated Progress Bars with Spinners")
    print("  • Bandwidth Tracking and Performance Metrics")
    print("  • Responsive Terminal Output with ANSI Colors")
    print("  • HTML Progress Reports with Auto-refresh")
    print("  • Integration with WorkflowBuilder Execution")
    print("  • Async Progress Tracking with Visual Feedback")
    print()

def print_demo_step(step_num: int, step_name: str, description: str):
    """Print demo step separator."""
    print()
    print("─" * 60)
    print(f"📋 DEMO STEP {step_num}: {step_name}")
    print(f"📝 {description}")
    print("─" * 60)

async def simulate_repository_processing(context, step, **params):
    """Simulate repository processing with realistic progress updates."""
    repo_url = params.get("repo_url", "https://github.com/example/repo")
    mock_mode = params.get("mock_mode", True)
    
    logger.info(f"Processing repository: {repo_url}")
    
    # Get enhanced logger from context if available
    enhanced_logger = params.get("enhanced_logger")
    
    if enhanced_logger:
        # Simulate clone progress
        for progress in [0.1, 0.3, 0.6, 0.8, 1.0]:
            await enhanced_logger.log_step_progress_async(
                step.id, 
                progress, 
                f"Cloning repository: {progress*100:.0f}%",
                bytes_processed=int(random.uniform(512, 2048))  # Simulate data transfer
            )
            
            # Simulate processing time
            delay = 0.3 if mock_mode else random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
    
    # Return realistic repository data
    files_count = random.randint(50, 200) if not mock_mode else 127
    size_mb = random.uniform(5.0, 50.0) if not mock_mode else 23.5
    
    return {
        "repo_url": repo_url,
        "files_discovered": files_count,
        "total_size_mb": size_mb,
        "processing_time": time.time(),
        "mock_mode": mock_mode,
        "status": "completed"
    }

async def simulate_pattern_discovery(context, step, **params):
    """Simulate AI-powered pattern discovery with progress tracking."""
    database_name = params.get("database_name", "demo_db")
    repo_data = context.get_step_result("repository_processing", {})
    enhanced_logger = params.get("enhanced_logger")
    
    files_count = repo_data.get("files_discovered", 100)
    
    if enhanced_logger:
        # Simulate pattern analysis progress
        patterns_found = 0
        
        for i, progress in enumerate([0.15, 0.35, 0.55, 0.75, 0.90, 1.0]):
            if i < 3:
                message = f"Analyzing {int(files_count * progress)} files..."
            elif i < 5:
                patterns_found = random.randint(5, 25)
                message = f"Found {patterns_found} database patterns"
            else:
                message = f"Pattern discovery complete: {patterns_found} matches"
            
            await enhanced_logger.log_step_progress_async(
                step.id,
                progress,
                message,
                bytes_processed=int(random.uniform(256, 1024))
            )
            
            await asyncio.sleep(random.uniform(0.2, 0.8))
    
    return {
        "database_name": database_name,
        "patterns_found": patterns_found,
        "files_analyzed": files_count,
        "high_confidence_matches": max(0, patterns_found - 5),
        "processing_time": time.time(),
        "status": "completed"
    }

async def simulate_refactoring_generation(context, step, **params):
    """Simulate refactoring plan generation with detailed progress."""
    patterns_data = context.get_step_result("pattern_discovery", {})
    enhanced_logger = params.get("enhanced_logger")
    
    patterns_count = patterns_data.get("patterns_found", 0)
    
    if enhanced_logger:
        # Simulate refactoring analysis
        for i, progress in enumerate([0.2, 0.4, 0.6, 0.8, 1.0]):
            if i == 0:
                message = "Analyzing code patterns and dependencies"
            elif i == 1:
                message = "Generating refactoring strategies"
            elif i == 2:
                message = f"Planning changes for {patterns_count} patterns"
            elif i == 3:
                message = "Optimizing refactoring sequence"
            else:
                message = "Refactoring plan generated successfully"
            
            await enhanced_logger.log_step_progress_async(
                step.id,
                progress,
                message,
                bytes_processed=int(random.uniform(128, 512))
            )
            
            await asyncio.sleep(random.uniform(0.3, 1.0))
    
    estimated_files = max(patterns_count * 2, 10)
    estimated_effort_hours = max(patterns_count * 0.5, 2.0)
    
    return {
        "patterns_to_refactor": patterns_count,
        "estimated_files_affected": estimated_files,
        "estimated_effort_hours": estimated_effort_hours,
        "recommended_approach": "gradual_migration",
        "risk_level": "medium",
        "status": "completed"
    }

async def simulate_pull_request_creation(context, step, **params):
    """Simulate pull request creation with realistic timing."""
    refactoring_data = context.get_step_result("refactoring_generation", {})
    enhanced_logger = params.get("enhanced_logger")
    
    files_affected = refactoring_data.get("estimated_files_affected", 10)
    
    if enhanced_logger:
        # Simulate PR creation steps
        for i, progress in enumerate([0.25, 0.5, 0.75, 1.0]):
            if i == 0:
                message = "Creating feature branch"
            elif i == 1:
                message = f"Applying changes to {files_affected} files"
            elif i == 2:
                message = "Generating pull request description"
            else:
                message = "Pull request created successfully"
            
            await enhanced_logger.log_step_progress_async(
                step.id,
                progress,
                message,
                bytes_processed=int(random.uniform(64, 256))
            )
            
            await asyncio.sleep(random.uniform(0.4, 1.2))
    
    return {
        "pr_title": f"Database decommissioning: Remove {params.get('database_name', 'demo_db')} references",
        "branch_name": f"feature/remove-{params.get('database_name', 'demo_db')}-db",
        "files_changed": files_affected,
        "pr_url": "https://github.com/example/repo/pull/123",
        "status": "created"
    }

async def create_demo_workflow(database_name: str, mock_mode: bool = True, enhanced_logger=None):
    """Create a demo workflow showcasing enhanced logging features."""
    
    # Create workflow configuration (unused but kept for documentation)
    
    # Create workflow builder
    builder = WorkflowBuilder("enhanced_logging_demo", "demo_config.json")
    builder.with_config(stop_on_error=False, default_timeout=30)
    
    # Add custom steps with enhanced logger integration
    builder.custom_step(
        "repository_processing",
        "Repository Processing",
        simulate_repository_processing,
        description="Clone and analyze repository structure",
        parameters={
            "repo_url": "https://github.com/example/sample-database-app",
            "mock_mode": mock_mode,
            "enhanced_logger": enhanced_logger
        }
    )
    
    builder.custom_step(
        "pattern_discovery", 
        "AI Pattern Discovery",
        simulate_pattern_discovery,
        description="Discover database usage patterns with AI",
        parameters={
            "database_name": database_name,
            "enhanced_logger": enhanced_logger
        }
    )
    
    builder.custom_step(
        "refactoring_generation",
        "Refactoring Plan Generation", 
        simulate_refactoring_generation,
        description="Generate comprehensive refactoring plan",
        parameters={
            "enhanced_logger": enhanced_logger
        }
    )
    
    builder.custom_step(
        "pull_request_creation",
        "Pull Request Creation",
        simulate_pull_request_creation,
        description="Create pull request with refactoring changes", 
        parameters={
            "database_name": database_name,
            "enhanced_logger": enhanced_logger
        }
    )
    
    return builder.build()

async def run_enhanced_logging_demo(database_name: str = "demo_db",
                                   mode: str = "mock",
                                   html_output_path: str = None):
    """Run the complete enhanced logging demo."""
    
    print_demo_header()
    
    # Demo Step 1: Initialize Enhanced Logger
    print_demo_step(1, "Enhanced Logger Initialization", 
                    "Creating enhanced logger with visual progress tracking")
    
    # Create enhanced logger with visual features
    enhanced_logger = await create_enhanced_workflow_logger_async(
        database_name=database_name,
        total_steps=4,  # Repository, Pattern Discovery, Refactoring, PR Creation
        log_level="INFO",
        enable_visual=True,
        enable_animations=True,
        html_output_path=html_output_path
    )
    
    print(f"✅ Enhanced logger initialized for database: {database_name}")
    print("📊 Visual progress tracking: ENABLED")
    print("🎬 Animations: ENABLED")
    if html_output_path:
        print(f"📄 HTML output: {html_output_path}")
    
    # Demo Step 2: Create and Execute Workflow
    print_demo_step(2, "Workflow Execution with Enhanced Logging",
                    "Running workflow with real-time animated progress")
    
    try:
        # Create demo workflow
        workflow = await create_demo_workflow(
            database_name, 
            mock_mode=(mode == "mock"),
            enhanced_logger=enhanced_logger
        )
        
        print("🚀 Starting workflow execution with enhanced logging...")
        print("👀 Watch for animated progress bars and real-time metrics!")
        print()
        
        # Execute workflow with enhanced logger
        start_time = time.time()
        result = await workflow.execute(enhanced_logger=enhanced_logger)
        execution_time = time.time() - start_time
        
        # Demo Step 3: Results Summary
        print_demo_step(3, "Workflow Results & Performance Metrics",
                       "Displaying comprehensive results and performance data")
        
        print(f"🎉 Workflow completed in {execution_time:.1f} seconds")
        print(f"📈 Success rate: {result.success_rate:.1f}%")
        print(f"✅ Steps completed: {result.steps_completed}")
        print(f"❌ Steps failed: {result.steps_failed}")
        print()
        
        # Display enhanced metrics
        enhanced_summary = enhanced_logger.get_enhanced_metrics_summary()
        enhanced_metrics = enhanced_summary.get("enhanced_metrics", {})
        
        print("📊 Enhanced Logging Performance Metrics:")
        print(f"  🔄 Current Step: {enhanced_metrics.get('current_step', 'N/A')}")
        print(f"  📈 Progress: {enhanced_metrics.get('progress_percentage', 0):.1f}%")
        print(f"  🚀 Bandwidth: {enhanced_metrics.get('bandwidth_mbps', 0):.2f} MB/s")
        print(f"  ⏱️  Total Bytes: {enhanced_metrics.get('bytes_processed', 0):,} bytes")
        print(f"  🎬 Animation State: {enhanced_metrics.get('animation_state', 'N/A')}")
        print()
        
        # Display step results
        print("📋 Step-by-Step Results:")
        for step_id, step_result in result.step_results.items():
            if isinstance(step_result, dict) and "status" in step_result:
                status_icon = "✅" if step_result["status"] == "completed" else "❌"
                print(f"  {status_icon} {step_id}: {step_result['status']}")
            else:
                print(f"  ✅ {step_id}: completed")
        
        # HTML report notification
        if html_output_path and Path(html_output_path).exists():
            print()
            print("📄 HTML Progress Report Generated!")
            print(f"🌐 Open in browser: file://{Path(html_output_path).absolute()}")
        
    except Exception as e:
        print(f"❌ Demo execution failed: {e}")
        raise
    
    finally:
        # Demo Step 4: Cleanup
        print_demo_step(4, "Cleanup & Resource Management",
                       "Properly cleaning up enhanced logging resources")
        
        try:
            await enhanced_logger.cleanup_async()
            print("✅ Enhanced logger cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    # Demo completion
    print()
    print("=" * 80)
    print("🎉 ENHANCED LOGGING DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("💡 Key Features Demonstrated:")
    print("  • Animated progress bars with real-time updates")
    print("  • Bandwidth tracking and performance metrics")
    print("  • Responsive terminal output with colors")
    print("  • HTML progress reports with auto-refresh")
    print("  • Seamless WorkflowBuilder integration")
    print("  • Async progress tracking with visual feedback")
    print()
    print("🚀 The enhanced logging system is ready for production use!")
    print()

def main():
    """Main demo execution function."""
    parser = argparse.ArgumentParser(
        description="GraphMCP Enhanced Logging System Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo/enhanced_logging_demo.py --mode mock --database demo_db
  python demo/enhanced_logging_demo.py --mode real --html-output progress.html
  python demo/enhanced_logging_demo.py --database test_db --html-output /tmp/demo.html
        """
    )
    
    parser.add_argument(
        "--database",
        default="demo_db",
        help="Database name for decommissioning demo (default: demo_db)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        default="mock",
        help="Execution mode: mock for fast demo, real for realistic timing"
    )
    
    parser.add_argument(
        "--html-output",
        help="Path for HTML progress report output (optional)"
    )
    
    args = parser.parse_args()
    
    # Run the demo
    try:
        asyncio.run(run_enhanced_logging_demo(
            database_name=args.database,
            mode=args.mode,
            html_output_path=args.html_output
        ))
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed: {str(e)}")
        logger.exception("Demo execution error")
        sys.exit(1)

if __name__ == "__main__":
    main()