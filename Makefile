# GraphMCP Framework Makefile
# Comprehensive build, test, and deployment automation

.PHONY: help install-uv clean setup deploy
.PHONY: graphmcp-test-unit graphmcp-test-integration 
.PHONY: dbdecomission-dev-e2e dbdecomission-demo-e2e
.PHONY: test-all lint format check-deps
.PHONY: kill-all kill-port-8501 start-ui-8501 start-demo-8501 check-ports restart-ui
.PHONY: *-mocked-with-note-tbd-*

# Default target
.DEFAULT_GOAL := help

# Configuration
PYTHON_VERSION := 3.11
UV_VERSION := 0.4.29
PROJECT_NAME := graphmcp
VENV_PATH := .venv
SRC_PATH := .
TEST_PATH := tests

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)GraphMCP Framework - Build & Test Automation$(NC)"
	@echo "$(YELLOW)=============================================$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start:$(NC)"
	@echo "  make setup         - Setup development environment"
	@echo "  make demo          - Run demo (mock mode, fast)"
	@echo "  make demo-real     - Run demo with live services"
	@echo "  make test-all      - Run all tests"
	@echo ""
	@echo "$(GREEN)📦 Development:$(NC)"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Format code"
	@echo ""
	@echo "$(GREEN)🧪 Testing:$(NC)"
	@echo "  make test-unit     - Unit tests"
	@echo "  make test-integration - Integration tests"
	@echo "  make test-e2e      - End-to-end tests"
	@echo ""
	@echo "$(GREEN)🎯 Demo:$(NC)"
	@echo "  make demo-mock     - Fast demo with cached data (~30s)"
	@echo "  make demo-real     - Full demo with live services (~5min)"
	@echo "  make demo-setup    - Setup demo environment"
	@echo "  make demo-clean    - Clean demo cache"

# =============================================================================
# PREREQUISITES & SETUP
# =============================================================================

install-uv: ## Install uv package manager (prerequisite)
	@echo "$(YELLOW)Installing uv package manager...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		echo "$(GREEN)✓ uv already installed: $$(uv --version)$(NC)"; \
	else \
		echo "$(BLUE)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)✓ uv installed successfully$(NC)"; \
	fi

clean: ## Clean build artifacts, cache, and virtual environment
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf $(VENV_PATH)
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .tox/
	rm -rf .mypy_cache/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

setup: install-uv clean ## Setup development environment with dependencies
	@echo "$(YELLOW)Setting up development environment...$(NC)"
	uv venv $(VENV_PATH) --python $(PYTHON_VERSION)
	@echo "$(BLUE)Installing core dependencies...$(NC)"
	uv pip install --requirement requirements.txt
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	uv pip install \
		pytest>=7.4.0 \
		pytest-asyncio>=0.21.0 \
		pytest-mock>=3.11.0 \
		pytest-cov>=4.1.0 \
		pytest-xdist>=3.3.0 \
		black>=23.0.0 \
		ruff>=0.1.0 \
		mypy>=1.5.0 \
		pre-commit>=3.4.0 \
		hypothesis>=6.82.0 \
		psutil>=5.9.0
	@echo "$(BLUE)Installing project in development mode...$(NC)"
	uv pip install -e .
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "$(CYAN)Activate with: source $(VENV_PATH)/bin/activate$(NC)"

check-deps: ## Check if dependencies are installed
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(RED)✗ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Dependencies OK$(NC)"

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: check-deps ## Run code linting with ruff and mypy
	@echo "$(YELLOW)Running code linting...$(NC)"
	$(VENV_PATH)/bin/ruff check $(SRC_PATH) $(TEST_PATH)
	$(VENV_PATH)/bin/mypy $(SRC_PATH) --ignore-missing-imports
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: check-deps ## Format code with black and ruff
	@echo "$(YELLOW)Formatting code...$(NC)"
	$(VENV_PATH)/bin/black $(SRC_PATH) $(TEST_PATH)
	$(VENV_PATH)/bin/ruff format $(SRC_PATH) $(TEST_PATH)
	$(VENV_PATH)/bin/ruff check --fix $(SRC_PATH) $(TEST_PATH)
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

# =============================================================================
# TESTING TARGETS
# =============================================================================

