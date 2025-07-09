"""
GraphMCP WorkflowBuilder Framework

A fluent builder for creating complex, multi-step, agentic workflows
that leverage multiple MCP servers.
"""

from __future__ import annotations
import logging
import time
import asyncio
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

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
                    step_result = await step.custom_function(context, step, **step.parameters)
                    results[step.id] = ensure_serializable(step_result)
                    context.set_shared_value(step.id, step_result) # Make result available in shared context
                    completed_count += 1
                else:
                    # Mock other step types
                    logger.info(f"Mock execution for step type {step.step_type}")
                    results[step.id] = {"status": "mocked_success", "step_type": step.step_type.name}
                    completed_count += 1
            except Exception as e:
                logger.error(f"Step {step.id} failed: {e}")
                results[step.id] = {"error": str(e)}
                failed_count += 1
                if self.config.stop_on_error:
                    break
        
        duration = time.time() - start_time
        success_rate = (completed_count / len(self.steps)) * 100 if self.steps else 100

        status = "completed" if failed_count == 0 else ("partial_success" if completed_count > 0 else "failed")

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
        self._config = WorkflowConfig(name=name, config_path=config_path, description=description)
        self._steps: List[WorkflowStep] = []

    def with_config(self, max_parallel_steps: int = 3, default_timeout: int = 120, stop_on_error: bool = False, default_retry_count: int = 2) -> WorkflowBuilder:
        """Configure workflow execution parameters."""
        self._config.max_parallel_steps = max_parallel_steps
        self._config.default_timeout = default_timeout
        self._config.stop_on_error = stop_on_error
        self._config.default_retry_count = default_retry_count
        return self

    def custom_step(self, step_id: str, name: str, func: Callable, 
                   description: str = "", parameters: Dict = None, 
                   depends_on: List[str] = None, timeout_seconds: int = None, 
                   retry_count: int = None, **kwargs) -> WorkflowBuilder:
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
            retry_count=retry_count or self._config.default_retry_count
        )
        self._steps.append(step)
        return self

    def repomix_pack_repo(self, step_id: str, repo_url: str, 
                         include_patterns: List[str] = None,
                         exclude_patterns: List[str] = None,
                         parameters: Dict = None, **kwargs) -> WorkflowBuilder:
        """Add a Repomix repository packing step."""
        async def step_func(context, step, **params):
            from clients import RepomixMCPClient
            client = context._clients.get('repomix') or RepomixMCPClient(context.config.config_path)
            context._clients['repomix'] = client
            return await client.pack_repository(
                params.get('repo_url', repo_url),
                params.get('include_patterns', include_patterns),
                params.get('exclude_patterns', exclude_patterns)
            )
        
        step_params = {
            "repo_url": repo_url,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns
        }
        if parameters:
            step_params.update(parameters)
        
        step = WorkflowStep(
            id=step_id,
            name=f"Pack Repo: {repo_url}",
            step_type=StepType.REPOMIX,
            custom_function=step_func,
            parameters=step_params,
            depends_on=kwargs.get('depends_on', []),
            timeout_seconds=kwargs.get('timeout_seconds', self._config.default_timeout),
            retry_count=kwargs.get('retry_count', self._config.default_retry_count)
        )
        self._steps.append(step)
        return self

    def github_analyze_repo(self, step_id: str, repo_url: str, 
                           parameters: Dict = None, **kwargs) -> WorkflowBuilder:
        """Add a GitHub repository analysis step."""
        async def step_func(context, step, **params):
            from clients import GitHubMCPClient
            client = context._clients.get('github') or GitHubMCPClient(context.config.config_path)
            context._clients['github'] = client
            return await client.analyze_repo_structure(params.get('repo_url', repo_url))

        step_params = {"repo_url": repo_url}
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Analyze Repo: {repo_url}",
            step_type=StepType.GITHUB,
            custom_function=step_func,
            parameters=step_params,
            depends_on=kwargs.get('depends_on', []),
            timeout_seconds=kwargs.get('timeout_seconds', self._config.default_timeout),
            retry_count=kwargs.get('retry_count', self._config.default_retry_count)
        )
        self._steps.append(step)
        return self

    def github_create_pr(self, step_id: str, title: str, head: str, base: str, 
                        body_template: str, parameters: Dict = None, **kwargs) -> WorkflowBuilder:
        """Add a GitHub pull request creation step."""
        async def step_func(context, step, **params):
            from clients import GitHubMCPClient
            client = context._clients.get('github') or GitHubMCPClient(context.config.config_path)
            context._clients['github'] = client
            # A real implementation would render the body_template with context
            body = params.get('body_template', body_template)
            return await client.create_pull_request(
                context.get_shared_value("repo_owner"),
                context.get_shared_value("repo_name"),
                params.get('title', title),
                params.get('head', head),
                params.get('base', base),
                body
            )

        step_params = {
            "title": title,
            "head": head,
            "base": base,
            "body_template": body_template
        }
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Create PR: {title}",
            step_type=StepType.GITHUB,
            custom_function=step_func,
            parameters=step_params,
            depends_on=kwargs.get('depends_on', []),
            timeout_seconds=kwargs.get('timeout_seconds', self._config.default_timeout),
            retry_count=kwargs.get('retry_count', self._config.default_retry_count)
        )
        self._steps.append(step)
        return self

    def slack_post(self, step_id: str, channel_id: str, text_or_fn: Union[str, Callable], 
                  parameters: Dict = None, **kwargs) -> WorkflowBuilder:
        """Add a Slack message posting step."""
        async def step_func(context, step, **params):
            from clients import SlackMCPClient
            client = context._clients.get('slack') or SlackMCPClient(context.config.config_path)
            context._clients['slack'] = client
            text_func = params.get('text_or_fn', text_or_fn)
            text = text_func(context) if callable(text_func) else text_func
            return await client.post_message(params.get('channel_id', channel_id), text)

        step_params = {
            "channel_id": channel_id,
            "text_or_fn": text_or_fn
        }
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name=f"Post to Slack: {channel_id}",
            step_type=StepType.SLACK,
            custom_function=step_func,
            parameters=step_params,
            depends_on=kwargs.get('depends_on', []),
            timeout_seconds=kwargs.get('timeout_seconds', self._config.default_timeout),
            retry_count=kwargs.get('retry_count', self._config.default_retry_count)
        )
        self._steps.append(step)
        return self
    
    def gpt_step(self, step_id: str, model: str, prompt: str, 
                parameters: Dict = None, **kwargs) -> WorkflowBuilder:
        """Add a GPT analysis step."""
        async def step_func(context, step, **params):
            # This would use an OpenAI client in a real implementation
            logger.info(f"Submitting to GPT model {params.get('model', model)} with prompt: {params.get('prompt', prompt)}")
            return {"summary": "This is a mock summary from GPT.", "model": params.get('model', model)}

        step_params = {
            "model": model,
            "prompt": prompt
        }
        if parameters:
            step_params.update(parameters)

        step = WorkflowStep(
            id=step_id,
            name="GPT Analysis",
            step_type=StepType.GPT,
            custom_function=step_func,
            parameters=step_params,
            depends_on=kwargs.get('depends_on', []),
            timeout_seconds=kwargs.get('timeout_seconds', self._config.default_timeout),
            retry_count=kwargs.get('retry_count', self._config.default_retry_count)
        )
        self._steps.append(step)
        return self

    def build(self) -> Workflow:
        """Build and return the configured workflow."""
        logger.info(f"Building workflow '{self._config.name}' with {len(self._steps)} steps.")
        return Workflow(self._config, self._steps) 