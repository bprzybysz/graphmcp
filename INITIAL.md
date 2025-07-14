## FEATURE: Pragmatic Database Decommissioning Workflow

**Goal**: After redeployment, cluster continues working with decommissioned database gracefully removed/disabled.

**Core Strategy**: Instead of complex refactoring, use "graceful deprecation":
1. **Infrastructure Removal**: Clean removal of Terraform resources, Helm charts
2. **Config Commenting**: Comment out database configs with clear decommission notices  
3. **Fail-Fast Code**: Replace database connections with explicit decommission exceptions
4. **Documentation Updates**: Mark databases as decommissioned with migration guidance
5. **Monitoring Cleanup**: Disable alerts to prevent false positives

**Implementation Focus**: ✅ COMPLETED
- ✅ Extract files using existing DatabaseReferenceExtractor  
- ✅ Categorize by complexity: Infrastructure (remove), Config (comment), Code (exception), Docs (notice)
- ✅ Prioritize P0 actions (Terraform, Helm) to ensure cluster stability
- ✅ Use clear decommission headers with ticket IDs and contact info
- ✅ Ensure reversible changes for emergency rollback

**FileDecommissionProcessor Implementation**:
- Located: `concrete/file_decommission_processor.py`
- Tests: `tests/unit/test_file_decommission_processor.py` (4/4 passing)
- E2E Validation: Real postgres_air files processed successfully

**Success Criteria**: Post-deployment cluster is functional, database is cleanly removed, and any remaining references fail fast with clear error messages pointing to migration guidance.

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
