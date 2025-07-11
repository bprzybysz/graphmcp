import pytest
import asyncio
import json
import pickle
import re
from unittest.mock import AsyncMock, patch, MagicMock, call
from pathlib import Path

from workflows import WorkflowBuilder, Workflow
from workflows.builder import WorkflowStep, StepType, WorkflowResult
from clients.base import BaseMCPClient, MCPConnectionError, MCPToolError

# --- Helper Functions (module-level for pickling) ---

async def security_scan_function(context, step):
    """Security scan function for workflow templates."""
    return {"status": "scan complete", "vulnerabilities": 0}

async def custom_function_helper(context, step):
    """Custom function for serialization testing."""
    return {"processed": True, "count": 42}

def dynamic_text_function(context):
    """Dynamic text function for Slack posts."""
    return f"Analysis complete: {context.get_shared_value('result_count', 0)} items"

# --- Placeholder classes from the documentation for tests to run ---

class RepoQuickScanTemplate:
    """Reusable template for repository scanning."""
    @staticmethod
    def apply(builder: WorkflowBuilder, step_prefix: str, params: dict) -> WorkflowBuilder:
        repo_url = params["repo_url"]

        return (builder
            .repomix_pack_repo(f"{step_prefix}_pack", repo_url)
            .github_analyze_repo(f"{step_prefix}_analyze", repo_url)
            .custom_step(f"{step_prefix}_security", "Security Scan", 
                         security_scan_function, depends_on=[f"{step_prefix}_pack"])
        )

class PromptTemplate:
    """Jinja-like template for dynamic prompts."""
    def __init__(self, template: str):
        self.template = template
    
    def render(self, context: dict) -> str:
        def replace_var(match):
            var_name = match.group(1).strip()
            # Basic navigation for nested objects, e.g., security_report.issues
            keys = var_name.split('.')
            value = context
            try:
                for key in keys:
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = getattr(value, key, None)
                    if value is None:
                        break
            except (KeyError, AttributeError):
                value = f"{{{{ {var_name} }}}}"
            return str(value if value is not None else f"{{{{ {var_name} }}}}")
        
        return re.sub(r'\{\{\s*([^}]+?)\s*\}\}', replace_var, self.template)

# --- Mock MCP Clients for Testing ---

class MockGitHubMCPClient:
    """Mock GitHub MCP client for testing."""
    
    def __init__(self, config_path, server_name="github"):
        self.config_path = config_path
        self.server_name = server_name
        self.connected = False
    
    async def connect(self):
        self.connected = True
    
    async def disconnect(self):
        self.connected = False
    
    async def call_tool_with_retry(self, tool_name, params, **kwargs):
        """Mock tool calls with realistic responses."""
        if tool_name == "analyze_repo_structure":
            return {
                "repository_url": params.get("repo_url", ""),
                "languages": {"TypeScript": 60, "JavaScript": 30, "CSS": 10},
                "file_count": 247,
                "config_files": [
                    {"path": "package.json", "type": "npm"},
                    {"path": "tsconfig.json", "type": "typescript"}
                ]
            }
        elif tool_name == "create_pull_request":
            return {
                "success": True,
                "number": 42,
                "url": "https://github.com/test/repo/pull/42",
                "title": params.get("title", "Test PR")
            }
        elif tool_name == "get_file_contents":
            return "# Test File Content\nThis is mock content for testing."
        else:
            return {"success": True, "mock": True}

class MockSlackMCPClient:
    """Mock Slack MCP client for testing."""
    
    def __init__(self, config_path, server_name="slack"):
        self.config_path = config_path
        self.server_name = server_name
        self.connected = False
        self.messages_sent = []
    
    async def connect(self):
        self.connected = True
    
    async def disconnect(self):
        self.connected = False
    
    async def call_tool_with_retry(self, tool_name, params, **kwargs):
        """Mock tool calls with realistic responses."""
        if tool_name == "post_message":
            message = {
                "channel": params.get("channel_id", params.get("channel")),
                "text": params.get("text", ""),
                "ts": "1234567890.123456"
            }
            self.messages_sent.append(message)
            return {
                "ok": True,
                "ts": message["ts"],
                "message": message
            }
        elif tool_name == "list_channels":
            return {
                "ok": True,
                "channels": [
                    {"id": "C01234567", "name": "general", "is_private": False},
                    {"id": "C09876543", "name": "dev-alerts", "is_private": False}
                ]
            }
        else:
            return {"ok": True, "mock": True}

