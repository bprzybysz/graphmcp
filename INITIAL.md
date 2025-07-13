## FEATURE: Working GraphMCP Workflow Demo

Build a functional demonstration of the GraphMCP workflow system using the database decommission workflow. Core goals:

1. **Clean up existing demo.py**: Refactor db decommission workflow without breaking functionality
2. **Record-and-replay**: Run workflow once with real data, serialize results to `tests/data/` for fast iteration
3. **Basic workflow execution**: Environment validation → repo processing → pattern discovery → refactoring
4. **Target case**: Repository `https://github.com/bprzybysz/postgres-sample-dbs`, database `postgres_air`

**Key Requirements:**
- Use WorkflowBuilder from `workflows/builder.py`
- Use WorkflowContext for data sharing between steps
- Support mock mode (using cached data) and real mode
- Basic logging for progress tracking

## EXAMPLES:

**Core Architecture Patterns** (`examples/mcp_base_client.py`):
- Follow the abstract base class pattern with SERVER_NAME attribute
- Implement async context managers (__aenter__/__aexit__)
- Use comprehensive error handling with custom exception hierarchies
- Load configurations with environment variable substitution

**Data Models** (`examples/data_models.py`):
- Use @dataclass with type hints for all workflow data structures
- Implement to_dict()/from_dict() for serialization
- Make all models pickle-safe for caching
- Include timestamps and state tracking

**Testing Patterns** (`examples/testing_patterns.py`):
- Use pytest-asyncio for async workflow testing
- Implement comprehensive test markers (@pytest.mark.unit, @pytest.mark.integration)
- Mock external services and MCP clients
- Test error scenarios and edge cases

**Build Automation** (`examples/makefile_patterns.md`):
- Follow the comprehensive Makefile pattern for demo commands
- Include targets like `make demo`, `make demo-mock`, `make demo-real`
- Implement proper help system and colored output
- Support Docker containerization for demos

## DOCUMENTATION:

**GraphMCP Core Documentation:**
- Workflow Builder API: `workflows/builder.py` - WorkflowBuilder, Workflow, WorkflowStep classes
- Step Types: `workflows/builder.py` - StepType enum and step execution patterns
- MCP Clients: `clients/` directory - Repomix, GitHub, Slack client implementations
- Demo Implementation: `demo.py` - Production database decommissioning workflow example

**Pattern Discovery System:**
- Engine: `concrete/pattern_discovery.py` - PatternDiscoveryEngine, SourceTypeClassifier
- Performance: `concrete/performance_optimization.py` - AsyncCache, serialization patterns
- Test Data: `tests/data/postgres_sample_dbs_packed.xml` - Mock repository structure

**Serialization and Caching:**
- Use AsyncCache from performance_optimization.py for step result caching
- Implement pickle-based serialization for complex workflow objects
- Use JSON serialization for configuration and simple data
- Support TTL-based cache expiration and LRU eviction

**External Service Integration:**
- Repomix MCP Server: Repository packing and analysis
- GitHub MCP Server: Git operations, PR creation, branch management
- Slack MCP Server: Notification and status updates

## OTHER CONSIDERATIONS:

**Essential Implementation Details:**

1. **Mock Data Strategy**:
   - Serialize repo_pack outputs (XML format) to `tests/data/`
   - Cache pattern discovery results for fast iteration
   - Target repo: `https://github.com/bprzybysz/postgres-sample-dbs`, db: `postgres_air`
   - Use environment variable to switch between mock/real modes

2. **Workflow Context**:
   - All steps must use WorkflowContext for data sharing
   - Use existing GraphMCP error handling patterns

3. **Critical Requirements**:
   - Don't break existing functionality in demo.py
   - Use WorkflowBuilder pattern consistently
   - Keep async patterns throughout
   - Basic error handling for external service failures
