"""
GraphMCP WorkflowBuilder Framework

A fluent builder for creating complex, multi-step, agentic workflows
that leverage multiple MCP servers.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union

from utils import ensure_serializable

logger = logging.getLogger(__name__)


class StepType(Enum):
    CUSTOM = auto()
    GITHUB = auto()
    CONTEXT7 = auto()
    FILESYSTEM = auto()
    BROWSER = auto()
    REPOMIX = auto()
    SLACK = auto()
    GPT = auto()


@dataclass
class WorkflowStep:
    id: str
    name: str
    step_type: StepType
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 120
    retry_count: int = 3
    server_name: Optional[str] = None
    tool_name: Optional[str] = None
    custom_function: Optional[Callable] = None

    # Add serialization helper for functions
    function: Optional[Callable] = field(default=None, repr=False)

    def __post_init__(self):
        # Alias for backward compatibility
        if self.custom_function and not self.function:
            self.function = self.custom_function
        elif self.function and not self.custom_function:
            self.custom_function = self.function


@dataclass
class WorkflowResult:
    status: str
    duration_seconds: float
    success_rate: float
    step_results: Dict[str, Any]
    steps_completed: int
    steps_failed: int

    def get_step_result(self, step_id: str, default: Any = None) -> Any:
        return self.step_results.get(step_id, default)


@dataclass
class WorkflowConfig:
    name: str
    config_path: str
    description: str = ""
    max_parallel_steps: int = 3
    default_timeout: int = 120
    stop_on_error: bool = False
    default_retry_count: int = 2


class WorkflowContext:
    """Workflow execution context for sharing data between steps."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self._shared_context = {}
        self._clients = {}

    def set_shared_value(self, key: str, value: Any):
        """Set a shared value accessible to all workflow steps."""
        self._shared_context[key] = ensure_serializable(value)

    def get_shared_value(self, key: str, default: Any = None) -> Any:
        """Get a shared value from the workflow context."""
        return self._shared_context.get(key, default)

    def get_step_result(self, step_id: str, default: Any = None) -> Any:
        """Get a step result from the shared context (alias for get_shared_value)."""
        return self.get_shared_value(step_id, default)


