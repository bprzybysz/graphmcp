#!/usr/bin/env python3
"""
Test script to validate the mocked pattern discovery step with real context data.
This ensures the mock loads the captured real discovery context properly.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from concrete.pattern_discovery import discover_patterns_step
from workflows.builder import WorkflowBuilder

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockContext:
    """Mock context for testing pattern discovery."""
    def __init__(self):
        self._clients = {}
        self.shared_values = {}
    
    def get_client(self, client_type):
        return self._clients.get(client_type)
    
    def set_shared_value(self, key, value):
        self.shared_values[key] = value
    
    def get_shared_value(self, key):
        return self.shared_values.get(key)

class MockStep:
    """Mock step for testing."""
    def __init__(self, name):
        self.name = name

async def test_mock_pattern_discovery():
    """Test the mocked pattern discovery with real context data."""
    logger.info("🧪 Testing mocked pattern discovery with real context data")
    
    # Create test context and step
    context = MockContext()
    step = MockStep("Pattern Discovery")
    
    # Parameters for postgres_air test
    database_name = "postgres_air"
    repo_owner = "bprzybys-nc"
    repo_name = "postgres-sample-dbs"
    
    logger.info(f"🎯 TARGET DATABASE: {database_name}")
    logger.info(f"📦 TARGET REPOSITORY: {repo_owner}/{repo_name}")
    
    try:
        # Execute the mock discovery step
        discovery_result = await discover_patterns_step(
            context, 
            step, 
            database_name=database_name,
            repo_owner=repo_owner,
            repo_name=repo_name
        )
        
        # Validate the results
        logger.info("✅ Mock discovery completed successfully!")
        logger.info(f"   Database: {discovery_result.get('database_name')}")
        logger.info(f"   Repository: {discovery_result.get('repository')}")
        logger.info(f"   Total files: {discovery_result.get('total_files')}")
        logger.info(f"   Matched files: {discovery_result.get('matched_files')}")
        
        # Check that we have real context data (not hardcoded mock)
        files = discovery_result.get('files', [])
        if len(files) > 0:
            logger.info(f"📁 Sample files found:")
            for i, file_data in enumerate(files[:5]):
                logger.info(f"   {i+1}. {file_data.get('path')} (matches: {file_data.get('matches', 0)})")
            
            # Verify this is real context data
            if discovery_result.get('total_files', 0) >= 70:  # Real data should have 73 files
                logger.info("✅ VALIDATED: Mock is using REAL captured context data!")
                logger.info(f"   Real context size: {discovery_result.get('total_files')} files")
                logger.info(f"   Real matches: {discovery_result.get('matched_files')} files")
                return True
            else:
                logger.error("❌ VALIDATION FAILED: Mock appears to be using hardcoded data")
                return False
        else:
            logger.error("❌ VALIDATION FAILED: No files found in discovery result")
            return False
            
    except Exception as e:
        logger.error(f"❌ Mock discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mock_pattern_discovery())
    if success:
        print("🎉 Mock validation completed successfully!")
        sys.exit(0)
    else:
        print("💥 Mock validation failed!")
        sys.exit(1) 