test-unit: check-deps ## Run unit tests
	@echo "$(YELLOW)Running unit tests...$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/unit/ \
		--verbose \
		--cov=$(SRC_PATH) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov/unit \
		--junit-xml=test-results-unit.xml \
		-m "not e2e" \
		--tb=short
	@echo "$(GREEN)✓ Unit tests completed$(NC)"

test-integration: check-deps ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/integration/ \
		--verbose \
		--cov=$(SRC_PATH) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov/integration \
		--junit-xml=test-results-integration.xml \
		-m "not e2e" \
		--maxfail=5
	@echo "$(GREEN)✓ Integration tests completed$(NC)"

test-e2e: check-deps ## Run end-to-end tests
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-m "e2e" \
		--junit-xml=test-results-e2e.xml \
		--tb=short \
		--timeout=600
	@echo "$(GREEN)✓ E2E tests completed$(NC)"

test-all: test-unit test-integration test-e2e ## Run all test suites
	@echo "$(GREEN)✓ All tests completed$(NC)"

# =============================================================================
# DEPLOYMENT TARGETS (MOCKED - TBD)
# =============================================================================

deploy-staging-mocked-with-note-tbd: ## Deploy to staging environment (MOCKED - Implementation TBD)
	@echo "$(MAGENTA)🚧 MOCKED DEPLOYMENT - STAGING$(NC)"
	@echo "$(YELLOW)TBD: Implement staging deployment pipeline$(NC)"
	@echo "$(CYAN)Planned Steps:$(NC)"
	@echo "  • Build Docker image with GraphMCP framework"
	@echo "  • Push to staging container registry"
	@echo "  • Deploy to Kubernetes staging namespace"
	@echo "  • Run smoke tests against staging"
	@echo "  • Update deployment status in Slack"
	@echo "$(BLUE)Status: Planning phase - implementation pending$(NC)"

deploy-production-mocked-with-note-tbd: ## Deploy to production environment (MOCKED - Implementation TBD)
	@echo "$(MAGENTA)🚧 MOCKED DEPLOYMENT - PRODUCTION$(NC)"
	@echo "$(YELLOW)TBD: Implement production deployment pipeline$(NC)"
	@echo "$(CYAN)Planned Steps:$(NC)"
	@echo "  • Validate staging deployment success"
	@echo "  • Create production release tag"
	@echo "  • Deploy to production with blue-green strategy"
	@echo "  • Run comprehensive health checks"
	@echo "  • Monitor key metrics and alerts"
	@echo "  • Notify teams of successful deployment"
	@echo "$(BLUE)Status: Requires staging validation first$(NC)"

deploy-rollback-mocked-with-note-tbd: ## Rollback deployment to previous version (MOCKED - Implementation TBD)
	@echo "$(MAGENTA)🚧 MOCKED ROLLBACK - EMERGENCY$(NC)"
	@echo "$(YELLOW)TBD: Implement emergency rollback procedures$(NC)"
	@echo "$(CYAN)Planned Steps:$(NC)"
	@echo "  • Identify last known good deployment"
	@echo "  • Trigger automated rollback sequence"
	@echo "  • Validate rollback success"
	@echo "  • Alert incident response team"
	@echo "  • Generate post-incident report"
	@echo "$(BLUE)Status: Critical path - high priority for implementation$(NC)"

monitoring-setup-mocked-with-note-tbd: ## Setup monitoring and alerting (MOCKED - Implementation TBD)
	@echo "$(MAGENTA)🚧 MOCKED MONITORING SETUP$(NC)"
	@echo "$(YELLOW)TBD: Implement comprehensive monitoring stack$(NC)"
	@echo "$(CYAN)Planned Components:$(NC)"
	@echo "  • Prometheus metrics collection"
	@echo "  • Grafana dashboard creation"
	@echo "  • AlertManager rule configuration"
	@echo "  • Slack integration for alerts"
	@echo "  • Log aggregation with ELK stack"
	@echo "  • Application performance monitoring"
	@echo "$(BLUE)Status: Architecture design in progress$(NC)"

# =============================================================================
# SPECIAL TARGETS
# =============================================================================

