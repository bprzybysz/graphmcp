# GraphMCP Workflow Builder

> **🏗️ Build complex MCP workflows with a fluent, type-safe interface**

The Workflow Builder provides a powerful, fluent interface for creating complex multi-step workflows that orchestrate multiple MCP servers. It follows the builder pattern to make workflow construction readable, maintainable, and type-safe.

## 🚀 Quick Start

```python
from graphmcp import WorkflowBuilder

# Create a simple workflow
workflow = (WorkflowBuilder("my-workflow", "config.json")
    .github_analyze_repo("analyze", "https://github.com/facebook/react")
    .context7_get_docs("docs", "/react/docs", depends_on=["analyze"])
    .github_search_code("search", "useState useEffect", depends_on=["analyze"])
    .build())

# Execute the workflow
result = await workflow.execute()
print(f"Status: {result.status}, Success Rate: {result.success_rate:.1f}%")
```

## 🎯 Key Features

- **Fluent Interface**: Chain method calls for readable workflow construction
- **Dependency Management**: Automatic dependency resolution and parallel execution
- **Type Safety**: Full type hints and validation
- **Error Handling**: Built-in retry logic and graceful error recovery
- **Conditional Logic**: Dynamic workflow branching based on results
- **Custom Steps**: Integrate your own functions seamlessly
- **Serialization Safe**: Compatible with LangGraph and state management systems
- **Performance**: Automatic parallelization of independent steps

## 🏗️ Builder Methods

### GitHub Operations

```python
# Repository analysis
.github_analyze_repo("step_id", "https://github.com/owner/repo")

# Code search
.github_search_code("step_id", "search query")

# File retrieval
.github_get_file("step_id", "owner", "repo", "path/to/file.js")
```

### Context7 Operations

```python
# Documentation search
.context7_search("step_id", "react hooks", library_id="/react/docs")

# Get library documentation
.context7_get_docs("step_id", "/react/docs", topic="advanced")
```

### Filesystem Operations

```python
# Scan files
.filesystem_scan("step_id", "*.py", base_path="/src")
```

### Browser Operations

```python
# Navigate to URL
.browser_navigate("step_id", "https://example.com")
```

### Control Flow

```python
# Conditional execution
.conditional("step_id", "len(previous_step.files) > 10")

# Custom functions
.custom_step("step_id", "Custom Analysis", my_function, parameters={"key": "value"})
```

### Configuration

```python
# Configure workflow execution
.with_config(
    max_parallel_steps=5,
    default_timeout=30,
    stop_on_error=False,
    default_retry_count=3
)
```

## 📋 Step Dependencies

Control execution order by specifying dependencies:

```python
workflow = (WorkflowBuilder("dependent-workflow", config_path)
    .github_analyze_repo("analyze", repo_url)
    .context7_get_docs("docs", "/lib/docs", depends_on=["analyze"])
    .github_search_code("search", "query", depends_on=["analyze"])
    .custom_step("summary", "Summarize", summarize_fn, depends_on=["docs", "search"])
    .build())
```

**Execution order:**
1. `analyze` (runs first)
2. `docs` and `search` (run in parallel after `analyze`)
3. `summary` (runs after both `docs` and `search` complete)

## 🔀 Conditional Logic

Create dynamic workflows that adapt based on results:

```python
workflow = (WorkflowBuilder("conditional-workflow", config_path)
    .github_analyze_repo("analyze", repo_url)
    
    # Only search TypeScript if project has TS files
    .github_search_code(
        "ts_search", 
        "interface class",
        depends_on=["analyze"],
        condition="len([f for f in analyze.files_found if f.endswith('.ts')]) > 0"
    )
    
    # Get docs only for large projects
    .context7_get_docs(
        "docs", 
        "/typescript/docs",
        depends_on=["analyze"],
        condition="len(analyze.files_found) > 100"
    )
    .build())
```

### Condition Expressions

Conditions are Python expressions evaluated with access to:
- **Step results**: `step_id.property` or `step_id["key"]`
- **Shared state**: `shared["key"]` or `context.get_shared_value("key")`
- **Workflow context**: `context` and `result` objects

```python
# Example conditions
condition="len(analyze.files_found) > 50"
condition="'typescript' in analyze.tech_stack"
condition="shared.get('user_preference') == 'detailed'"
condition="result.steps_completed > 3"
```

## ⚙️ Custom Steps

Integrate your own functions into workflows:

