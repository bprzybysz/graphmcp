from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseWorkflowStep(ABC):
    """
    Abstract base class for a single step in a workflow.
    """

    def __init__(self, step_config: Dict[str, Any]):
        self.config = step_config

    @abstractmethod
    async def execute(self, workflow_context: Dict[str, Any]) -> Any:
        """
        Execute the logic for this workflow step.

        Args:
            workflow_context: A dictionary containing the shared workflow context.

        Returns:
            Any: The result of the step's execution.
        """
        pass

    @property
    def name(self) -> str:
        """The name of the step."""
        return self.config.get("name", self.__class__.__name__)
