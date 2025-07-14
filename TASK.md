## TASK.md - Database Reference Extractor Implementation
!!!!FULLY IMPLEMENTED 



**Created**: 2025-07-14  
**Status**: Planning Phase  
**Target**: Essential implementation only (pruned from full PRP)  

### =Ë Executive Summary
Implement minimal Database Reference Extractor: finds database references in packed repository files using normal grep, extracts matching files while preserving directory structure. Focus on unit tests + 1 e2e test with configurable parameters.

### <¯ Essential Tasks

#### Phase 1: Core Implementation
- [x] **Step 1**: Create `concrete/database_reference_extractor.py` with basic DatabaseReferenceExtractor class
- [x] **Step 2**: Implement `_parse_repomix_file()` to parse XML format
- [x] **Step 3**: Implement `_grep_file_content()` using normal regex search (not contextual rules)
- [x] **Step 4**: Implement `_extract_file()` preserving directory structure
- [x] **Step 5**: Create MatchedFile dataclass for results

#### Phase 2: Essential Testing
- [x] **Step 6**: Create `tests/test_database_reference_extractor.py` with basic test structure
- [x] **Step 7**: Implement unit test `test_extract_references_basic()` with mock data
- [x] **Step 8**: Implement unit test `test_directory_preservation()` 
- [x] **Step 9**: Implement unit test `test_no_matches_found()`
- [x] **Step 10**: Implement parameterized e2e test `test_real_extraction()` with real postgres_air data

#### Phase 3: Documentation
- [x] **Step 11**: Update QUICK_REFERENCE.md with test coverage table
- [x] **Step 12**: Add basic usage example to README or QUICK_REFERENCE

### =' Implementation Details

#### Core Requirements
1. **Normal Grep**: Use `re.findall()` or similar, NOT the contextual rules engine
2. **Directory Preservation**: Extract files to `tests/tmp/pattern_match/{database_name}/original/path/structure`
3. **Repomix Parsing**: Parse XML format `<file path="...">content</file>`
4. **Parameterized Test**: Allow different `target_repo_pack_path` and `database_name` values

#### File Structure
```
concrete/
  database_reference_extractor.py  # Core implementation
tests/
  test_database_reference_extractor.py  # Unit + e2e tests
  tmp/
    pattern_match/  # Output directory for extracted files
      postgres_air/  # Database-specific subdirectory
```

### =Ê Success Criteria (Minimal)
- [x] Extract database references using normal grep
- [x] Preserve directory structure in extracted files  
- [x] 3 unit tests + 1 parameterized e2e test passing
- [x] Basic test coverage table in QUICK_REFERENCE.md

### =« Out of Scope (Pruned)
- Enhanced logging integration
- Progress tracking/visualization
- Performance optimization  
- HTML reports
- Complex error handling
- Comprehensive documentation

### = Progress Tracking
- **Phase 1 Progress**: 0/5 steps completed
- **Phase 2 Progress**: 0/5 steps completed  
- **Phase 3 Progress**: 0/2 steps completed
- **Overall Progress**: 0/12 steps completed (0%)

---

**Next**: Execute Step 1 - Create core DatabaseReferenceExtractor class