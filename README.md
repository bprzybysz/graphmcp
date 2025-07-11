# GraphMCP Framework

An enhanced framework for orchestrating complex code analysis and repository management workflows, featuring a rebuilt, modern UI and a modular, testable workflow engine.

## Overview

GraphMCP provides a powerful and flexible system for building, executing, and monitoring sophisticated workflows. The refactored architecture focuses on clean design, modularity, and a great developer experience, enabling rapid development of new capabilities.

## Key Features

- **Modern Streamlit UI**: A completely rebuilt, responsive user interface for real-time workflow monitoring.
- **Modular Workflow Engine**: Build complex workflows from reusable, independent steps.
- **Mock/Real Execution**: Seamlessly switch between mock and real implementations for development and testing.
- **Async-First Architecture**: High-performance, asynchronous operations for all workflow steps.
- **Centralized State Management**: Predictable and reliable state handling for the UI.
- **Comprehensive Testing**: Full suite of unit, integration, and E2E tests for the new architecture.

## Quick Start

### 1. Setup
First, set up your development environment and install all dependencies.

```bash
make setup
source .venv/bin/activate
```

### 2. Run the UI
To launch the new Streamlit user interface:

```bash
streamlit run don-concrete/ui/app.py
```
Navigate to `http://localhost:8501` to view the application.

### 3. Run a Workflow (CLI)
To run the database decommissioning workflow from the command line:

```bash
# Run in mock mode (default)
python demo.py --database my_test_db

# Run with real implementations (requires configuration)
USE_MOCK_PACK="false" USE_MOCK_DISCOVERY="false" python demo.py --database my_test_db
```

## Testing

The project includes a comprehensive test suite.

```bash
# Run all unit and integration tests
.venv/bin/pytest

# Run a specific test suite (e.g., integration)
.venv/bin/pytest tests/integration/
```

## Configuration

The primary configuration for the new workflow system is `enhanced_mcp_config.json`. The legacy `mcp_config.json` may still be used by older components but should be migrated.

For workflow-specific configuration, such as mock data paths, refer to the individual workflow step implementations in `don-concrete/workflow/steps/`.

## New Architecture

The refactored codebase follows a clean, modular structure:

```
graphmcp/
├── don-concrete/
│   ├── ui/                   # New Streamlit UI
│   │   ├── app.py            # Main UI entry point
│   │   ├── components/       # Reusable UI components
│   │   ├── state/            # UI state management
│   │   └── layouts/          # UI layout definitions
│   └── workflow/             # New workflow engine
│       ├── manager.py        # Core workflow manager
│       ├── steps/            # Modular workflow steps
│       └── mock/             # Mock implementations
├── legacy/                   # Old implementation (for reference)
├── tests/                    # New test suite
│   ├── unit/
│   └── integration/
├── customized/
│   └── unused_db_decomission/  # Workflow definitions
│       ├── builder.py            # WorkflowBuilder for creating workflows
│       └── db_decommission.py    # Example DB decommissioning workflow
└── demo.py                   # CLI entry point for the new workflow
```

## Development

### Migrating to the New System
If you are working with the legacy codebase, refer to the `MIGRATION_GUIDE.md` for detailed instructions on how to adapt your code to the new architecture.

### Creating New Workflows and Steps
The new system is designed for extensibility.
- **To create a new workflow**: Use the `WorkflowBuilder` as shown in `customized/unused_db_decomission/db_decommission.py`.
- **To create a new step**: Create a new class in `don-concrete/workflow/steps/` that inherits from `BaseWorkflowStep`. Follow the mock/real implementation pattern seen in other steps.

## Contributing

1. Fork the repository.
2. Create a feature branch for your changes.
3. Ensure your code follows the new architecture patterns.
4. Add comprehensive tests for any new functionality.
5. Run `.venv/bin/pytest` to ensure all tests pass.
6. Submit a pull request.

## License

[Add your license information here] 