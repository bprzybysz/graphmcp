Following the principles of context engineering, here is the `PLANNING.md` document for the refactoring effort, along with the four new Product Requirements Documents (PRDs) for each specified step.

### **PLANNING.md**

# Planning for Database Decommissioning Workflow Refactoring

## Overview

This planning document outlines the approach to refactor the existing database decommissioning workflow implementation. The goal is to improve modularity, maintainability, and observability by separating helper functions, integrating structured logging, and cleaning up legacy code, adhering to context engineering best practices[1].

## Refactoring Steps

1.  **Refactor Workflow Definition**: Separate helper functions from the main workflow definition to modularize code for better testability and clarity[1].
2.  **Integrate Structured Logging**: Replace existing logging with the new structured logging system, ensuring compatibility with existing workflow interfaces[2].
3.  **Remove Legacy Logging and Unused Code**: Delete old logging classes and files, and remove unused helper functions and code paths to reduce technical debt[2].
4.  **Prune PRDs and Documentation**: Distill existing PRDs into focused examples, patterns, and templates to align documentation with the current implementation[1][3].

## Timeline

| Step | Description | Estimated Duration |
| :--- | :--- | :--- |
| 1 | Refactor Workflow Definition | 3 days |
| 2 | Integrate Structured Logging | 2 days |
| 3 | Remove Legacy Logging and Unused Code | 1 day |
| 4 | Prune PRDs and Documentation | 2 days |

## Dependencies

*   Access to the existing codebase and documentation is required[2].
*   The new structured logging components must be available and stable.
*   A dedicated test environment is needed for validation at each stage.

## Risks and Mitigations

| Risk | Mitigation Strategy |
| :--- | :--- |
| **Integration Issues** | Introduce the new logging system incrementally, with feature flags if necessary, to isolate potential problems. |
| **Regression Bugs** | Implement a comprehensive suite of unit and integration tests before and after refactoring each module. |
| **Outdated Documentation** | Adopt a "docs-as-code" approach, updating documentation in the same pull request as the code changes. |

### **Refactor_Workflow_Definition.prd.md**

# TASK 1: Refactor Workflow Definition

## 1. Objective/'

To refactor the database decommissioning workflow by separating helper functionalities from the main workflow definition. This will improve the modularity, maintainability, and testability of the codebase, which is a core principle of effective context engineering[1].

## 2. Background

The current implementation in `concrete/db_decommission.py` intermingles workflow orchestration with the underlying logic of each step[2]. This monolithic structure makes the code difficult to understand, test, and extend. By separating concerns, we can create a more robust and scalable system.

## 3. Requirements

*   Extract helper functions (e.g., validation, repository processing, pattern discovery) into new, dedicated modules[2].
*   The primary workflow file should only contain orchestration logic, using the `WorkflowBuilder` to call the separated helper functions.
*   The refactoring must not alter the existing external behavior or interface of the workflow.
*   Each new module and its functions must be independently testable.
*   Full compatibility with the existing `WorkflowBuilder` and `WorkflowContext` must be preserved.

## 4. Success Criteria

*   The line count of the main workflow definition file is significantly reduced.
*   Helper functions are organized into logical, single-responsibility modules.
*   Unit test coverage for the extracted helper functions is above 90%.
*   There are no regressions in the end-to-end workflow execution.

## 5. Validation

*   All existing workflow integration tests must pass without modification.
*   New unit tests must be created for each extracted helper function.
*   A full integration test will be performed to validate the end-to-end functionality of the refactored workflow.

### **Integrate_Structured_Logging.prd.md**

# TASK 2: Integrate Structured Logging

## 1. Objective

To replace the legacy logging system (`EnhancedDatabaseWorkflowLogger`) with the new, JSON-first `WorkflowLogger` across the entire database decommissioning workflow and its related components[2].

## 2. Background

The project has a newly implemented structured logging system (`graphmcp/logging/workflow_logger.py`) that is not yet used by the main workflow. The current `EnhancedDatabaseWorkflowLogger` lacks the structured, dual-sink (console and JSON) capabilities required for improved observability and tool integration[2].

## 3. Requirements