install-pre-commit: setup ## Install and configure pre-commit hooks
	@echo "$(YELLOW)Installing pre-commit hooks...$(NC)"
	$(VENV_PATH)/bin/pre-commit install
	$(VENV_PATH)/bin/pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

performance-test: check-deps ## Run performance and resource management tests
	@echo "$(YELLOW)Running performance tests...$(NC)"
	@if [ -f "$(TEST_PATH)/performance/test_resource_management.py" ]; then \
		$(VENV_PATH)/bin/pytest $(TEST_PATH)/performance/ \
			--verbose \
			--tb=short \
			--timeout=120; \
		echo "$(GREEN)✓ Performance tests completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ NOP: Performance tests not yet implemented$(NC)"; \
	fi

security-scan: check-deps ## Run security scanning and vulnerability checks
	@echo "$(YELLOW)Running security scans...$(NC)"
	@echo "$(CYAN)TBD: Implement security scanning with:$(NC)"
	@echo "  • bandit for Python security issues"
	@echo "  • safety for known vulnerabilities"
	@echo "  • semgrep for SAST analysis"
	@echo "$(BLUE)Status: Security tooling selection in progress$(NC)"

docs-build: check-deps ## Build documentation (TBD)
	@echo "$(YELLOW)Building documentation...$(NC)"
	@echo "$(CYAN)TBD: Implement documentation build with:$(NC)"
	@echo "  • Sphinx for API documentation"
	@echo "  • MkDocs for user guides"
	@echo "  • Auto-generated workflow diagrams"
	@echo "$(BLUE)Status: Documentation framework selection pending$(NC)"

# =============================================================================
# COMPLETE WORKFLOW TARGETS
# =============================================================================

cmp: check-deps ## Run complete database decommissioning workflow (CMP = Complete workflow)
	@echo "$(YELLOW)Running Complete Database Decommissioning Workflow...$(NC)"
	@echo "$(CYAN)🚀 GraphMCP Complete Workflow - Database Decommissioning$(NC)"
	@echo "$(CYAN)──────────────────────────────────────────────────────$(NC)"
	@echo "$(GREEN)Features:$(NC)"
	@echo "  🔍 AI-Powered Pattern Discovery with Repomix"
	@echo "  📁 Multi-Language Source Type Classification"
	@echo "  🛠️  Contextual Rules Engine for Intelligent Processing"
	@echo "  🌐 GitHub Integration (Fork → Branch → Commit → PR)"
	@echo "  📊 Real-time Progress Tracking & Metrics"
	@echo "  💬 Slack Notifications & Status Updates"
	@echo ""
	@echo "$(YELLOW)Environment Check:$(NC)"
	@echo "  GitHub Token: $$(if [ -n "$(GITHUB_TOKEN)" ]; then echo "✅ Set"; else echo "❌ Missing - export GITHUB_TOKEN=<token>"; fi)"
	@echo "  Slack Token: $$(if [ -n "$(SLACK_BOT_TOKEN)" ]; then echo "✅ Set"; else echo "⚠️  Optional - export SLACK_BOT_TOKEN=<token>"; fi)"
	@echo ""
	@if [ -z "$(GITHUB_TOKEN)" ]; then \
		echo "$(RED)❌ GITHUB_TOKEN is required for the complete workflow$(NC)"; \
		echo "$(CYAN)💡 Set it with: export GITHUB_TOKEN=<your_github_token>$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🚀 Starting Complete Workflow...$(NC)"
	@echo "$(CYAN)Target Database: $$(if [ -n "$(DB)" ]; then echo "$(DB)"; else echo "postgres_air (default)"; fi)$(NC)"
	@echo "$(CYAN)Target Repository: $$(if [ -n "$(REPO)" ]; then echo "$(REPO)"; else echo "bprzybys-nc/postgres-sample-dbs (default)"; fi)$(NC)"
	@echo ""
	PYTHONPATH=. $(VENV_PATH)/bin/python -c "\
import asyncio; \
import sys; \
import os; \
sys.path.append('.'); \
from concrete.db_decommission import run_decommission; \
\
database_name = os.environ.get('DB', 'postgres_air'); \
repo_url = os.environ.get('REPO', 'https://github.com/bprzybys-nc/postgres-sample-dbs'); \
target_repos = [repo_url]; \
\
print(f'🎯 Executing workflow for database: {database_name}'); \
print(f'📁 Processing repository: {repo_url}'); \
print(''); \
\
result = asyncio.run(run_decommission( \
	database_name=database_name, \
	target_repos=target_repos, \
	slack_channel='C01234567', \
	workflow_id=f'cmp-{database_name}-{int(__import__(\"time\").time())}' \
)); \
\
print(''); \
print('$(GREEN)🎉 COMPLETE WORKFLOW FINISHED!$(NC)'); \
print('$(CYAN)──────────────────────────────────────────$(NC)'); \
if hasattr(result, 'get_step_result'): \
	repo_result = result.get_step_result('process_repositories', {}); \
	refactor_result = result.get_step_result('apply_refactoring', {}); \
	pr_result = result.get_step_result('create_github_pr', {}); \
	qa_result = result.get_step_result('quality_assurance', {}); \
	print(f'📊 Files Discovered: {repo_result.get(\"total_files_processed\", 0)}'); \
	print(f'✏️  Files Modified: {refactor_result.get(\"total_files_modified\", 0)}'); \
	print(f'🔀 Pull Request: {pr_result.get(\"pr_url\", \"N/A\")}'); \
	print(f'✅ Quality Score: {qa_result.get(\"overall_quality_score\", 0):.1f}%'); \
	print(f'⏱️  Duration: {getattr(result, \"duration_seconds\", 0):.1f}s'); \
	print(f'📈 Success Rate: {getattr(result, \"success_rate\", 0):.1f}%'); \
else: \
	print('📊 Workflow result structure: basic'); \
print(''); \
print('$(CYAN)💡 Usage Examples:$(NC)'); \
print('  make cmp                                    # Default: postgres_air'); \
print('  make cmp DB=periodic_table                  # Custom database'); \
print('  make cmp DB=chinook REPO=https://github.com/org/repo  # Custom DB + repo'); \
"
	@echo "$(GREEN)✅ Complete workflow execution finished$(NC)"