class MockRepomixMCPClient:
    """Mock Repomix MCP client for testing."""
    
    def __init__(self, config_path, server_name="repomix"):
        self.config_path = config_path
        self.server_name = server_name
        self.connected = False
    
    async def connect(self):
        self.connected = True
    
    async def disconnect(self):
        self.connected = False
    
    async def call_tool_with_retry(self, tool_name, params, **kwargs):
        """Mock tool calls with realistic responses."""
        if tool_name == "pack_remote_repository":
            return {
                "success": True,
                "repository_url": params.get("url", ""),
                "files_packed": 156,
                "total_size": 2048576,
                "output_file": "/tmp/repo_pack.txt",
                "summary": "Repository packed successfully"
            }
        elif tool_name == "pack_repository":
            # Legacy method support
            return {
                "repository_url": params.get("repo_url", ""),
                "packed_content": "Mock packed content...",
                "file_count": 156,
                "total_size": 2048576
            }
        else:
            return {"success": True, "mock": True}

# --- Unit Tests ---

class TestWorkflowBuilderExtensions:
    """Test new builder pattern methods and functionality."""
    
    @pytest.fixture
    def mock_clients(self):
        """Provide mock clients for testing."""
        return {
            "github": MockGitHubMCPClient,
            "slack": MockSlackMCPClient,
            "repomix": MockRepomixMCPClient
        }
    
    def test_repomix_pack_repo_step_creation(self, mock_config_path):
        """Test Repomix repository packing step creation."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        result_builder = builder.repomix_pack_repo(
            "pack_repo",
            "https://github.com/microsoft/typescript",
            include_patterns=["**/*.ts", "**/*.js"],
            exclude_patterns=["node_modules/**"]
        )
        
        assert result_builder is builder
        assert len(builder._steps) == 1
        step = builder._steps[0]
        
        assert step.id == "pack_repo"
        assert step.step_type == StepType.REPOMIX
        assert step.parameters["repo_url"] == "https://github.com/microsoft/typescript"
        assert step.parameters["include_patterns"] == ["**/*.ts", "**/*.js"]
        assert step.parameters["exclude_patterns"] == ["node_modules/**"]

    def test_github_create_pr_step_creation(self, mock_config_path):
        """Test GitHub pull request creation step."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        result_builder = builder.github_create_pr(
            "create_pr",
            title="Test PR",
            head="feature-branch",
            base="main",
            body_template="This is a test PR for {{ repo_name }}",
            depends_on=["validation"]
        )
        
        assert result_builder is builder
        step = builder._steps[0]
        
        assert step.id == "create_pr"
        assert step.step_type == StepType.GITHUB
        assert step.parameters["title"] == "Test PR"
        assert step.parameters["head"] == "feature-branch"
        assert step.parameters["base"] == "main"
        assert step.depends_on == ["validation"]

    def test_slack_post_step_with_function(self, mock_config_path):
        """Test Slack posting step with dynamic text function."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        builder.slack_post(
            "notify_team",
            "C01234567",
            dynamic_text_function,
            depends_on=["analysis_step"]
        )
        
        step = builder._steps[0]
        assert step.id == "notify_team"
        assert step.step_type == StepType.SLACK
        assert step.parameters["channel_id"] == "C01234567"
        assert callable(step.parameters["text_or_fn"])
        assert step.depends_on == ["analysis_step"]

    def test_gpt_step_with_templating(self, mock_config_path):
        """Test GPT step with prompt templating."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        prompt_template = "Analyze: {{ files_count }}"
        
        builder.gpt_step(
            "analyze_with_gpt", "gpt-4o-mini", prompt_template,
            parameters={"max_tokens": 1000, "temperature": 0.2},
            depends_on=["repo_analysis"]
        )
        
        step = builder._steps[0]
        assert step.id == "analyze_with_gpt"
        assert step.step_type == StepType.GPT
        assert step.parameters["model"] == "gpt-4o-mini"
        assert step.parameters["prompt"] == prompt_template
        assert step.parameters["max_tokens"] == 1000
        assert step.parameters["temperature"] == 0.2

    def test_custom_step_creation(self, mock_config_path):
        """Test custom step creation with proper function handling."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        builder.custom_step(
            "custom_processing",
            "Custom Processing Step",
            custom_function_helper,
            description="Test custom step description",
            parameters={"mode": "advanced"},
            timeout_seconds=60
        )
        
        step = builder._steps[0]
        assert step.id == "custom_processing"
        assert step.step_type == StepType.CUSTOM
        assert step.name == "Custom Processing Step"
        assert step.description == "Test custom step description"
        assert step.parameters["mode"] == "advanced"
        assert step.timeout_seconds == 60
        assert callable(step.function)

    def test_step_template_application(self, mock_config_path):
        """Test step template macro functionality."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        # Apply the template
        RepoQuickScanTemplate.apply(
            builder,
            step_prefix="quick_scan",
            params={"repo_url": "https://github.com/facebook/react"}
        )
        
        assert len(builder._steps) == 3
        step_ids = [step.id for step in builder._steps]
        assert "quick_scan_pack" in step_ids
        assert "quick_scan_analyze" in step_ids
        assert "quick_scan_security" in step_ids
        
        security_step = next(s for s in builder._steps if s.id == "quick_scan_security")
        assert "quick_scan_pack" in security_step.depends_on

    def test_workflow_configuration(self, mock_config_path):
        """Test workflow configuration settings."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        workflow = (builder
            .repomix_pack_repo("pack", "https://github.com/test/repo")
            .with_config(
                max_parallel_steps=3,
                default_timeout=90,
                stop_on_error=True,
                default_retry_count=2
            )
            .build()
        )
        
        assert workflow.config.max_parallel_steps == 3
        assert workflow.config.default_timeout == 90
        assert workflow.config.stop_on_error == True
        assert workflow.config.default_retry_count == 2

    def test_prompt_template_rendering(self):
        """Test prompt template variable substitution."""
        template = PromptTemplate("Repo: {{ repo_name }}, Files: {{ file_count }}, Status: {{ status }}")
        
        context = {"repo_name": "typescript", "file_count": 150, "status": "analyzed"}
        rendered = template.render(context)
        
        assert "Repo: typescript" in rendered
        assert "Files: 150" in rendered
        assert "Status: analyzed" in rendered
        assert "{{" not in rendered

    def test_prompt_template_nested_values(self):
        """Test prompt template with nested object access."""
        template = PromptTemplate("Issues: {{ security_report.issues }}, Severity: {{ security_report.max_severity }}")
        
        context = {
            "security_report": {
                "issues": 3,
                "max_severity": "high"
            }
        }
        rendered = template.render(context)
        
        assert "Issues: 3" in rendered
        assert "Severity: high" in rendered

class TestMockClientFunctionality:
    """Test that mock clients provide realistic behavior for testing."""
    
    @pytest.mark.asyncio
    async def test_mock_github_client(self, mock_config_path):
        """Test mock GitHub client provides expected responses."""
        client = MockGitHubMCPClient(mock_config_path)
        
        # Test repository analysis
        result = await client.call_tool_with_retry("analyze_repo_structure", {
            "repo_url": "https://github.com/test/repo"
        })
        
        assert result["repository_url"] == "https://github.com/test/repo"
        assert "languages" in result
        assert "file_count" in result
        assert isinstance(result["config_files"], list)
    
    @pytest.mark.asyncio
    async def test_mock_slack_client(self, mock_config_path):
        """Test mock Slack client tracks messages properly."""
        client = MockSlackMCPClient(mock_config_path)
        
        # Test message posting
        result = await client.call_tool_with_retry("post_message", {
            "channel": "C01234567",
            "text": "Test message"
        })
        
        assert result["ok"] == True
        assert "ts" in result
        assert len(client.messages_sent) == 1
        assert client.messages_sent[0]["text"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_mock_repomix_client(self, mock_config_path):
        """Test mock Repomix client provides packing responses."""
        client = MockRepomixMCPClient(mock_config_path)
        
        # Test repository packing
        result = await client.call_tool_with_retry("pack_remote_repository", {
            "url": "https://github.com/test/repo"
        })
        
        assert result["success"] == True
        assert "files_packed" in result
        assert "total_size" in result
        assert "output_file" in result

class TestSerializationSafety:
    """Test that all new components are serialization-safe."""

    def test_workflow_with_templates_serializable(self, mock_config_path):
        """Test that workflows using templates remain serializable."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        workflow = (RepoQuickScanTemplate.apply(
                builder, step_prefix="scan", 
                params={"repo_url": "https://github.com/test/repo"}
            )
            .gpt_step("summarize", "gpt-4o-mini", "Summarize: {{ scan_results }}")
            .build()
        )
        
        # Test workflow configuration serialization (skip steps with functions)
        config_data = {
            "name": workflow.config.name,
            "max_parallel_steps": workflow.config.max_parallel_steps,
            "step_count": len(workflow.steps)
        }
        
        pickled_config = pickle.dumps(config_data)
        unpickled_config = pickle.loads(pickled_config)
        
        assert unpickled_config["name"] == "test-workflow"
        assert unpickled_config["step_count"] == 4

    def test_prompt_template_serializable(self):
        """Test that prompt templates are serializable."""
        template = PromptTemplate("Analyze {{ data }} with {{ model }}")
        
        pickled_template = pickle.dumps(template)
        unpickled_template = pickle.loads(pickled_template)
        
        assert unpickled_template.template == template.template

    def test_workflow_steps_structure_serializable(self, mock_config_path):
        """Test that workflow step metadata is serializable."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        builder.custom_step("test", "Test Step", custom_function_helper)
        workflow = builder.build()
        
        # Test step metadata serialization (excluding functions)
        step_metadata = [{
            "id": step.id,
            "name": step.name,
            "step_type": step.step_type.name,
            "parameters": {k: v for k, v in step.parameters.items() if not callable(v)}
        } for step in workflow.steps]
        
        pickled_metadata = pickle.dumps(step_metadata)
        unpickled_metadata = pickle.loads(pickled_metadata)
        
        assert len(unpickled_metadata) == 1
        assert unpickled_metadata[0]["id"] == "test"

    def test_workflow_config_serializable(self, mock_config_path):
        """Test that workflow configuration is fully serializable."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        workflow = builder.build()
        
        # Test that config is serializable
        pickled_config = pickle.dumps(workflow.config)
        unpickled_config = pickle.loads(pickled_config)
        
        assert unpickled_config.name == "test-workflow"
        assert unpickled_config.max_parallel_steps == 3

