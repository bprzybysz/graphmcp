# ContextualRulesEngine Integration Tests

This directory contains comprehensive integration tests for the real `ContextualRulesEngine` that validate the complete refactoring workflow for non-agent based database decommissioning.

## 🎯 Test Coverage

### 1. Rule Definitions Testing
- **Infrastructure Rules**: Terraform, Helm, Kubernetes, Docker Compose
- **Configuration Rules**: YAML/JSON configs, environment variables
- **SQL Rules**: CREATE/USE statements, table references
- **Python Rules**: Django, SQLAlchemy, connection strings, imports
- **Documentation Rules**: Markdown references, code blocks

### 2. Framework Detection Logic
- **Terraform**: Resource detection and specific patterns
- **Helm**: Values.yaml and chart configurations 
- **Django**: Settings.py and model detection
- **Kubernetes**: Deployment manifests and environment variables
- **SQLAlchemy**: Engine and session configurations

### 3. Complex Pattern Matching
- **Real Regex Patterns**: Tests actual patterns from rule definitions
- **Template Variables**: Validates `{{TARGET_DB}}` replacement
- **Multi-line Matching**: Complex SQL and configuration blocks
- **Case Sensitivity**: Various database name formats

### 4. Rule Action Methods
- **`_comment_out_patterns()`**: Line-by-line commenting with proper prefixes
- **`_add_deprecation_notice()`**: Deprecation warnings before matched lines
- **`_remove_matching_lines()`**: Complete line removal for specified patterns

### 5. End-to-End File Processing
- **Complete Workflow**: Classification → Rule Application → File Updates
- **Multiple File Types**: Terraform, Python, SQL, YAML, Markdown
- **Framework-Specific Rules**: Only applicable rules are applied
- **Change Tracking**: Detailed logging of all modifications

### 6. Error Handling & Edge Cases
- **Empty Files**: Graceful handling of empty content
- **No Matches**: Files with no database references
- **Invalid Patterns**: Malformed regex pattern handling
- **Large Files**: Performance with 1000+ line files

### 7. Performance Validation
- **Individual Tests**: <5 seconds per file processing
- **Batch Processing**: Multiple files within time limits
- **Memory Usage**: Efficient pattern matching
- **Scalability**: Large repository simulation

## 🚀 Running the Tests

### Quick Start
```bash
# Run all integration tests
.venv/bin/python -m pytest tests/integration/test_contextual_rules_integration.py -v

# Run with the custom test runner
./tests/integration/run_contextual_rules_tests.py
```

### Test Runner Options
```bash
# Fast execution (skip performance tests)
./tests/integration/run_contextual_rules_tests.py --fast

# Performance tests only
./tests/integration/run_contextual_rules_tests.py --performance

# Verbose output
./tests/integration/run_contextual_rules_tests.py --verbose

# Run specific test category
./tests/integration/run_contextual_rules_tests.py --pattern terraform
./tests/integration/run_contextual_rules_tests.py --pattern framework
./tests/integration/run_contextual_rules_tests.py --pattern "rule actions"
```

### Individual Test Categories
```bash
# Rule definition tests
python -m pytest tests/integration/test_contextual_rules_integration.py::TestContextualRulesEngineIntegration::test_load_infrastructure_rules -v

# Framework detection tests  
python -m pytest tests/integration/test_contextual_rules_integration.py::TestContextualRulesEngineIntegration::test_terraform_framework_detection -v

# Pattern matching tests
python -m pytest tests/integration/test_contextual_rules_integration.py::TestContextualRulesEngineIntegration::test_terraform_resource_pattern_matching -v

# Rule action method tests
python -m pytest tests/integration/test_contextual_rules_integration.py::TestContextualRulesEngineIntegration::test_comment_out_patterns_method -v

# End-to-end processing tests
python -m pytest tests/integration/test_contextual_rules_integration.py::TestContextualRulesEngineIntegration::test_terraform_file_processing_end_to_end -v

# Performance tests
python -m pytest tests/integration/test_contextual_rules_integration.py::TestContextualRulesEnginePerformance -v
```