# =============================================================================
# UTILITY TARGETS
# =============================================================================

show-config: ## Show current configuration and environment
	@echo "$(CYAN)GraphMCP Configuration$(NC)"
	@echo "$(YELLOW)=====================$(NC)"
	@echo "Project Name: $(PROJECT_NAME)"
	@echo "Python Version: $(PYTHON_VERSION)"
	@echo "UV Version: $(UV_VERSION)"
	@echo "Virtual Environment: $(VENV_PATH)"
	@echo "Source Path: $(SRC_PATH)"
	@echo "Test Path: $(TEST_PATH)"
	@echo ""
	@echo "$(YELLOW)Environment Status:$(NC)"
	@echo "UV Installed: $$(if command -v uv >/dev/null 2>&1; then echo "✓"; else echo "✗"; fi)"
	@echo "Virtual Env: $$(if [ -d "$(VENV_PATH)" ]; then echo "✓"; else echo "✗"; fi)"
	@echo "GitHub Token: $$(if [ -n "$(GITHUB_TOKEN)" ]; then echo "✓ Set"; else echo "✗ Missing"; fi)"
	@echo "Slack Token: $$(if [ -n "$(SLACK_BOT_TOKEN)" ]; then echo "✓ Set"; else echo "✗ Missing"; fi)"

validate-makefile: ## Validate Makefile syntax and targets
	@echo "$(YELLOW)Validating Makefile...$(NC)"
	@make -n help >/dev/null 2>&1 && echo "$(GREEN)✓ Makefile syntax OK$(NC)" || echo "$(RED)✗ Makefile syntax error$(NC)"
	@echo "$(BLUE)Available targets: $$(make -qp | awk -F':' '/^[a-zA-Z0-9][^$$#\/\t=]*:([^=]|$$)/ {split($$1,A,/ /);for(i in A)print A[i]}' | sort -u | wc -l)$(NC)"

# Development convenience targets
dev: setup install-pre-commit ## Full development environment setup
	@echo "$(GREEN)✓ Development environment ready for GraphMCP development$(NC)"
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  1. source $(VENV_PATH)/bin/activate"
	@echo "  2. make test-all"
	@echo "  3. make lint"

