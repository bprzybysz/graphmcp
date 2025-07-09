"""
GraphMCP: A framework for building complex, multi-server agentic workflows.
"""

from .clients import (
    BaseMCPClient,
    GitHubMCPClient,
    Context7MCPClient, 
    FilesystemMCPClient,
    BrowserMCPClient,
    RepomixMCPClient,
    SlackMCPClient,
)

from .workflows import (
    WorkflowBuilder,
    Workflow,
    WorkflowStep,
    WorkflowResult,
    WorkflowConfig,
    StepType,
)

__all__ = [
    # Clients
    "BaseMCPClient",
    "GitHubMCPClient",
    "Context7MCPClient", 
    "FilesystemMCPClient",
    "BrowserMCPClient",
    "RepomixMCPClient",
    "SlackMCPClient",
    # Workflows
    "WorkflowBuilder",
    "Workflow",
    "WorkflowStep",
    "WorkflowResult",
    "WorkflowConfig",
    "StepType",
] 