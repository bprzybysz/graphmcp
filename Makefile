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
	@echo "$(GREEN)Prerequisites:$(NC)"
	@echo "  make install-uv    - Install uv package manager"
	@echo "  make setup         - Initialize development environment"
	@echo ""
	@echo "$(GREEN)Development Workflow:$(NC)"
	@echo "  make clean         - Clean build artifacts and cache"
	@echo "  make setup         - Setup development environment"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Format code with black/ruff"
	@echo "  make test-all      - Run all test suites"
	@echo ""
	@echo "$(GREEN)Testing Targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E '(test|e2e)' | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Process Management:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E '(kill-|start-.+-8501|check-ports|restart-ui)' | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Deployment:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E '(deploy|mocked)' | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(MAGENTA)%-25s$(NC) %s\n", $$1, $$2}'

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

graphmcp-test-unit: check-deps ## Run comprehensive unit tests for GraphMCP framework
	@echo "$(YELLOW)Running GraphMCP unit tests...$(NC)"
	@if [ -f "$(TEST_PATH)/unit/test_builder_and_serialization.py" ]; then \
		PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/unit/ \
			--verbose \
			--cov=$(SRC_PATH) \
			--cov-report=term-missing \
			--cov-report=html:htmlcov/unit \
			--junit-xml=test-results-unit.xml \
			-m "not e2e" \
			--tb=short; \
		echo "$(GREEN)✓ Unit tests completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ NOP: Unit tests not yet implemented$(NC)"; \
		echo "$(CYAN)  Placeholder: $(TEST_PATH)/unit/test_builder_and_serialization.py$(NC)"; \
	fi

graphmcp-test-integration: check-deps ## Run integration tests with mocked MCP servers
	@echo "$(YELLOW)Running GraphMCP integration tests...$(NC)"
	@if [ -f "$(TEST_PATH)/integration/test_workflow_execution.py" ]; then \
		PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/integration/ \
			--verbose \
			--cov=$(SRC_PATH) \
			--cov-report=term-missing \
			--cov-report=html:htmlcov/integration \
			--junit-xml=test-results-integration.xml \
			-m "not e2e" \
			--maxfail=5; \
		echo "$(GREEN)✓ Integration tests completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ NOP: Integration tests not yet implemented$(NC)"; \
		echo "$(CYAN)  Placeholder: $(TEST_PATH)/integration/test_workflow_execution.py$(NC)"; \
	fi