## 📊 Expected Results

### ✅ Success Criteria
- **All Rule Loading Tests Pass**: All 5 rule definition loaders work correctly
- **Framework Detection Works**: 4+ frameworks correctly identified
- **Pattern Matching Accurate**: Complex regex patterns match expected content
- **Rule Actions Function**: All 3 action types produce correct transformations
- **End-to-End Processing**: Complete workflow succeeds for all file types
- **Performance Targets Met**: <5s per file, <30s for batch processing

### 📈 Performance Benchmarks
| Test Category | Target Time | Measured |
|---------------|-------------|----------|
| Rule Loading | <1s | ~0.16s ✅ |
| Framework Detection | <2s | - |
| Pattern Matching | <3s | - |
| Rule Actions | <2s | - |
| End-to-End Processing | <5s | - |
| Performance Tests | <30s | - |

## 🔧 Test Environment Setup

### Prerequisites
```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Install test dependencies
pip install pytest pytest-asyncio

# Verify core modules can be imported
python -c "from concrete.contextual_rules_engine import ContextualRulesEngine; print('✅ Ready')"
```

### Environment Variables
```bash
# Optional: Set test database name
export TEST_DATABASE_NAME="test_airline_db"

# Optional: Enable verbose logging
export PYTEST_VERBOSE=1
```

## 🆚 Comparison: Integration vs Fast Tests

| Aspect | Fast Tests | Integration Tests |
|--------|------------|-------------------|
| **Speed** | <0.01ms per test | <5s per test |
| **Scope** | Simplified refactoring logic | Real ContextualRulesEngine |
| **Patterns** | Basic regex: `\b{db}\b` | Complex: `r'resource\s+"[^"]*database[^"]*"\s+"{{TARGET_DB}}"'` |
| **Rules** | 5 hardcoded transformations | Real rule definitions from files |
| **Frameworks** | File type only | Full framework detection |
| **Actions** | Simple replacements | Real `_comment_out_patterns()`, etc. |
| **Purpose** | Validate refactoring principles | Validate production implementation |

## 🚨 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure virtual environment is active and dependencies installed
2. **Test Timeouts**: Large files may need timeout adjustment (default: 5 minutes)
3. **Pattern Failures**: Check that regex patterns use proper escaping
4. **Framework Detection**: Verify file content includes framework-specific markers

### Debug Commands
```bash
# Test basic imports
python -c "from tests.integration.test_contextual_rules_integration import TestContextualRulesEngineIntegration; print('✅ Imports work')"

# Validate rule loading
python -c "from concrete.contextual_rules_engine import create_contextual_rules_engine; engine = create_contextual_rules_engine(); rules = engine._load_infrastructure_rules(); print(f'✅ {len(rules)} rules loaded')"

# Check source type classification
python -c "from concrete.source_type_classifier import SourceTypeClassifier; classifier = SourceTypeClassifier(); result = classifier.classify_file('test.tf', 'resource \"aws_db\" \"test\" {}'); print(f'✅ Classified as {result.source_type}')"
```

## 📋 Test Checklist

Before deploying ContextualRulesEngine to production:

- [ ] All rule definition tests pass
- [ ] Framework detection works for all 4+ frameworks
- [ ] Complex pattern matching validates correctly
- [ ] All 3 rule action methods function properly
- [ ] End-to-end processing succeeds for all file types
- [ ] Error handling gracefully manages edge cases
- [ ] Performance meets <5s per file target
- [ ] Batch processing completes within time limits

## 🎉 Success Metrics

**Integration tests passing means:**
- ✅ Real ContextualRulesEngine is production-ready
- ✅ Non-agent refactoring logic is thoroughly validated
- ✅ All file types and frameworks are supported
- ✅ Performance targets are met
- ✅ Error handling is robust

These integration tests complement the fast refactoring tests by validating the actual production implementation rather than simplified test logic. 