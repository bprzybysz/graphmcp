# PRP: GraphMCP Working Workflow Demo

## Goal
Build a functional demonstration of the GraphMCP workflow system using the database decommission workflow with record-and-replay capabilities, clean architecture, and support for both mock and real data modes.

## Why
- **Validate GraphMCP Architecture**: Prove the WorkflowBuilder pattern works end-to-end
- **Enable Fast Iteration**: Cached data allows rapid development without external service dependencies  
- **Demonstrate Real Value**: Show database decommissioning workflow processing real repository data
- **Foundation for Future Workflows**: Establish patterns for other GraphMCP use cases

## What
A refactored database decommissioning workflow that:
- Uses WorkflowBuilder from `workflows/builder.py` 
- Supports mock mode (cached data) and real mode (live services)
- Processes target repository `https://github.com/bprzybysz/postgres-sample-dbs` for database `postgres_air`
- Implements record-and-replay for repo pack outputs and pattern discovery results
- Maintains existing functionality while following GraphMCP patterns

### Success Criteria
- [ ] Workflow executes successfully in both mock and real modes
- [ ] Cached data stored in `tests/data/` for fast iteration
- [ ] Environment validation → repo processing → pattern discovery → refactoring pipeline works
- [ ] No breaking changes to existing demo.py functionality
- [ ] Basic logging provides clear progress tracking

## All Needed Context

### Documentation & References
```yaml
- file: workflows/builder.py
  why: Core WorkflowBuilder, Workflow, WorkflowStep classes and StepType enum patterns

- file: demo.py  
  why: Existing database decommissioning workflow implementation to preserve

- file: concrete/pattern_discovery.py
  why: PatternDiscoveryEngine and SourceTypeClassifier patterns to integrate

- file: concrete/performance_optimization.py
  why: AsyncCache and serialization patterns for record-and-replay

- file: examples/mcp_base_client.py
  why: Abstract base class pattern with SERVER_NAME and async context managers

- file: examples/data_models.py
  why: @dataclass patterns with to_dict()/from_dict() serialization

- file: examples/testing_patterns.py
  why: pytest-asyncio patterns and test markers for validation

- file: tests/data/postgres_air_real_repo_pack.xml
  why: Example of mock repository structure data format

- docfile: CLAUDE.md
  why: Project-wide coding standards, testing requirements, and architectural constraints
```

### Current Codebase Tree
```bash
graphmcp/
├── workflows/
│   └── builder.py              # WorkflowBuilder framework
├── concrete/
│   ├── db_decommission.py      # Database workflow implementation  
│   ├── pattern_discovery.py   # PatternDiscoveryEngine
│   └── performance_optimization.py # AsyncCache for serialization
├── clients/                    # MCP client implementations
├── examples/                   # Architecture patterns
├── tests/
│   └── data/                   # Mock data storage location
├── demo.py                     # Current demo script
└── CLAUDE.md                   # Project coding standards
```

### Desired Codebase Tree
```bash
graphmcp/
├── workflows/
│   ├── builder.py              # [EXISTING] WorkflowBuilder framework
│   └── context.py              # [NEW] WorkflowContext for data sharing
├── concrete/
│   ├── db_decommission.py      # [MODIFY] Use WorkflowBuilder pattern
│   ├── pattern_discovery.py   # [EXISTING] PatternDiscoveryEngine  
│   └── performance_optimization.py # [EXISTING] AsyncCache
├── demo/
│   ├── __init__.py             # [NEW] Demo package
│   ├── config.py               # [NEW] Environment/mode configuration
│   └── runner.py               # [NEW] Refactored demo execution
├── tests/
│   └── data/
│       ├── postgres_air_repo_pack.xml   # [NEW] Cached repo data
│       └── postgres_air_patterns.json  # [NEW] Cached pattern results
├── demo.py                     # [MODIFY] Updated to use new structure
└── Makefile                    # [NEW] Demo automation targets
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: WorkflowBuilder requires async functions for all steps
# Example: All custom_function parameters must be async callables

# CRITICAL: AsyncCache requires pickle-safe objects for serialization
# Example: Lambda functions and local classes cannot be cached

# CRITICAL: MCP clients use async context managers (__aenter__/__aexit__)
# Example: Always use 'async with client:' pattern

# CRITICAL: Environment variable substitution uses ${VAR_NAME} syntax
# Example: Config values like "repo_url": "${TARGET_REPO_URL}"

# GOTCHA: Repomix XML output can be very large (>10MB for real repos)
# Pattern: Use streaming XML parsing or chunked processing

# GOTCHA: Pattern discovery is CPU-intensive for large codebases  
# Pattern: Use AsyncCache with TTL to avoid repeated processing
```

