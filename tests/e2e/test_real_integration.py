import pytest
import os
import asyncio
from unittest.mock import patch
import json
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()


# DONT CHANGE IT AS IT IS NOT THE REASON!!!!!!
from workflows import WorkflowBuilder # Corrected import statement
from workflows.db_decommission import create_optimized_db_decommission_workflow
from clients import (
    RepomixMCPClient, 
    GitHubMCPClient, 
    FilesystemMCPClient, 
    SlackMCPClient
)

# --- Placeholder Helper Functions ---
async def validate_github_results(context, step):
    analysis = context.get_step_result("analyze")
    assert "repository_url" in analysis
    assert "languages" in analysis
    return {"validation": "passed"}

async def verify_slack_post(context, step):
    slack_result = context.get_shared_value("notify")
    print(f"DEBUG: Slack Post Result: {slack_result}") # Added debug print
    assert slack_result["success"] is True
    assert "ts" in slack_result # Changed from message_ts to ts as per Slack API response
    return {"verification": "passed"}

@pytest.fixture
def real_config_path(tmp_path):
    """
    Loads MCP server configurations from clients/mcp_config.json and
    appends/overrides with e2e-specific settings and environment variables.
    """
    config_file_path = Path("clients/mcp_config.json")
    with open(config_file_path, 'r') as f:
        config = json.load(f)

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Define common args for server-github and server-slack
    common_args_npx_y = ["-y"]

    # Configure GitHub server
    github_config = {
        "command": "npx",
        "args": common_args_npx_y + ["@modelcontextprotocol/server-github@2025.4.8"], # Explicit version
        "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "") }
    }
    config["mcpServers"]["github"] = github_config

    # Configure Slack server
    slack_config = {
        "command": "npx",
        "args": common_args_npx_y + ["@modelcontextprotocol/server-slack"],
        "env": { "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", "") }
    }
    config["mcpServers"]["slack"] = slack_config

    # Configure Repomix server
    # Repomix is already in mcp_config.json, ensure it's correct
    repomix_config = {
        "command": "npx",
        "args": common_args_npx_y + ["repomix", "--mcp"]
    }
    config["mcpServers"]["repomix"] = repomix_config

    # Configure Filesystem server
    filesystem_config = {
        "command": "npx",
        "args": common_args_npx_y + ["@modelcontextprotocol/server-filesystem@2025.7.1", str(tmp_path)], # Added tmp_path as allowed dir
        "env": {
            "ALLOWED_EXTENSIONS": ".py,.js,.ts,.yaml,.yml,.md,.txt,.json"
        }
    }
    config["mcpServers"]["filesystem"] = filesystem_config


    config_file = tmp_path / "real_config.json"
    config_file.write_text(json.dumps(config, indent=2))
    return str(config_file)

@pytest.fixture
async def github_test_fork():
    """Setup and teardown a GitHub fork for testing."""
    GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        pytest.skip("GITHUB_PERSONAL_ACCESS_TOKEN not available")
    
    fork_data = {
        "source_repo": "https://github.com/bprzybys-nc/postgres-sample-dbs",
        "source_owner": "bprzybys-nc", 
        "source_name": "postgres-sample-dbs",
        "fork_owner": None,  # Will be set from GitHub API
        "fork_name": "postgres-sample-dbs",
        "test_branch": f"test-e2e-{int(time.time())}",
        "created_fork": False,
        "created_branch": False
    }
    
    yield fork_data  # Provide fork data to test
    
    # Cleanup in finally block
    try:
        if fork_data.get("created_branch") or fork_data.get("created_fork"):
            import subprocess
            
            # Delete test branch if created
            if fork_data.get("created_branch") and fork_data.get("fork_owner"):
                try:
                    subprocess.run([
                        "gh", "api", "-X", "DELETE",
                        f"/repos/{fork_data['fork_owner']}/{fork_data['fork_name']}/git/refs/heads/{fork_data['test_branch']}"
                    ], check=True, capture_output=True)
                    print(f"✅ Deleted test branch: {fork_data['test_branch']}")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ Failed to delete branch: {e}")
            
            # Delete fork if created  
            if fork_data.get("created_fork") and fork_data.get("fork_owner"):
                try:
                    subprocess.run([
                        "gh", "api", "-X", "DELETE", 
                        f"/repos/{fork_data['fork_owner']}/{fork_data['fork_name']}"
                    ], check=True, capture_output=True)
                    print(f"✅ Deleted fork: {fork_data['fork_owner']}/{fork_data['fork_name']}")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ Failed to delete fork: {e}")
                    
    except Exception as e:
        print(f"⚠️ Error during GitHub cleanup: {e}")