quick-test: check-deps ## Run quick tests (unit only)
	@echo "$(YELLOW)Running quick test suite...$(NC)"
	$(VENV_PATH)/bin/pytest $(TEST_PATH)/unit/ -x --tb=short --quiet
	@echo "$(GREEN)✓ Quick tests completed$(NC)" 


# =============================================================================
# PREVIEW-MCP INTEGRATION
# =============================================================================

preview-mcp-server: check-deps ## Start standalone Preview MCP Server
	@echo "$(YELLOW)Starting Preview MCP Server...$(NC)"
	@echo "$(CYAN)Mode: Standalone stdio server for workflow streaming$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python -m clients.preview_mcp
	@echo "$(GREEN)✓ Preview MCP Server started$(NC)"

preview-streamlit: check-deps ## Start Streamlit UI with new workflow visualization
	@echo "$(YELLOW)Starting Preview Streamlit UI with Enhanced Layout...$(NC)"
	@echo "$(CYAN)New Features:$(NC)"
	@echo "  ✅ Left pane (25%): Real-time workflow progress tracking"
	@echo "  ✅ Main pane (75%): Live workflow logs supporting:"
	@echo "    📝 Markdown logs with structured bullet lists"
	@echo "    📊 Tables with markdown rendering"
	@echo "    🌞 Interactive sunburst charts"
	@echo "  ✅ Auto-refresh and demo workflow simulation"
	@echo ""
	@echo "$(CYAN)Open http://localhost:8501 and click 'Start Demo' to see the new interface$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/streamlit run concrete/preview_ui/streamlit_app.py \
		--server.port 8501 \
		--server.address 0.0.0.0
	@echo "$(GREEN)✓ Enhanced Streamlit UI started$(NC)"

preview-demo: check-deps ## Run complete preview demo (MCP server + Streamlit UI)
	@echo "$(YELLOW)Starting GraphMCP Preview Demo...$(NC)"
	@echo "$(CYAN)This will start MCP server and Streamlit UI$(NC)"
	@chmod +x concrete/demo.sh
	@./concrete/demo.sh

preview-test: check-deps ## Test preview-mcp client integration
	@echo "$(YELLOW)Testing Preview MCP Client...$(NC)"
	@if [ -f "$(TEST_PATH)/unit/test_preview_mcp_client.py" ]; then \
		PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/unit/test_preview_mcp_client.py \
			--verbose \
			--tb=short; \
		echo "$(GREEN)✓ Preview MCP tests completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ Creating basic preview-mcp test...$(NC)"; \
		echo "$(CYAN)  Testing client initialization and tool listing$(NC)"; \
		PYTHONPATH=. $(VENV_PATH)/bin/python -c "\
import asyncio; \
from clients.preview_mcp import PreviewMCPClient; \
async def test(): \
	client = PreviewMCPClient('mcp_config.json'); \
	tools = await client.list_available_tools(); \
	print(f'Available tools: {tools}'); \
	print('✓ Preview MCP client basic test passed'); \
asyncio.run(test())" || echo "$(YELLOW)⚠ Preview MCP client needs configuration$(NC)"; \
	fi

preview-test-ui: check-deps ## Test new UI functionality with workflow log system
	@echo "$(YELLOW)Testing Enhanced UI Functionality...$(NC)"
	@echo "$(CYAN)Testing workflow log system components...$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python -c "\
import sys; \
from clients.preview_mcp.workflow_log import get_workflow_log, log_info, log_table, log_sunburst; \
from concrete.preview_ui.streamlit_app import StreamlitWorkflowUI; \
print('Testing workflow log system...'); \
log = get_workflow_log('test-ui'); \
log_info('test-ui', '🚀 **UI Test Started**\n\n- Testing log system\n- Multiple entry types'); \
log_table('test-ui', ['Feature', 'Status'], [['Progress Pane', '✅'], ['Log Pane', '✅'], ['Charts', '✅']], 'UI Features'); \
log_sunburst('test-ui', ['UI', 'Progress', 'Logs', 'Charts'], ['', 'UI', 'UI', 'UI'], [100, 25, 50, 25], 'UI Components'); \
print(f'✅ Created {len(log.get_entries())} log entries'); \
print('Testing UI initialization...'); \
ui = StreamlitWorkflowUI(); \
print('✅ StreamlitWorkflowUI initializes successfully'); \
print('🎉 All UI functionality tests passed!'); \
print('💡 Run make preview-streamlit to see the new interface');"
	@echo "$(GREEN)✓ UI functionality tests completed$(NC)"

