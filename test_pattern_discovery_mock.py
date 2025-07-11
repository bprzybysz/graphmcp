import pytest
import asyncio
import os
import logging
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock necessary modules before they are imported by the module under test
import sys
sys.modules['clients'] = MagicMock()
sys.modules['clients.github'] = MagicMock()
sys.modules['clients.repomix'] = MagicMock()

from concrete.pattern_discovery import discover_patterns_step, PatternDiscoveryEngine

# Mock classes for context and step
class MockStep:
    def __init__(self, name):
        self.name = name
        self.metadata = {}

class MockContext:
    def __init__(self):
        self._clients = {
            'ovr_repomix': MagicMock(),
            'ovr_github': MagicMock()
        }
        self.config = type('MockConfig', (), {'config_path': 'mcp_config.json'})()
        self._shared_values = {}

    def get_shared_value(self, key, default=None):
        return self._shared_values.get(key, default)

    def set_shared_value(self, key, value):
        self._shared_values[key] = value

@pytest.mark.asyncio
async def test_discover_patterns_step_mocked():
    """
    Tests the discover_patterns_step in mocked mode to ensure it returns
    the hardcoded realistic data for the 'postgres_air' database.
    """
    # 1. Setup
    context = MockContext()
    step = MockStep("pattern_discovery")

    # Ensure the mock flags are correctly set in the environment or module
    # For this test, we rely on the `USE_MOCK_DISCOVERY = True` flag in pattern_discovery.py
    logger.info("Testing discover_patterns_step with USE_MOCK_DISCOVERY = True")

    # 2. Execute
    # Call the step function we want to test
    result = await discover_patterns_step(
        context,
        step,
        database_name="postgres_air",
        repo_owner="bprzybys-nc",
        repo_name="postgres-sample-dbs"
    )

    # 3. Assert
    logger.info(f"Result from mocked step: {result}")
    
    assert result is not None, "The result should not be None"
    assert result['database_name'] == 'postgres_air', "Database name should match"
    assert result['repository'] == 'bprzybys-nc/postgres-sample-dbs', "Repository name should match"
    
    assert 'files' in result, "Result should contain a 'files' key"
    files = result['files']
    assert isinstance(files, list), "'files' should be a list"
    assert len(files) > 0, "Mocked result should contain at least one file"
    
    # Check for a specific file we know should be in the mock data
    expected_file_path = "config/database.yml"
    db_yml_file = next((f for f in files if f.get('path') == expected_file_path), None)
    
    assert db_yml_file is not None, f"Expected file '{expected_file_path}' not found in mock result"
    
    # Check the content of the file
    assert 'content' in db_yml_file, "File entry should have 'content'"
    assert 'postgres_air' in db_yml_file['content'], "File content should reference 'postgres_air'"
    assert 'patterns' in db_yml_file, "File entry should have 'patterns' key"
    assert len(db_yml_file['patterns']) > 0, "File patterns should not be empty"

    logger.info("✅ Test passed: Mocked discover_patterns_step returned expected data.")

if __name__ == "__main__":
    asyncio.run(test_discover_patterns_step_mocked()) 