class Workflow:
    """Represents a compiled, executable workflow."""

    def __init__(self, config: WorkflowConfig, steps: List[WorkflowStep]):
        self.config = config
        self.steps = steps

    async def execute(self) -> WorkflowResult:
        """Execute the workflow with proper context management."""
        logger.info(f"Executing workflow: {self.config.name}")
        start_time = time.time()
        results = {}
        completed_count = 0
        failed_count = 0

        # Create workflow context
        context = WorkflowContext(self.config)

        # Simplified sequential execution for demonstration
        for step in self.steps:
            logger.info(f"Executing step: {step.id} ({step.name})")
            try:
                if step.custom_function:
                    # Pass parameters correctly to the function
                    step_result = await step.custom_function(
                        context, step, **step.parameters
                    )
                    results[step.id] = ensure_serializable(step_result)
                    context.set_shared_value(
                        step.id, step_result
                    )  # Make result available in shared context
                    completed_count += 1
                else:
                    # Execute MCP tool steps
                    if step.server_name and step.tool_name:
                        try:
                            # Dynamically import the client based on server_name
                            if step.server_name == "ovr_github":
                                from clients import GitHubMCPClient as ClientClass
                            elif step.server_name == "ovr_repomix":
                                from clients import RepomixMCPClient as ClientClass
                            elif (
                                step.server_name == "ovr_slack"
                            ):  # Temporarily re-add Slack for completeness, will skip it in db_decommission.py
                                from clients import SlackMCPClient as ClientClass
                            else:
                                raise ValueError(
                                    f"Unsupported server name: {step.server_name}"
                                )

                            client = context._clients.get(
                                step.server_name
                            ) or ClientClass(context.config.config_path)
                            context._clients[step.server_name] = client

                            logger.info(
                                f"Calling MCP tool '{step.tool_name}' on server '{step.server_name}' for step '{step.id}'"
                            )
                            tool_result = await client.call_tool_with_retry(
                                step.tool_name,
                                step.parameters,
                                retry_count=step.retry_count,
                            )
                            results[step.id] = ensure_serializable(tool_result)
                            context.set_shared_value(step.id, tool_result)
                            completed_count += 1
                        except Exception as client_e:
                            logger.error(
                                f"MCP client call failed for step {step.id} ({step.name}): {client_e}"
                            )
                            results[step.id] = {"error": str(client_e)}
                            failed_count += 1
                            if self.config.stop_on_error:
                                break
                    else:
                        # Fallback for unhandled step types (should not happen if all are covered)
                        logger.warning(
                            f"Unhandled step type: {step.step_type.name} for step {step.id}. Mocking execution."
                        )
                        results[step.id] = {
                            "status": "mocked_unhandled",
                            "step_type": step.step_type.name,
                        }
                        completed_count += 1
            except Exception as e:
                logger.error(f"Step {step.id} failed: {e}")
                results[step.id] = {"error": str(e)}
                failed_count += 1
                if self.config.stop_on_error:
                    break

        duration = time.time() - start_time
        success_rate = (completed_count / len(self.steps)) * 100 if self.steps else 100

        status = (
            "completed"
            if failed_count == 0
            else ("partial_success" if completed_count > 0 else "failed")
        )

        # Cleanup: Close all cached MCP clients to prevent memory leaks
        for client_name, client in context._clients.items():
            try:
                await client.close()
                logger.debug(f"Closed MCP client: {client_name}")
            except Exception as e:
                logger.warning(f"Error closing MCP client {client_name}: {e}")

        return WorkflowResult(
            status=status,
            duration_seconds=duration,
            success_rate=success_rate,
            step_results=results,
            steps_completed=completed_count,
            steps_failed=failed_count,
        )


