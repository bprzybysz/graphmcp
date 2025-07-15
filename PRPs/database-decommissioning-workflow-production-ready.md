name: "Database Decommissioning Workflow - Production Ready Implementation"
description: |

## Purpose
Fix the database decommissioning workflow to work properly with errorless execution, implementing mock data fallback, QA step data flow fixes, and proper file refactoring logic with data structure handling.

## Core Principles
1. **Context is King**: All necessary MCP patterns, async workflow examples, and validation loops included
2. **Mock Data Strategy**: Serialize repo_pack outputs to tests/data/ for fast iteration
3. **Information Dense**: Use existing GraphMCP patterns and structured logging
4. **Progressive Success**: Fix critical issues incrementally with validation
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Make the database decommissioning workflow run errorlessly with command:
```bash
source .venv/bin/activate && python run_db_workflow.py --database postgres_air --repo "https://github.com/bprzybysz/postgres-sample-dbs"
```

## Why
- **Business value**: Automate database decommissioning with quality assurance
- **Integration**: Fix existing workflow issues preventing production deployment
- **Problems solved**: Mock data fallback, QA data flow, refactoring logic handling

## What
Fix three critical issues identified in INITIAL.md:
1. Repomix integration needs mock data fallback fixes
2. QA step data flow requires discovery results from previous steps
3. File refactoring logic needs proper data structure handling

### Success Criteria
- [ ] Command runs without errors using mock data when --mock=True
- [ ] QA step properly receives discovery results from previous steps
- [ ] File refactoring logic handles data structures correctly
- [ ] Repo pack is cached and reused between runs
- [ ] All existing tests pass
- [ ] Workflow produces meaningful output with structured logging

## All Needed Context

### Documentation & References (MUST READ)
```yaml
# CORE ARCHITECTURE PATTERNS
- file: examples/mcp_base_client.py
  why: Follow abstract base class pattern with SERVER_NAME attribute, async context managers, comprehensive error handling
  
- file: examples/data_models.py
  why: Use @dataclass with type hints, to_dict()/from_dict() methods, pickle-safe serialization
  
- file: examples/testing_patterns.py
  why: pytest-asyncio patterns, comprehensive test markers, mock configurations

# WORKFLOW IMPLEMENTATION
- file: concrete/db_decommission/workflow_steps.py
  why: Current step implementations, data flow patterns, context sharing
  
- file: concrete/db_decommission/utils.py
  why: Workflow creation, configuration management, helper functions
  
- file: concrete/db_decommission/data_models.py
  why: Existing data structures, validation patterns, result handling

# MOCK DATA STRATEGY
- file: tests/data/postgres_air_real_repo_pack.xml
  why: Target repo structure for postgres_air database
  
- file: tests/data/postgres_air_mock_patterns.json
  why: Mock pattern discovery results for fast iteration

# VALIDATION PATTERNS
- file: pytest.ini
  why: Test markers (@pytest.mark.unit, @pytest.mark.integration, @pytest.mark.e2e)
  
- file: Makefile
  why: Validation commands (make test-unit, make lint, make format)

# EXTERNAL REFERENCES
- url: https://github.com/modelcontextprotocol/servers
  why: Official MCP server patterns for Repomix integration
  
- url: https://repomix.com/guide/mcp-server
  why: Repomix MCP server configuration and usage patterns
```

### Current Codebase Structure
```bash
graphmcp/
├── concrete/db_decommission/
│   ├── __init__.py              # Main workflow exports
│   ├── workflow_steps.py        # Step implementations (NEEDS FIXES)
│   ├── utils.py                 # Workflow creation utilities
│   ├── data_models.py           # Data structures
│   ├── validation_checks.py     # QA validation logic
│   ├── pattern_discovery.py     # Pattern discovery engine
│   └── repository_processors.py # Repo processing logic
├── tests/data/
│   ├── postgres_air_real_repo_pack.xml    # Real repo data
│   ├── postgres_air_mock_patterns.json    # Mock patterns
│   └── postgres_air_mock_repo_pack.xml    # Mock repo pack
├── run_db_workflow.py           # Main entry point (NEEDS MOCK SUPPORT)
└── mcp_config.json              # MCP server configuration
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: MCP clients require async context managers
async with RepomixClient(config_path) as client:
    result = await client.call_tool("pack_repository", params)

# CRITICAL: WorkflowContext data sharing pattern
context.set_shared_value("discovery", discovery_result)
discovery_result = context.get_shared_value("discovery", {})

# CRITICAL: Structured logging with workflow_id
logger = get_logger(workflow_id=f"db_decommission_{database_name}", config=config)

# CRITICAL: FileDecommissionProcessor expects specific data structure
processor = FileDecommissionProcessor()
result = await processor.process_files(source_dir, database_name, ticket_id)

# GOTCHA: Repomix outputs need to be preserved in tests/data/
# Don't delete repo_pack outputs - cache them for mock mode
```

