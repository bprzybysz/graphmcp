#!/usr/bin/env python3
"""
Test script to verify UI-backend integration with mocking.
The UI should be naive - it just calls backend APIs and gets appropriate data.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from concrete.pattern_discovery import PatternDiscoveryEngine
from clients.repomix import RepomixMCPClient
from clients.github import GitHubMCPClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ui_backend_integration():
    """Test that UI can call backend and get mocked data transparently."""
    logger.info("🧪 Testing UI-backend integration with transparent mocking")
    
    try:
        # This is exactly what the UI does - it's naive about mocking
        pattern_engine = PatternDiscoveryEngine()
        
        # Mock clients (UI creates these normally)
        repomix_client = RepomixMCPClient("mcp_config.json")
        github_client = GitHubMCPClient("mcp_config.json")
        
        # UI parameters 
        repo_url = "https://github.com/bprzybys-nc/postgres-sample-dbs"
        repo_owner = "bprzybys-nc"
        repo_name = "postgres-sample-dbs"
        database_name = "postgres_air"
        
        logger.info(f"🎯 UI calling backend for: {database_name}")
        logger.info(f"📦 Repository: {repo_owner}/{repo_name}")
        
        # UI calls backend - completely naive about mocking
        discovery_result = await pattern_engine.discover_patterns_in_repository(
            repomix_client, github_client, repo_url, database_name, repo_owner, repo_name
        )
        
        # Validate results
        logger.info("✅ Backend response received!")
        logger.info(f"   Database: {discovery_result.get('database_name')}")
        logger.info(f"   Repository: {discovery_result.get('repository')}")
        logger.info(f"   Total files: {discovery_result.get('total_files')}")
        logger.info(f"   Matched files: {discovery_result.get('matched_files')}")
        
        # Check that we got real context data (indicating mock is working)
        files = discovery_result.get('files', [])
        if len(files) > 0:
            logger.info(f"📁 Sample files received:")
            for i, file_data in enumerate(files[:3]):
                logger.info(f"   {i+1}. {file_data.get('path')}")
            
            # Verify this is mocked real context data
            if discovery_result.get('total_files', 0) >= 70:  # Real data has 73 files
                logger.info("✅ SUCCESS: UI got real context via backend mocking!")
                logger.info(f"   Total files: {discovery_result.get('total_files')}")
                logger.info(f"   Matched files: {discovery_result.get('matched_files')}")
                logger.info("   UI is completely naive - backend handled mocking transparently")
                return True
            else:
                logger.error("❌ FAILURE: UI got hardcoded data instead of real context")
                return False
        else:
            logger.error("❌ FAILURE: No files received from backend")
            return False
            
    except Exception as e:
        logger.error(f"❌ UI-backend integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ui_backend_integration())
    if success:
        print("🎉 UI-backend integration test passed!")
        print("✅ UI is naive about mocking")
        print("✅ Backend handles mocking transparently") 
        print("✅ Real context data flows to UI")
        sys.exit(0)
    else:
        print("💥 UI-backend integration test failed!")
        sys.exit(1) 