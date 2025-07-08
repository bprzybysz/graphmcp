#!/usr/bin/env python3
"""
Test script for GraphMCP package

This script validates that the new graphmcp package works correctly
and can be used as a drop-in replacement for DirectMCPClient.
"""

import asyncio
import sys
from pathlib import Path

# Test the new graphmcp package
try:
    from workbench.graphmcp import MultiServerMCPClient, GitHubMCPClient, Context7MCPClient
    print("✅ Successfully imported graphmcp components")
except ImportError as e:
    print(f"❌ Failed to import graphmcp: {e}")
    sys.exit(1)

# Test the migration compatibility layer
try:
    from workbench.db_decommission_workflow.migrate_to_graphmcp import DirectMCPClient
    print("✅ Successfully imported migration compatibility layer")
except ImportError as e:
    print(f"❌ Failed to import compatibility layer: {e}")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic functionality without making actual MCP calls."""
    
    config_path = "graphmcp/ovora_mcp_config.json"
    
    if not Path(config_path).exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        # Test MultiServerMCPClient initialization
        client = MultiServerMCPClient.from_config_file(config_path)
        print("✅ MultiServerMCPClient initialization successful")
        
        # Test configuration access
        config = client.get_config()
        servers = client.list_servers()
        print(f"✅ Configuration loaded: {len(servers)} servers found")
        
        # Test specialized client initialization
        github_client = GitHubMCPClient(config_path)
        context7_client = Context7MCPClient(config_path)
        print("✅ Specialized clients initialized successfully")
        
        # Test compatibility layer
        compat_client = DirectMCPClient.from_config_file(config_path)
        print("✅ Compatibility layer works correctly")
        
        # Test that interfaces match
        assert hasattr(compat_client, 'call_github_tools')
        assert hasattr(compat_client, 'call_context7_tools')
        assert hasattr(compat_client, 'get_file_contents')
        assert hasattr(compat_client, 'search_code')
        print("✅ All expected methods are available")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def test_imports():
    """Test that all expected imports work correctly."""
    
    try:
        # Test main package imports
        from workbench.graphmcp import (
            MultiServerMCPClient,
            GitHubMCPClient,
            Context7MCPClient,
            FilesystemMCPClient,
            BrowserMCPClient,
            BaseMCPClient,
            MCPConfigManager,
            MCPSessionManager,
            ensure_serializable,
            GitHubSearchResult,
            Context7Documentation,
            FilesystemScanResult,
            MCPUtilityError,
            MCPSessionError,
        )
        print("✅ All main package imports successful")
        
        # Test utils imports
        from workbench.graphmcp.utils import (
            MCPConfigManager,
            MCPSessionManager,
            MCPRetryHandler,
        )
        print("✅ Utils package imports successful")
        
        # Test clients imports
        from workbench.graphmcp.clients import (
            BaseMCPClient,
            GitHubMCPClient,
            Context7MCPClient,
        )
        print("✅ Clients package imports successful")
        
        # Test composite imports
        from workbench.graphmcp.composite import MultiServerMCPClient
        print("✅ Composite package imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_data_models():
    """Test that data models are properly serializable."""
    
    try:
        import pickle
        import time
        
        from workbench.graphmcp import (
            GitHubSearchResult,
            Context7Documentation, 
            FilesystemScanResult,
        )
        
        # Test GitHubSearchResult
        github_result = GitHubSearchResult(
            repository_url="https://github.com/test/repo",
            files_found=["README.md", "package.json"],
            matches=[{"file": "README.md", "content": "test"}],
            search_query="test query"
        )
        
        pickle.dumps(github_result)
        print("✅ GitHubSearchResult is serializable")
        
        # Test Context7Documentation
        context7_result = Context7Documentation(
            library_id="/test/lib",
            topic="testing",
            content_sections=["section 1", "section 2"],
            summary="test documentation"
        )
        
        pickle.dumps(context7_result)
        print("✅ Context7Documentation is serializable")
        
        # Test FilesystemScanResult
        filesystem_result = FilesystemScanResult(
            base_path="/test/path",
            pattern="*.py",
            files_found=["test.py", "main.py"],
            matches=[{"file": "test.py", "type": "match"}]
        )
        
        pickle.dumps(filesystem_result)
        print("✅ FilesystemScanResult is serializable")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model serialization test failed: {e}")
        return False


async def main():
    """Run all tests."""
    
    print("Testing GraphMCP Package")
    print("=" * 40)
    
    # Test imports
    print("\n1. Testing imports...")
    imports_ok = test_imports()
    
    # Test data models
    print("\n2. Testing data models...")
    models_ok = test_data_models()
    
    # Test basic functionality
    print("\n3. Testing basic functionality...")
    basic_ok = await test_basic_functionality()
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"  Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"  Data Models: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"  Basic Functionality: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    
    all_passed = imports_ok and models_ok and basic_ok
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 GraphMCP package is ready for use!")
        print("   You can now replace DirectMCPClient imports with:")
        print("   from workbench.graphmcp import MultiServerMCPClient as DirectMCPClient")
    else:
        print("\n⚠️  Please fix the failing tests before using GraphMCP")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 