## Implementation Blueprint

### Data Models and Structure
```python
# workflows/context.py - WorkflowContext for data sharing
@dataclass
class WorkflowContext:
    """Shared data context for workflow steps."""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def set(self, key: str, value: Any):
        """Set context data with serialization safety."""
        self.data[key] = ensure_serializable(value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get context data."""
        return self.data.get(key, default)

# demo/config.py - Environment configuration
@dataclass  
class DemoConfig:
    """Configuration for demo execution."""
    mode: str  # 'mock' or 'real'
    target_repo: str
    target_database: str
    cache_dir: str = "tests/data"
    
    @classmethod
    def from_env(cls) -> 'DemoConfig':
        """Load configuration from environment variables."""
        return cls(
            mode=os.getenv('DEMO_MODE', 'mock'),
            target_repo=os.getenv('TARGET_REPO', 'https://github.com/bprzybysz/postgres-sample-dbs'),
            target_database=os.getenv('TARGET_DATABASE', 'postgres_air')
        )
```

### List of Tasks to Complete
```yaml
Task 1 - Create WorkflowContext:
CREATE workflows/context.py:
  - MIRROR pattern from: examples/data_models.py
  - IMPLEMENT @dataclass with to_dict()/from_dict() methods
  - ADD ensure_serializable() integration for caching safety

Task 2 - Create Demo Configuration:
CREATE demo/config.py:
  - IMPLEMENT DemoConfig dataclass with environment loading
  - ADD mode switching logic (mock vs real)
  - INCLUDE cache directory and target repository settings

Task 3 - Create Demo Runner:
CREATE demo/runner.py:
  - EXTRACT demo execution logic from demo.py
  - IMPLEMENT WorkflowBuilder integration
  - ADD record-and-replay caching logic

Task 4 - Refactor Database Workflow:
MODIFY concrete/db_decommission.py:
  - FIND create_db_decommission_workflow function
  - REPLACE custom workflow logic with WorkflowBuilder pattern
  - PRESERVE existing step functionality and error handling
  - ADD WorkflowContext integration for data sharing

Task 5 - Update Main Demo Script:
MODIFY demo.py:
  - REPLACE direct workflow execution with demo.runner calls
  - PRESERVE existing CLI argument handling
  - ADD mode selection (--mock/--real flags)
  - MAINTAIN backward compatibility

Task 6 - Create Cache Management:
CREATE demo/cache.py:
  - IMPLEMENT repo pack data caching to tests/data/
  - ADD pattern discovery result caching
  - USE AsyncCache from performance_optimization.py
  - INCLUDE cache invalidation and TTL logic

Task 7 - Add Build Automation:
CREATE Makefile targets:
  - ADD make demo, make demo-mock, make demo-real
  - INCLUDE help system with colored output
  - IMPLEMENT proper environment setup
```

### Per Task Pseudocode