*   All logging calls within the workflow and its helper modules must be migrated to the new `WorkflowLogger`.
*   The logger should be configured to output both human-readable console logs and structured JSON logs to a file (`dbworkflow.log`)[2].
*   Structured data, such as tables for file discovery and trees for repository structure, must be logged using the appropriate methods (`log_table`, `log_tree`).
*   The integration must support progress tracking without heavy visual animations, aligning with a performance-focused design[2].

## 4. Success Criteria

*   All logs are emitted through the new `WorkflowLogger`.
*   The `dbworkflow.log` file contains valid, structured JSON entries for all logged events.
*   Console output remains clean and human-readable.
*   Metrics such as `files_discovered` and `patterns_found` are accurately captured and logged as structured data.

## 5. Validation

*   The content and structure of the `dbworkflow.log` file will be verified against a predefined schema.
*   Console output will be manually reviewed for clarity and correctness.
*   The complete workflow will be executed, and the resulting logs will be analyzed to ensure no information loss compared to the old system.

### **Remove_Legacy_Logging_Unused_Code.prd.md**

# TASK 3: Remove Legacy Code

## 1. Objective

To improve codebase clarity and reduce technical debt by completely removing the old, unused logging systems and any helper functions made redundant by the recent workflow refactoring.

## 2. Background

Following the integration of the new `WorkflowLogger`, several legacy logging files (`concrete/enhanced_logger.py`, `concrete/workflow_logger.py`) and associated helper functions are now obsolete[2]. Leaving them in the codebase creates confusion and increases the risk of them being used incorrectly.

## 3. Requirements

*   Identify and delete all files and classes related to the legacy logging system.
*   Conduct a codebase-wide search to find and remove any remaining usages or imports of the old loggers.
*   Identify and remove any helper functions that are no longer called after the main workflow refactoring.
*   Ensure that the project's dependencies can be updated if any are solely used by the removed code.

## 4. Success Criteria

*   The legacy logger files are successfully deleted from the repository.
*   The project compiles and runs without any errors related to missing modules or functions.
*   A static analysis of the codebase confirms there are no dead or unreachable code paths related to the removed components.
*   The overall size and complexity of the codebase are measurably reduced.

## 5. Validation

*   The full suite of unit, integration, and end-to-end tests must pass after the removal of the legacy code.
*   A manual code review will be conducted to confirm that no remnants of the old systems remain.
*   The application will be run in a staging environment to ensure no unexpected runtime errors occur.

### **Prune_PRDs_and_Documentation.prd.md**

# TASK4: Prune Documentation

## 1. Objective

To distill the existing, large-scale PRDs and PRPs into a concise, maintainable, and "living" set of documentation that includes focused examples, reusable patterns, and actionable templates, following context engineering best practices[1][3].

## 2. Background

The project's current PRD and PRP files are comprehensive but have become partially outdated after implementation. They contain a mix of requirements, planning, and design notes that are no longer fully aligned with the final state of the code. This makes them difficult to use for onboarding and future development.

## 3. Requirements

*   Review all documents in the `PRDs/` and `PRPs/` directories.
*   Extract the core, implemented requirements and patterns from these documents.
*   Create a new, organized documentation structure (e.g., `docs/patterns/`, `docs/examples/`, `docs/templates/`).
*   The new documentation should be directly linked to the code it describes.
*   Outdated or unimplemented specifications should be archived or removed.

## 4. Success Criteria

*   The project's documentation is concise, accurate, and reflects the current state of the implementation.
*   The new documentation includes a library of code patterns and examples that developers can easily reference.
*   Onboarding time for new developers is reduced, as they can rely on the updated, focused documentation.
*   The new documentation serves as a reliable single source of truth for the project's architecture and established patterns.

## 5. Validation

*   The newly created documentation will be reviewed by the development team for accuracy and clarity.
*   A new developer will be tasked with using the documentation to perform a small, guided task to test its effectiveness.
*   All links and code references within the documentation will be automatically checked to ensure they are not broken.
[21] [Context Engineering: The End of Vibe Coding! 100x Better ...](https://www.youtube.com/watch?v=uohI3h4kqyg)