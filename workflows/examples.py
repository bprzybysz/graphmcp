"""
Workflow Builder Examples

Comprehensive examples showing how to use the WorkflowBuilder
to create complex MCP workflows for various use cases.
"""

import asyncio
from typing import Any

from .builder import WorkflowBuilder
from .models import WorkflowExecutionContext, WorkflowStep


# =================================================================
# Example 1: Simple Repository Analysis Workflow
# =================================================================

def create_simple_repo_analysis_workflow(config_path: str) -> "Workflow":
    """
    Create a simple workflow that analyzes a GitHub repository.
    
    This workflow:
    1. Analyzes the repository structure
    2. Gets documentation for detected technologies
    3. Searches for specific patterns in the code
    """
    workflow = (WorkflowBuilder("simple-repo-analysis", config_path)
        .github_analyze_repo(
            "analyze_repo", 
            "https://github.com/facebook/react"
        )
        .context7_get_docs(
            "get_react_docs", 
            "/react/docs", 
            topic="hooks",
            depends_on=["analyze_repo"]
        )
        .github_search_code(
            "find_hooks", 
            "repo:facebook/react useState useEffect",
            depends_on=["analyze_repo"]
        )
        .build()
    )
    return workflow


# =================================================================
# Example 2: Conditional Workflow with Branching Logic
# =================================================================

def create_conditional_workflow(config_path: str) -> "Workflow":
    """
    Create a workflow that makes decisions based on analysis results.
    
    This workflow:
    1. Analyzes a repository
    2. Conditionally searches for TypeScript files if detected
    3. Gets documentation only for large projects
    4. Performs different actions based on project size
    """
    workflow = (WorkflowBuilder("conditional-analysis", config_path)
        .github_analyze_repo(
            "analyze", 
            "https://github.com/microsoft/typescript"
        )
        .conditional(
            "has_typescript",
            "len([f for f in analyze.get('files_found', []) if f.endswith('.ts')]) > 10",
            depends_on=["analyze"]
        )
        .github_search_code(
            "find_interfaces", 
            "repo:microsoft/typescript interface",
            depends_on=["has_typescript"],
            condition="has_typescript"
        )
        .context7_get_docs(
            "get_ts_docs",
            "/typescript/docs",
            depends_on=["analyze"],
            condition="len(analyze.get('files_found', [])) > 100"
        )
        .filesystem_scan(
            "scan_local",
            "*.md",
            depends_on=["analyze"],
            condition="len(analyze.get('files_found', [])) < 50"
        )
        .build()
    )
    return workflow


# =================================================================
# Example 3: Parallel Processing Workflow
# =================================================================

def create_parallel_workflow(config_path: str) -> "Workflow":
    """
    Create a workflow that processes multiple repositories in parallel.
    
    This workflow:
    1. Analyzes multiple repositories simultaneously
    2. Aggregates results from all analyses
    3. Generates a comparison report
    """
    repos = [
        "https://github.com/facebook/react",
        "https://github.com/vuejs/vue",
        "https://github.com/angular/angular"
    ]
    
    builder = WorkflowBuilder("parallel-analysis", config_path)
    
    # Add parallel analysis steps for each repo
    for i, repo in enumerate(repos):
        step_id = f"analyze_repo_{i}"
        builder.github_analyze_repo(step_id, repo)
    
    # Add aggregation step that depends on all analyses
    analysis_steps = [f"analyze_repo_{i}" for i in range(len(repos))]
    
    builder.custom_step(
        "aggregate_results",
        "Aggregate Analysis Results",
        aggregate_repo_analyses,
        parameters={"repo_count": len(repos)},
        depends_on=analysis_steps
    )
    
    return builder.build()


async def aggregate_repo_analyses(
    context: WorkflowExecutionContext, 
    step: WorkflowStep,
    repo_count: int
) -> dict:
    """Custom function to aggregate repository analysis results."""
    aggregated = {
        "total_repos": repo_count,
        "total_files": 0,
        "technologies": set(),
        "repo_summaries": []
    }
    
    # Collect results from all analysis steps
    for step_id, result in context.shared_state.items():
        if step_id.startswith("analyze_repo_"):
            if isinstance(result, dict):
                aggregated["total_files"] += len(result.get("files_found", []))
                aggregated["technologies"].update(result.get("tech_stack", []))
                aggregated["repo_summaries"].append({
                    "repo": result.get("repository_url", "unknown"),
                    "files": len(result.get("files_found", [])),
                    "tech": result.get("tech_stack", [])
                })
    
    # Convert set to list for serialization
    aggregated["technologies"] = list(aggregated["technologies"])
    
    return aggregated