## Implementation Blueprint

### Data Models Structure
```python
# EXISTING - These are already implemented correctly
@dataclass
class QualityAssuranceResult:
    database_reference_check: ValidationResult
    rule_compliance_check: ValidationResult
    service_integrity_check: ValidationResult
    overall_status: ValidationResult
    details: dict
    recommendations: list

@dataclass
class DecommissioningSummary:
    workflow_id: str
    database_name: str
    total_files_processed: int
    successful_files: int
    failed_files: int
    # ... other fields
```

### List of Tasks to Complete (IN ORDER)

```yaml
Task 1: Fix Mock Data Support in run_db_workflow.py
MODIFY run_db_workflow.py:
  - ADD argument parser support for --mock flag
  - IMPLEMENT mock data loading from tests/data/
  - PRESERVE repo_pack outputs when not in mock mode
  - ENSURE backward compatibility with existing args

Task 2: Fix QA Step Data Flow in workflow_steps.py
MODIFY concrete/db_decommission/workflow_steps.py:
  - FIND quality_assurance_step function (line ~46)
  - FIX discovery_result = context.get_shared_value("discovery", {})
  - ENSURE discovery results are properly structured
  - VALIDATE QA checks receive correct data format

Task 3: Fix File Refactoring Logic Data Handling
MODIFY concrete/db_decommission/workflow_steps.py:
  - FIND apply_refactoring_step function (line ~162)
  - FIX FileDecommissionProcessor data structure handling
  - ENSURE proper source_dir and output_dir management
  - VALIDATE refactoring results format for downstream steps

Task 4: Implement Repo Pack Caching Strategy
MODIFY concrete/db_decommission/repository_processors.py:
  - ADD cache_repo_pack function
  - IMPLEMENT load_cached_repo_pack function
  - ENSURE cache invalidation based on repo URL/hash
  - PRESERVE cache in tests/data/ directory

Task 5: Add Mock Mode Integration
MODIFY concrete/db_decommission/utils.py:
  - ADD mock_mode parameter to run_decommission function
  - IMPLEMENT mock data loading logic
  - ENSURE mock data follows same structure as real data
  - VALIDATE mock mode produces meaningful results

Task 6: Update Validation Gates
MODIFY existing unit tests:
  - UPDATE test_db_decommission.py for mock mode
  - ADD tests for QA step data flow
  - VALIDATE refactoring logic with proper data structures
  - ENSURE all tests pass with mock data
```

### Per Task Pseudocode

```python
# Task 1: Mock Data Support
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock', action='store_true', help='Use mock data')
    args = parser.parse_args()
    
    # PATTERN: Check for cached data first
    if args.mock:
        repo_pack_path = f"tests/data/{database_name}_mock_repo_pack.xml"
        if Path(repo_pack_path).exists():
            print(f"Using cached repo pack: {repo_pack_path}")
        else:
            print("Mock data not found, falling back to real data")
            args.mock = False
    
    result = await run_decommission(
        database_name=args.database,
        target_repos=[args.repo],
        mock_mode=args.mock
    )

# Task 2: QA Step Data Flow Fix
async def quality_assurance_step(context, step, database_name, ...):
    # CRITICAL: Ensure discovery results are properly retrieved
    discovery_result = context.get_shared_value("discovery", {})
    
    # VALIDATION: Check data structure
    if not discovery_result or "files" not in discovery_result:
        logger.log_warning("No discovery results found, creating empty structure")
        discovery_result = {"files": [], "extraction_directory": ""}
    
    # PATTERN: Pass structured data to validation checks
    reference_check = await perform_database_reference_check(
        discovery_result, database_name
    )

# Task 3: File Refactoring Logic Fix
async def apply_refactoring_step(context, step, database_name, ...):
    discovery_result = context.get_shared_value("discovery", {})
    
    # CRITICAL: Validate source directory exists
    source_dir = discovery_result.get("extraction_directory", 
                                     f"tests/tmp/pattern_match/{database_name}")
    
    if not Path(source_dir).exists():
        logger.log_warning(f"Source directory not found: {source_dir}")
        return {"success": False, "message": "Source directory not found"}
    
    # PATTERN: Use existing processor with proper error handling
    processor = FileDecommissionProcessor()
    result = await processor.process_files(
        source_dir=source_dir,
        database_name=database_name,
        ticket_id="DB-DECOMM-001"
    )
```

