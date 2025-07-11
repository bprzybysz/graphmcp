from .manager import WorkflowManager


class WorkflowManagerCompat:
    """
    Maintains backward compatibility with the legacy workflow system
    by wrapping the new WorkflowManager.
    """

    def __init__(self, new_manager: WorkflowManager):
        self._manager = new_manager

    async def start_workflow(self, *args, **kwargs) -> str:
        """
        Compatibility method to start a workflow.

        TODO: Translate legacy arguments to the new workflow configuration.
        """
        print("Using compatibility layer to start workflow.")

        # This is a placeholder. A real implementation would create
        # a config dictionary from the legacy arguments.
        new_config = {}

        return await self._manager.start_workflow(config=new_config)

    # TODO: Add other compatibility methods as needed to match the
    # legacy workflow manager's interface.
