#!/usr/bin/env python3
"""
Simple test script to verify mocked components work correctly.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

async def test_repomix_mock():
    """Test RepomixMCPClient mock."""
    print("1️⃣ Testing RepomixMCPClient mock...")
    
    try:
        from clients.repomix import RepomixMCPClient
        
        client = RepomixMCPClient("test_config.json")
        result = await client.pack_remote_repository("https://github.com/bprzybys-nc/postgres-sample-dbs")
        
        print(f"   ✅ MOCK SUCCESS: {result.get('source', 'unknown')}")
        print(f"   📊 Files: {result.get('files_packed', 0)}")
        print(f"   📁 Output: {result.get('output_file', 'N/A')}")
        print(f"   💾 Size: {result.get('total_size', 0)} bytes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MOCK FAILED: {e}")
        return False

async def test_pattern_discovery_mock():
    """Test pattern discovery mock."""
    print("\n2️⃣ Testing pattern discovery mock...")
    
    try:
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
        
        result = await discover_patterns_step(
            mock_context, 
            mock_step, 
            database_name='postgres_air',
            repo_owner='bprzybys-nc',
            repo_name='postgres-sample-dbs'
        )
        
        print(f"   ✅ MOCK SUCCESS: {result.get('discovery_strategy', 'unknown')}")
        print(f"   📊 Files found: {result.get('total_files', 0)}")
        print(f"   🎯 Matches: {result.get('matched_files', 0)}")
        print(f"   📁 File types: {len(result.get('files_by_type', {}))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MOCK FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_analyze_repository_structure_mock():
    """Test analyze_repository_structure mock."""
    print("\n3️⃣ Testing analyze_repository_structure mock...")
    
    try:
        from concrete.pattern_discovery import PatternDiscoveryEngine
        
        engine = PatternDiscoveryEngine()
        result = await engine.analyze_repository_structure(
            repomix_client=None,  # Mock doesn't need real client
            repo_url="https://github.com/bprzybys-nc/postgres-sample-dbs",
            repo_owner="bprzybys-nc",
            repo_name="postgres-sample-dbs"
        )
        
        print(f"   ✅ MOCK SUCCESS: {result.get('source', 'unknown')}")
        print(f"   📊 Files found: {len(result.get('files', []))}")
        print(f"   📁 Total size: {result.get('total_size', 0)} bytes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MOCK FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_test_data():
    """Check if test data file exists."""
    print("\n📁 Checking test data availability...")
    
    test_data_file = Path("tests/data/postgres_sample_dbs_packed.xml")
    
    if test_data_file.exists():
        size = test_data_file.stat().st_size
        print(f"   ✅ Test data found: {test_data_file}")
        print(f"   📊 Size: {size:,} bytes ({size / 1024 / 1024:.1f} MB)")
        return True
    else:
        print(f"   ❌ Test data missing: {test_data_file}")
        return False

async def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 MOCK COMPONENTS TEST")
    print("=" * 60)
    
    # Check test data first
    data_ok = check_test_data()
    
    # Test individual components
    tests = [
        test_repomix_mock,
        test_pattern_discovery_mock,
        test_analyze_repository_structure_mock
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"📁 Test data: {'✅ Available' if data_ok else '❌ Missing'}")
    
    if passed == total and data_ok:
        print("\n🎉 ALL MOCKS WORKING CORRECTLY!")
        print("\n📋 HACK/TODO Summary:")
        print("  1. RepomixMCPClient.pack_remote_repository() - MOCKED ✅")
        print("  2. PatternDiscoveryEngine.analyze_repository_structure() - MOCKED ✅") 
        print("  3. discover_patterns_step() - MOCKED ✅")
        print("\n🔄 To restore real functionality:")
        print("  - Set USE_MOCK_PACK = False in clients/repomix.py")
        print("  - Set USE_MOCK_DISCOVERY = False in concrete/pattern_discovery.py")
        print("  - Uncomment real logic in analyze_repository_structure()")
        print("\n🚀 Ready to run mocked workflow!")
    else:
        print(f"\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 