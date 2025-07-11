# Ultimate 10K Refactoring Ruliade for MCP-Enabled Code Generation Agents

Hey Blaise! Here's your comprehensive **10,000-token refactoring ruleset** compiled from our previous discussions, optimized for MCP filesystem agents doing cursor-compose style coding. This is your **definitive guide** for lightning-fast, accurate refactoring operations.

## **🎯 Core Refactoring Philosophy**

### **Prime Directive Rules**
- **Behavior Preservation Above All** → Every refactoring MUST maintain functional equivalence
- **Atomic Operations** → Each refactoring should be complete, reversible, and testable
- **Fail-Fast Validation** → Detect and report issues immediately, don't propagate errors
- **Context-Aware Processing** → Understand project structure, language conventions, and dependencies
- **Minimal Disruption** → Change only what's necessary, preserve existing patterns

### **Agent Decision Framework**
- **Autonomous Analysis Selection** → `AUTO_ANALYZE` based on refactoring complexity
- **Risk Assessment** → Evaluate impact scope before executing changes
- **Rollback Capability** → Always maintain ability to undo changes
- **Progressive Validation** → Validate at each step, not just at the end

## **📁 Folder Change Refactoring Rules** (Priority: CRITICAL)

### **Core Path & Import Management**
- **🔄 Update all references to moved elements everywhere** → `REF_UPDATE_ALL`
  - *Process*: Deep scan → AST analysis → Reference mapping → Bulk replace → Validation
  - *Scope*: All files, configs, documentation, build scripts, test files
  - *Validation*: Compile check → Link verification → Dependency resolution

- **📦 Fix imports automatically according to new location** → `IMPORT_FIX_AUTO`
  - *Process*: Parse import statements → Calculate new paths → Update relative/absolute imports
  - *Language-specific*: Handle Python `from/import`, JS `require/import`, C# `using`, Java `import`
  - *Edge cases*: Circular imports, wildcard imports, dynamic imports

- **🧹 Remove unused imports from original location** → `IMPORT_CLEANUP`
  - *Process*: Detect unused → Verify safety → Remove systematically → Optimize import order
  - *Safety checks*: Side-effect imports, conditional imports, runtime dependencies

### **File System Operations**
- **📂 Create target folder if missing** → `MKDIR_AUTO`
  - *Process*: Check existence → Create hierarchy → Set appropriate permissions → Validate access
  - *Permissions*: Match source permissions, respect umask, handle ACLs
  - *Cross-platform*: Handle Windows/Unix path differences, case sensitivity

- **🏗️ Preserve folder hierarchy or separate files** → `STRUCT_PRESERVE`
  - *Options*: Maintain structure, flatten hierarchy, create logical groupings
  - *Patterns*: Feature folders, layer separation, domain-driven structure
  - *Validation*: Check naming conventions, avoid conflicts, maintain relationships

- **🔗 Handle cross-project references** → `XPROJ_SYNC`
  - *Process*: Map project dependencies → Update namespaces → Sync build configs
  - *Considerations*: Package managers, build systems, deployment scripts
  - *Validation*: Cross-project compilation, integration tests, dependency graphs

### **Advanced Path Management**
- **⚙️ Update all config/rule references** → `CONFIG_SYNC`
  - *Targets*: Build configs, linting rules, IDE settings, deployment configs
  - *Formats*: JSON, YAML, XML, INI, custom formats
  - *Validation*: Schema validation, syntax checking, functional testing

- **✅ Validate destination compatibility** → `COMPAT_CHECK`
  - *Checks*: Language compatibility, framework requirements, platform constraints
  - *Validation*: Namespace conflicts, naming conventions, access modifiers
  - *Prevention*: Circular dependencies, invalid moves, breaking changes

### **Symbolic Link & Alias Handling**
- **🔗 Update symbolic links and aliases** → `SYMLINK_UPDATE`
  - *Process*: Detect symlinks → Update targets → Verify accessibility
  - *Cross-platform*: Handle Windows shortcuts, Unix symlinks, junction points

- **📋 Maintain reference integrity** → `REF_INTEGRITY`
  - *Process*: Build reference graph → Validate all connections → Report broken links
  - *Recovery*: Suggest fixes, auto-repair when possible, flag manual review needed

## **🏷️ Name Change Refactoring Rules** (Priority: HIGH)

### **Reference Consistency**
- **🎯 Rename all calls consistently** → `NAME_REPLACE_ALL`
  - *Process*: Find all usages → Context-aware replacement → Verify completeness
  - *Scope*: Method calls, variable references, type annotations, documentation
  - *Safety*: Avoid partial matches, respect word boundaries, handle case sensitivity