```python
async def my_analysis(context, step, **params):
    """Custom analysis function."""
    # Access previous step results
    repo_data = context.get_shared_value("analyze_repo")
    
    # Perform custom logic
    analysis = {"metric": len(repo_data.get("files_found", []))}
    
    # Store results for later steps
    context.set_shared_value("my_metric", analysis["metric"])
    
    return analysis

workflow = (WorkflowBuilder("custom-workflow", config_path)
    .github_analyze_repo("analyze_repo", repo_url)
    .custom_step(
        "custom_analysis",
        "My Custom Analysis", 
        my_analysis,
        parameters={"option": "detailed"},
        depends_on=["analyze_repo"]
    )
    .build())
```

### Custom Function Requirements

- **Signature**: `async def func(context, step, **params)` or `def func(context, step, **params)`
- **Serializable**: Function must be pickle-safe (no lambdas, local functions)
- **Return**: Must return serializable data (dict, list, str, int, etc.)

## 🔄 Parallel Execution

The workflow engine automatically parallelizes independent steps:

```python
workflow = (WorkflowBuilder("parallel-workflow", config_path)
    # These run in parallel (no dependencies)
    .github_analyze_repo("repo1", "https://github.com/facebook/react")
    .github_analyze_repo("repo2", "https://github.com/vuejs/vue") 
    .github_analyze_repo("repo3", "https://github.com/angular/angular")
    
    # This runs after all analyses complete
    .custom_step("aggregate", "Combine Results", aggregate_fn, 
                depends_on=["repo1", "repo2", "repo3"])
    .build())
```

Control parallelism with configuration:

```python
.with_config(max_parallel_steps=2)  # Limit to 2 concurrent steps
```

## 🛠️ Error Handling

### Retry Configuration

```python
# Per-step retry configuration
.github_analyze_repo("analyze", repo_url, retry_count=5, timeout_seconds=60)

# Global retry configuration
.with_config(default_retry_count=3, default_timeout=30)
```

### Error Recovery Patterns

```python
workflow = (WorkflowBuilder("resilient-workflow", config_path)
    # Primary operation (might fail)
    .github_analyze_repo("primary", "https://github.com/might/fail")
    
    # Fallback operation
    .github_analyze_repo("fallback", "https://github.com/known/good", 
                        condition="primary is None")
    
    # Works with either result
    .custom_step("process", "Process Result", process_either,
                depends_on=["primary", "fallback"])
    
    .with_config(stop_on_error=False)  # Continue despite failures
    .build())
```

## 📊 Workflow Results

Access comprehensive execution results:

```python
result = await workflow.execute()

# Overall status
print(f"Status: {result.status}")  # "completed", "failed", "partial"
print(f"Success Rate: {result.success_rate:.1f}%")
print(f"Duration: {result.duration_seconds:.1f}s")

# Step-specific results
analyze_result = result.get_step_result("analyze_repo")
print(f"Files found: {len(analyze_result.get('files_found', []))}")

# Error information
if result.errors:
    print(f"Errors: {result.errors}")
    print(f"Failed steps: {result.failed_steps}")

# Execution metadata
print(f"Steps: {result.steps_completed}/{result.total_steps}")
print(f"Final result: {result.final_result}")
```

## 🎨 Usage Patterns

### Pattern 1: Repository Analysis Pipeline

```python
def create_repo_analysis_pipeline(repo_url: str, config_path: str):
    return (WorkflowBuilder("repo-pipeline", config_path)
        .github_analyze_repo("analyze", repo_url)
        .custom_step("extract_tech", "Extract Tech Stack", extract_tech_stack, 
                    depends_on=["analyze"])
        .context7_search("search_docs", "documentation", depends_on=["extract_tech"])
        .github_search_code("find_patterns", "TODO FIXME", depends_on=["analyze"])
        .custom_step("generate_report", "Generate Report", create_report,
                    depends_on=["search_docs", "find_patterns"])
        .build())
```

### Pattern 2: Multi-Repository Comparison

```python
def create_comparison_workflow(repos: list, config_path: str):
    builder = WorkflowBuilder("comparison", config_path)
    
    # Analyze all repos in parallel
    for i, repo in enumerate(repos):
        builder.github_analyze_repo(f"repo_{i}", repo)
    
    # Aggregate results
    repo_steps = [f"repo_{i}" for i in range(len(repos))]
    builder.custom_step("compare", "Compare Repositories", compare_repos,
                       depends_on=repo_steps)
    
    return builder.build()
```

### Pattern 3: Conditional Documentation Workflow

