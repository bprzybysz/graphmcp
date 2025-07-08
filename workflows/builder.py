"""
Workflow Builder

Provides a fluent interface for building complex MCP workflows using the builder pattern.
This follows GraphMCP's design principles and provides type-safe workflow construction.

Example usage:
    workflow = (WorkflowBuilder("repo-analysis", "config.json")
        .github_analyze_repo("analyze", "https://github.com/facebook/react")
        .context7_get_docs("get_react_docs", "/react/docs", topic="hooks", depends_on=["analyze"])
        .conditional("check_typescript", "len(analyze.tech_stack) > 2", depends_on=["analyze"])
        .github_search_code("find_types", "*.ts interface", depends_on=["check_typescript"])
        .build())
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .models import (
    StepFunction,
    StepType,
    WorkflowConfig,
    WorkflowExecutionContext,
    WorkflowResult,
    WorkflowStep,
)
from ..utils import MCPConfigManager, ensure_serializable

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """
    Builder for creating complex MCP workflows with a fluent interface.
    
    This class follows the builder pattern to provide a clean, readable
    way to construct multi-step workflows that use various MCP servers.
    
    Key features:
    - Fluent interface with method chaining
    - Type-safe step configuration
    - Dependency management between steps
    - Built-in retry and error handling
    - Serialization-safe for LangGraph integration
    """

    def __init__(self, name: str, config_path: str, description: str = ""):
        """
        Initialize workflow builder.
        
        Args:
            name: Name of the workflow
            config_path: Path to MCP configuration file
            description: Optional description of the workflow
        """
        self.config = WorkflowConfig(
            name=name,
            description=description,
            config_path=config_path
        )
        self._steps: List[WorkflowStep] = []
        self._step_counter = 0
        
        # Validate config file exists and is valid
        self._config_manager = MCPConfigManager.from_file(config_path)
        config_status = self._config_manager.validate_config()
        if not config_status.is_valid:
            raise ValueError(f"Invalid MCP config: {config_status.validation_errors}")
        
        logger.info(f"Initialized WorkflowBuilder: {name}")

    def _generate_step_id(self, base_name: str) -> str:
        """Generate unique step ID."""
        self._step_counter += 1
        return f"{base_name}_{self._step_counter}"

    def _add_step(self, step: WorkflowStep) -> "WorkflowBuilder":
        """Add a step to the workflow and return self for chaining."""
        # Validate dependencies exist
        for dep in step.depends_on:
            if not any(s.id == dep for s in self._steps):
                raise ValueError(f"Step dependency '{dep}' not found")
        
        self._steps.append(step)
        logger.debug(f"Added step: {step.id} ({step.step_type.value})")
        return self

    # =================================================================
    # GitHub Operations
    # =================================================================

    def github_analyze_repo(
        self,
        step_id: str,
        repo_url: str,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add GitHub repository analysis step.
        
        Args:
            step_id: Unique identifier for this step
            repo_url: GitHub repository URL to analyze
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.GITHUB_ANALYSIS,
            name=f"Analyze GitHub Repository: {repo_url}",
            server_name="github",
            tool_name="analyze_repository",
            parameters={"repo_url": repo_url},
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    def github_search_code(
        self,
        step_id: str,
        query: str,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add GitHub code search step.
        
        Args:
            step_id: Unique identifier for this step
            query: Search query
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.GITHUB_SEARCH,
            name=f"Search GitHub Code: {query}",
            server_name="github",
            tool_name="search_code",
            parameters={"query": query},
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    def github_get_file(
        self,
        step_id: str,
        owner: str,
        repo: str,
        path: str,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add GitHub file reading step.
        
        Args:
            step_id: Unique identifier for this step
            owner: Repository owner
            repo: Repository name
            path: File path
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.GITHUB_FILE_READ,
            name=f"Read GitHub File: {owner}/{repo}/{path}",
            server_name="github",
            tool_name="get_file_contents",
            parameters={"owner": owner, "repo": repo, "path": path},
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    # =================================================================
    # Context7 Operations
    # =================================================================

    def context7_search(
        self,
        step_id: str,
        query: str,
        library_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add Context7 documentation search step.
        
        Args:
            step_id: Unique identifier for this step
            query: Search query
            library_id: Optional library ID to search within
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        params = {"query": query}
        if library_id:
            params["library_id"] = library_id
            
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.CONTEXT7_SEARCH,
            name=f"Search Context7: {query}",
            server_name="context7",
            tool_name="search_documentation",
            parameters=params,
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    def context7_get_docs(
        self,
        step_id: str,
        library_id: str,
        topic: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add Context7 library documentation retrieval step.
        
        Args:
            step_id: Unique identifier for this step
            library_id: Library ID to get documentation for
            topic: Optional specific topic to focus on
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        params = {"library_id": library_id}
        if topic:
            params["topic"] = topic
            
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.CONTEXT7_DOCS,
            name=f"Get Context7 Docs: {library_id}",
            server_name="context7",
            tool_name="get_library_docs",
            parameters=params,
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    # =================================================================
    # Filesystem Operations
    # =================================================================

    def filesystem_scan(
        self,
        step_id: str,
        pattern: str,
        base_path: str = ".",
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add filesystem scanning step.
        
        Args:
            step_id: Unique identifier for this step
            pattern: File pattern to search for
            base_path: Base directory to scan
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.FILESYSTEM_SCAN,
            name=f"Scan Filesystem: {pattern}",
            server_name="filesystem",
            tool_name="search_files",
            parameters={"pattern": pattern, "base_path": base_path},
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    # =================================================================
    # Browser Operations
    # =================================================================

    def browser_navigate(
        self,
        step_id: str,
        url: str,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add browser navigation step.
        
        Args:
            step_id: Unique identifier for this step
            url: URL to navigate to
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.BROWSER_NAVIGATE,
            name=f"Navigate to: {url}",
            server_name="browser",
            tool_name="navigate_to_url",
            parameters={"url": url},
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    # =================================================================
    # Control Flow Operations
    # =================================================================

    def conditional(
        self,
        step_id: str,
        condition: str,
        depends_on: Optional[List[str]] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add conditional step that evaluates an expression.
        
        Args:
            step_id: Unique identifier for this step
            condition: Python expression to evaluate
            depends_on: List of step IDs this step depends on
            **kwargs: Additional step configuration
        """
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.CONDITIONAL,
            name=f"Conditional: {condition}",
            condition=condition,
            depends_on=depends_on or [],
            **kwargs
        )
        return self._add_step(step)

    def custom_step(
        self,
        step_id: str,
        name: str,
        step_function: StepFunction,
        parameters: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Add custom step with user-defined function.
        
        Args:
            step_id: Unique identifier for this step
            name: Human-readable name for the step
            step_function: Function to execute (must be serializable)
            parameters: Parameters to pass to the function
            depends_on: List of step IDs this step depends on
            condition: Optional condition expression
            **kwargs: Additional step configuration
        """
        # Validate that function is serializable
        ensure_serializable(step_function)
        
        step = WorkflowStep(
            id=step_id,
            step_type=StepType.CUSTOM,
            name=name,
            parameters={
                "function": step_function,
                "params": parameters or {}
            },
            depends_on=depends_on or [],
            condition=condition,
            **kwargs
        )
        return self._add_step(step)

    # =================================================================
    # Configuration Methods
    # =================================================================

    def with_config(
        self,
        max_parallel_steps: Optional[int] = None,
        default_timeout: Optional[int] = None,
        stop_on_error: Optional[bool] = None,
        default_retry_count: Optional[int] = None,
        **kwargs
    ) -> "WorkflowBuilder":
        """
        Update workflow configuration.
        
        Args:
            max_parallel_steps: Maximum number of parallel steps
            default_timeout: Default timeout for steps
            stop_on_error: Whether to stop workflow on first error
            default_retry_count: Default retry count for failed steps
            **kwargs: Additional configuration options
        """
        if max_parallel_steps is not None:
            self.config.max_parallel_steps = max_parallel_steps
        if default_timeout is not None:
            self.config.default_timeout = default_timeout
        if stop_on_error is not None:
            self.config.stop_on_error = stop_on_error
        if default_retry_count is not None:
            self.config.default_retry_count = default_retry_count
            
        # Update any additional config options
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        return self

    # =================================================================
    # Build Methods
    # =================================================================

    def build(self) -> "Workflow":
        """
        Build the workflow and return executable workflow object.
        
        Returns:
            Workflow object ready for execution
        """
        if not self._steps:
            raise ValueError("Cannot build empty workflow")
        
        # Validate workflow structure
        self._validate_workflow()
        
        # Create workflow instance
        return Workflow(
            config=self.config,
            steps=self._steps.copy(),
            config_manager=self._config_manager
        )

    def _validate_workflow(self) -> None:
        """Validate workflow structure and dependencies."""
        step_ids = {step.id for step in self._steps}
        
        # Check for duplicate step IDs
        if len(step_ids) != len(self._steps):
            raise ValueError("Duplicate step IDs found")
        
        # Check all dependencies exist
        for step in self._steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(f"Step '{step.id}' depends on unknown step '{dep}'")
        
        # Check for circular dependencies (simplified check)
        for step in self._steps:
            visited = set()
            self._check_circular_deps(step.id, visited, {})
    
    def _check_circular_deps(self, step_id: str, visited: set, dep_map: dict) -> None:
        """Check for circular dependencies."""
        if not dep_map:
            # Build dependency map
            for step in self._steps:
                dep_map[step.id] = step.depends_on
        
        if step_id in visited:
            raise ValueError(f"Circular dependency detected involving step '{step_id}'")
        
        visited.add(step_id)
        for dep in dep_map.get(step_id, []):
            self._check_circular_deps(dep, visited, dep_map)
        visited.remove(step_id)


class Workflow:
    """
    Executable workflow created by WorkflowBuilder.
    
    This class handles the actual execution of workflow steps,
    managing MCP clients, dependencies, and error handling.
    """

    def __init__(self, config: WorkflowConfig, steps: List[WorkflowStep], config_manager: MCPConfigManager):
        """
        Initialize workflow for execution.
        
        Args:
            config: Workflow configuration
            steps: List of workflow steps
            config_manager: MCP configuration manager
        """
        self.config = config
        self.steps = {step.id: step for step in steps}
        self.config_manager = config_manager
        
        # Execution state
        self._execution_context: Optional[WorkflowExecutionContext] = None
        
        logger.info(f"Created workflow '{config.name}' with {len(steps)} steps")

    async def execute(self) -> WorkflowResult:
        """
        Execute the workflow and return results.
        
        Returns:
            WorkflowResult containing execution results and metadata
        """
        from .engine import WorkflowEngine
        
        # Create execution context
        self._execution_context = WorkflowExecutionContext(config=self.config)
        
        # Create and run workflow engine
        engine = WorkflowEngine(self.config_manager)
        result = await engine.execute_workflow(
            steps=list(self.steps.values()),
            context=self._execution_context
        )
        
        return result

    def get_step_dependencies(self, step_id: str) -> List[str]:
        """Get dependencies for a specific step."""
        step = self.steps.get(step_id)
        return step.depends_on if step else []

    def get_execution_order(self) -> List[List[str]]:
        """
        Get execution order as list of parallel batches.
        
        Returns:
            List where each element is a list of step IDs that can run in parallel
        """
        # Simple topological sort to determine execution order
        remaining = set(self.steps.keys())
        completed = set()
        batches = []
        
        while remaining:
            # Find steps that can run (all dependencies completed)
            ready = []
            for step_id in remaining:
                step = self.steps[step_id]
                if all(dep in completed for dep in step.depends_on):
                    ready.append(step_id)
            
            if not ready:
                raise ValueError("Circular dependency or missing dependency detected")
            
            batches.append(ready)
            for step_id in ready:
                remaining.remove(step_id)
                completed.add(step_id)
        
        return batches

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Workflow(name='{self.config.name}', steps={len(self.steps)})" 