```python
# Task 1 - WorkflowContext
@dataclass
class WorkflowContext:
    # PATTERN: Follow examples/data_models.py structure
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        # CRITICAL: Use ensure_serializable for caching
        return {"data": ensure_serializable(self.data)}
    
    @classmethod  
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowContext':
        # PATTERN: Standard deserialization pattern
        return cls(data=data.get("data", {}))

# Task 3 - Demo Runner with WorkflowBuilder
async def run_demo_workflow(config: DemoConfig) -> None:
    # PATTERN: Use WorkflowBuilder fluent interface
    builder = WorkflowBuilder()
    
    workflow = (builder
        .add_step("validate_env", StepType.CUSTOM, validate_environment)
        .add_step("get_repo", StepType.REPOMIX, get_repository_pack)  
        .add_step("discover_patterns", StepType.CUSTOM, discover_database_patterns)
        .add_step("generate_refactoring", StepType.CUSTOM, generate_refactoring_plan)
        .build()
    )
    
    # CRITICAL: Pass WorkflowContext for data sharing
    context = WorkflowContext()
    await workflow.execute(context)

# Task 4 - Database Workflow Integration  
def create_db_decommission_workflow(database_name: str) -> Workflow:
    # REPLACE: Direct step execution with WorkflowBuilder
    builder = WorkflowBuilder()
    
    # PRESERVE: Existing step logic but wrap in WorkflowStep
    return (builder
        .add_step("validate", StepType.CUSTOM, 
                 lambda ctx: validate_database_environment(database_name))
        .add_step("analyze", StepType.REPOMIX,
                 lambda ctx: analyze_repository_structure())
        .build()
    )
```

### Integration Points
```yaml
CACHING:
  - location: tests/data/
  - pattern: "Use AsyncCache with pickle serialization"
  - files: "postgres_air_repo_pack.xml, postgres_air_patterns.json"

ENVIRONMENT:
  - add to: demo/config.py
  - pattern: "DEMO_MODE = os.getenv('DEMO_MODE', 'mock')"
  - variables: "TARGET_REPO, TARGET_DATABASE, CACHE_TTL"

WORKFLOW:
  - integrate: workflows/builder.py WorkflowBuilder
  - pattern: "builder.add_step().add_step().build()"
  - context: "WorkflowContext for step data sharing"

CLI:
  - modify: demo.py argument parsing
  - add: "--mock, --real, --cache-dir flags"
  - preserve: "existing --database and --quick options"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check workflows/context.py demo/ --fix
mypy workflows/context.py demo/
black workflows/context.py demo/

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# CREATE test_workflow_context.py
def test_context_serialization():
    """WorkflowContext serializes/deserializes correctly"""
    ctx = WorkflowContext()
    ctx.set("test_data", {"key": "value"})
    
    serialized = ctx.to_dict()
    restored = WorkflowContext.from_dict(serialized)
    
    assert restored.get("test_data") == {"key": "value"}

def test_demo_config_from_env():
    """DemoConfig loads from environment variables"""
    with mock.patch.dict(os.environ, {"DEMO_MODE": "real"}):
        config = DemoConfig.from_env()
        assert config.mode == "real"

# CREATE test_demo_runner.py  
@pytest.mark.asyncio
async def test_mock_mode_execution():
    """Demo runs successfully in mock mode"""
    config = DemoConfig(mode="mock", target_repo="test", target_database="test")
    
    # Should complete without external service calls
    await run_demo_workflow(config)
```

```bash
# Run and iterate until passing:
pytest test_workflow_context.py test_demo_runner.py -v
# If failing: Read error, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test mock mode (should work without network)
python demo.py --database postgres_air --mock

# Expected: Workflow completes using cached data
# Check: tests/data/ contains postgres_air_*.xml and *.json

# Test real mode (requires network and MCP servers)  
python demo.py --database postgres_air --real

# Expected: Workflow fetches live data and caches results
# Check: New cached files created in tests/data/
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check .`
- [ ] No type errors: `mypy workflows/ demo/`
- [ ] Mock mode runs successfully: `python demo.py --mock`
- [ ] Real mode runs successfully: `python demo.py --real`
- [ ] Cached data properly stored in tests/data/
- [ ] Existing demo.py functionality preserved
- [ ] WorkflowBuilder integration complete
- [ ] Basic logging provides progress tracking

---

## Anti-Patterns to Avoid
- ❌ Don't break existing demo.py CLI interface
- ❌ Don't create new patterns when WorkflowBuilder exists
- ❌ Don't skip caching - it enables fast iteration
- ❌ Don't hardcode repository URLs - use configuration
- ❌ Don't ignore AsyncCache serialization requirements
- ❌ Don't mix sync and async patterns in workflow steps
- ❌ Don't create files longer than 500 lines per CLAUDE.md