import json
import os
from typing import Dict, Any

class MockDataProvider:
    """
    Provides access to mock data used in tests and mock workflow runs.
    """
    _cache: Dict[str, Any] = {}

    @staticmethod
    def _load_data(path: str, is_json: bool = True) -> Any:
        """Loads data from a file, with caching."""
        if path in MockDataProvider._cache:
            return MockDataProvider._cache[path]

        if not os.path.exists(path):
            raise FileNotFoundError(f"Mock data file not found: {path}")

        with open(path, 'r') as f:
            if is_json:
                data = json.load(f)
            else:
                data = f.read()
        
        MockDataProvider._cache[path] = data
        return data

    @staticmethod
    def get_discovery_outcome() -> Dict[str, Any]:
        """Returns the mock discovery outcome context."""
        return MockDataProvider._load_data("tests/data/discovery_outcome_context.json")

    @staticmethod
    def get_packed_repository() -> str:
        """Returns the content of the mock packed repository XML."""
        return MockDataProvider._load_data("tests/data/postgres_sample_dbs_packed.xml", is_json=False)
