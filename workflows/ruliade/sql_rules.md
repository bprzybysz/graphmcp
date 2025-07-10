# SQL Source Type Rules - Database Decommissioning

## Overview
Rules for handling SQL database dumps, migration files, schema definitions, and database-specific assets.

## Priority: **CRITICAL**
**Rationale**: Physical database assets must be removed before code references to prevent broken dependencies

## Pre-Processing Setup
- **Branch Strategy**: Create `deprecate-{{TARGET_DB}}-sql` branch
- **Backup Strategy**: Create final archive of all SQL assets before removal
- **Dependencies**: Verify no active database connections or processes

## SQL Dump Files

### R-SQL-1: Database Dump Files
**Priority**: CRITICAL
- **R-SQL-1.1**: Delete primary SQL dump files (`.sql`, `.sql.gz`, `.dump`, `.bak`)
- **R-SQL-1.2**: Remove compressed database archives (`.zip`, `.tar.gz`, `.7z`)
- **R-SQL-1.3**: Delete database export files from automated backups
- **R-SQL-1.4**: Remove sample data files specific to the database
- **R-SQL-1.5**: Clean up temporary dump files and partial exports

### R-SQL-2: Database Backup Files
**Priority**: CRITICAL
- **R-SQL-2.1**: Remove backup or alternative versions from backup directories
- **R-SQL-2.2**: Delete incremental backup files
- **R-SQL-2.3**: Remove point-in-time recovery files
- **R-SQL-2.4**: Clean up backup verification and validation files
- **R-SQL-2.5**: Remove backup metadata and catalog files

**Validation**: Verify no broken file references remain in scripts or documentation
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} dump files" && git tag deprec-sql-dumps`

## Migration and Schema Files

### R-SQL-3: Migration Files
**Priority**: HIGH
- **R-SQL-3.1**: Delete `{{TARGET_DB}}` migration folders or mark as obsolete
- **R-SQL-3.2**: Remove migration scripts specific to the database
- **R-SQL-3.3**: Update migration tracking tables to mark as completed/obsolete
- **R-SQL-3.4**: Remove rollback migration scripts
- **R-SQL-3.5**: Clean up migration metadata and version files

### R-SQL-4: Schema Definition Files
**Priority**: HIGH
- **R-SQL-4.1**: Remove database schema definition files (`.sql`, `.ddl`)
- **R-SQL-4.2**: Delete table creation scripts specific to database
- **R-SQL-4.3**: Remove stored procedure and function definitions
- **R-SQL-4.4**: Clean up view and trigger definitions
- **R-SQL-4.5**: Remove database-specific indexes and constraints

**Validation**: Migration systems function correctly without removed files
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} migrations and schemas" && git tag deprec-sql-migrations`

## Shared SQL Files

### R-SQL-5: Multi-Database SQL Files
**Priority**: HIGH
- **R-SQL-5.1**: Check shared SQL files for `{{TARGET_DB}}` references in comments
- **R-SQL-5.2**: Remove database-specific queries from shared scripts
- **R-SQL-5.3**: Update cross-database join queries and references
- **R-SQL-5.4**: Remove database name qualifiers (e.g., `{{TARGET_DB}}.table_name`)
- **R-SQL-5.5**: Update database selection logic in multi-database scripts

### R-SQL-6: SQL Template and Generator Files
**Priority**: MEDIUM
- **R-SQL-6.1**: Remove database templates and scaffolding
- **R-SQL-6.2**: Update SQL code generators to exclude database
- **R-SQL-6.3**: Remove database-specific SQL snippets and examples
- **R-SQL-6.4**: Update SQL documentation templates

**Validation**: Shared scripts execute correctly without database references
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} from shared SQL files" && git tag deprec-sql-shared`

## Data and Seed Files

### R-SQL-7: Seed and Test Data
**Priority**: MEDIUM
- **R-SQL-7.1**: Remove database-specific seed data files
- **R-SQL-7.2**: Delete test data and fixtures for the database
- **R-SQL-7.3**: Remove sample datasets and demo data
- **R-SQL-7.4**: Clean up data import and export scripts
- **R-SQL-7.5**: Remove database-specific data validation scripts

### R-SQL-8: ETL and Data Pipeline SQL
**Priority**: MEDIUM
- **R-SQL-8.1**: Remove ETL scripts that source from the database
- **R-SQL-8.2**: Update data pipeline SQL to exclude database tables
- **R-SQL-8.3**: Remove database-specific data transformation scripts
- **R-SQL-8.4**: Update data quality and validation queries
- **R-SQL-8.5**: Remove database from data lineage documentation

**Validation**: Data pipelines function correctly without database
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} data and ETL scripts" && git tag deprec-sql-data`

## Database-Specific SQL Features

### R-SQL-9: Stored Procedures and Functions
**Priority**: HIGH
- **R-SQL-9.1**: Drop stored procedures specific to the database
- **R-SQL-9.2**: Remove user-defined functions that reference database tables
- **R-SQL-9.3**: Clean up database-specific triggers
- **R-SQL-9.4**: Remove custom database types and domains
- **R-SQL-9.5**: Drop database-specific aggregate functions