# =================================================================
# Example 4: Complex Multi-Stage Workflow
# =================================================================

def create_complex_workflow(config_path: str) -> "Workflow":
    """
    Create a complex workflow with multiple stages and dependencies.
    
    This workflow demonstrates:
    - Multi-stage processing
    - Complex dependencies
    - Custom functions
    - Error handling configuration
    - Mixed MCP server usage
    """
    workflow = (WorkflowBuilder("complex-analysis", config_path, 
                               description="Complex multi-stage repository analysis")
        
        # Stage 1: Initial Discovery
        .github_analyze_repo("discover", "https://github.com/facebook/react")
        .filesystem_scan("scan_local", "*.json", base_path=".")
        
        # Stage 2: Technology Analysis (depends on discovery)
        .custom_step(
            "extract_tech_stack",
            "Extract Technology Stack",
            extract_technology_stack,
            depends_on=["discover"]
        )
        .context7_search(
            "search_main_tech",
            "react hooks components",
            depends_on=["extract_tech_stack"]
        )
        
        # Stage 3: Detailed Analysis (depends on tech analysis)
        .github_search_code(
            "find_components",
            "repo:facebook/react component",
            depends_on=["extract_tech_stack"]
        )
        .context7_get_docs(
            "get_detailed_docs",
            "/react/docs",
            topic="advanced",
            depends_on=["search_main_tech"]
        )
        
        # Stage 4: Cross-reference Analysis (depends on detailed analysis)
        .custom_step(
            "cross_reference",
            "Cross-reference Code and Docs",
            cross_reference_analysis,
            depends_on=["find_components", "get_detailed_docs"]
        )
        
        # Stage 5: Final Report (depends on everything)
        .custom_step(
            "generate_report",
            "Generate Final Report",
            generate_final_report,
            depends_on=["cross_reference", "scan_local"]
        )
        
        # Configure workflow settings
        .with_config(
            max_parallel_steps=3,
            default_timeout=60,
            stop_on_error=False,  # Continue even if some steps fail
            default_retry_count=2
        )
        .build()
    )
    return workflow


async def extract_technology_stack(
    context: WorkflowExecutionContext, 
    step: WorkflowStep
) -> list:
    """Extract technology stack from repository analysis."""
    discover_result = context.get_shared_value("discover", {})
    
    # Extract technologies from file extensions and patterns
    files = discover_result.get("files_found", [])
    tech_stack = set()
    
    for file_path in files:
        if file_path.endswith((".js", ".jsx")):
            tech_stack.add("javascript")
        elif file_path.endswith((".ts", ".tsx")):
            tech_stack.add("typescript")
        elif file_path.endswith(".py"):
            tech_stack.add("python")
        elif file_path.endswith((".html", ".htm")):
            tech_stack.add("html")
        elif file_path.endswith(".css"):
            tech_stack.add("css")
    
    # Store in shared context for other steps
    tech_list = list(tech_stack)
    context.set_shared_value("tech_stack", tech_list)
    
    return tech_list


async def cross_reference_analysis(
    context: WorkflowExecutionContext, 
    step: WorkflowStep
) -> dict:
    """Cross-reference code findings with documentation."""
    components = context.get_shared_value("find_components", {})
    docs = context.get_shared_value("get_detailed_docs", {})
    
    analysis = {
        "components_found": len(components.get("matches", [])),
        "documentation_sections": len(docs.get("content_sections", [])),
        "coverage_analysis": "Good" if len(docs.get("content_sections", [])) > 5 else "Limited",
        "recommendations": []
    }
    
    # Add recommendations based on analysis
    if analysis["components_found"] > 10:
        analysis["recommendations"].append("Consider component organization")
    
    if analysis["documentation_sections"] < 3:
        analysis["recommendations"].append("Improve documentation coverage")
    
    return analysis