class TestWorkflowExecution:
    """Test workflow execution with mock context."""
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, mock_config_path):
        """Test execution of a simple workflow with proper context."""
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        
        workflow = (builder
            .custom_step("step1", "Simple Step", custom_function_helper)
            .build()
        )
        
        result = await workflow.execute()
        
        assert result.status in ["completed", "partial_success"]
        assert len(result.step_results) == 1
        assert result.step_results["step1"]["processed"] == True

    @pytest.mark.asyncio
    async def test_multi_step_workflow_execution(self, mock_config_path):
        """Test execution of multi-step workflow with dependencies."""
        async def step1_func(context, step):
            context.set_shared_value("step1_result", "data from step 1")
            return {"success": True, "data": "step1 data"}
        
        async def step2_func(context, step):
            step1_data = context.get_shared_value("step1_result")
            return {"success": True, "processed": step1_data}
        
        builder = WorkflowBuilder("test-workflow", mock_config_path)
        workflow = (builder
            .custom_step("step1", "First Step", step1_func)
            .custom_step("step2", "Second Step", step2_func, depends_on=["step1"])
            .build()
        )
        
        result = await workflow.execute()
        
        assert result.status in ["completed", "partial_success"]
        assert len(result.step_results) == 2
        assert result.step_results["step2"]["processed"] == "data from step 1" 