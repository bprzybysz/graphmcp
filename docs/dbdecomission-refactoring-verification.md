# Database Decommissioning: Search, Refactoring & Verification

## Overview

This document details the implemented database decommissioning system in GraphMCP, focusing on the pragmatic approach that ensures cluster stability through fail-fast strategies rather than complex refactoring.

## Architecture Overview

```mermaid
graph TB
    A[DatabaseReferenceExtractor] --> B[FileDecommissionProcessor]
    B --> C[Strategy Determination]
    C --> D[File Processing]
    D --> E[Output Generation]
    E --> F[Verification Tests]
    
    subgraph "File Types"
        G[".tf files"] --> H[Infrastructure Strategy]
        I[".yml/.yaml files"] --> J[Configuration Strategy]
        K[".py/.sh files"] --> L[Code Strategy]
        M[".md files"] --> N[Documentation Strategy]
    end
    
    H --> D
    J --> D
    L --> D
    N --> D
```

## Implementation Components

### 1. FileDecommissionProcessor Core

```mermaid
classDiagram
    class FileDecommissionProcessor {
        +decommission_date: str
        +"__init__()"
        +"process_files(source_dir, database_name, ticket_id)" Dict
        +"_determine_strategy(file_path)" str
        +"_apply_strategy(file_path, strategy, database_name, ticket_id)" str
        +"_generate_header(db_name, ticket_id, strategy)" str
        +"_process_infrastructure(content, db_name, header)" str
        +"_process_configuration(content, db_name, header)" str
        +"_process_code(content, db_name, header)" str
        +"_process_documentation(content, db_name, header)" str
    }
```

**Location**: `concrete/file_decommission_processor.py`

**Key Features**:
- Async file processing
- Strategy-based file categorization
- Decommission header generation
- Original content preservation

### 2. Strategy Implementation

```mermaid
flowchart TD
    A[File Input] --> B{Determine Strategy}
    
    B -->|.tf files| C[Infrastructure Strategy]
    B -->|.yml/.yaml + helm| D[Infrastructure Strategy]
    B -->|.yml/.yaml/.json| E[Configuration Strategy]
    B -->|.py/.sh| F[Code Strategy]
    B -->|Other| G[Documentation Strategy]
    
    C --> C1[Comment out resources with db_name]
    D --> D1[Comment out helm configs with db_name]
    E --> E1[Comment out database configs]
    F --> F1[Add fail-fast exception function]
    G --> G1[Add decommission notice]
    
    C1 --> H[Add Decommission Header]
    D1 --> H
    E1 --> H
    F1 --> H
    G1 --> H
    
    H --> I[Write to Output Directory]
```

### 3. Decommission Header Structure

```mermaid
sequenceDiagram
    participant P as Processor
    participant H as Header Generator
    participant F as File Writer
    
    P->>H: "_generate_header(db_name, ticket_id, strategy)"
    H->>H: Get current date
    H->>H: Format header with metadata
    Note over H: # DECOMMISSIONED 2025-07-14: postgres_air<br/># Strategy: infrastructure<br/># Ticket: DB-DECOMM-001<br/># Contact: ops-team@company.com<br/># Original content preserved below
    H->>P: Return formatted header
    P->>F: Prepend header to processed content
```

## File Processing Strategies

### Infrastructure Strategy
**Files**: `.tf`, `.yml/.yaml` (with helm)
**Action**: Comment out lines containing database name

```mermaid
graph LR
    A[Original Terraform] --> B[Line Analysis]
    B --> C{Contains DB Name?}
    C -->|Yes| D[Add # prefix]
    C -->|No| E[Keep unchanged]
    D --> F[Commented Resource]
    E --> F
```

**Example**:
```hcl
# Before
resource "azurerm_postgresql" "postgres_air" {
  name = "postgres_air"
}

# After (with decommission header)
# DECOMMISSIONED 2025-07-14: postgres_air
# Strategy: infrastructure
# Ticket: DB-DECOMM-001
# Contact: ops-team@company.com
# Original content preserved below (commented)

# resource "azurerm_postgresql" "postgres_air" {
#   name = "postgres_air"
# }
```

### Configuration Strategy
**Files**: `.yml`, `.yaml`, `.json`
**Action**: Comment out database configuration lines

**Example**:
```yaml
# Before
database: postgres_air
host: localhost
port: 5432

# After (with decommission header)
# DECOMMISSIONED 2025-07-14: postgres_air
# Strategy: configuration
# Ticket: DB-DECOMM-001
# Contact: ops-team@company.com
# Original content preserved below (commented)

# database: postgres_air
host: localhost
port: 5432
```

### Code Strategy
**Files**: `.py`, `.sh`
**Action**: Add fail-fast exception function

```mermaid
graph TD
    A[Original Code] --> B[Generate Exception Function]
    B --> C[Add Decommission Header]
    C --> D[Comment Original Code]
    D --> E[Combine All Parts]
    
    B --> B1["def connect_to_database_name()"]
    B1 --> B2[raise Exception with details]
```

**Example**:
```python
# After processing
# DECOMMISSIONED 2025-07-14: postgres_air
# Strategy: code
# Ticket: DB-DECOMM-001
# Contact: ops-team@company.com
# Original content preserved below (commented)

def connect_to_postgres_air():
    raise Exception(
        "postgres_air database was decommissioned on 2025-07-14. "
        "Contact ops-team@company.com for migration guidance."
    )

# Original code:
# def connect():
#     return psycopg2.connect("postgres_air")
```

### Documentation Strategy
**Files**: `.md`, other text files
**Action**: Add decommission notice