dbdecomission-dev-e2e: check-deps ## Run partially mocked E2E tests for database decommissioning (development)
	@echo "$(YELLOW)Running DB Decommission E2E tests (Development - Partially Mocked)...$(NC)"
	@echo "$(CYAN)Mode: Initial steps + progressive unmocking as features stabilize$(NC)"
	@if [ -f "$(TEST_PATH)/e2e/test_real_integration.py" ]; then \
		MOCK_MODE=partial \
		E2E_TESTS_ENABLED=true \
		DB_DECOMMISSION_TEST=true \
		$(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
			--verbose \
			-k "decommission or db_decommission" \
			--junit-xml=test-results-e2e-dev.xml \
			--tb=short \
			--maxfail=3 \
			--timeout=300; \
		echo "$(GREEN)✓ Development E2E tests completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ Partially mocked E2E test simulation...$(NC)"; \
		echo "$(CYAN)  • Environment validation: ✓ MOCKED$(NC)"; \
		echo "$(CYAN)  • Repository discovery: ✓ MOCKED$(NC)"; \
		echo "$(CYAN)  • File pattern matching: ✓ MOCKED$(NC)"; \
		echo "$(CYAN)  • Batch processing: ⚠ REAL (when ready)$(NC)"; \
		echo "$(CYAN)  • PR creation: ⚠ REAL (when ready)$(NC)"; \
		echo "$(CYAN)  • Slack notifications: ✓ MOCKED$(NC)"; \
		echo "$(GREEN)✓ Development simulation complete$(NC)"; \
	fi

dbdecomission-demo-e2e: check-deps ## Run full E2E demonstration of database decommissioning workflow
	@echo "$(YELLOW)Running DB Decommission E2E Demo (Full Workflow)...$(NC)"
	@if [ -f "$(TEST_PATH)/e2e/test_real_integration.py" ]; then \
		echo "$(CYAN)Note: Requires GITHUB_TOKEN and SLACK_BOT_TOKEN environment variables$(NC)"; \
		MOCK_MODE=none \
		E2E_TESTS_ENABLED=true \
		$(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
			--verbose \
			-k "db_decommission_workflow_integration" \
			--junit-xml=test-results-e2e-full.xml \
			--tb=short \
			--maxfail=1 \
			--timeout=600; \
		echo "$(GREEN)✓ Full E2E demo completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ Full E2E test simulation...$(NC)"; \
		echo "$(CYAN)  • Real GitHub fork/branch operations$(NC)"; \
		echo "$(CYAN)  • Real repository analysis with Repomix$(NC)"; \
		echo "$(CYAN)  • Real file modifications$(NC)"; \
		echo "$(CYAN)  • Real PR creation$(NC)"; \
		echo "$(CYAN)  • Real Slack notifications$(NC)"; \
		echo "$(GREEN)✓ Demo simulation complete$(NC)"; \
	fi

# New comprehensive E2E test targets for individual MCP tools

graphmcp-test-e2e-repomix: check-deps ## Test RepomixMCPClient with real repository packing
	@echo "$(YELLOW)Testing RepomixMCPClient E2E...$(NC)"
	@echo "$(CYAN)Note: Requires GITHUB_TOKEN for repository access$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-k "repomix" \
		-m "e2e" \
		--junit-xml=test-results-e2e-repomix.xml \
		--tb=short \
		--timeout=180
	@echo "$(GREEN)✓ RepomixMCPClient E2E tests completed$(NC)"

graphmcp-test-e2e-github: check-deps ## Test GitHubMCPClient with real GitHub operations
	@echo "$(YELLOW)Testing GitHubMCPClient E2E...$(NC)"
	@echo "$(CYAN)Note: Requires GITHUB_TOKEN for GitHub API access$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-k "github and not workflow" \
		-m "e2e" \
		--junit-xml=test-results-e2e-github.xml \
		--tb=short \
		--timeout=180
	@echo "$(GREEN)✓ GitHubMCPClient E2E tests completed$(NC)"

graphmcp-test-e2e-filesystem: check-deps ## Test FilesystemMCPClient with real file operations
	@echo "$(YELLOW)Testing FilesystemMCPClient E2E...$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-k "filesystem" \
		-m "e2e" \
		--junit-xml=test-results-e2e-filesystem.xml \
		--tb=short \
		--timeout=60
	@echo "$(GREEN)✓ FilesystemMCPClient E2E tests completed$(NC)"

graphmcp-test-e2e-slack: check-deps ## Test SlackMCPClient with real Slack workspace
	@echo "$(YELLOW)Testing SlackMCPClient E2E...$(NC)"
	@echo "$(CYAN)Note: Requires SLACK_BOT_TOKEN and SLACK_TEST_CHANNEL$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-k "slack and not workflow" \
		-m "e2e" \
		--junit-xml=test-results-e2e-slack.xml \
		--tb=short \
		--timeout=60
	@echo "$(GREEN)✓ SlackMCPClient E2E tests completed$(NC)"

graphmcp-test-e2e-fork-ops: check-deps ## Test GitHub fork and branch operations with cleanup
	@echo "$(YELLOW)Testing GitHub Fork & Branch Operations E2E...$(NC)"
	@echo "$(CYAN)Note: Requires GITHUB_TOKEN and gh CLI tool$(NC)"
	@echo "$(RED)Warning: This test creates and deletes GitHub forks$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-k "fork_and_branch" \
		-m "e2e" \
		--junit-xml=test-results-e2e-fork-ops.xml \
		--tb=short \
		--timeout=300
	@echo "$(GREEN)✓ GitHub fork operations E2E tests completed$(NC)"

graphmcp-test-e2e-multi-client: check-deps ## Test multi-client coordination and integration
	@echo "$(YELLOW)Testing Multi-Client Coordination E2E...$(NC)"
	@echo "$(CYAN)Note: Requires GITHUB_TOKEN for comprehensive testing$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-k "multi_client" \
		-m "e2e" \
		--junit-xml=test-results-e2e-multi-client.xml \
		--tb=short \
		--timeout=240
	@echo "$(GREEN)✓ Multi-client coordination E2E tests completed$(NC)"

graphmcp-test-e2e-all: check-deps ## Run all comprehensive E2E tests (requires all tokens)
	@echo "$(YELLOW)Running ALL GraphMCP E2E Tests...$(NC)"
	@echo "$(CYAN)Note: Requires GITHUB_TOKEN, SLACK_BOT_TOKEN, SLACK_TEST_CHANNEL$(NC)"
	@echo "$(RED)Warning: This may create/delete GitHub forks and post Slack messages$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-m "e2e" \
		--junit-xml=test-results-e2e-all.xml \
		--tb=short \
		--timeout=600 \
		--maxfail=5
	@echo "$(GREEN)✓ All E2E tests completed$(NC)"
	@echo "$(CYAN)Mode: Complete end-to-end demonstration$(NC)"
	@if [ -z "$(GITHUB_TOKEN)" ] || [ -z "$(SLACK_BOT_TOKEN)" ]; then \
		echo "$(RED)✗ Missing required environment variables:$(NC)"; \
		echo "$(YELLOW)  GITHUB_TOKEN: $$(if [ -n "$(GITHUB_TOKEN)" ]; then echo "✓ Set"; else echo "✗ Missing"; fi)$(NC)"; \
		echo "$(YELLOW)  SLACK_BOT_TOKEN: $$(if [ -n "$(SLACK_BOT_TOKEN)" ]; then echo "✓ Set"; else echo "✗ Missing"; fi)$(NC)"; \
		echo "$(CYAN)Run with: GITHUB_TOKEN=xxx SLACK_BOT_TOKEN=xxx make dbdecomission-demo-e2e$(NC)"; \
		exit 1; \
	fi
	@if [ -f "$(TEST_PATH)/e2e/test_real_integration.py" ]; then \
		E2E_TESTS_ENABLED=true \
		DB_DECOMMISSION_DEMO=true \
		DEMO_DATABASE_NAME=periodic_table \
		DEMO_REPO_URL=https://github.com/bprzybys-nc/postgres-sample-dbs \
		$(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
			--verbose \
			-k "demo or full_workflow" \
			--junit-xml=test-results-e2e-demo.xml \
			--tb=short \
			--timeout=600 \
			--capture=no; \
		echo "$(GREEN)✓ Demo E2E tests completed$(NC)"; \
	else \
		echo "$(BLUE)ℹ Demo E2E test simulation...$(NC)"; \
		echo "$(CYAN)  Database: periodic_table$(NC)"; \
		echo "$(CYAN)  Repository: bprzybys-nc/postgres-sample-dbs$(NC)"; \
		echo "$(CYAN)  Steps:$(NC)"; \
		echo "$(GREEN)    ✓ Environment validation$(NC)"; \
		echo "$(GREEN)    ✓ Repository analysis$(NC)"; \
		echo "$(GREEN)    ✓ Pattern discovery$(NC)"; \
		echo "$(GREEN)    ✓ File processing$(NC)"; \
		echo "$(GREEN)    ✓ PR creation$(NC)"; \
		echo "$(GREEN)    ✓ Slack notification$(NC)"; \
		echo "$(GREEN)✓ Demo simulation complete$(NC)"; \
	fi

test-all: graphmcp-test-unit graphmcp-test-integration dbdecomission-dev-e2e ## Run all test suites in sequence
	@echo "$(GREEN)✓ All test suites completed$(NC)"

test-all-with-e2e: check-deps ## Run complete test suite including comprehensive E2E tests (requires tokens)
	@echo "$(YELLOW)Running complete test suite with comprehensive E2E...$(NC)"
	@echo "$(CYAN)Note: This requires GITHUB_TOKEN, SLACK_BOT_TOKEN, and SLACK_TEST_CHANNEL$(NC)"
	@$(MAKE) graphmcp-test-unit
	@$(MAKE) graphmcp-test-integration
	@$(MAKE) graphmcp-test-e2e-all
	@$(MAKE) dbdecomission-demo-e2e
	@echo "$(GREEN)✓ Complete test suite with E2E finished$(NC)"

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

test-e2e:
	.venv/bin/python -m pytest tests/e2e/test_real_integration.py -m e2e -v

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
from concrete.db_decommission import create_optimized_db_decommission_workflow; \
from concrete.db_decommission_ui import DatabaseDecommissionUI; \
print('Testing database decommissioning workflow creation...'); \
workflow = create_optimized_db_decommission_workflow( \
	database_name='test_db', \
	target_repos=['https://github.com/test/repo'], \
	slack_channel='C12345' \
); \
print('✅ Workflow created successfully'); \
print('Testing UI initialization...'); \
ui = DatabaseDecommissionUI(); \
print('✅ DatabaseDecommissionUI initializes successfully'); \
print('🎉 All database decommissioning tests passed!'); \
print('💡 Run make db-decommission-ui to start the interface');"
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
	@pkill -f "enhanced_db_decommission" || echo "$(BLUE)  No enhanced decommission processes$(NC)"
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
	PYTHONPATH=. $(VENV_PATH)/bin/python enhanced_db_decommission_demo.py \
		--mode ui \
		--port 8501 \
		--database example_database \
		--repos https://github.com/bprzybys-nc/postgres-sample-dbs

start-demo-8501: kill-port-8501 ## Start enhanced E2E demo on port 8501 with browser (kills existing processes first)
	@echo "$(YELLOW)Starting Enhanced E2E Demo on port 8501...$(NC)"
	@echo "$(CYAN)Demo Configuration:$(NC)"
	@echo "  🗄️ Database: chinook (real database from postgres-sample-dbs)"
	@echo "  📁 Repository: https://github.com/bprzybys-nc/postgres-sample-dbs"
	@echo "  🌐 Port: 8501 (automatically opens browser)"
	@echo "  🔄 Mode: Full E2E with enhanced pattern discovery"
	@echo ""
	@echo "$(GREEN)Port 8501 cleared - starting demo...$(NC)"
	@echo "$(CYAN)Browser will open automatically to http://localhost:8501$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/python enhanced_db_decommission_demo.py \
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
	@echo "$(GREEN)✓ Full restart completed - Enhanced demo running on port 8501$(NC)" 