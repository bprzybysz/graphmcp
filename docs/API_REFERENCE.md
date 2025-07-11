# GraphMCP API Builder Reference

## Overview

This document provides complete API reference for the GraphMCP Database Decommissioning Workflow, including Python SDK, REST API, and programmatic interfaces.

## Table of Contents

1. [Python SDK](#python-sdk)
2. [Core Classes](#core-classes)
3. [Workflow Functions](#workflow-functions)
4. [Monitoring API](#monitoring-api)
5. [Error Handling](#error-handling)
6. [Configuration API](#configuration-api)
7. [Examples](#examples)

## Python SDK

### Installation

```bash
pip install graphmcp-db-decommission
```

### Basic Usage

```python
from don_concrete.db_decommission import create_db_decommission_workflow
import asyncio

async def main():
    # Create workflow
    workflow = create_db_decommission_workflow()
    
    # Execute
    result = await workflow.execute(
        database_name="my_database",
        target_repos=["https://github.com/org/repo1"],
        slack_channel="#database-ops"
    )
    
    print(f"Success: {result.success}")
    return result

# Run workflow
result = asyncio.run(main())
```

## Core Classes

### WorkflowResult

The primary result object returned by workflow execution.

```python
@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    
    workflow_id: str
    database_name: str
    success: bool
    duration_seconds: float
    start_time: datetime
    end_time: datetime
    
    # Step results
    step_results: Dict[str, Any]
    
    # Processing metrics
    repositories_processed: int
    files_discovered: int
    files_processed: int
    files_modified: int
    
    # Error tracking
    errors: List[str]
    warnings: List[str]
    
    # Metrics and logs
    metrics: Dict[str, Any]
    log_file_path: str
```

#### Methods

```python
# Convert to dictionary
result_dict = result.to_dict()

# Get step result
env_result = result.get_step_result("validate_environment")

# Check if specific step succeeded
if result.step_succeeded("process_repositories"):
    print("Repository processing completed successfully")

# Get error summary
error_summary = result.get_error_summary()
```

### DatabaseWorkflowLogger

Centralized logging system for workflow execution.

```python
from don_concrete.workflow_logger import create_workflow_logger

# Create logger for specific database
logger = create_workflow_logger("my_database")

# Log step start
logger.log_step_start(
    step_name="validate_environment",
    description="Validating environment setup",
    parameters={"database_name": "my_database"}
)

# Log step completion
logger.log_step_end(
    step_name="validate_environment",
    result={"status": "success"},
    success=True
)

# Log errors and warnings
logger.log_error("Connection failed", exception=e)
logger.log_warning("High memory usage detected")

# Export logs
logger.export_logs("path/to/export.json")
```

### MonitoringSystem

Production monitoring and health checks.

```python
from don_concrete.monitoring import get_monitoring_system

# Get monitoring instance
monitoring = get_monitoring_system()

# Perform health checks
health_results = await monitoring.perform_health_check()

# Check specific health aspect
memory_health = await monitoring.perform_health_check("memory_usage")

# Send alerts
await monitoring.send_alert(
    severity=AlertSeverity.WARNING,
    title="High Memory Usage",
    message="Memory usage is at 85%",
    metadata={"current_usage": "85%"}
)

# Get monitoring dashboard
dashboard = monitoring.get_monitoring_dashboard()
```

### ErrorHandler

Comprehensive error handling and recovery.

```python
from don_concrete.error_handling import get_error_handler, ErrorCategory, ErrorSeverity

# Get error handler
error_handler = get_error_handler()

# Handle error with context
await error_handler.handle_error(
    exception=e,
    severity=ErrorSeverity.HIGH,
    category=ErrorCategory.NETWORK,
    workflow_id="workflow_123",
    database_name="my_database"
)

# Execute with error handling
result = await error_handler.execute_with_error_handling(
    operation=my_async_function,
    arg1="value1",
    error_category=ErrorCategory.EXTERNAL_SERVICE,
    severity=ErrorSeverity.MEDIUM
)

# Get error summary
summary = error_handler.get_error_summary()
```

## Workflow Functions

### create_db_decommission_workflow()

Creates the main database decommissioning workflow.

```python
def create_db_decommission_workflow() -> Workflow:
    """
    Create database decommissioning workflow with 4 steps:
    1. Environment validation
    2. Repository processing  
    3. Quality assurance
    4. Workflow summary
    
    Returns:
        Workflow: Configured workflow instance
    """
```

### validate_environment_step()

Environment validation and component initialization.

```python
async def validate_environment_step(
    context: WorkflowContext,
    step: WorkflowStep,
    database_name: str = "example_database",
    workflow_id: str = None
) -> Dict[str, Any]:
    """
    Validate environment and initialize components.
    
    Args:
        context: Workflow execution context
        step: Current workflow step
        database_name: Target database name
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing validation results and component status
        
    Raises:
        RuntimeError: If critical validation fails
    """
```

### process_repositories_step()

Repository processing with AI-powered pattern discovery.

```python
async def process_repositories_step(
    context: WorkflowContext,
    step: WorkflowStep, 
    target_repos: List[str],
    database_name: str = "example_database",
    slack_channel: str = "#database-decommission",
    workflow_id: str = None
) -> Dict[str, Any]:
    """
    Process repositories with pattern discovery and contextual rules.
    
    Args:
        context: Workflow execution context
        step: Current workflow step
        target_repos: List of repository URLs to process
        database_name: Target database name
        slack_channel: Slack channel for notifications
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing processing results and metrics
    """
```

### quality_assurance_step()

Quality assurance checks and validation.

```python
async def quality_assurance_step(
    context: WorkflowContext,
    step: WorkflowStep,
    database_name: str = "example_database",
    repo_owner: str = "",
    repo_name: str = "",
    workflow_id: str = None
) -> Dict[str, Any]:
    """
    Perform comprehensive quality assurance checks.
    
    Args:
        context: Workflow execution context
        step: Current workflow step
        database_name: Target database name
        repo_owner: Repository owner
        repo_name: Repository name
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing QA results and recommendations
    """
```

### workflow_summary_step()

Workflow summary generation and metrics compilation.

```python
async def workflow_summary_step(
    context: WorkflowContext,
    step: WorkflowStep,
    database_name: str = "example_database",
    workflow_id: str = None
) -> Dict[str, Any]:
    """
    Generate comprehensive workflow summary and metrics.
    
    Args:
        context: Workflow execution context
        step: Current workflow step
        database_name: Target database name
        workflow_id: Unique workflow identifier
        
    Returns:
        Dict containing workflow summary and final metrics
    """
```

## Monitoring API

### Health Check Functions

```python
# System resource monitoring
async def check_system_resources() -> HealthCheckResult:
    """Check CPU, memory, and disk usage."""

async def check_memory_usage() -> HealthCheckResult:
    """Detailed memory usage analysis."""

async def check_disk_space() -> HealthCheckResult:
    """Check available disk space."""

async def check_network_connectivity() -> HealthCheckResult:
    """Test external API connectivity."""

async def check_mcp_services() -> HealthCheckResult:
    """Verify MCP service configuration."""

async def check_environment_config() -> HealthCheckResult:
    """Validate environment configuration."""

async def check_log_files() -> HealthCheckResult:
    """Check log file accessibility and size."""
```

### Metrics Collection

```python
from don_concrete.monitoring import SystemMetrics

# Collect system metrics
metrics = monitoring.collect_system_metrics()

print(f"CPU: {metrics.cpu_percent}%")
print(f"Memory: {metrics.memory_percent}%")
print(f"Disk: {metrics.disk_percent}%")
print(f"Network connections: {metrics.network_connections}")
```

### Alert System

```python
from don_concrete.monitoring import AlertSeverity

# Send different severity alerts
await monitoring.send_alert(
    AlertSeverity.INFO,
    "Workflow Started",
    "Database decommissioning workflow initiated"
)

await monitoring.send_alert(
    AlertSeverity.WARNING,
    "High Resource Usage",
    "Memory usage exceeds 80%",
    {"memory_percent": 85, "threshold": 80}
)

await monitoring.send_alert(
    AlertSeverity.CRITICAL,
    "Service Failure",
    "GitHub API connection failed",
    {"service": "github", "error": "timeout"}
)

await monitoring.send_alert(
    AlertSeverity.EMERGENCY,
    "System Critical",
    "Disk space critically low",
    {"disk_free_percent": 2}
)
```

## Error Handling

### Error Categories

```python
from don_concrete.error_handling import ErrorCategory

ErrorCategory.NETWORK          # Network connectivity issues
ErrorCategory.AUTHENTICATION   # API authentication failures
ErrorCategory.CONFIGURATION    # Configuration errors
ErrorCategory.RESOURCE         # System resource issues
ErrorCategory.BUSINESS_LOGIC   # Application logic errors
ErrorCategory.EXTERNAL_SERVICE # Third-party service failures
ErrorCategory.DATA_VALIDATION  # Data validation errors
ErrorCategory.SYSTEM          # General system errors
```

### Error Severity Levels

```python
from don_concrete.error_handling import ErrorSeverity

ErrorSeverity.LOW      # Informational errors
ErrorSeverity.MEDIUM   # Standard errors
ErrorSeverity.HIGH     # Important errors requiring attention
ErrorSeverity.CRITICAL # Critical errors affecting workflow
```

### Recovery Strategies

```python
from don_concrete.error_handling import ErrorRecoveryStrategy

# Create custom recovery strategy
strategy = ErrorRecoveryStrategy(
    max_retries=3,
    backoff_factor=2.0
)

# Execute with recovery
result = await strategy.execute_with_recovery(
    my_async_function,
    arg1="value1"
)
```

### Circuit Breaker

```python
from don_concrete.error_handling import CircuitBreaker

# Create circuit breaker for external service
breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
    expected_exception=requests.RequestException
)

# Execute through circuit breaker
result = await breaker.call(api_call_function, url, params)
```

## Configuration API

### Parameter Service

```python
from don_concrete.parameter_service import get_parameter_service

# Get parameter service
param_service = get_parameter_service()

# Access parameters
github_token = param_service.get_secret("GITHUB_PERSONAL_ACCESS_TOKEN")
slack_token = param_service.get_secret("SLACK_BOT_TOKEN")
log_level = param_service.get_parameter("LOG_LEVEL")

# Get all parameters
all_params = param_service.get_all_parameters()

# Check validation issues
issues = param_service.validation_issues
if issues:
    print(f"Configuration issues: {issues}")
```

### Environment Configuration

```python
# Load from different sources
param_service.load_from_env_file(".env.production")
param_service.load_secrets_from_file("production-secrets.json")

# Override parameters programmatically
param_service.set_parameter("LOG_LEVEL", "DEBUG")
param_service.set_secret("CUSTOM_API_KEY", "your-key")
```

## Examples

### Complete Workflow Execution

```python
import asyncio
from don_concrete.db_decommission import create_db_decommission_workflow
from don_concrete.monitoring import get_monitoring_system
from don_concrete.error_handling import get_error_handler

async def run_complete_workflow():
    # Initialize monitoring
    monitoring = get_monitoring_system()
    error_handler = get_error_handler()
    
    try:
        # Create workflow
        workflow = create_db_decommission_workflow()
        
        # Execute with full error handling
        result = await error_handler.execute_with_error_handling(
            workflow.execute,
            database_name="legacy_database",
            target_repos=[
                "https://github.com/company/service1",
                "https://github.com/company/service2"
            ],
            slack_channel="#database-migration"
        )
        
        # Log success
        await monitoring.send_alert(
            AlertSeverity.INFO,
            "Workflow Completed",
            f"Database decommissioning completed successfully",
            result.to_dict()
        )
        
        return result
        
    except Exception as e:
        # Handle workflow failure
        await error_handler.handle_error(
            exception=e,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            database_name="legacy_database"
        )
        raise

# Run the workflow
result = asyncio.run(run_complete_workflow())
print(f"Workflow completed: {result.success}")
```

### Custom Health Check Integration

```python
import asyncio
from don_concrete.monitoring import get_monitoring_system, HealthCheckResult, HealthStatus

async def custom_database_health_check():
    """Custom health check for database connectivity."""
    try:
        # Your database connection logic
        connection = connect_to_database()
        result = connection.execute("SELECT 1")
        
        return HealthCheckResult(
            name="database_connectivity",
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            duration_ms=50.0,
            timestamp=datetime.utcnow(),
            metadata={"host": "db.example.com", "port": 5432}
        )
    except Exception as e:
        return HealthCheckResult(
            name="database_connectivity",
            status=HealthStatus.CRITICAL,
            message=f"Database connection failed: {e}",
            duration_ms=0.0,
            timestamp=datetime.utcnow(),
            metadata={"error": str(e)}
        )

# Register custom health check
monitoring = get_monitoring_system()
monitoring.add_health_check("database_connectivity", custom_database_health_check)
```

### Programmatic Configuration

```python
import os
from don_concrete.parameter_service import get_parameter_service

def setup_production_config():
    """Configure for production environment."""
    param_service = get_parameter_service()
    
    # Set production parameters
    param_service.set_parameter("LOG_LEVEL", "WARNING")
    param_service.set_parameter("DEV_MODE", "false")
    param_service.set_parameter("STRUCTURED_LOGGING", "true")
    param_service.set_parameter("MCP_TIMEOUT", "300")
    param_service.set_parameter("MCP_RETRY_COUNT", "5")
    
    # Load production secrets from secure source
    param_service.load_secrets_from_vault("production-vault")
    
    return param_service

# Use in application startup
param_service = setup_production_config()
```

### Parameter Access Example

```python
import os
from don_concrete.parameter_service import get_parameter_service

def check_parameters():
    param_service = get_parameter_service()
    
    if param_service.validation_issues:
        print(f"Config validation errors: {param_service.validation_issues}")
        return

    print(f"Log Level: {param_service.get_parameter('LOG_LEVEL', 'INFO')}")
```

### Full REST API Example

```python
import requests
import time

# Start workflow
# ...
```

## Best Practices

### Error Handling

```python
# Always use proper error handling
try:
    result = await workflow.execute(database_name="test")
except Exception as e:
    logger.error(f"Workflow failed: {e}")
    await send_failure_notification(e)
    raise

# Use appropriate error categories
await error_handler.handle_error(
    exception=e,
    category=ErrorCategory.EXTERNAL_SERVICE,  # Specific category
    severity=ErrorSeverity.HIGH,             # Appropriate severity
    workflow_id=workflow_id,                 # Context
    database_name=database_name
)
```

### Resource Management

```python
# Monitor resource usage
monitoring = get_monitoring_system()
health = await monitoring.perform_health_check("system_resources")

if health.status == HealthStatus.WARNING:
    logger.warning("High resource usage detected")
    # Consider reducing parallelism or adding delays

# Clean up resources
async with workflow_context() as context:
    result = await workflow.execute()
    # Context automatically cleaned up
```

### Configuration Management

```python
# Validate configuration before execution
param_service = get_parameter_service()
if param_service.validation_issues:
    raise ConfigurationError(f"Config issues: {param_service.validation_issues}")

# Use environment-specific configuration
env = os.getenv("ENVIRONMENT", "development")
config_file = f".env.{env}"
param_service.load_from_env_file(config_file)
```

For more examples and detailed usage patterns, see the [Integration Guide](INTEGRATION_GUIDE.md) and [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md). 