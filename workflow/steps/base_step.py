from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseWorkflowStep(ABC):
    """
    Abstract base class for a single step in a workflow.
    """

    def __init__(self, step_config: Dict[str, Any]):
        self.config = step_config

    @abstractmethod
    async def execute(self, context: Any, step: Any, **params) -> Any:
        """
        Execute the logic for this workflow step.

        Args:
            context: The shared workflow context object.
            step: The workflow step object being executed.
            params: The parameters for this step.

        Returns:
            Any: The result of the step's execution.
        """

    @property
    def name(self) -> str:
        """The name of the step."""
        return self.config.get("name", self.__class__.__name__)
