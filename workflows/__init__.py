"""
GraphMCP Workflows Package

Provides workflow building capabilities for creating complex multi-step
MCP-based workflows with a fluent builder interface.

This package follows GraphMCP's core design principles:
- Never store actual mcp_use objects
- Always ensure serializability 
- Use proven patterns from working implementations
- Provide comprehensive error handling
- Enable resource cleanup
"""

from .builder import WorkflowBuilder
from .models import (
    WorkflowStep,
    WorkflowResult,
    WorkflowConfig,
    WorkflowExecutionContext,
)

__all__ = [
    "WorkflowBuilder",
    "WorkflowStep",
    "WorkflowResult", 
    "WorkflowConfig",
    "WorkflowExecutionContext",
] 