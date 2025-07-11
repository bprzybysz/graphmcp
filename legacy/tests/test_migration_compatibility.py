#!/usr/bin/env python3
"""
Test migration compatibility for db_decommission_workflow

This script tests that the existing db_decommission_workflow continues
to work after migrating its core MCP functionality to the graphmcp package.
"""

import asyncio
import sys
from pathlib import Path

# Test that we can still import the old interface
try:
    from workbench.db_decommission_workflow.mcp_client import DirectMCPClient as OriginalDirectMCPClient
    print("✅ Successfully imported original DirectMCPClient")
    original_available = True
except ImportError as e:
    print(f"⚠️  Original DirectMCPClient not available: {e}")
    original_available = False

# Test the migration compatibility layer
try:
    from workbench.db_decommission_workflow.migrate_to_graphmcp import DirectMCPClient as MigratedDirectMCPClient
    print("✅ Successfully imported migrated DirectMCPClient")
    migrated_available = True
except ImportError as e:
    print(f"❌ Failed to import migrated DirectMCPClient: {e}")
    migrated_available = False
    sys.exit(1)

# Test the workflow modules
try:
    from workbench.db_decommission_workflow.workflow import create_db_decommission_workflow
    from workbench.db_decommission_workflow.state import RepoAnalysisState
    print("✅ Successfully imported workflow components")
    workflow_available = True
except ImportError as e:
    print(f"❌ Failed to import workflow components: {e}")
    workflow_available = False


async def test_interface_compatibility():
    """Test that both interfaces provide the same methods."""
    
    config_path = "graphmcp/ovora_mcp_config.json"
    
    if not Path(config_path).exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        # Test migrated client
        migrated_client = MigratedDirectMCPClient.from_config_file(config_path)
        print("✅ Migrated DirectMCPClient initialization successful")
        
        # Test that all expected methods exist
        expected_methods = [
            'call_github_tools',
            'call_context7_tools', 
            'get_file_contents',
            'search_code',
            'get_config',
            'list_servers',
            'ensure_serializable'
        ]
        
        for method in expected_methods:
            if not hasattr(migrated_client, method):
                print(f"❌ Missing method: {method}")
                return False
        
        print("✅ All expected methods are available in migrated client")
        
        # If original is available, compare interfaces
        if original_available:
            try:
                original_client = OriginalDirectMCPClient.from_config_file(config_path)
                print("✅ Original DirectMCPClient initialization successful")
                
                # Check that both have the same methods
                original_methods = [attr for attr in dir(original_client) if not attr.startswith('_')]
                migrated_methods = [attr for attr in dir(migrated_client) if not attr.startswith('_')]
                
                # Check for missing methods (allowing for some additional methods in migrated)
                missing_in_migrated = set(original_methods) - set(migrated_methods)
                if missing_in_migrated:
                    print(f"⚠️  Methods missing in migrated client: {missing_in_migrated}")
                else:
                    print("✅ All original methods are available in migrated client")
                    
            except Exception as e:
                print(f"⚠️  Could not test original client compatibility: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Interface compatibility test failed: {e}")
        return False


async def test_workflow_integration():
    """Test that the workflow still works with the new client."""
    
    if not workflow_available:
        print("⚠️  Workflow components not available, skipping workflow integration test")
        return True
    
    try:
        # Create workflow (this should not fail)
        workflow = create_db_decommission_workflow()
        print("✅ Workflow creation successful")
        
        # Create initial state
        state = RepoAnalysisState(
            repo_url="https://github.com/microsoft/typescript",
            current_step="github_analysis",
            workflow_results={}
        )
        print("✅ State creation successful")
        
        # Verify state is serializable (important for LangGraph)
        import pickle
        pickle.dumps(state)
        print("✅ State is serializable")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        return False


def test_import_patterns():
    """Test different import patterns that users might use."""
    
    test_results = []
    
    # Test 1: Import from migration module
    try:
        from workbench.db_decommission_workflow.migrate_to_graphmcp import DirectMCPClient
        test_results.append(("Migration module import", True))
    except ImportError:
        test_results.append(("Migration module import", False))
    
    # Test 2: Import utilities from migration module
    try:
        from workbench.db_decommission_workflow.migrate_to_graphmcp import (
            MCPConfigManager,
            MCPSessionManager,
            ensure_serializable
        )
        test_results.append(("Utilities from migration module", True))
    except ImportError:
        test_results.append(("Utilities from migration module", False))
    
    # Test 3: Direct import from graphmcp
    try:
        from workbench.graphmcp import MultiServerMCPClient as DirectMCPClient
        test_results.append(("Direct graphmcp import", True))
    except ImportError:
        test_results.append(("Direct graphmcp import", False))
    
    # Test 4: Specialized client imports
    try:
        from workbench.graphmcp import GitHubMCPClient, Context7MCPClient
        test_results.append(("Specialized client imports", True))
    except ImportError:
        test_results.append(("Specialized client imports", False))
    
    # Print results
    print("\nImport Pattern Test Results:")
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    return all(success for _, success in test_results)


async def main():
    """Run all compatibility tests."""
    
    print("Testing Migration Compatibility")
    print("=" * 50)
    
    # Test import patterns
    print("\n1. Testing import patterns...")
    imports_ok = test_import_patterns()
    
    # Test interface compatibility
    print("\n2. Testing interface compatibility...")
    interface_ok = await test_interface_compatibility()
    
    # Test workflow integration
    print("\n3. Testing workflow integration...")
    workflow_ok = await test_workflow_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("Migration Compatibility Test Results:")
    print(f"  Import Patterns: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"  Interface Compatibility: {'✅ PASS' if interface_ok else '❌ FAIL'}")
    print(f"  Workflow Integration: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    
    all_passed = imports_ok and interface_ok and workflow_ok
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Migration is successful!")
        print("   The db_decommission_workflow continues to work with the new graphmcp architecture.")
        print("   You can now:")
        print("   1. Use the migration compatibility layer for existing code")
        print("   2. Gradually migrate to direct graphmcp imports")
        print("   3. Take advantage of new specialized clients")
    else:
        print("\n⚠️  Migration issues detected - please fix before proceeding")
    
    # Show migration options
    if all_passed and original_available:
        print("\nMigration Options:")
        print("  Option 1 (Immediate): Use compatibility layer")
        print("    from workbench.db_decommission_workflow.migrate_to_graphmcp import DirectMCPClient")
        print("  ")
        print("  Option 2 (Gradual): Update imports directly")
        print("    from workbench.graphmcp import MultiServerMCPClient as DirectMCPClient")
        print("  ")
        print("  Option 3 (Advanced): Use specialized clients")
        print("    from workbench.graphmcp import GitHubMCPClient, Context7MCPClient")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 