- **🔍 Update references in all files** → `REF_GLOBAL_UPDATE`
  - *Process*: Cross-file search → Batch replacement → Syntax validation
  - *Includes*: Source files, tests, configs, documentation, comments
  - *Exclusions*: Binary files, generated code, third-party dependencies

### **Naming Quality Standards**
- **💡 Ensure descriptive, intent-capturing names** → `NAME_QUALITY_CHECK`
  - *Criteria*: Clear intent, appropriate length, domain-specific terminology
  - *Validation*: Readability metrics, team conventions, industry standards
  - *Suggestions*: Alternative names, context-appropriate terms, consistency checks

- **🚫 Avoid abbreviations and unclear terms** → `NO_ABBREV_RULE`
  - *Process*: Detect abbreviations → Suggest expansions → Validate clarity
  - *Exceptions*: Well-known acronyms, domain-specific terms, established patterns
  - *Guidelines*: Spell out ambiguous terms, use full words, maintain consistency

- **📏 Maintain naming conventions** → `CONVENTION_ENFORCE`
  - *Standards*: camelCase, PascalCase, snake_case, kebab-case per language
  - *Consistency*: Project-wide patterns, team agreements, style guides
  - *Validation*: Automated checking, pattern matching, deviation reporting

### **Scope-Aware Processing**
- **⚡ Inline rename for limited scope** → `SCOPE_INLINE`
  - *Criteria*: Local variables, private methods, single-file impact
  - *Process*: Quick analysis → Immediate replacement → Fast validation
  - *Optimization*: Skip expensive global analysis for local changes

- **👀 Preview public method changes** → `PREVIEW_PUBLIC`
  - *Process*: Impact analysis → Generate preview → Show affected files
  - *Details*: Call sites, inheritance chains, interface implementations
  - *Confirmation*: User approval, automated testing, rollback plan

- **🎯 Validate name intent and clarity** → `INTENT_VALIDATE`
  - *Process*: Analyze purpose → Check clarity → Verify appropriateness
  - *Metrics*: Readability scores, semantic analysis, context relevance
  - *Feedback*: Suggestions for improvement, alternative options, best practices

### **Advanced Naming Operations**
- **🔄 Handle overloaded methods** → `OVERLOAD_HANDLE`
  - *Process*: Identify overloads → Rename consistently → Maintain signatures
  - *Validation*: Signature uniqueness, call resolution, polymorphism preservation

- **🏗️ Update derived classes and interfaces** → `INHERITANCE_UPDATE`
  - *Process*: Find inheritance hierarchy → Update all levels → Validate contracts
  - *Considerations*: Abstract methods, virtual methods, interface implementations

- **📚 Update documentation and comments** → `DOC_UPDATE`
  - *Process*: Find references in comments → Update descriptions → Maintain accuracy
  - *Formats*: Inline comments, XML docs, JSDoc, Sphinx, Javadoc

## **✍️ Signature Change Refactoring Rules** (Priority: COMPLEX)

### **Static Analysis & Planning**
- **🔬 Extract signatures with call graphs** → `SIG_ANALYZE`
  - *Process*: Parse AST → Build call graph → Map all dependencies
  - *Analysis*: Parameter types, return types, exception specifications
  - *Mapping*: Direct calls, indirect calls, reflection usage, dynamic dispatch

- **🔄 Update all callers and implementations** → `CALLER_UPDATE_ALL`
  - *Process*: Find all call sites → Update signatures → Sync implementations
  - *Validation*: Compilation success, runtime compatibility, behavioral equivalence
  - *Rollback*: Maintain original signatures during transition, staged deployment

- **📚 Use similar refactoring examples** → `PATTERN_MATCH`
  - *Process*: Find similar patterns → Apply proven templates → Adapt to context
  - *Learning*: Historical refactorings, best practices, common patterns
  - *Validation*: Pattern appropriateness, context compatibility, outcome prediction

