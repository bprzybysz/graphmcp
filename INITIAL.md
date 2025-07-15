## FEATURE: Database Decommissioning Workflow - Production Ready

### Overview
A comprehensive database decommissioning workflow that automatically identifies, processes, and removes database references from target repositories with quality assurance and automated PR creation.

### Architecture Flow
1. **Environment Validation**: Validates environment setup and initializes components with centralized secrets management
2. **Repository Processing**: Uses Repomix MCP to pack target repositories into XML format and save /Users/blaisem4/src/graphmcp/tests/data/ dont delete it after flow
3. **Pattern Discovery**: From repo pack as filepath Extracts files containion database references using pattern matching and file classification
4. **Contextual Refactoring**: Applies type-specific refactoring rules based on file classification to the file
5. **Quality Assurance**: Performs comprehensive validation checks on refactored code. QA step data flow requires discovery results from previous steps
6. **GitHub Integration**: Creates forks, branches, and pull requests with changes
7. **Workflow Summary**: Generates detailed metrics and completion reports

MAKE IT WORK PROPERLY proven by errorless run 'source .venv/bin/activate && python run_db_workflow.py --database postgres_air --repo "https://github.com/bprzybysz/postgres-sample-dbs"' with these params
once you manage download repopack properly dont del it and in next step use as a branch when param --mock=True or --mock 

### Current Status
- ✅ Environment validation and MCP client initialization
- ✅ Repository packing with Repomix integration
- ✅ Pattern discovery and file extraction
- ✅ Structured logging and metrics collection
- ✅ Quality assurance framework
- ⚠️ **ISSUES IDENTIFIED**: 
  - Repomix integration needs mock data fallback fixes
  - QA step data flow requires discovery results from previous steps
  - File refactoring logic needs proper data structure handling

### Key Features
- **Multi-MCP Integration**: GitHub, Slack, and Repomix MCP servers
- **Structured Logging**: Comprehensive workflow tracking with visual output
- **Error Handling**: Graceful degradation with detailed error reporting
- **Quality Assurance**: Automated validation of database reference removal
- **Visual Reporting**: Git diff-style (reed/green) output with dark theme formatting for refactor changes preview
- **Cleanup**: Debug level to file log but info level white/color structured logging supported. there should be logic for levels setup.
- **Cleanup**: Check console output think of hopw to loeverage visual eeffectts to present relovant data in output


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
