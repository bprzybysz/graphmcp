#!/usr/bin/env python3
"""
Enhanced Database Decommissioning Demo Script

This script provides multiple ways to run the enhanced database decommissioning workflow:
1. Run the enhanced workflow with real-time execution
2. Launch the Streamlit monitoring app for live progress tracking  
3. Run both simultaneously for a complete e2e demo experience
4. Production-ready execution with comprehensive logging

Features:
- Centralized parameter service integration
- Enhanced pattern discovery and contextual rules
- Real-time progress monitoring via Streamlit
- Comprehensive logging and error handling
- Multiple execution modes for different use cases
"""

import asyncio
import argparse
import logging
import sys
import subprocess
import time
import signal
import os
from pathlib import Path

# Import the enhanced database decommissioning workflow
from concrete.enhanced_db_decommission import (
    run_enhanced_decommission,
    initialize_environment_with_centralized_secrets
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_db_demo.log')
    ]
)

logger = logging.getLogger(__name__)

class EnhancedDemoRunner:
    """Enhanced database decommissioning demo runner."""
    
    def __init__(self):
        self.streamlit_process = None
        self.workflow_task = None
        
    def cleanup(self):
        """Clean up resources."""
        logger.info("🧹 Cleaning up resources...")
        
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
            except Exception as e:
                logger.error(f"Error stopping Streamlit: {e}")
        
        if self.workflow_task and not self.workflow_task.done():
            self.workflow_task.cancel()
    
    async def run_workflow_only(self, database_name: str, target_repos: list, slack_channel: str):
        """Run only the enhanced workflow."""
        logger.info("🔄 Starting enhanced database decommissioning workflow...")
        logger.info(f"📊 Database: {database_name}")
        logger.info(f"📁 Repositories: {len(target_repos)}")
        logger.info(f"💬 Slack Channel: {slack_channel}")
        
        try:
            await run_enhanced_decommission(
                database_name=database_name,
                target_repos=target_repos,
                slack_channel=slack_channel
            )
            logger.info("✅ Enhanced workflow completed successfully!")
        except Exception as e:
            logger.error(f"❌ Enhanced workflow failed: {e}")
            raise
    
    def launch_streamlit_app(self, port: int = 8501):
        """Launch the Streamlit monitoring app."""
        logger.info(f"🚀 Launching Enhanced Streamlit app on port {port}...")
        
        streamlit_file = "concrete/examples/enhanced_db_decommission_ui.py"
        if not Path(streamlit_file).exists():
            raise FileNotFoundError(f"Streamlit app file not found: {streamlit_file}")
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            streamlit_file,
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        try:
            self.streamlit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment to check if it started successfully
            time.sleep(3)
            if self.streamlit_process.poll() is None:
                logger.info("✅ Streamlit app launched successfully!")
                logger.info(f"🌐 Access the app at: http://localhost:{port}")
                return True
            else:
                stdout, stderr = self.streamlit_process.communicate()
                logger.error("❌ Streamlit failed to start:")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to launch Streamlit: {e}")
            return False
    
    async def run_e2e_demo(self, database_name: str, target_repos: list, slack_channel: str, port: int = 8501):
        """Run the complete E2E demo with Streamlit monitoring."""
        logger.info("🚀 Starting Enhanced Database Decommissioning E2E Demo")
        logger.info("=" * 60)
        
        # Initialize environment with centralized parameter service
        logger.info("🔐 Initializing environment with centralized parameter service...")
        try:
            param_service = initialize_environment_with_centralized_secrets()
            if param_service.validation_issues:
                logger.warning(f"⚠️ Found {len(param_service.validation_issues)} parameter validation issues:")
                for issue in param_service.validation_issues:
                    logger.warning(f"   - {issue}")
            else:
                logger.info("✅ Parameter service initialized successfully with no issues")
        except Exception as e:
            logger.error(f"❌ Failed to initialize parameter service: {e}")
            raise
        
        # Launch Streamlit app
        if not self.launch_streamlit_app(port):
            logger.error("❌ Streamlit app launch failed. Cannot proceed.")
            return
        
        # Wait for Streamlit to fully initialize
        logger.info("⏳ Waiting 5 seconds for Streamlit to fully initialize...")
        await asyncio.sleep(5)
        
        # Start the enhanced workflow
        logger.info("🔄 Starting enhanced workflow execution...")
        try:
            self.workflow_task = asyncio.create_task(
                self.run_workflow_only(database_name, target_repos, slack_channel)
            )
            
            # Keep the demo running and provide status updates
            while not self.workflow_task.done():
                await asyncio.sleep(10)
                logger.info("📊 Demo running... Check Streamlit app for results")
            
            # Wait for workflow completion
            await self.workflow_task
            logger.info("🎉 E2E Demo completed successfully!")
            
        except asyncio.CancelledError:
            logger.info("🛑 Demo cancelled by user")
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function to run the enhanced database decommissioning demo."""
    parser = argparse.ArgumentParser(description="Enhanced Database Decommissioning Demo")
    parser.add_argument("--mode", choices=["workflow", "streamlit", "e2e"], default="e2e",
                       help="Demo mode: workflow only, streamlit only, or full e2e")
    parser.add_argument("--database", default="demo_production_db", 
                       help="Database name to decommission")
    parser.add_argument("--repos", nargs="+", 
                       default=["https://github.com/bprzybys-nc/postgres-sample-dbs"],
                       help="Target repository URLs")
    parser.add_argument("--slack-channel", default="C01234567",
                       help="Slack channel ID for notifications")
    parser.add_argument("--port", type=int, default=8501,
                       help="Port for Streamlit app")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Enhanced Database Decommissioning Demo - Mode: {args.mode}")
    
    demo_runner = EnhancedDemoRunner()
    demo_runner.setup_signal_handlers()
    
    try:
        if args.mode == "workflow":
            await demo_runner.run_workflow_only(args.database, args.repos, args.slack_channel)
        elif args.mode == "streamlit":
            if demo_runner.launch_streamlit_app(args.port):
                logger.info("🌐 Streamlit app is running. Press Ctrl+C to stop.")
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass
        elif args.mode == "e2e":
            await demo_runner.run_e2e_demo(args.database, args.repos, args.slack_channel, args.port)
        
    except KeyboardInterrupt:
        logger.info("🛑 Demo stopped by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return 1
    finally:
        demo_runner.cleanup()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 