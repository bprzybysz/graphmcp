#!/usr/bin/env python3
"""
Test script to run the mocked workflow and verify the HACK/TODO implementations work correctly.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

async def test_mocked_workflow():
    """Test the workflow with mocked components."""
    print("🚀 Testing mocked workflow with local repomix data...")
    
    try:
        from concrete.db_decommission import run_decommission
        
        # Configure logging to see the HACK/TODO messages
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        print("📦 Running decommission workflow with mocked data...")
        result = await run_decommission(
            database_name='postgres_air',
            target_repos=['https://github.com/bprzybys-nc/postgres-sample-dbs'],
            slack_channel='C01234567',
            workflow_id='test_mock_workflow'
        )
        
        print(f"✅ Workflow completed successfully!")
        if hasattr(result, 'status'):
            print(f"   Status: {result.status}")
        if hasattr(result, 'steps_completed'):
            print(f"   Steps completed: {result.steps_completed}")
        
        return result
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_individual_components():
    """Test individual mocked components."""
    print("\n🔧 Testing individual mocked components...")
    
    try:
        # Test mocked RepomixMCPClient
        print("1. Testing RepomixMCPClient mock...")
        from clients.repomix import RepomixMCPClient
        
        client = RepomixMCPClient("test_config.json")
        result = await client.pack_remote_repository("https://github.com/bprzybys-nc/postgres-sample-dbs")
        
        print(f"   ✅ RepomixMCPClient mock result: {result.get('source', 'unknown')} - {result.get('files_packed', 0)} files")
        
        # Test mocked pattern discovery
        print("2. Testing pattern discovery mock...")
        from concrete.pattern_discovery import discover_patterns_step
        
        # Create minimal mock context
        class MockContext:
            def __init__(self):
                self._clients = {}
                self.config = type('Config', (), {'config_path': 'test_config.json'})()
            
            def set_shared_value(self, key, value):
                pass
        
        mock_context = MockContext()
        mock_step = None
        
        discovery_result = await discover_patterns_step(
            mock_context, 
            mock_step, 
            database_name='postgres_air',
            repo_owner='bprzybys-nc',
            repo_name='postgres-sample-dbs'
        )
        
        print(f"   ✅ Pattern discovery mock result: {discovery_result.get('discovery_strategy', 'unknown')} - {discovery_result.get('matched_files', 0)} matches")
        
        return True
        
    except Exception as e:
        print(f"❌ Component testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 MOCK WORKFLOW TESTING")
    print("=" * 60)
    
    # Test individual components first
    components_ok = await test_individual_components()
    
    if components_ok:
        print("\n" + "=" * 60)
        print("🚀 FULL WORKFLOW TESTING")
        print("=" * 60)
        
        # Test full workflow
        workflow_result = await test_mocked_workflow()
        
        if workflow_result:
            print("\n✅ All tests passed! Mocked workflow is working correctly.")
            print("\n📋 HACK/TODO Summary:")
            print("  1. RepomixMCPClient.pack_remote_repository() - MOCKED ✅")
            print("  2. PatternDiscoveryEngine.analyze_repository_structure() - MOCKED ✅") 
            print("  3. discover_patterns_step() - MOCKED ✅")
            print("\n🔄 To restore real functionality:")
            print("  - Set USE_MOCK_PACK = False in clients/repomix.py")
            print("  - Set USE_MOCK_DISCOVERY = False in concrete/pattern_discovery.py")
            print("  - Uncomment real logic in analyze_repository_structure()")
        else:
            print("\n❌ Workflow test failed!")
    else:
        print("\n❌ Component tests failed!")

if __name__ == "__main__":
    asyncio.run(main()) 