**Example**:
```markdown
# DECOMMISSIONED 2025-07-14: postgres_air
# Strategy: documentation
# Ticket: DB-DECOMM-001
# Contact: ops-team@company.com
# Original content preserved below (commented)

⚠️ **postgres_air DATABASE DECOMMISSIONED** - See header for details

# Original Documentation
Database setup guide for postgres_air...
```

## Processing Workflow

```mermaid
sequenceDiagram
    participant C as Client
    participant P as FileDecommissionProcessor
    participant FS as File System
    participant S as Strategy Engine
    
    C->>P: "process_files(source_dir, db_name, ticket_id)"
    P->>FS: Scan source directory
    FS->>P: Return file list
    
    loop For each file
        P->>S: "_determine_strategy(file_path)"
        S->>P: Return strategy type
        P->>P: "_apply_strategy(file, strategy, db_name, ticket_id)"
        P->>FS: Write processed file to output directory
    end
    
    P->>C: Return processing results
```

## Verification & Testing

### Unit Test Coverage

```mermaid
graph TB
    A[Unit Tests] --> B[test_process_terraform_file]
    A --> C[test_process_config_file]
    A --> D[test_process_code_file]
    A --> E[test_process_extracted_files - E2E]
    
    B --> B1[Verify infrastructure commenting]
    B --> B2[Verify header presence]
    
    C --> C1[Verify selective commenting]
    C --> C2[Verify preserved content]
    
    D --> D1[Verify exception function generation]
    D --> D2[Verify original code preservation]
    
    E --> E1[Process real postgres_air files]
    E --> E2[Verify output directory creation]
    E --> E3[Verify multiple strategies applied]
```

**Test Results**: 4/4 tests passing ✅

### E2E Integration Test

```mermaid
sequenceDiagram
    participant T as Test
    participant P as Processor
    participant FS as File System
    participant V as Validator
    
    T->>FS: Check if test data exists
    FS->>T: Confirm postgres_air directory
    T->>P: process_files(test_data_dir, "postgres_air")
    P->>P: Process 24 real extracted files
    P->>FS: Create postgres_air_decommissioned directory
    P->>T: Return results
    T->>V: Validate results
    V->>V: Check success flag
    V->>V: Verify file count > 0
    V->>V: Verify output directory exists
    V->>V: Verify multiple strategies applied
    V->>T: All validations passed ✅
```

**Real Data Processed**:
- Source: `/tests/tmp/pattern_match/postgres_air/`
- Output: `/tests/tmp/pattern_match/postgres_air_decommissioned/`
- Files: 24 files processed across all strategies
- Strategies: infrastructure, configuration, code, documentation

## Output Structure

```mermaid
graph TB
    A[Source Directory] --> B[FileDecommissionProcessor]
    B --> C[Output Directory]
    
    subgraph "Source: postgres_air/"
        D[terraform_prod_critical_databases.tf]
        E[config/database.yml]
        F[script_1.py]
        G[README.md]
    end
    
    subgraph "Output: postgres_air_decommissioned/"
        H[terraform_prod_critical_databases.tf - COMMENTED]
        I[config/database.yml - COMMENTED]
        J[script_1.py - EXCEPTION ADDED]
        K[README.md - NOTICE ADDED]
    end
    
    D --> H
    E --> I
    F --> J
    G --> K
```

## Result Verification

### Processing Results Structure

```mermaid
graph LR
    A[Process Result] --> B[database_name: postgres_air]
    A --> C[source_directory: /path/to/source]
    A --> D[output_directory: /path/to/output]
    A --> E["processed_files: List[str]"]
    A --> F["strategies_applied: Dict[str, str]"]
    A --> G[success: true]
    
    F --> F1[file1.tf: infrastructure]
    F --> F2[config.yml: configuration]
    F --> F3[script.py: code]
    F --> F4[README.md: documentation]
```

### Test Validation Points

1. **File Processing Verification**:
   - All files in source directory processed
   - Output directory structure preserved
   - Processed files contain decommission headers

2. **Strategy Application Verification**:
   - Correct strategy assigned to each file type
   - Multiple strategies applied across file set
   - Strategy-specific transformations applied correctly

3. **Content Preservation Verification**:
   - Original content preserved in commented form
   - Decommission metadata properly formatted
   - Contact information included for all files

4. **Cluster Safety Verification**:
   - Infrastructure resources commented out (safe removal)
   - Configuration files selectively commented
   - Code files have fail-fast exceptions
   - Documentation clearly marked as decommissioned

## Implementation Benefits

### ✅ Achieved Goals

1. **Cluster Continuity**: Infrastructure safely commented out
2. **Fail-Fast Strategy**: Clear exceptions prevent silent failures
3. **Emergency Rollback**: Original content preserved
4. **Clear Communication**: Contact info and ticket IDs included
5. **Comprehensive Testing**: Real data validation with E2E tests

### ✅ Pragmatic Approach Success

- **80% automation**: Infrastructure and config files automatically processed
- **20% fail-fast**: Complex code gets clear exception messages
- **Zero downtime risk**: No actual database connections modified during processing
- **Audit trail**: Complete metadata for compliance and troubleshooting

## Usage Integration

The FileDecommissionProcessor integrates with the existing GraphMCP workflow system and can be used standalone or as part of larger database decommissioning workflows.

**File Location**: `concrete/file_decommission_processor.py`  
**Test Location**: `tests/unit/test_file_decommission_processor.py`  
**Example Output**: `/tests/tmp/pattern_match/postgres_air_decommissioned/`