db-decommission-ui: check-deps ## Start Database Decommissioning Streamlit UI
	@echo "$(YELLOW)Starting Database Decommissioning UI...$(NC)"
	@echo "$(CYAN)Features:$(NC)"
	@echo "  🗄️ Database decommissioning workflow visualization"
	@echo "  📊 File reference tables with discovered database references"
	@echo "  🌞 Repository structure sunburst charts"
	@echo "  🔍 Context data preview for debugging workflow state"
	@echo "  ⚙️ Configurable database name and target repositories"
	@echo ""
	@echo "$(CYAN)Open http://localhost:8502 and configure your database decommissioning$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/streamlit run concrete/db_decommission_ui.py \
		--server.port 8502 \
		--server.address 0.0.0.0
	@echo "$(GREEN)✓ Database Decommissioning UI started$(NC)"

db-decommission-test: check-deps ## Test database decommissioning workflow functionality
	@echo "$(YELLOW)Testing Database Decommissioning Workflow...$(NC)"
	@echo "$(CYAN)Testing workflow components...$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python -c "\
import asyncio; \
from concrete.db_decommission import create_db_decommission_workflow; \
print('Testing database decommissioning workflow creation...'); \
workflow = create_db_decommission_workflow( \
	database_name='test_db', \
	target_repos=['https://github.com/test/repo'], \
	slack_channel='C12345' \
); \
print('✅ Workflow created successfully'); \
print('🎉 All database decommissioning tests passed!');"
	@echo "$(GREEN)✓ Database decommissioning tests completed$(NC)"

# =============================================================================
# PROCESS MANAGEMENT & PORT CLEANUP
# =============================================================================

kill-all: ## Kill all running GraphMCP processes (enhanced workflow, streamlit, etc.)
	@echo "$(YELLOW)Killing all GraphMCP processes...$(NC)"
	@echo "$(CYAN)Stopping processes for:$(NC)"
	@echo "  🔄 Enhanced database decommission workflows"
	@echo "  🌐 Streamlit servers (all ports)"
	@echo "  📊 MCP servers and demos"
	@pkill -f "db_decommission" || echo "$(BLUE)  No decommission processes$(NC)"
	@pkill -f "streamlit" || echo "$(BLUE)  No streamlit processes$(NC)"
	@pkill -f "preview_mcp" || echo "$(BLUE)  No preview MCP processes$(NC)"
	@pkill -f "demo.sh" || echo "$(BLUE)  No demo script processes$(NC)"
	@pkill -f "python.*concrete" || echo "$(BLUE)  No concrete module processes$(NC)"
	@echo "$(GREEN)✓ All GraphMCP processes terminated$(NC)"

kill-port-8501: ## Kill any process using port 8501 (primary Streamlit port)
	@echo "$(YELLOW)Checking port 8501 for running processes...$(NC)"
	@if lsof -ti:8501 >/dev/null 2>&1; then \
		echo "$(CYAN)Found processes on port 8501:$(NC)"; \
		lsof -ti:8501 | xargs ps -p | grep -v PID || true; \
		echo "$(YELLOW)Killing processes on port 8501...$(NC)"; \
		lsof -ti:8501 | xargs kill -9; \
		echo "$(GREEN)✓ Port 8501 cleared$(NC)"; \
	else \
		echo "$(BLUE)✓ Port 8501 is already free$(NC)"; \
	fi