# Initialize _github_token and _slack_bot_token AFTER load_dotenv()
_github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
_slack_bot_token = os.getenv("SLACK_BOT_TOKEN")

@pytest.mark.e2e
@pytest.mark.skipif(
    not ("BP6yrK" in _github_token),
    reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set or does not contain sequence in it"
)
@pytest.mark.skipif(
    not ("yMTEx" in _slack_bot_token),
    reason="SLACK_BOT_TOKEN env var not set or does not contain sequence in it"
)
class TestE2EIntegration:
    """End-to-end tests with real MCP servers (when available)."""

    @pytest.mark.asyncio
    async def test_real_github_integration(self, real_config_path, session_client_health_check):
        """Test with a real GitHub MCP server (if configured)."""
        workflow = (WorkflowBuilder("e2e-github", real_config_path)
            .github_analyze_repo("analyze", "https://github.com/microsoft/typescript")
            .custom_step("validate", "Validate Results", validate_github_results, depends_on=["analyze"])
            .build()
        )
        # This test will fail if the real MCP server isn't running, which is expected.
        # We are testing the integration code, not the server itself here.
        result = await workflow.execute()
        assert result.status == "completed"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Slack integration awaiting approval") # Keep this specific skip
    async def test_real_slack_integration(self, real_config_path, session_client_health_check):
        """Test with a real Slack MCP server (if configured)."""
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "C01234567")
        workflow = (WorkflowBuilder("e2e-slack", real_config_path)
            .slack_post("notify", test_channel, "🧪 E2E test message from GraphMCP")
            .custom_step("verify", "Verify Slack Post", verify_slack_post, depends_on=["notify"])
            .build()
        )
        result = await workflow.execute()
        assert result.status == "completed"
        assert result.step_results["notify"]["success"] is True 

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Slack integration awaiting approval") # Keep this specific skip
    async def test_slack_token_health_check(self, real_config_path, session_client_health_check):
        """Performs a basic health check on the Slack MCP token by listing users."""
        workflow = (WorkflowBuilder("e2e-slack-health", real_config_path)
            .custom_step("health_check", "Slack Token Health Check", self._slack_token_health_check)
            .build()
        )
        result = await workflow.execute()
        assert result.status == "completed"
        assert result.step_results["health_check"]["success"] is True

    @pytest.mark.asyncio
    async def _slack_token_health_check(self, context, step):
        from clients import SlackMCPClient
        client = context._clients.get('slack') or SlackMCPClient(context.config.config_path)
        context._clients['slack'] = client
        users = await client.list_users()
        return {"success": True, "user_count": len(users)}

    @pytest.mark.asyncio
    async def test_repomix_pack_remote_repository(self, real_config_path, session_client_health_check):
        """Test RepomixMCPClient pack_remote_repository with real repo."""
        repomix_client = RepomixMCPClient(real_config_path)
        
        try:
            # Test packing a small, known repository
            result = await repomix_client.pack_remote_repository(
                repo_url="https://github.com/neondatabase-labs/postgres-sample-dbs",
                include_patterns=["**/*"], # Broaden include patterns for testing
                exclude_patterns=["node_modules/**", ".git/**"]
            )
            
            # Verify pack result structure
            if "error" in result:
                print(f"❌ Repomix packing failed: {result['error']}")
                pytest.fail(f"Repomix packing failed with error: {result['error']}")

            assert result["success"] is True
            assert result["packed_files_count"] > 0
            print(f"✅ Repomix packed {result['packed_files_count']} files. Output: {result.get('output_path', 'N/A')}")

        except Exception as e:
            pytest.fail(f"test_repomix_pack_remote_repository failed: {e}")
        finally:
            await repomix_client.close()

    @pytest.mark.asyncio
    async def test_repomix_analyze_codebase_structure(self, real_config_path, session_client_health_check):
        """Test RepomixMCPClient analyze_codebase_structure."""
        repomix_client = RepomixMCPClient(real_config_path)
        
        try:
            # Test analyzing codebase structure
            result = await repomix_client.analyze_codebase_structure(
                repo_url="https://github.com/neondatabase-labs/postgres-sample-dbs"
            )
            
            # Verify structure analysis result
            if "error" in result:
                print(f"❌ Repomix analysis failed: {result['error']}")
                pytest.fail(f"Repomix analysis failed with error: {result['error']}")

            assert "repository_url" in result
            assert "files_analyzed" in result
            assert result["files_analyzed"] > 0
            print(f"✅ Repomix analyzed {result['files_analyzed']} files from {result['repository_url']}")

        except Exception as e:
            pytest.fail(f"test_repomix_analyze_codebase_structure failed: {e}")
        finally:
            await repomix_client.close()

    @pytest.mark.asyncio
    async def test_filesystem_operations(self, real_config_path, session_client_health_check):
        """Test basic filesystem operations with real Filesystem MCP server."""
        filesystem_client = FilesystemMCPClient(real_config_path)
        test_dir = Path(tempfile.mkdtemp())
        test_file = test_dir / "test_file.txt"
        file_content = "Hello, GraphMCP Filesystem!"
        
        try:
            # Write file
            write_success = await filesystem_client.write_file(str(test_file), file_content)
            assert write_success is True, "File write should succeed"
            print(f"✅ Successfully wrote to {test_file}")

            # Read file
            read_content = await filesystem_client.read_file(str(test_file))
            assert read_content == file_content, "Read content should match written content"
            print(f"✅ Successfully read from {test_file}")

            # List directory (should contain test_file)
            listed_files = await filesystem_client.list_dir(str(test_dir))
            assert str(test_file.name) in listed_files, "Test file should be in listed directory"
            print(f"✅ {test_file.name} found in {test_dir}")

        except Exception as e:
            pytest.fail(f"test_filesystem_operations failed: {e}")
        finally:
            if filesystem_client: 
                await filesystem_client.close()
            if test_dir.exists():
                import shutil
                shutil.rmtree(test_dir)

    @pytest.mark.asyncio
    async def test_github_repo_operations(self, real_config_path, session_client_health_check):
        """Test GitHub repository operations."""
        github_client = GitHubMCPClient(real_config_path)
        try:
            # Test get_repository
            repo_info = await github_client.get_repository("microsoft", "typescript")
            assert repo_info["name"] == "typescript"
            assert repo_info["owner"]["login"] == "microsoft"
            print(f"✅ Successfully retrieved GitHub repository info for {repo_info['full_name']}")

            # Test get_file_contents
            file_content_result = await github_client.get_file_contents(
                "microsoft", "typescript", "README.md"
            )
            assert "# TypeScript" in file_content_result
            print(f"✅ Successfully retrieved README.md content for microsoft/typescript")

        except Exception as e:
            pytest.fail(f"test_github_repo_operations failed: {e}")
        finally:
            await github_client.close()

    @pytest.mark.asyncio
    async def test_github_fork_and_branch_operations(self, real_config_path, github_test_fork, session_client_health_check):
        """Test GitHub fork and branch creation/deletion with real GitHub MCP server."""
        github_client = GitHubMCPClient(real_config_path)
        fork_data = github_test_fork

        try:
            # Fork the repository
            fork_result = await github_client.fork_repository(fork_data["source_owner"], fork_data["source_name"])
            assert fork_result["name"] == fork_data["source_name"]
            assert "full_name" in fork_result
            fork_data["fork_owner"] = fork_result["owner"]["login"]
            fork_data["created_fork"] = True
            print(f"✅ Successfully forked repository to {fork_data['fork_owner']}/{fork_data['fork_name']}")
            # Give GitHub some time to create the fork
            await asyncio.sleep(5) 

            # Create a new branch
            create_branch_result = await github_client.create_branch(
                fork_data["fork_owner"],
                fork_data["fork_name"],
                fork_data["test_branch"],
                from_branch="main" # Base branch for the new branch
            )
            assert "ref" in create_branch_result and fork_data["test_branch"] in create_branch_result["ref"]
            fork_data["created_branch"] = True
            print(f"✅ Successfully created branch {fork_data['test_branch']}")
            
        except Exception as e:
            pytest.fail(f"test_github_fork_and_branch_operations failed: {e}")
        finally:
            await github_client.close()

    # This test is intentionally skipped as Slack integration is awaiting proper setup.
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Slack integration awaiting approval") # Keep this specific skip
    async def test_slack_real_integration(self, real_config_path, session_client_health_check):
        """Test a real Slack integration by sending a message."""
        slack_client = SlackMCPClient(real_config_path)
        test_channel = os.getenv("SLACK_TEST_CHANNEL")
        if not test_channel:
            pytest.skip("SLACK_TEST_CHANNEL environment variable not set.")

        try:
            message_result = await slack_client.post_message(
                channel_id=test_channel,
                text="Hello from GraphMCP E2E test!"
            )
            assert message_result["ok"] is True
            assert "ts" in message_result
            print(f"✅ Successfully posted message to Slack channel {test_channel}")

        except Exception as e:
            pytest.fail(f"test_slack_real_integration failed: {e}")
        finally:
            await slack_client.close()

    @pytest.mark.asyncio
    async def test_db_decommission_workflow_integration(self, real_config_path, github_test_fork, session_client_health_check):
        """
        End-to-end test for the db_decommission workflow with real clients.
        This simulates a full run of the database decommissioning process.
        """
        # Use the real GitHub client to pre-create a dummy file for the workflow to find
        github_client = GitHubMCPClient(real_config_path)
        fork_data = github_test_fork
        if not fork_data.get("fork_owner") or not fork_data.get("test_branch"):
            pytest.skip("GitHub fork or test branch not available for db_decommission workflow.")

        dummy_file_path = f"test_db_decommission_{int(time.time())}.sql"
        dummy_file_content = "SELECT * FROM old_database;"

        try:
            # Ensure the test branch exists
            await github_client.create_branch(
                fork_data["fork_owner"],
                fork_data["fork_name"],
                fork_data["test_branch"],
                from_branch="main"
            )
            print(f"Ensured test branch {fork_data['test_branch']} exists.")

            # Create dummy SQL file for the workflow to find
            await github_client.create_or_update_file(
                owner=fork_data["fork_owner"],
                repo=fork_data["fork_name"],
                path=f"sql/{dummy_file_path}",
                content=dummy_file_content,
                message=f"Add dummy SQL file {dummy_file_path}",
                branch=fork_data["test_branch"]
            )
            print(f"Created dummy SQL file: sql/{dummy_file_path}")

            # Build and execute the workflow
            workflow = create_optimized_db_decommission_workflow(
                workflow_id="e2e-db-decommission",
                config_path=real_config_path,
                github_repo_owner=fork_data["fork_owner"],
                github_repo_name=fork_data["fork_name"],
                github_branch=fork_data["test_branch"],
                slack_channel=os.getenv("SLACK_TEST_CHANNEL", "C01234567"),
                db_pattern=".sql",
                dry_run=True
            )

            result = await workflow.execute()
            assert result.status == "completed"
            assert result.step_results["find_db_files"]["success"] is True
            assert dummy_file_path in result.step_results["find_db_files"]["found_files"]
            assert result.step_results["notify_slack"]["success"] is True # Assuming Slack post is successful
            print(f"✅ DB Decommission Workflow completed successfully for {dummy_file_path}")

        except Exception as e:
            pytest.fail(f"test_db_decommission_workflow_integration failed: {e}")
        finally:
            await github_client.close()

    @pytest.mark.asyncio
    async def test_multi_client_coordination(self, real_config_path, session_client_health_check):
        """Test coordination between multiple real MCP clients in a single workflow."""
        # This test ensures that different clients can be used sequentially
        # or in parallel within a single workflow without conflicts.
        
        github_client = GitHubMCPClient(real_config_path)
        filesystem_client = FilesystemMCPClient(real_config_path)
        repomix_client = RepomixMCPClient(real_config_path)
        
        test_temp_dir = Path(tempfile.mkdtemp())
        test_local_file = test_temp_dir / "coordinated_test.txt"
        initial_content = "Coordination test content."

        try:
            # 1. Filesystem: Write a local file
            write_success = await filesystem_client.write_file(str(test_local_file), initial_content)
            assert write_success is True, "Failed to write initial local file."

            # 2. GitHub: Get a repository info
            repo_info = await github_client.get_repository("microsoft", "vscode")
            assert repo_info["name"] == "vscode", "Failed to get VSCode repo info."

            # 3. Repomix: Pack a remote repository
            pack_result = await repomix_client.pack_remote_repository(
                repo_url="https://github.com/microsoft/vscode",
                include_patterns=["**/*.json"]
            )
            assert pack_result["success"] is True and pack_result["packed_files_count"] > 0, \
                "Failed to pack remote VSCode repository with JSON files."
            
            # 4. Filesystem: Read the local file to ensure it's still there
            read_content = await filesystem_client.read_file(str(test_local_file))
            assert read_content == initial_content, "Local file content changed unexpectedly."

            print("✅ Multi-client coordination test completed successfully.")

        except Exception as e:
            pytest.fail(f"test_multi_client_coordination failed: {e}")
        finally:
            if github_client: await github_client.close()
            if filesystem_client: await filesystem_client.close()
            if repomix_client: await repomix_client.close()
            if test_temp_dir.exists():
                import shutil
                shutil.rmtree(test_temp_dir) 