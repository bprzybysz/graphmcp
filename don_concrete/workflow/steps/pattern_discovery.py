import os
import json
import asyncio
from typing import Any, Dict

from .base_step import BaseWorkflowStep

# HACK: Using a hardcoded path for mock data as per plan.
MOCK_DISCOVERY_PATH = "tests/data/discovery_outcome_context.json"

class PatternDiscoveryStep(BaseWorkflowStep):
    """
    A workflow step for discovering patterns in a processed repository.
    """

    async def execute(self, context: Any, step: Any, **params) -> Dict[str, Any]:
        """
        Executes the pattern discovery logic.

        If USE_MOCK_DISCOVERY is set, it returns a mock result.
        Otherwise, it simulates a real pattern discovery task.
        """
        use_mock = os.getenv("USE_MOCK_DISCOVERY", "true").lower() == "true"
        
        # This step depends on the output of the repository processing step
        repo_pack_path = context.get_step_result("repository_processing", {}).get("packed_repo_path")
        if not repo_pack_path:
            raise ValueError("Repository pack path not found in workflow context.")

        if use_mock:
            return await self._execute_mock(repo_pack_path)
        else:
            return await self._execute_real(repo_pack_path)

    async def _execute_mock(self, repo_pack_path: str) -> Dict[str, Any]:
        """
        Executes the mock version of the step.
        """
        print(f"Executing MOCK pattern discovery on: {repo_pack_path}")
        await asyncio.sleep(3)

        if not os.path.exists(MOCK_DISCOVERY_PATH):
             raise FileNotFoundError(f"Mock data not found at: {MOCK_DISCOVERY_PATH}")

        with open(MOCK_DISCOVERY_PATH, 'r') as f:
            discovery_data = json.load(f)

        return {
            "status": "mock_success",
            "source_pack": repo_pack_path,
            "discovery_result": discovery_data,
            "message": "Mock pattern discovery complete."
        }

    async def _execute_real(self, repo_pack_path: str) -> Dict[str, Any]:
        """
        Executes the real pattern discovery logic.
        
        TODO: Implement real pattern discovery.
        """
        print(f"Executing REAL pattern discovery on: {repo_pack_path}")
        await asyncio.sleep(10)

        return {
            "status": "real_success",
            "source_pack": repo_pack_path,
            "discovery_result": {"patterns_found": 100}, # Placeholder
            "message": "Real pattern discovery complete."
        }