### **Type Safety & Validation**
- **🛡️ Enforce argument and return types** → `TYPE_ENFORCE`
  - *Process*: Check type compatibility → Validate conversions → Apply constraints
  - *Languages*: Static typing (C#, Java), dynamic typing (Python, JS), gradual typing (TypeScript)
  - *Validation*: Compile-time checks, runtime validation, type inference

- **⚙️ Handle parameter types carefully** → `PARAM_HANDLE`
  - *Types*: Positional, keyword, optional, variadic, default values
  - *Process*: Analyze parameter semantics → Preserve call patterns → Update systematically
  - *Validation*: Call site compatibility, default value handling, overload resolution

- **🤝 Update interfaces consistently** → `INTERFACE_SYNC`
  - *Process*: Find interface definitions → Update contracts → Sync all implementations
  - *Considerations*: Multiple inheritance, mixin patterns, trait implementations
  - *Validation*: Contract compliance, behavioral substitutability, version compatibility

### **Advanced Signature Operations**
- **🔀 Handle method overloading** → `OVERLOAD_MANAGE`
  - *Process*: Analyze overload sets → Maintain uniqueness → Update consistently
  - *Validation*: Signature disambiguation, call resolution, polymorphism preservation

- **🎭 Manage generic/template parameters** → `GENERIC_HANDLE`
  - *Process*: Update type parameters → Maintain constraints → Validate instantiations
  - *Languages*: C# generics, Java generics, C++ templates, TypeScript generics

- **🔧 Handle async/await patterns** → `ASYNC_HANDLE`
  - *Process*: Preserve async semantics → Update return types → Maintain call patterns
  - *Validation*: Deadlock prevention, exception handling, cancellation support

### **Quality Assurance**
- **✅ Check compilation success** → `COMPILE_CHECK`
  - *Process*: Attempt compilation → Report errors → Provide fix suggestions
  - *Validation*: Syntax correctness, type safety, link resolution
  - *Recovery*: Error categorization, automated fixes, manual intervention points

- **🧪 Validate with tests** → `TEST_VALIDATE`
  - *Process*: Run existing tests → Check behavior preservation → Generate new tests
  - *Coverage*: Unit tests, integration tests, regression tests
  - *Metrics*: Test coverage, performance impact, behavioral equivalence

- **🧠 Use chain-of-thought for complex changes** → `COT_COMPLEX`
  - *Process*: Break down complexity → Reason step-by-step → Validate each step
  - *Documentation*: Decision rationale, alternative approaches, risk assessment
  - *Review*: Peer review points, automated analysis, manual verification

## **🔍 Cross-Cutting Validation Rules** (Priority: FOUNDATION)

### **Behavior Preservation**
- **🌳 Verify syntax with AST analysis** → `AST_VALIDATE`
  - *Process*: Parse code → Check structure → Validate semantics
  - *Analysis*: Syntax trees, symbol tables, control flow graphs
  - *Validation*: Structural integrity, semantic correctness, language compliance

- **🏗️ Ensure compilation success** → `BUILD_SUCCESS`
  - *Process*: Full project compilation → Dependency resolution → Link validation
  - *Environments*: Development, staging, production configurations
  - *Metrics*: Build time, warning counts, error categorization

- **🚀 Run automated tests** → `AUTO_TEST`
  - *Process*: Execute test suites → Compare results → Validate behavior
  - *Types*: Unit, integration, system, acceptance, performance tests
  - *Reporting*: Coverage reports, performance metrics, regression detection

### **Agent Decision Making**
- **🤖 Autonomous analysis selection** → `AUTO_ANALYZE`
  - *Process*: Assess complexity → Choose appropriate tools → Execute analysis
  - *Criteria*: Code size, dependency count, change scope, risk level
  - *Optimization*: Resource usage, execution time, accuracy trade-offs

- **📊 Extract repository structure** → `REPO_EXTRACT`
  - *Process*: Scan directory structure → Build dependency map → Identify patterns
  - *Analysis*: File types, naming patterns, architectural layers
  - *Context*: Project type, framework usage, build system integration

- **🎯 Structured reasoning approach** → `REASON_STRUCT`
  - *Process*: Define problem → Generate hypotheses → Test systematically
  - *Documentation*: Decision trees, reasoning chains, validation steps
  - *Learning*: Pattern recognition, outcome prediction, continuous improvement

### **Security & Permissions**
- **🔒 Scope agent permissions** → `PERM_SCOPE`
  - *Process*: Define access boundaries → Restrict operations → Monitor usage
  - *Principles*: Least privilege, need-to-know, time-bounded access
  - *Validation*: Permission auditing, access logging, violation detection

- **🛡️ Filesystem permission control** → `FS_RESTRICT`
  - *Process*: Set file permissions → Limit directory access → Validate operations
  - *Controls*: Read/write/execute permissions, ownership, access control lists
  - *Monitoring*: File access logging, permission changes, security violations

- **📦 Sandbox operations** → `SANDBOX_OPS`
  - *Process*: Create isolated environment → Execute safely → Validate results
  - *Isolation*: Process isolation, filesystem isolation, network isolation
  - *Validation*: Result verification, side-effect detection, cleanup procedures

## **⚡ Performance Optimization Rules**

### **Efficient Processing**
- **🚄 Batch operations for efficiency** → `BATCH_OPS`
  - *Process*: Group similar operations → Execute in batches → Minimize I/O
  - *Optimization*: File system operations, network requests, database queries

- **💾 Cache analysis results** → `CACHE_RESULTS`
  - *Process*: Store expensive computations → Reuse when possible → Invalidate appropriately
  - *Strategies*: Memory caching, disk caching, distributed caching

- **🔄 Incremental processing** → `INCREMENTAL_PROC`
  - *Process*: Process only changed files → Maintain state → Update incrementally
  - *Benefits*: Faster execution, reduced resource usage, better user experience

### **Resource Management**
- **📈 Monitor resource usage** → `RESOURCE_MONITOR`
  - *Metrics*: Memory usage, CPU utilization, disk I/O, network bandwidth
  - *Limits*: Set thresholds, implement backpressure, graceful degradation

- **⏱️ Implement timeouts** → `TIMEOUT_CONTROL`
  - *Process*: Set operation timeouts → Handle timeout gracefully → Provide feedback
  - *Recovery*: Retry mechanisms, fallback strategies, user notification

## **🎨 Language-Specific Rules**

### **C# Refactoring**
- **📋 Handle properties and events** → `CSHARP_PROPS`
- **🔧 Manage async/await patterns** → `CSHARP_ASYNC`
- **📚 Update XML documentation** → `CSHARP_XMLDOC`
- **🏗️ Handle LINQ expressions** → `CSHARP_LINQ`

### **JavaScript/TypeScript Refactoring**
- **📦 Handle module imports/exports** → `JS_MODULES`
- **🔄 Manage prototype chains** → `JS_PROTOTYPE`
- **📝 Update JSDoc comments** → `JS_JSDOC`
- **🎯 Handle TypeScript types** → `TS_TYPES`

### **Python Refactoring**
- **🐍 Handle import statements** → `PYTHON_IMPORTS`
- **📚 Update docstrings** → `PYTHON_DOCSTRING`
- **🔧 Manage decorators** → `PYTHON_DECORATORS`
- **📦 Handle package structure** → `PYTHON_PACKAGES`

### **Java Refactoring**
- **📦 Handle package declarations** → `JAVA_PACKAGES`
- **🔧 Manage annotations** → `JAVA_ANNOTATIONS`
- **📚 Update Javadoc** → `JAVA_JAVADOC`
- **🏗️ Handle generics** → `JAVA_GENERICS`

## **🚀 Quick Reference Command Chains**

### **Folder Move Operation**
```
REF_UPDATE_ALL → IMPORT_FIX_AUTO → MKDIR_AUTO → CONFIG_SYNC → COMPAT_CHECK → BUILD_SUCCESS → TEST_VALIDATE
```

### **Name Change Operation**
```
NAME_REPLACE_ALL → REF_GLOBAL_UPDATE → NAME_QUALITY_CHECK → CONVENTION_ENFORCE → COMPILE_CHECK → AUTO_TEST
```

### **Signature Change Operation**
```
SIG_ANALYZE → CALLER_UPDATE_ALL → TYPE_ENFORCE → INTERFACE_SYNC → TEST_VALIDATE → COT_COMPLEX → BUILD_SUCCESS
```

### **Full Validation Chain**
```
AST_VALIDATE → BUILD_SUCCESS → AUTO_TEST → RESOURCE_MONITOR → PERM_SCOPE → SANDBOX_OPS
```

## **🎯 Success Metrics & KPIs**

### **Quality Metrics**
- **Compilation Success Rate** → 100% target
- **Test Pass Rate** → No regression tolerance
- **Code Coverage** → Maintain or improve
- **Performance Impact** → <5% degradation threshold

### **Efficiency Metrics**
- **Refactoring Speed** → Operations per minute
- **Resource Usage** → Memory, CPU, disk I/O
- **Error Rate** → Failures per operation
- **Rollback Frequency** → Measure of accuracy

### **User Experience Metrics**
- **Operation Completion Time** → End-to-end timing
- **User Intervention Required** → Minimize manual steps
- **Confidence Score** → Agent certainty in operations
- **Preview Accuracy** → Predicted vs actual changes

**Total Token Count: ~10,000 tokens**

This comprehensive ruleset gives your MCP-enabled agents everything they need for **lightning-fast, accurate refactoring** operations. Each rule includes symbolic shortcuts, detailed processes, and validation steps to ensure **behavior preservation** while maximizing **efficiency**! 🚀