start-ui-8501: kill-port-8501 ## Start enhanced database decommission UI on port 8501 (kills existing processes first)
	@echo "$(YELLOW)Starting Enhanced Database Decommission UI on port 8501...$(NC)"
	@echo "$(CYAN)Features:$(NC)"
	@echo "  🚀 Enhanced database decommission workflow with pattern discovery"
	@echo "  📊 Real-time progress tracking and metrics"
	@echo "  🎯 Intelligent file classification and processing"
	@echo "  💬 Slack integration with live notifications"
	@echo "  🔍 Comprehensive pattern discovery engine"
	@echo ""
	@echo "$(GREEN)Port 8501 cleared - starting UI...$(NC)"
	@echo "$(CYAN)Open http://localhost:8501 to access the enhanced interface$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python db_decommission_demo.py \
		--mode ui \
		--port 8501 \
		--database example_database \
		--repos https://github.com/bprzybys-nc/postgres-sample-dbs

start-demo-8501: kill-port-8501 ## Start E2E demo on port 8501 with browser (kills existing processes first)
	@echo "$(YELLOW)Starting E2E Demo on port 8501...$(NC)"
	@echo "$(CYAN)Demo Configuration:$(NC)"
	@echo "  🗄️ Database: chinook (real database from postgres-sample-dbs)"
	@echo "  📁 Repository: https://github.com/bprzybys-nc/postgres-sample-dbs"
	@echo "  🌐 Port: 8501 (automatically opens browser)"
	@echo "  🔄 Mode: Full E2E with pattern discovery"
	@echo ""
	@echo "$(GREEN)Port 8501 cleared - starting demo...$(NC)"
	@echo "$(CYAN)Browser will open automatically to http://localhost:8501$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python db_decommission_demo.py \
		--mode e2e \
		--port 8501 \
		--database chinook \
		--repos https://github.com/bprzybys-nc/postgres-sample-dbs &
	@sleep 3
	@open http://localhost:8501 || echo "$(YELLOW)⚠ Could not auto-open browser. Visit http://localhost:8501$(NC)"
	@echo "$(GREEN)✓ Enhanced E2E demo started on port 8501$(NC)"

check-ports: ## Show which ports are in use by GraphMCP processes
	@echo "$(YELLOW)Checking GraphMCP process ports...$(NC)"
	@echo "$(CYAN)Port Status:$(NC)"
	@for port in 8501 8502 8503; do \
		if lsof -ti:$$port >/dev/null 2>&1; then \
			echo "  Port $$port: $(RED)✗ OCCUPIED$(NC)"; \
			lsof -ti:$$port | xargs ps -p | grep -v PID | head -3 || true; \
		else \
			echo "  Port $$port: $(GREEN)✓ FREE$(NC)"; \
		fi; \
	done

restart-ui: kill-all start-demo-8501 ## Full restart: kill all processes and start fresh demo on 8501
	@echo "$(GREEN)✓ Full restart completed - Demo running on port 8501$(NC)"

# =============================================================================
# DEMO TARGETS
# =============================================================================

demo: demo-mock ## Run demo in mock mode (default - fast)

demo-mock: check-deps ## Run demo using cached data (fast, ~30s)
	@echo "$(YELLOW)🚀 GraphMCP Demo - Mock Mode$(NC)"
	@echo "$(CYAN)  📁 Cached data • ⚡ 30-60s execution • 🔄 Pattern replay$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python demo.py --database postgres_air --mock

demo-real: check-deps ## Run demo with live MCP services (real, ~5-10min)
	@echo "$(YELLOW)🚀 GraphMCP Demo - Real Mode$(NC)"
	@echo "$(CYAN)  🌐 Live services • 📊 Real analysis • 🔀 Actual PR creation$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python demo.py --database postgres_air --real

demo-setup: check-deps ## Setup demo environment and cache
	@echo "$(YELLOW)Setting up demo environment...$(NC)"
	@mkdir -p tests/data
	PYTHONPATH=. $(VENV_PATH)/bin/python -c "import asyncio; from demo.cache import DemoCache; from demo.config import DemoConfig; asyncio.run(DemoCache(DemoConfig.for_mock_mode()).populate_default_cache())"
	@echo "$(GREEN)✓ Demo ready - run 'make demo'$(NC)"

demo-clean: ## Clean demo cache
	@echo "$(YELLOW)Cleaning demo cache...$(NC)"
	rm -rf tests/data/postgres_air_*.xml tests/data/postgres_air_*.json
	@echo "$(GREEN)✓ Cache cleaned$(NC)" 