### Integration Points
```yaml
WORKFLOW_CONTEXT:
  - shared_values: discovery, refactoring, github_pr
  - step_results: validate_environment, process_repositories, etc.
  
MOCK_DATA:
  - location: tests/data/
  - files: postgres_air_mock_repo_pack.xml, postgres_air_mock_patterns.json
  - pattern: Load from cache if exists, otherwise generate and save
  
LOGGING:
  - framework: graphmcp.logging with structured output
  - workflow_id: db_decommission_{database_name}_{timestamp}
  - levels: INFO for user, DEBUG for development
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# CRITICAL: Run these FIRST - fix any errors before proceeding
source .venv/bin/activate
ruff check --fix concrete/db_decommission/
mypy concrete/db_decommission/ --ignore-missing-imports

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```bash
# Run comprehensive unit tests
source .venv/bin/activate
pytest tests/unit/test_db_decommission.py -v
pytest tests/unit/test_db_decommission_validation_helpers.py -v
pytest tests/unit/test_db_decommission_utils.py -v

# Expected: All tests pass. If failing, fix code not tests.
```

### Level 3: Integration Test
```bash
# Test mock mode
source .venv/bin/activate
python run_db_workflow.py --database postgres_air --repo "https://github.com/bprzybysz/postgres-sample-dbs" --mock

# Expected: Workflow completes successfully with mock data
# Check logs for structured output and meaningful results
```

### Level 4: Real Data Test
```bash
# Test with real data (requires environment variables)
export GITHUB_TOKEN=your_token_here
source .venv/bin/activate
python run_db_workflow.py --database postgres_air --repo "https://github.com/bprzybysz/postgres-sample-dbs"

# Expected: Workflow completes successfully, generates PR
# Repo pack should be cached in tests/data/
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/unit/ -v`
- [ ] No linting errors: `ruff check concrete/db_decommission/`
- [ ] No type errors: `mypy concrete/db_decommission/`
- [ ] Mock mode works: `python run_db_workflow.py --mock --database postgres_air`
- [ ] QA step receives discovery results properly
- [ ] File refactoring handles data structures correctly
- [ ] Repo pack is cached and reused
- [ ] Structured logging shows meaningful output
- [ ] Error handling is graceful with informative messages

---

## Anti-Patterns to Avoid
- ❌ Don't break existing workflow step interfaces
- ❌ Don't modify data model structures unnecessarily
- ❌ Don't skip validation because "it should work"
- ❌ Don't delete cached repo packs - preserve them
- ❌ Don't ignore context.get_shared_value() patterns
- ❌ Don't hardcode paths - use configuration
- ❌ Don't bypass structured logging patterns

## Confidence Level Assessment
**Score: 8/10**

This PRP has high confidence for one-pass implementation because:
- ✅ Complete context from existing codebase analysis
- ✅ Specific file locations and line numbers identified
- ✅ Mock data strategy clearly defined
- ✅ Validation loops are executable
- ✅ Error patterns and fixes are well-documented
- ✅ Integration points are clearly mapped
- ⚠️ Some complexity in data flow between steps may require iteration
- ⚠️ MCP server integration may need debugging

The workflow is well-established with clear patterns to follow. The main fixes are targeted and don't require architectural changes.