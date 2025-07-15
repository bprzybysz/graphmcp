# API Reference: Database Decommissioning Workflow

## Overview

This document provides comprehensive API documentation for the Database Decommissioning Workflow System, including function signatures, parameters, return values, and usage examples.

## Table of Contents

1. [Core Workflow Functions](#core-workflow-functions)
2. [Workflow Steps](#workflow-steps)
3. [Data Models](#data-models)
4. [Helper Functions](#helper-functions)
5. [Client Operations](#client-operations)
6. [Validation Functions](#validation-functions)
7. [Error Classes](#error-classes)
8. [Configuration](#configuration)

---

## Core Workflow Functions

### `create_db_decommission_workflow()`

Creates a complete database decommissioning workflow with all steps configured.

```python
def create_db_decommission_workflow(
    database_name: str = "example_database",
    target_repos: Optional[List[str]] = None,
    slack_channel: str = "C01234567",
    config_path: str = "mcp_config.json",
    workflow_id: Optional[str] = None
) -> Workflow
```

**Parameters:**
- `database_name` (str): Name of the database to decommission
- `target_repos` (Optional[List[str]]): List of repository URLs to process. Defaults to postgres-sample-dbs
- `slack_channel` (str): Slack channel ID for notifications
- `config_path` (str): Path to MCP configuration file
- `workflow_id` (Optional[str]): Unique workflow identifier. Auto-generated if not provided

**Returns:**
- `Workflow`: Configured workflow ready for execution

**Example:**
```python
workflow = create_db_decommission_workflow(
    database_name="legacy_db",
    target_repos=["https://github.com/org/repo1", "https://github.com/org/repo2"],
    slack_channel="#database-migrations"
)
result = await workflow.execute()
```

### `run_decommission()`

Execute the database decommissioning workflow with simplified parameters.

```python
async def run_decommission(
    database_name: str = "postgres_air",
    target_repos: Optional[List[str]] = None,
    slack_channel: str = "C01234567",
    workflow_id: Optional[str] = None
) -> Any
```

**Parameters:**
- `database_name` (str): Name of the database to decommission
- `target_repos` (Optional[List[str]]): List of repository URLs to process
- `slack_channel` (str): Slack channel ID for notifications
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Any`: Workflow execution result with status and metrics

**Example:**
```python
result = await run_decommission(
    database_name="postgres_air",
    target_repos=["https://github.com/user/repo"],
    slack_channel="#database-decommission"
)
print(f"Status: {result.status}")
```

---

## Workflow Steps

### `validate_environment_step()`

Validates environment setup and initializes components.

```python
async def validate_environment_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `step` (Any): Step configuration object
- `database_name` (str): Name of the database to decommission
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: Validation results with component status

**Response Format:**
```python
{
    "database_name": "example_database",
    "parameter_service_initialized": True,
    "search_patterns": ["\\bexample_database\\b", "'example_database'"],
    "validation_results": [
        {
            "status": "PASSED",
            "component": "parameter_service",
            "message": "Parameter service connection validated"
        }
    ],
    "success": True,
    "duration": 1.23
}
```

### `process_repositories_step()`

Processes repositories with pattern discovery and contextual rules.

```python
async def process_repositories_step(
    context: Any,
    step: Any,
    target_repos: List[str],
    database_name: str = "example_database",
    slack_channel: str = "#database-decommission",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `step` (Any): Step configuration object
- `target_repos` (List[str]): List of repository URLs to process
- `database_name` (str): Name of the database to decommission
- `slack_channel` (str): Slack channel for notifications
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: Repository processing results

**Response Format:**
```python
{
    "database_name": "example_database",
    "total_repositories": 2,
    "repositories_processed": 2,
    "repositories_failed": 0,
    "total_files_processed": 150,
    "total_files_modified": 25,
    "repository_results": [
        {
            "repository": "https://github.com/org/repo1",
            "owner": "org",
            "name": "repo1",
            "success": True,
            "files_found": 75,
            "files_processed": 75,
            "files_modified": 12
        }
    ],
    "success": True,
    "duration": 45.67
}
```

### `apply_refactoring_step()`

Applies contextual refactoring rules to discovered files.

```python
async def apply_refactoring_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `step` (Any): Step configuration object
- `database_name` (str): Name of the database to decommission
- `repo_owner` (str): Repository owner name
- `repo_name` (str): Repository name
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: Refactoring results

**Response Format:**
```python
{
    "database_name": "example_database",
    "total_files_processed": 25,
    "total_files_modified": 18,
    "files_by_type": {
        "python": ["file1.py", "file2.py"],
        "config": ["config.json"]
    },
    "refactoring_results": [
        {
            "path": "file1.py",
            "source_type": "python",
            "changes_made": 3,
            "modified_content": "...",
            "success": True
        }
    ],
    "success": True,
    "duration": 12.34
}
```

### `create_github_pr_step()`

Creates GitHub fork, branch, and pull request with changes.

```python
async def create_github_pr_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `step` (Any): Step configuration object
- `database_name` (str): Name of the database to decommission
- `repo_owner` (str): Repository owner name
- `repo_name` (str): Repository name
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: GitHub PR creation results

**Response Format:**
```python
{
    "success": True,
    "fork_owner": "user",
    "branch_name": "decommission-example_database-1234567890",
    "files_committed": 18,
    "pr_number": 42,
    "pr_url": "https://github.com/org/repo/pull/42",
    "pr_title": "Database Decommission: Remove example_database references",
    "duration": 8.91
}
```

### `quality_assurance_step()`

Performs comprehensive quality assurance checks.

```python
async def quality_assurance_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `step` (Any): Step configuration object
- `database_name` (str): Name of the database to decommission
- `repo_owner` (str): Repository owner name
- `repo_name` (str): Repository name
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: Quality assurance results

**Response Format:**
```python
{
    "database_name": "example_database",
    "qa_checks": [
        {
            "check": "database_reference_removal",
            "status": "PASSED",
            "confidence": 95,
            "description": "Database references properly identified"
        }
    ],
    "all_checks_passed": True,
    "quality_score": 92.5,
    "recommendations": [
        "Monitor application logs for any database connection errors",
        "Update documentation to reflect database decommissioning"
    ],
    "success": True,
    "duration": 3.45
}
```

### `workflow_summary_step()`

Generates comprehensive workflow summary and metrics.

```python
async def workflow_summary_step(
    context: Any,
    step: Any,
    database_name: str = "example_database",
    workflow_id: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `step` (Any): Step configuration object
- `database_name` (str): Name of the database to decommission
- `workflow_id` (Optional[str]): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: Workflow summary and metrics

**Response Format:**
```python
{
    "database_name": "example_database",
    "workflow_version": "v2.0",
    "summary": {
        "repositories_processed": 2,
        "files_discovered": 150,
        "files_processed": 25,
        "files_modified": 18,
        "total_duration": 71.6,
        "success_rate": 95.2
    },
    "features_used": {
        "pattern_discovery": True,
        "contextual_rules_engine": True,
        "comprehensive_logging": True,
        "source_type_classification": True,
        "graceful_error_handling": True
    },
    "next_steps": [
        "Monitor applications for any connectivity issues",
        "Update database documentation",
        "Schedule infrastructure cleanup"
    ],
    "success": True,
    "duration": 2.11
}
```

---

## Data Models

### `FileProcessingResult`

Result from processing a single file during decommissioning.

```python
@dataclass
class FileProcessingResult:
    file_path: str
    source_type: SourceType
    success: bool
    total_changes: int
    rules_applied: Optional[List[str]] = None
    error_message: Optional[str] = None
    timestamp: Optional[float] = None
    processing_duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
```

### `QualityAssuranceResult`

Result from quality assurance checks.

```python
@dataclass
class QualityAssuranceResult:
    database_reference_check: ValidationResult
    rule_compliance_check: ValidationResult
    service_integrity_check: ValidationResult
    overall_status: ValidationResult
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
```

### `WorkflowStepResult`

Result from a single workflow step execution.

```python
@dataclass
class WorkflowStepResult:
    step_name: str
    step_id: str
    success: bool
    duration_seconds: float
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
```

### `DecommissioningSummary`

Summary of the entire decommissioning workflow.

```python
@dataclass
class DecommissioningSummary:
    workflow_id: str
    database_name: str
    total_files_processed: int
    successful_files: int
    failed_files: int
    total_changes: int
    rules_applied: List[str]
    execution_time_seconds: float
    quality_assurance: QualityAssuranceResult
    github_pr_url: Optional[str] = None
    timestamp: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
```

---

## Helper Functions

### GitHub Helpers

#### `create_fork_and_branch()`

Creates fork and branch for database decommissioning changes.

```python
async def create_fork_and_branch(
    github_client: Any,
    repo_owner: str,
    repo_name: str,
    database_name: str,
    logger: Any
) -> Dict[str, Any]
```

**Parameters:**
- `github_client` (Any): GitHub MCP client instance
- `repo_owner` (str): Repository owner name
- `repo_name` (str): Repository name
- `database_name` (str): Database name for branch naming
- `logger` (Any): Structured logger instance

**Returns:**
- `Dict[str, Any]`: Fork and branch information

#### `commit_file_changes()`

Commits modified files to the feature branch.

```python
async def commit_file_changes(
    github_client: Any,
    fork_owner: str,
    repo_name: str,
    branch_name: str,
    modified_files: List[Dict[str, Any]],
    database_name: str,
    logger: Any
) -> Dict[str, Any]
```

**Parameters:**
- `github_client` (Any): GitHub MCP client instance
- `fork_owner` (str): Fork owner name
- `repo_name` (str): Repository name
- `branch_name` (str): Feature branch name
- `modified_files` (List[Dict[str, Any]]): List of modified file results
- `database_name` (str): Database name for commit messages
- `logger` (Any): Structured logger instance

**Returns:**
- `Dict[str, Any]`: Commit results

#### `create_pull_request()`

Creates pull request for database decommissioning changes.

```python
async def create_pull_request(
    github_client: Any,
    repo_owner: str,
    repo_name: str,
    fork_owner: str,
    branch_name: str,
    database_name: str,
    modified_files: List[Dict[str, Any]],
    refactoring_result: Dict[str, Any],
    files_committed: int,
    logger: Any
) -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: PR creation results

### Client Helpers

#### `initialize_github_client()`

Initializes GitHub MCP client with proper error handling.

```python
async def initialize_github_client(
    context: Any,
    logger: Any
) -> Optional[Any]
```

**Parameters:**
- `context` (Any): WorkflowContext for data sharing
- `logger` (Any): Structured logger instance

**Returns:**
- `Optional[Any]`: GitHubMCPClient instance or None if initialization fails

#### `send_slack_notification_with_retry()`

Sends Slack notification with retry logic.

```python
async def send_slack_notification_with_retry(
    slack_client: Any,
    channel: str,
    message: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    max_retries: int = 3,
    logger: Optional[Any] = None
) -> bool
```

**Parameters:**
- `slack_client` (Any): SlackMCPClient instance
- `channel` (str): Slack channel to send message to
- `message` (str): Message content
- `attachments` (Optional[List[Dict[str, Any]]]): Optional message attachments
- `max_retries` (int): Maximum number of retry attempts
- `logger` (Optional[Any]): Optional logger instance

**Returns:**
- `bool`: True if notification sent successfully, False otherwise

---

## Client Operations

### `AgenticFileProcessor`

Processes files in batches using an agentic, category-based approach.

```python
class AgenticFileProcessor:
    def __init__(
        self,
        source_classifier: SourceTypeClassifier,
        contextual_rules_engine: Any,
        github_client: Any,
        repo_owner: str,
        repo_name: str
    ):
        """Initialize the AgenticFileProcessor."""
    
    async def process_files(
        self,
        files_to_process: List[Dict[str, str]],
        batch_size: int = 3
    ) -> List[FileProcessingResult]:
        """Classify, batch, and process files using an agentic workflow."""
```

**Methods:**

#### `process_files()`

Processes files in batches using AI-powered analysis.

**Parameters:**
- `files_to_process` (List[Dict[str, str]]): List of file dictionaries with path and content
- `batch_size` (int): Number of files to process in each batch

**Returns:**
- `List[FileProcessingResult]`: List of processing results

---

## Validation Functions

### `perform_database_reference_check()`

Checks if database references were properly identified and handled.

```python
async def perform_database_reference_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]
```

**Parameters:**
- `discovery_result` (Dict[str, Any]): Results from pattern discovery
- `database_name` (str): Name of the database being decommissioned

**Returns:**
- `Dict[str, Any]`: Check results and confidence metrics

### `perform_rule_compliance_check()`

Checks if pattern discovery followed proper rules and classification.

```python
async def perform_rule_compliance_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]
```

**Parameters:**
- `discovery_result` (Dict[str, Any]): Results from pattern discovery
- `database_name` (str): Name of the database being decommissioned

**Returns:**
- `Dict[str, Any]`: Rule compliance results

### `perform_service_integrity_check()`

Assesses risk to service integrity based on file types and patterns.

```python
async def perform_service_integrity_check(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]
```

**Parameters:**
- `discovery_result` (Dict[str, Any]): Results from pattern discovery
- `database_name` (str): Name of the database being decommissioned

**Returns:**
- `Dict[str, Any]`: Service integrity risk assessment

---

## Error Classes

### `ValidationResult`

Enumeration of validation results.

```python
class ValidationResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
```

### Common Exceptions

```python
class DatabaseDecommissionError(Exception):
    """Base exception for database decommissioning errors."""
    pass

class ValidationError(DatabaseDecommissionError):
    """Raised when validation fails."""
    pass

class ProcessingError(DatabaseDecommissionError):
    """Raised when file processing fails."""
    pass

class GitHubError(DatabaseDecommissionError):
    """Raised when GitHub operations fail."""
    pass
```

---

## Configuration

### Environment Variables

| Variable | Type | Description | Default | Required |
|----------|------|-------------|---------|----------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | str | GitHub API access token | None | Yes |
| `SLACK_BOT_TOKEN` | str | Slack bot token for notifications | None | No |
| `OPENAI_API_KEY` | str | OpenAI API key for AI processing | None | No |
| `LOG_LEVEL` | str | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO | No |
| `LOG_FILE` | str | Path to log file | dbworkflow.log | No |
| `DATABASE_NAME` | str | Default database name | None | No |
| `TARGET_REPOS` | str | Comma-separated list of repository URLs | None | No |
| `SLACK_CHANNEL` | str | Default Slack channel for notifications | None | No |

### Configuration Objects

#### `WorkflowConfig`

Configuration for database decommissioning workflow.

```python
@dataclass
class WorkflowConfig:
    database_name: str
    repo_owner: str
    repo_name: str
    max_parallel_steps: int = 4
    default_timeout: int = 120
    log_file: str = "dbworkflow.log"
    enable_console_logging: bool = True
    enable_json_logging: bool = True
    enable_slack_notifications: bool = True
    dry_run: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
```

#### `LoggingConfig`

Configuration for structured logging.

```python
class LoggingConfig:
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create logging configuration from environment variables."""
    
    def get_logger(self, workflow_id: str) -> Any:
        """Get configured logger instance."""
```

---

## Usage Examples

### Basic Workflow Execution

```python
import asyncio
from concrete.db_decommission.utils import run_decommission

async def main():
    result = await run_decommission(
        database_name="legacy_db",
        target_repos=[
            "https://github.com/org/service-1",
            "https://github.com/org/service-2"
        ],
        slack_channel="#database-migrations"
    )
    
    print(f"Workflow Status: {result.status}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Duration: {result.duration_seconds:.1f}s")

asyncio.run(main())
```

### Custom Workflow Configuration

```python
from concrete.db_decommission.utils import create_db_decommission_workflow

# Create custom workflow
workflow = create_db_decommission_workflow(
    database_name="test_db",
    target_repos=["https://github.com/user/repo"],
    slack_channel="#testing",
    config_path="test_config.json"
)

# Execute with custom timeout
result = await workflow.execute(timeout=1800)

# Access step results
env_result = result.get_step_result("validate_environment")
repo_result = result.get_step_result("process_repositories")
```

### Error Handling Example

```python
from concrete.db_decommission.workflow_steps import validate_environment_step
from concrete.db_decommission.data_models import ValidationResult

try:
    result = await validate_environment_step(
        context=context,
        step=step,
        database_name="test_db"
    )
    
    if not result["success"]:
        failed_validations = [
            v for v in result["validation_results"] 
            if v["status"] == ValidationResult.FAILED.value
        ]
        
        for validation in failed_validations:
            print(f"Validation failed: {validation['message']}")
            
except Exception as e:
    logger.log_error("Critical validation error", e)
    raise
```

---

This API reference provides comprehensive documentation for all public functions, classes, and interfaces in the Database Decommissioning Workflow System. For implementation details, refer to the source code and architecture documentation.