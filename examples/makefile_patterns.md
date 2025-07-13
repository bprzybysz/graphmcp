# GraphMCP Makefile Patterns

This demonstrates the comprehensive Makefile patterns used in GraphMCP for build automation, testing, and deployment.

## Key Patterns to Follow

### 1. Comprehensive Help System
```makefile
help: ## Show this help message
	@echo "$(CYAN)GraphMCP Framework - Build & Test Automation$(NC)"
	@echo "$(YELLOW)=============================================$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-25s$(NC) %s\n", $$1, $$2}'
```

### 2. Colored Output for Better UX
```makefile
# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m # No Color
```

### 3. Environment Setup with Modern Tools
```makefile
install-uv: ## Install uv package manager (prerequisite)
	@if command -v uv >/dev/null 2>&1; then \
		echo "$(GREEN)✓ uv already installed: $$(uv --version)$(NC)"; \
	else \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

setup: install-uv clean ## Setup development environment with dependencies
	uv venv $(VENV_PATH) --python $(PYTHON_VERSION)
	uv pip install --requirement requirements.txt
	uv pip install -e .
```

### 4. Comprehensive Testing Strategy
```makefile
# Multiple test levels with clear separation
graphmcp-test-unit: check-deps ## Run comprehensive unit tests
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/unit/ \
		--verbose \
		--cov=$(SRC_PATH) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov/unit \
		-m "not e2e"

graphmcp-test-integration: check-deps ## Run integration tests with mocked MCP servers  
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/integration/ \
		--verbose \
		-m "not e2e" \
		--maxfail=5

graphmcp-test-e2e-all: check-deps ## Run all comprehensive E2E tests
	@echo "$(CYAN)Note: Requires GITHUB_TOKEN, SLACK_BOT_TOKEN, SLACK_TEST_CHANNEL$(NC)"
	PYTHONPATH=. $(VENV_PATH)/bin/pytest $(TEST_PATH)/e2e/ \
		--verbose \
		-m "e2e" \
		--timeout=600 \
		--maxfail=5
```

### 5. Process Management and Port Cleanup
```makefile
kill-all: ## Kill all running GraphMCP processes
	@pkill -f "db_decommission" || echo "$(BLUE)  No decommission processes$(NC)"
	@pkill -f "streamlit" || echo "$(BLUE)  No streamlit processes$(NC)"
	@pkill -f "preview_mcp" || echo "$(BLUE)  No preview MCP processes$(NC)"

check-ports: ## Show which ports are in use by GraphMCP processes
	@for port in 8501 8502 8503; do \
		if lsof -ti:$$port >/dev/null 2>&1; then \
			echo "  Port $$port: $(RED)✗ OCCUPIED$(NC)"; \
		else \
			echo "  Port $$port: $(GREEN)✓ FREE$(NC)"; \
		fi; \
	done
```

### 6. Complete Workflow Targets
```makefile
cmp: check-deps ## Run complete database decommissioning workflow
	@echo "$(YELLOW)Running Complete Database Decommissioning Workflow...$(NC)"
	@if [ -z "$(GITHUB_TOKEN)" ]; then \
		echo "$(RED)❌ GITHUB_TOKEN is required$(NC)"; \
		exit 1; \
	fi
	PYTHONPATH=. $(VENV_PATH)/bin/python -c "\
import asyncio; \
from concrete.db_decommission import run_decommission; \
result = asyncio.run(run_decommission( \
	database_name='$(DB)', \
	target_repos=['$(REPO)'], \
	slack_channel='C01234567' \
));"
```

### 7. Development Environment Management
```makefile
dev: setup install-pre-commit ## Full development environment setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  1. source $(VENV_PATH)/bin/activate"
	@echo "  2. make test-all"
	@echo "  3. make lint"

clean: ## Clean build artifacts, cache, and virtual environment
	rm -rf $(VENV_PATH) build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .ruff_cache/ __pycache__/
	find . -type f -name "*.pyc" -delete
```

### 8. Code Quality and Linting
```makefile
lint: check-deps ## Run code linting with ruff and mypy
	$(VENV_PATH)/bin/ruff check $(SRC_PATH) $(TEST_PATH)
	$(VENV_PATH)/bin/mypy $(SRC_PATH) --ignore-missing-imports

format: check-deps ## Format code with black and ruff
	$(VENV_PATH)/bin/black $(SRC_PATH) $(TEST_PATH)
	$(VENV_PATH)/bin/ruff format $(SRC_PATH) $(TEST_PATH)
	$(VENV_PATH)/bin/ruff check --fix $(SRC_PATH) $(TEST_PATH)
```

### 9. UI and Demo Management
```makefile
preview-demo: check-deps ## Run complete preview demo (MCP server + Streamlit UI)
	@echo "$(YELLOW)Starting GraphMCP Preview Demo...$(NC)"
	@chmod +x concrete/demo.sh
	@./concrete/demo.sh

start-demo-8501: kill-port-8501 ## Start E2E demo on port 8501 with browser
	PYTHONPATH=. $(VENV_PATH)/bin/python db_decommission_demo.py \
		--mode e2e \
		--port 8501 &
	@sleep 3
	@open http://localhost:8501 || echo "$(YELLOW)Visit http://localhost:8501$(NC)"
```

### 10. Configuration Validation
```makefile
show-config: ## Show current configuration and environment
	@echo "$(CYAN)GraphMCP Configuration$(NC)"
	@echo "Project Name: $(PROJECT_NAME)"
	@echo "Python Version: $(PYTHON_VERSION)"
	@echo "GitHub Token: $$(if [ -n "$(GITHUB_TOKEN)" ]; then echo "✓ Set"; else echo "✗ Missing"; fi)"

validate-makefile: ## Validate Makefile syntax and targets
	@make -n help >/dev/null 2>&1 && echo "$(GREEN)✓ Makefile syntax OK$(NC)"
```

## Best Practices Demonstrated

1. **Dependency Checking**: Always check dependencies before running tasks
2. **Environment Validation**: Validate required environment variables
3. **Graceful Failures**: Provide helpful error messages and suggestions
4. **Process Management**: Clean up processes and ports automatically
5. **Colored Output**: Use colors to improve readability and user experience
6. **Comprehensive Help**: Auto-generate help from comment annotations
7. **Modular Targets**: Break complex workflows into smaller, reusable targets
8. **Error Handling**: Handle failures gracefully with informative messages
9. **Resource Cleanup**: Always clean up processes, ports, and temporary files
10. **Developer Experience**: Provide clear next steps and configuration status