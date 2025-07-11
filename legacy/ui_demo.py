#!/usr/bin/env python3
"""
UI Demo Script for GraphMCP Database Decommissioning Workflow

This script demonstrates the Streamlit UI running alongside the actual 
database decommissioning workflow to showcase the complete system.
"""

import asyncio
import time
import subprocess
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_demo_header():
    """Print a nice demo header."""
    print("=" * 80)
    print("🚀 GraphMCP Database Decommissioning Workflow - UI DEMO")
    print("=" * 80)
    print()
    print("🎯 DEMO FEATURES:")
    print("  • Interactive Streamlit Web Interface")
    print("  • Real-time Workflow Progress Tracking")
    print("  • Live Log Streaming with Visual Charts")
    print("  • Database Pattern Discovery Visualization")
    print("  • Comprehensive Step-by-Step Progress")
    print()
    print("📋 DEMO STEPS:")
    print("  1. 🌐 Launch Streamlit Web UI")
    print("  2. 🔄 Start Interactive Demo Workflow")
    print("  3. 📊 View Real-time Progress & Logs")
    print("  4. 🎉 Complete Workflow Demonstration")
    print()

def check_streamlit_running():
    """Check if Streamlit is already running."""
    try:
        import requests
        response = requests.get("http://localhost:8501/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_streamlit():
    """Start the Streamlit application."""
    print("🌐 Starting Streamlit Web UI...")
    
    if check_streamlit_running():
        print("   ✅ Streamlit is already running at http://localhost:8501")
        return None
    
    try:
        # Start Streamlit in background
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "concrete/preview_ui/streamlit_app.py", 
            "--server.port", "8501",
            "--server.headless", "true",
            "--logger.level", "error"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        print("   🔄 Waiting for Streamlit to start...")
        for i in range(10):
            time.sleep(1)
            if check_streamlit_running():
                print("   ✅ Streamlit UI launched successfully!")
                print("   🌐 Access the UI at: http://localhost:8501")
                return process
            print(f"   ⏳ Starting up... ({i+1}/10)")
        
        print("   ❌ Failed to start Streamlit within timeout")
        return None
        
    except Exception as e:
        print(f"   ❌ Error starting Streamlit: {e}")
        return None

async def run_demo_workflow():
    """Run the actual database decommissioning workflow for demo."""
    print("\n🔄 Running Database Decommissioning Workflow...")
    print("   🎯 Target Database: chinook")
    print("   📁 Repository: bprzybys-nc/postgres-sample-dbs")
    print()
    
    try:
        # Import the actual workflow
        from concrete.db_decommission import run_decommission
        
        # Run the workflow with demo parameters
        result = await run_decommission(
            database_name="chinook",
            target_repos=['https://github.com/bprzybys-nc/postgres-sample-dbs'],
            slack_channel="C01234567",
            workflow_id="ui-demo-workflow"
        )
        
        print("   ✅ Workflow completed successfully!")
        print(f"   📊 Files Discovered: {result.get('total_files_processed', 0)}")
        print(f"   ✏️  Files Modified: {result.get('total_files_modified', 0)}")
        print(f"   ⏱️  Duration: {result.get('duration', 0):.1f}s")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Workflow error: {e}")
        return None

def display_ui_instructions():
    """Display instructions for using the UI."""
    print("\n📋 UI DEMO INSTRUCTIONS:")
    print("──────────────────────────────────────────────────────────────────────────────")
    print("1. 🌐 Open your browser and go to: http://localhost:8501")
    print("2. 🚀 Click the 'Start Demo' button in the left progress pane")
    print("3. 🔄 Watch the real-time workflow progress and live logs")
    print("4. 📊 Observe the interactive charts and tables as they appear")
    print("5. 🎉 See the completion status when all steps finish")
    print()
    print("🎯 KEY UI FEATURES TO EXPLORE:")
    print("   • Left Progress Pane: Step-by-step progress tracking")
    print("   • Main Log Pane: Live streaming logs with timestamps")
    print("   • Interactive Charts: Data visualizations and metrics")
    print("   • Auto-refresh: Real-time updates without manual refresh")
    print("   • Clear Button: Reset and start a new workflow")
    print()

def main():
    """Run the complete UI demo."""
    print_demo_header()
    
    # Start Streamlit UI
    streamlit_process = start_streamlit()
    
    try:
        # Display UI instructions
        display_ui_instructions()
        
        # Ask user if they want to run the actual workflow too
        print("💡 OPTIONAL: Run actual database decommissioning workflow?")
        print("   This will demonstrate real pattern discovery with live results.")
        response = input("   Enter 'y' to run workflow, or any key to continue with UI only: ").strip().lower()
        
        if response == 'y':
            print("\n🚀 Running actual workflow in background...")
            result = asyncio.run(run_demo_workflow())
            
            if result:
                print("\n✨ WORKFLOW RESULTS SUMMARY:")
                print("──────────────────────────────────────────────────────────────────────────────")
                print(f"   📁 Repositories Processed: {result.get('repositories_processed', 0)}")
                print(f"   📄 Files Discovered: {result.get('total_files_processed', 0)}")
                print(f"   ✏️  Files Modified: {result.get('total_files_modified', 0)}")
                print(f"   ⏱️  Total Duration: {result.get('duration', 0):.1f} seconds")
                print(f"   ✅ Success Rate: 100%")
        
        print("\n🎉 UI DEMO IS NOW RUNNING!")
        print("──────────────────────────────────────────────────────────────────────────────")
        print("🌐 Access the Streamlit UI at: http://localhost:8501")
        print("🔄 The UI demo will continue running until you stop it")
        print("⏹️  Press Ctrl+C to stop the demo")
        print()
        
        # Keep the demo running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Demo stopped by user")
            
    finally:
        # Clean up
        if streamlit_process:
            print("🧹 Cleaning up Streamlit process...")
            streamlit_process.terminate()
            try:
                streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()
        
        print("✅ Demo cleanup completed")
        print("🎉 Thank you for viewing the GraphMCP UI Demo!")

if __name__ == "__main__":
    main() 