```python
def create_docs_workflow(config_path: str):
    return (WorkflowBuilder("docs-workflow", config_path)
        .github_analyze_repo("analyze", repo_url)
        .conditional("has_js", "'javascript' in analyze.tech_stack", 
                    depends_on=["analyze"])
        .conditional("has_python", "'python' in analyze.tech_stack",
                    depends_on=["analyze"])
        .context7_get_docs("js_docs", "/javascript/docs", 
                          depends_on=["has_js"], condition="has_js")
        .context7_get_docs("python_docs", "/python/docs",
                          depends_on=["has_python"], condition="has_python")
        .custom_step("merge_docs", "Merge Documentation", merge_documentation,
                    depends_on=["js_docs", "python_docs"])
        .build())
```

## 🔧 Advanced Configuration

### Workflow-Level Settings

```python
workflow = (WorkflowBuilder("advanced-workflow", config_path)
    # ... add steps ...
    .with_config(
        max_parallel_steps=10,      # Concurrent step limit
        default_timeout=120,        # Default step timeout (seconds)
        stop_on_error=True,        # Stop on first failure
        default_retry_count=5,     # Default retries per step
        retry_delay_seconds=2.0,   # Delay between retries
        enable_step_logging=True,  # Log step execution
        enable_timing=True         # Track step timing
    )
    .build())
```

### Step-Level Settings

```python
.github_analyze_repo(
    "analyze",
    repo_url,
    retry_count=3,           # Step-specific retry count
    timeout_seconds=60,      # Step-specific timeout
    depends_on=["other"],    # Dependencies
    condition="some_check",  # Execution condition
    description="Analyze the repository structure and dependencies"
)
```

## 🧪 Testing Workflows

### Unit Testing Steps

```python
import pytest
from graphmcp.workflows import WorkflowExecutionContext, WorkflowStep

async def test_custom_function():
    # Create mock context
    context = WorkflowExecutionContext(config=mock_config)
    context.set_shared_value("test_data", {"files": ["file1.py", "file2.js"]})
    
    # Create mock step
    step = WorkflowStep(id="test", step_type=StepType.CUSTOM, name="Test")
    
    # Test function
    result = await my_custom_function(context, step)
    
    assert result["status"] == "success"
    assert len(result["processed_files"]) == 2
```

### Integration Testing

```python
async def test_workflow_execution():
    # Create test workflow
    workflow = (WorkflowBuilder("test-workflow", "test_config.json")
        .custom_step("step1", "Test Step", mock_function)
        .custom_step("step2", "Test Step 2", mock_function_2, depends_on=["step1"])
        .build())
    
    # Execute and verify
    result = await workflow.execute()
    
    assert result.status == "completed"
    assert result.steps_completed == 2
    assert "step1" in result.step_results
    assert "step2" in result.step_results
```

## 📚 Examples

See `examples.py` for comprehensive examples including:

- **Simple Repository Analysis**: Basic workflow with GitHub and Context7
- **Conditional Workflows**: Dynamic branching based on analysis results  
- **Parallel Processing**: Multiple repositories analyzed simultaneously
- **Complex Multi-Stage**: Advanced workflow with custom functions
- **Error Recovery**: Resilient workflows with fallback strategies

## ⚡ Performance Tips

1. **Minimize Dependencies**: Only add dependencies when actually needed
2. **Use Parallel Steps**: Let independent steps run concurrently
3. **Optimize Conditions**: Keep condition expressions simple and fast
4. **Cache Results**: Store intermediate results in shared context
5. **Configure Timeouts**: Set appropriate timeouts for your use case
6. **Limit Parallelism**: Don't overwhelm MCP servers with too many concurrent requests

## 🔍 Debugging

### Enable Detailed Logging

```python
import logging
logging.getLogger('graphmcp.workflows').setLevel(logging.DEBUG)
```

### Inspect Execution Order

```python
workflow = builder.build()
execution_order = workflow.get_execution_order()
print("Execution batches:", execution_order)
```

### Monitor Step Results

```python
result = await workflow.execute()
for step_id, step_result in result.step_results.items():
    print(f"{step_id}: {type(step_result)} = {step_result}")
```

## 🤝 Contributing

The Workflow Builder follows GraphMCP's core design principles:

- **Never store MCP objects**: Only store serializable data
- **Always ensure serializability**: All results must be pickle-safe
- **Use proven patterns**: Follow established MCP session patterns
- **Comprehensive error handling**: Handle all failure modes gracefully
- **Resource cleanup**: Ensure proper cleanup in all execution paths

---

*The Workflow Builder is part of the GraphMCP framework - a reusable foundation for building complex MCP-based applications.* 