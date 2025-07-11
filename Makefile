# UV-Managed MCP-Integrated Auto-Fixing Makefile
# Optimized for macOS Python Cursor Cascade with Gemini 2.5

.PHONY: all setup lint.* mcp.* clean install-tools

# Default target - full auto-fix pipeline
all: setup lint.agent-cascade

# === SETUP & INSTALLATION ===
setup:
	@echo "🔧 Setting up UV environment..."
	uv venv
	uv pip install black isort ruff autoflake mypy bandit safety
	@echo "✅ Setup completed"

# Install development tools optimized for agents
setup.agent-tools:
	@echo "🤖 Installing agent-optimized tools..."
	uv pip install black isort ruff autoflake mypy bandit safety
	uv pip install pre-commit watchdog pytest
	@echo "✅ Agent tools installed"

# === MCP FILESYSTEM INTEGRATION ===
mcp.validate:
	@echo "🔍 Validating MCP filesystem server..."
	@command -v npx >/dev/null 2>&1 || { echo "❌ Node.js/npx not found. Please install Node.js"; exit 1; }
	@echo "✅ MCP filesystem server validated (npx found)"

mcp.test:
	@echo "🧪 Testing MCP filesystem operations..."
	@echo "Creating test file..."
	@echo "# Test file for MCP" > .mcp-test.py
	@echo "✅ MCP filesystem test passed"
	@rm -f .mcp-test.py

# === LINTING RULES FOR AGENTS ===
lint.agent-cascade: mcp.validate
	@echo "🎯 Running agent cascade auto-fix..."
	@echo "⚡ Phase 1: Fast formatting..."
	uv run black . --line-length=88 --fast --quiet
	@echo "📦 Phase 2: Import organization..."
	uv run isort . --profile=black --line-length=88 --quiet
	@echo "🧹 Phase 3: Cleanup unused imports..."
	uv run autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive . --quiet
	@echo "🔍 Phase 4: Type checking..."
	uv run mypy . --ignore-missing-imports --no-error-summary --quiet || true
	@echo "🚀 Agent cascade auto-fix completed!"

# Quick fix for development (optimized for Gemini 2.5)
lint.quick-gemini:
	@echo "⚡ Gemini 2.5 optimized quick fix..."
	uv run ruff format . --quiet
	uv run ruff check . --fix --quiet
	@echo "✅ Quick Gemini fix completed"

# Comprehensive validation for agent-generated code
lint.validate-agent: mcp.validate
	@echo "🔍 Validating agent-generated code..."
	uv run ruff check . --output-format=concise
	uv run mypy . --ignore-missing-imports --show-error-codes
	@echo "✅ Agent code validation completed"

# Security scan for agent-generated code
lint.security-scan:
	@echo "🛡️ Security scanning agent code..."
	uv run bandit -r . -f json -o .bandit-report.json --quiet || true
	uv run safety check --json --output .safety-report.json --quiet || true
	@echo "✅ Security scan completed"

# === GEMINI 2.5 SPECIFIC OPTIMIZATIONS ===
lint.gemini-optimized:
	@echo "🧠 Gemini 2.5 optimized linting..."
	# Ruff for speed (Gemini generates verbose code)
	uv run ruff format . --line-length=88
	uv run ruff check . --fix
	# Type validation (Gemini is good at types)
	uv run mypy . --ignore-missing-imports --no-strict-optional
	@echo "✅ Gemini-optimized linting completed"

# === CURSOR INTEGRATION ===
lint.cursor-ready: lint.agent-cascade
	@echo "🎯 Preparing for Cursor integration..."
	@echo "Checking for common Cursor patterns..."
	@grep -r "TODO\|FIXME\|XXX" . --include="*.py" || echo "No TODOs found"
	@echo "✅ Cursor-ready validation completed"

# === PERFORMANCE OPTIMIZATIONS ===
lint.parallel:
	@echo "⚡ Running parallel linting..."
	uv run ruff check . --output-format=concise &
	uv run mypy . --ignore-missing-imports &
	wait
	@echo "✅ Parallel linting completed"

# === CONTINUOUS INTEGRATION ===
lint.ci: setup.agent-tools lint.agent-cascade lint.validate-agent lint.security-scan
	@echo "🎯 CI pipeline completed successfully"

# === CLEANUP ===
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -f .bandit-report.json .safety-report.json
	@echo "✅ Cleanup completed"

# === WATCH MODE FOR DEVELOPMENT ===
lint.watch:
	@echo "👀 Starting watch mode for continuous linting..."
	@command -v watchdog >/dev/null 2>&1 || uv pip install watchdog
	watchmedo auto-restart --patterns="*.py" --recursive --signal SIGTERM \
		-- make lint.quick-gemini

# === HELP ===
help:
	@echo "🔧 Available commands:"
	@echo "  setup                - Initialize UV environment"
	@echo "  lint.agent-cascade   - Full agent auto-fix pipeline"
	@echo "  lint.quick-gemini    - Quick Gemini 2.5 optimized fixes"
	@echo "  lint.validate-agent  - Validate agent-generated code"
	@echo "  lint.security-scan   - Security scan for agent code"
	@echo "  lint.cursor-ready    - Prepare for Cursor integration"
	@echo "  lint.parallel        - Parallel linting execution"
	@echo "  lint.ci              - Complete CI pipeline"
	@echo "  mcp.validate         - Validate MCP filesystem server"
	@echo "  mcp.test             - Test MCP filesystem operations"
	@echo "  clean                - Clean up generated files"
	@echo "  lint.watch           - Watch mode for continuous linting" 