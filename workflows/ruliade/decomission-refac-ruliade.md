# Database Decommissioning Refactoring Rules - Priority Ordered

## Pre-Refactor Setup

**Target Definition**: Define `{{TARGET_DB}}` as the database name to be removed  
**Search Variants**: Include case variations (`{{target_db}}`, `{{TARGET-DB}}`, `{{Target_Db}}`)  
**Backup Strategy**: Create dedicated Git branch `deprecate-{{TARGET_DB}}` before starting

## Group 1: Infrastructure-as-Code (Terraform & IaC) - **HIGHEST PRIORITY**

**Why First**: Infrastructure changes can cascade to all other components and may require approval/coordination

**Rules**:
- **R1.1**: Backup `.tfstate` files before any modifications
- **R1.2**: Remove `{{TARGET_DB}}` resource blocks from Terraform configuration files
- **R1.3**: Use `terraform state rm "{{TARGET_DB_RESOURCE_ADDRESS}}"` to remove from state without destroying
- **R1.4**: Update or remove database-specific variables from `.tfvars` files
- **R1.5**: Remove `{{TARGET_DB}}` references from Terraform modules and data sources
- **R1.6**: Update provider configurations that include database-specific settings
- **R1.7**: Remove database-specific outputs from Terraform output blocks
- **R1.8**: Update Terraform destroy protection flags (`prevent_destroy = false`)

**Validation**: Run `terraform plan` to verify no unintended changes  
**Commit Point**: `git commit -m "terraform: remove {{TARGET_DB}} IaC" && git tag deprec-terraform`

## Group 2: SQL Files and Database Dumps - **CRITICAL**

**Why Second**: Physical database assets must be removed before code references

**Rules**:
- **R2.1**: Delete primary SQL dump files (`.sql`, `.sql.gz`, `.dump`, `.bak`)
- **R2.2**: Remove database-specific configuration files
- **R2.3**: Check shared SQL files for `{{TARGET_DB}}` references in comments or queries
- **R2.4**: Remove backup or alternative versions
- **R2.5**: Update file listing scripts, manifests, or inventory files

**Validation**: Verify no broken file references remain  
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} dumps" && git tag deprec-sql`

## Group 3: Python Dependencies and Requirements - **HIGH PRIORITY**

**Why Third**: Dependency changes affect all subsequent code modifications

**Rules**:
- **R3.1**: Remove `{{TARGET_DB}}`-specific drivers and connectors
- **R3.2**: Run `pipdeptree --reverse {{driver_pkg}}` to identify transitive dependencies
- **R3.3**: Update setup.py or pyproject.toml to remove unnecessary dependencies
- **R3.4**: Remove `{{TARGET_DB}}`-specific environment variables from `.env` files
- **R3.5**: Regenerate lockfiles (`pip-compile`, `poetry lock`) and commit diff

**Validation**: Create fresh virtual environment and verify clean installation  
**Commit Point**: `git commit -m "deps: remove {{TARGET_DB}} dependencies" && git tag deprec-deps`

## Group 4: Python Logic Files - **HIGH PRIORITY**

**Why Fourth**: Core application logic must be updated after dependencies are clean

**Rules**:
- **R4.1**: Remove database connection configurations from Python config files
- **R4.2**: Delete or update import statements referencing `{{TARGET_DB}}`-specific modules
- **R4.3**: Remove database-specific classes, functions, and methods
- **R4.4**: Update or remove connection strings and credential references
- **R4.5**: Remove ORM models, query builders, and data access layers for `{{TARGET_DB}}`
- **R4.6**: Update database selection logic in main application files
- **R4.7**: Handle migration files: delete `{{TARGET_DB}}` migration folders or mark as obsolete
- **R4.8**: Remove database-specific error handling and exception cases

**Validation**: Run `python -m py_compile` on all modified files  
**Commit Point**: `git commit -m "python: remove {{TARGET_DB}} logic" && git tag deprec-python`

## Group 5: Setup and Configuration Files - **MEDIUM PRIORITY**

**Why Fifth**: Configuration updates after core logic is clean

**Rules**:
- **R5.1**: Remove `{{TARGET_DB}}` entries from setup scripts
- **R5.2**: Update configuration files (`.yml`, `.yaml`, `.json`, `.ini`) to remove database references
- **R5.3**: Remove `{{TARGET_DB}}_*` environment variables
- **R5.4**: Update connection string examples and templates
- **R5.5**: Remove database-specific Docker Compose services
- **R5.6**: Update Kubernetes manifests or Helm charts

**Validation**: Ensure setup process works without removed database  
**Commit Point**: `git commit -m "config: remove {{TARGET_DB}} configuration" && git tag deprec-config`

## Group 6: CI/CD and Infrastructure - **MEDIUM PRIORITY**

**Why Sixth**: Pipeline updates after application changes are complete

**Rules**:
- **R6.1**: Remove `{{TARGET_DB}}` from CI/CD pipeline configurations
- **R6.2**: Update Docker Compose to remove database services
- **R6.3**: Remove database initialization scripts from containers
- **R6.4**: Update health checks and monitoring configurations
- **R6.5**: Remove `{{TARGET_DB}}`-specific secrets and environment variables

**Validation**: Run dry-run build or pipeline validation  
**Commit Point**: `git commit -m "ci: remove {{TARGET_DB}} from pipelines" && git tag deprec-ci`

## Group 7: Documentation Files - **LOWER PRIORITY**

**Why Seventh**: Documentation updates after functional changes are complete

**Rules**:
- **R7.1**: Remove entire `{{TARGET_DB}}` section from table of contents
- **R7.2**: Delete complete database section including heading, description, and subsections
- **R7.3**: Update summary statistics (table counts, record counts, file sizes)
- **R7.4**: Remove `{{TARGET_DB}}` from comparison tables and size listings
- **R7.5**: Scan for inline mentions using case-insensitive search
- **R7.6**: Update licensing section if database-specific license exists

**Validation**: Ensure remaining sections flow logically  
**Commit Point**: `git commit -m "docs: remove {{TARGET_DB}} documentation" && git tag deprec-docs`

## Group 8: Final Cleanup and Cross-References - **LOWEST PRIORITY**

**Why Last**: Final sweep to catch any remaining references

**Rules**:
- **R8.1**: Global case-insensitive search for any remaining `{{TARGET_DB}}` references
- **R8.2**: Remove from example queries or sample code
- **R8.3**: Update any remaining automation scripts
- **R8.4**: Check for hardcoded paths or URLs containing `{{TARGET_DB}}`
- **R8.5**: Remove from test fixtures or test data references

**Validation**: Global search for `{{TARGET_DB}}` should return zero results  
**Commit Point**: `git commit -m "cleanup: final {{TARGET_DB}} removal" && git tag deprec-complete`

## Emergency Rollback Strategy

```bash
# Rollback to specific phase
git reset --hard deprec-terraform  # Infrastructure rollback
git reset --hard deprec-deps       # Dependencies rollback
git reset --hard deprec-python     # Python logic rollback

# Complete rollback
git reset --hard HEAD~8  # Full rollback to pre-refactor state
```

## Quality Gates

- **After Group 1**: Infrastructure plan shows no unexpected changes
- **After Group 3**: Fresh pip install succeeds
- **After Group 4**: Python imports work without errors
- **After Group 8**: Global search returns zero `{{TARGET_DB}}` matches