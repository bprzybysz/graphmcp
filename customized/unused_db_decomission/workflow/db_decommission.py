"""
Defines the database decommissioning workflow using the new WorkflowBuilder.
"""

from .builder import WorkflowBuilder
from don_concrete.workflow.steps.repository_processing import RepositoryProcessingStep
from don_concrete.workflow.steps.pattern_discovery import PatternDiscoveryStep
from don_concrete.workflow.steps.file_processing import FileProcessingStep
from don_concrete.workflow.steps.rule_application import RuleApplicationStep
from don_concrete.workflow.steps.quality_assurance import QualityAssuranceStep

def create_decommission_workflow(
    database_name: str,
    target_repos: list[str],
    slack_channel: str,
    config_path: str = "enhanced_mcp_config.json"
):
    """
    Creates the database decommissioning workflow.
    """
    builder = WorkflowBuilder(
        name=f"Decommission-{database_name}",
        config_path=config_path,
        description=f"A workflow to decommission the {database_name} database."
    )

    repo_url = target_repos[0] if target_repos else ""

    # This is a simplified workflow definition. A real implementation
    # would have more complex parameter mapping and dependencies.
    (builder
        .custom_step(
            step_id="repository_processing",
            name="Process Repository",
            func=RepositoryProcessingStep({"repo_url": repo_url}).execute,
            parameters={"repo_url": repo_url} # Pass parameters for the step
        )
        .custom_step(
            step_id="pattern_discovery",
            name="Discover Patterns",
            func=PatternDiscoveryStep({}).execute,
            depends_on=["repository_processing"]
        )
        .custom_step(
            step_id="file_processing",
            name="Process Files",
            func=FileProcessingStep({}).execute,
            depends_on=["pattern_discovery"]
        )
        .custom_step(
            step_id="rule_application",
            name="Apply Rules",
            func=RuleApplicationStep({}).execute,
            depends_on=["file_processing"]
        )
        .custom_step(
            step_id="quality_assurance",
            name="Run QA Checks",
            func=QualityAssuranceStep({}).execute,
            depends_on=["rule_application"]
        )
    )

    return builder.build() 