class WorkflowBuilder:
    """A fluent builder for constructing GraphMCP workflows."""

    def __init__(self, name: str, config_path: str, description: str = ""):
        self._config = WorkflowConfig(
            name=name, config_path=config_path, description=description
        )
        self._steps: List[WorkflowStep] = []

    def with_config(
        self,
        max_parallel_steps: int = 3,
        default_timeout: int = 120,
        stop_on_error: bool = False,
        default_retry_count: int = 2,
    ) -> WorkflowBuilder:
        """Configure workflow execution parameters."""
        self._config.max_parallel_steps = max_parallel_steps
        self._config.default_timeout = default_timeout
        self._config.stop_on_error = stop_on_error
        self._config.default_retry_count = default_retry_count
        return self

    def custom_step(
        self,
        step_id: str,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Optional[Dict] = None,
        depends_on: Optional[List[str]] = None,
        timeout_seconds: Optional[int] = None,
        retry_count: Optional[int] = None,
        **kwargs,
    ) -> WorkflowBuilder:
        """Add a custom step with a user-defined function."""
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.CUSTOM,
            custom_function=func,
            parameters=parameters or {},
            depends_on=depends_on or [],
            timeout_seconds=timeout_seconds or self._config.default_timeout,
            retry_count=retry_count or self._config.default_retry_count,
        )
        self._steps.append(step)
        return self

    def repomix_pack_repo(
        self,
        step_id: str,
        repo_url: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        parameters: Optional[Dict] = None,
        **kwargs,
    ) -> WorkflowBuilder:
        """Add a Repomix repository packing step."""
        # Remove the async def step_func as it will now be handled by Workflow.execute

        step_params = {
            "repo_url": repo_url,
            "include_patterns": include_patterns or [],
            "exclude_patterns": exclude_patterns or [],
        }
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Pack Repo: {repo_url}",
            step_type=StepType.REPOMIX,
            server_name="ovr_repomix",  # Set server_name
            tool_name="pack_remote_repository",  # Set tool_name
            parameters=step_params,
            depends_on=kwargs.get("depends_on", []),
            timeout_seconds=kwargs.get("timeout_seconds", self._config.default_timeout),
            retry_count=kwargs.get("retry_count", self._config.default_retry_count),
        )
        self._steps.append(step)
        return self

    def github_analyze_repo(
        self, step_id: str, repo_url: str, parameters: Optional[Dict] = None, **kwargs
    ) -> WorkflowBuilder:
        """Add a GitHub repository analysis step."""
        # Remove the async def step_func

        step_params = {"repo_url": repo_url}
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Analyze Repo: {repo_url}",
            step_type=StepType.GITHUB,
            server_name="ovr_github",  # Set server_name
            tool_name="analyze_repo_structure",  # Set tool_name
            parameters=step_params,
            depends_on=kwargs.get("depends_on", []),
            timeout_seconds=kwargs.get("timeout_seconds", self._config.default_timeout),
            retry_count=kwargs.get("retry_count", self._config.default_retry_count),
        )
        self._steps.append(step)
        return self

    def github_create_pr(
        self,
        step_id: str,
        title: str,
        head: str,
        base: str,
        body_template: str,
        parameters: Optional[Dict] = None,
        **kwargs,
    ) -> WorkflowBuilder:
        """Add a GitHub pull request creation step."""
        # Remove the async def step_func

        step_params = {
            "title": title,
            "head": head,
            "base": base,
            "body_template": body_template,
        }
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Create PR: {title}",
            step_type=StepType.GITHUB,
            server_name="ovr_github",  # Set server_name
            tool_name="create_pull_request",  # Set tool_name
            parameters=step_params,
            depends_on=kwargs.get("depends_on", []),
            timeout_seconds=kwargs.get("timeout_seconds", self._config.default_timeout),
            retry_count=kwargs.get("retry_count", self._config.default_retry_count),
        )
        self._steps.append(step)
        return self

    def slack_post(
        self,
        step_id: str,
        channel_id: str,
        text_or_fn: Union[str, Callable],
        parameters: Optional[Dict] = None,
        **kwargs,
    ) -> WorkflowBuilder:
        """Add a Slack message posting step. Supports both text strings and dynamic text functions."""
        step_params = {"channel_id": channel_id, "text_or_fn": text_or_fn}
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Slack Post: {channel_id}",
            step_type=StepType.SLACK,
            server_name="ovr_slack",
            tool_name="slack_post_message",  # Corrected tool name
            parameters=step_params,
            depends_on=kwargs.get("depends_on", []),
            timeout_seconds=kwargs.get("timeout_seconds", self._config.default_timeout),
            retry_count=kwargs.get("retry_count", self._config.default_retry_count),
        )
        self._steps.append(step)
        return self

    def gpt_step(
        self,
        step_id: str,
        model: str,
        prompt: str,
        parameters: Optional[Dict] = None,
        **kwargs,
    ) -> WorkflowBuilder:
        """Add a GPT analysis step."""

        async def step_func(context, step, **params):
            # This would use an OpenAI client in a real implementation
            logger.info(
                f"Submitting to GPT model {params.get('model', model)} with prompt: {params.get('prompt', prompt)}"
            )
            return {
                "summary": "This is a mock summary from GPT.",
                "model": params.get("model", model),
            }

        step_params = {"model": model, "prompt": prompt}
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name="GPT Analysis",
            step_type=StepType.GPT,
            custom_function=step_func,
            parameters=step_params,
            depends_on=kwargs.get("depends_on", []),
            timeout_seconds=kwargs.get("timeout_seconds", self._config.default_timeout),
            retry_count=kwargs.get("retry_count", self._config.default_retry_count),
        )
        self._steps.append(step)
        return self

    def build(self) -> Workflow:
        """Build and return the configured workflow."""
        logger.info(
            f"Building workflow '{self._config.name}' with {len(self._steps)} steps."
        )
        return Workflow(self._config, self._steps)