async def generate_final_report(
    context: WorkflowExecutionContext, 
    step: WorkflowStep
) -> dict:
    """Generate a comprehensive final report."""
    report = {
        "workflow_name": context.config.name,
        "execution_time": step.start_time,
        "analysis_summary": {},
        "findings": {},
        "recommendations": [],
        "metadata": {
            "steps_executed": len(context.shared_state),
            "technologies_found": context.get_shared_value("tech_stack", []),
        }
    }
    
    # Collect key findings from various steps
    cross_ref = context.get_shared_value("cross_reference", {})
    if cross_ref:
        report["findings"]["code_documentation_alignment"] = cross_ref.get("coverage_analysis")
        report["recommendations"].extend(cross_ref.get("recommendations", []))
    
    # Add summary statistics
    discover_result = context.get_shared_value("discover", {})
    if discover_result:
        report["analysis_summary"]["total_files"] = len(discover_result.get("files_found", []))
        report["analysis_summary"]["repository"] = discover_result.get("repository_url")
    
    local_scan = context.get_shared_value("scan_local", {})
    if local_scan:
        report["analysis_summary"]["local_files"] = len(local_scan.get("files_found", []))
    
    return report


# =================================================================
# Example 5: Error Recovery Workflow
# =================================================================

def create_error_recovery_workflow(config_path: str) -> "Workflow":
    """
    Create a workflow that demonstrates error handling and recovery.
    
    This workflow:
    1. Attempts operations that might fail
    2. Has fallback strategies
    3. Continues execution despite failures
    """
    workflow = (WorkflowBuilder("error-recovery", config_path)
        
        # Primary analysis (might fail with invalid repo)
        .github_analyze_repo(
            "primary_analysis", 
            "https://github.com/nonexistent/repo",
            retry_count=1
        )
        
        # Fallback analysis with known good repo
        .github_analyze_repo(
            "fallback_analysis",
            "https://github.com/facebook/react",
            depends_on=[],  # No dependencies - runs in parallel
            condition="primary_analysis is None or 'error' in str(primary_analysis)"
        )
        
        # Analysis that works with either result
        .custom_step(
            "robust_analysis",
            "Robust Analysis",
            robust_analysis_function,
            depends_on=["primary_analysis", "fallback_analysis"]
        )
        
        .with_config(
            stop_on_error=False,  # Continue despite failures
            default_retry_count=1  # Quick retries
        )
        .build()
    )
    return workflow


async def robust_analysis_function(
    context: WorkflowExecutionContext, 
    step: WorkflowStep
) -> dict:
    """Analysis function that works with successful results from either step."""
    primary = context.get_shared_value("primary_analysis")
    fallback = context.get_shared_value("fallback_analysis")
    
    # Use whichever analysis succeeded
    analysis_data = fallback if fallback else primary
    
    if not analysis_data:
        return {"status": "no_data", "message": "No analysis data available"}
    
    return {
        "status": "success",
        "source": "fallback" if fallback else "primary",
        "file_count": len(analysis_data.get("files_found", [])),
        "technologies": analysis_data.get("tech_stack", [])
    }


# =================================================================
# Usage Examples
# =================================================================

async def run_workflow_examples():
    """
    Run all workflow examples to demonstrate different patterns.
    """
    config_path = "mcp_config.json"  # Replace with your config path
    
    print("🚀 Running Workflow Builder Examples")
    print("=" * 50)
    
    # Example 1: Simple workflow
    print("\n1. Simple Repository Analysis:")
    simple_workflow = create_simple_repo_analysis_workflow(config_path)
    try:
        result = await simple_workflow.execute()
        print(f"   Status: {result.status}")
        print(f"   Success Rate: {result.success_rate:.1f}%")
        print(f"   Duration: {result.duration_seconds:.1f}s")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2: Conditional workflow
    print("\n2. Conditional Workflow:")
    conditional_workflow = create_conditional_workflow(config_path)
    try:
        result = await conditional_workflow.execute()
        print(f"   Status: {result.status}")
        print(f"   Steps completed: {result.steps_completed}/{result.total_steps}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3: Parallel workflow
    print("\n3. Parallel Processing:")
    parallel_workflow = create_parallel_workflow(config_path)
    try:
        result = await parallel_workflow.execute()
        print(f"   Status: {result.status}")
        aggregated = result.get_step_result("aggregate_results")
        if aggregated:
            print(f"   Total files: {aggregated.get('total_files', 0)}")
            print(f"   Technologies: {', '.join(aggregated.get('technologies', []))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    # Run examples if script is executed directly
    asyncio.run(run_workflow_examples()) 