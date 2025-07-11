"""Structured logging for MCP server workflow tracking."""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog


def configure_logging(log_level: str = "INFO", structured: bool = True) -> None:
    """Configure structured logging for the application."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    if structured:
        # Configure structured logging with timestamps and context
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                (
                    structlog.dev.ConsoleRenderer()
                    if sys.stdout.isatty()
                    else structlog.processors.JSONRenderer()
                ),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper())
            ),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Use simple console logging for development
        structlog.configure(
            processors=[structlog.dev.ConsoleRenderer()],
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


class WorkflowLogger:
    """Specialized logger for workflow events."""

    def __init__(self, workflow_id: str, session_id: str):
        self.workflow_id = workflow_id
        self.session_id = session_id
        self.logger = structlog.get_logger().bind(
            workflow_id=workflow_id, session_id=session_id
        )

    def log_step_start(
        self, step_id: str, step_name: str, input_data: Dict[str, Any]
    ) -> None:
        """Log workflow step start."""
        self.logger.info(
            "Workflow step started",
            step_id=step_id,
            step_name=step_name,
            input_data_keys=list(input_data.keys()),
            event_type="step_start",
        )

    def log_step_complete(
        self, step_id: str, step_name: str, output_data: Dict[str, Any]
    ) -> None:
        """Log workflow step completion."""
        self.logger.info(
            "Workflow step completed",
            step_id=step_id,
            step_name=step_name,
            output_data_keys=list(output_data.keys()),
            event_type="step_complete",
        )

    def log_step_error(
        self,
        step_id: str,
        step_name: str,
        error: str,
        error_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log workflow step error."""
        self.logger.error(
            "Workflow step failed",
            step_id=step_id,
            step_name=step_name,
            error_message=error,
            error_context=error_context or {},
            event_type="step_error",
        )

    def log_agent_action(
        self, agent_name: str, action: str, details: Dict[str, Any]
    ) -> None:
        """Log agent action."""
        self.logger.info(
            "Agent action executed",
            agent_name=agent_name,
            action=action,
            details=details,
            event_type="agent_action",
        )

    def log_context_update(self, key: str, value_type: str) -> None:
        """Log context update."""
        self.logger.info(
            "Context updated",
            context_key=key,
            value_type=value_type,
            event_type="context_update",
        )

    def log_streaming_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log streaming events."""
        self.logger.debug(
            "Streaming event",
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_workflow_complete(
        self, duration_seconds: float, steps_completed: int, total_steps: int
    ) -> None:
        """Log workflow completion."""
        self.logger.info(
            "Workflow completed",
            duration_seconds=duration_seconds,
            steps_completed=steps_completed,
            total_steps=total_steps,
            success_rate=steps_completed / total_steps if total_steps > 0 else 0,
            event_type="workflow_complete",
        )

    def log_workflow_error(self, error: str, step_failed: Optional[str] = None) -> None:
        """Log workflow-level error."""
        self.logger.error(
            "Workflow failed",
            error_message=error,
            step_failed=step_failed,
            event_type="workflow_error",
        )


class AgentLogger:
    """Specialized logger for agent events."""

    def __init__(self, agent_name: str, workflow_id: str):
        self.agent_name = agent_name
        self.workflow_id = workflow_id
        self.logger = structlog.get_logger().bind(
            agent_name=agent_name, workflow_id=workflow_id
        )

    def log_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """Log tool invocation."""
        self.logger.info(
            "Tool called",
            tool_name=tool_name,
            tool_input_keys=list(tool_input.keys()),
            event_type="tool_call",
        )

    def log_tool_result(
        self, tool_name: str, success: bool, result_summary: str
    ) -> None:
        """Log tool result."""
        self.logger.info(
            "Tool result",
            tool_name=tool_name,
            success=success,
            result_summary=result_summary,
            event_type="tool_result",
        )

    def log_llm_call(
        self, model_name: str, prompt_length: int, response_length: int
    ) -> None:
        """Log LLM interaction."""
        self.logger.info(
            "LLM call",
            model_name=model_name,
            prompt_length=prompt_length,
            response_length=response_length,
            event_type="llm_call",
        )

    def log_streaming_token(self, token: str, token_index: int) -> None:
        """Log streaming token (debug level)."""
        self.logger.debug(
            "Streaming token",
            token=token,
            token_index=token_index,
            event_type="streaming_token",
        )

    def log_memory_update(self, memory_type: str, operation: str) -> None:
        """Log memory operations."""
        self.logger.info(
            "Memory operation",
            memory_type=memory_type,
            operation=operation,
            event_type="memory_update",
        )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a bound logger instance."""
    return structlog.get_logger(name)


def create_workflow_logger(workflow_id: str, session_id: str) -> WorkflowLogger:
    """Create a workflow logger instance."""
    return WorkflowLogger(workflow_id, session_id)


def create_agent_logger(agent_name: str, workflow_id: str) -> AgentLogger:
    """Create an agent logger instance."""
    return AgentLogger(agent_name, workflow_id)