### R-SQL-10: Database Objects
**Priority**: HIGH
- **R-SQL-10.1**: Remove database-specific views and materialized views
- **R-SQL-10.2**: Drop database-specific sequences and identity columns
- **R-SQL-10.3**: Remove custom indexes specific to database queries
- **R-SQL-10.4**: Clean up database-specific partitions and sharding
- **R-SQL-10.5**: Remove database-specific foreign key constraints

**Validation**: Database objects are properly cleaned up
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} database objects" && git tag deprec-sql-objects`

## SQL Documentation and Comments

### R-SQL-11: SQL Documentation
**Priority**: LOW
- **R-SQL-11.1**: Remove database sections from SQL documentation
- **R-SQL-11.2**: Update SQL style guides and standards
- **R-SQL-11.3**: Remove database-specific query examples
- **R-SQL-11.4**: Clean up SQL performance tuning documentation
- **R-SQL-11.5**: Update SQL security guidelines

### R-SQL-12: Inline SQL Comments
**Priority**: LOW
- **R-SQL-12.1**: Remove database references from SQL comments (`-- {{TARGET_DB}}`)
- **R-SQL-12.2**: Clean up block comments (`/* {{TARGET_DB}} */`)
- **R-SQL-12.3**: Update SQL header comments and documentation
- **R-SQL-12.4**: Remove database-specific TODO comments
- **R-SQL-12.5**: Update SQL change log comments

**Validation**: SQL documentation is consistent and complete
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} from SQL documentation" && git tag deprec-sql-docs`

## SQL Automation and Tooling

### R-SQL-13: SQL Automation Scripts
**Priority**: MEDIUM
- **R-SQL-13.1**: Update file listing scripts, manifests, or inventory files
- **R-SQL-13.2**: Remove database from SQL linting and validation tools
- **R-SQL-13.3**: Update SQL formatting and code style tools
- **R-SQL-13.4**: Remove database-specific SQL testing frameworks
- **R-SQL-13.5**: Update SQL performance monitoring tools

### R-SQL-14: Database Administration Scripts
**Priority**: MEDIUM
- **R-SQL-14.1**: Remove database maintenance scripts
- **R-SQL-14.2**: Update database monitoring and health check scripts
- **R-SQL-14.3**: Remove database backup and restore automation
- **R-SQL-14.4**: Clean up database user and permission management scripts
- **R-SQL-14.5**: Update database statistics and reporting scripts

**Validation**: SQL tooling works correctly without database references
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} from SQL tooling" && git tag deprec-sql-tooling`

## Cross-Database References

### R-SQL-15: Cross-Database Queries
**Priority**: HIGH
- **R-SQL-15.1**: Remove cross-database JOIN queries
- **R-SQL-15.2**: Update federated query definitions
- **R-SQL-15.3**: Remove database links and external data sources
- **R-SQL-15.4**: Update database synonym definitions
- **R-SQL-15.5**: Remove cross-database replication configurations

### R-SQL-16: Database Integration Points
**Priority**: HIGH
- **R-SQL-16.1**: Remove database from data synchronization scripts
- **R-SQL-16.2**: Update database federation configurations
- **R-SQL-16.3**: Remove database from multi-tenant query routing
- **R-SQL-16.4**: Update database sharding and partitioning logic
- **R-SQL-16.5**: Remove database from distributed transaction scripts

**Validation**: Cross-database integrations function correctly
**Commit Point**: `git commit -m "sql: remove {{TARGET_DB}} cross-database references" && git tag deprec-sql-integration`

## Quality Gates and Validation

### Pre-Commit Validation
- [ ] No active database connections exist
- [ ] All SQL dump files are properly archived
- [ ] Migration scripts are marked as obsolete
- [ ] Shared SQL files validate correctly
- [ ] Cross-database references are updated

### Post-Commit Validation
- [ ] No broken file references remain
- [ ] Migration systems function correctly
- [ ] Data pipelines operate without database
- [ ] SQL tooling works properly
- [ ] Documentation is consistent

## Emergency Rollback Strategy

```bash
# Rollback SQL file changes
git reset --hard deprec-sql-dumps^
git reset --hard deprec-sql-migrations^
git reset --hard deprec-sql-shared^

# Restore from archive if needed
tar -xzf {{TARGET_DB}}-sql-backup-$(date +%Y%m%d).tar.gz

# Restore database from backup if critical
pg_restore -d postgres {{TARGET_DB}}-final-backup.dump
```

## SQL-Specific Testing Checklist

- [ ] All SQL dump files removed or archived
- [ ] Migration scripts marked as obsolete
- [ ] Shared SQL files execute without errors
- [ ] Data pipelines function correctly
- [ ] Cross-database queries updated
- [ ] SQL tooling operates properly
- [ ] Database objects properly cleaned up
- [ ] No dangling database references remain 