# Configuration Source Type Rules - Database Decommissioning

## Overview
Rules for handling configuration files, environment variables, setup scripts, and deployment configurations.

## Priority: **MEDIUM**
**Rationale**: Configuration updates should occur after core logic is clean but before documentation

## Pre-Processing Setup
- **Branch Strategy**: Create `deprecate-{{TARGET_DB}}-config` branch  
- **Backup Strategy**: Backup configuration files and environment templates
- **Dependencies**: Ensure application logic changes are complete

## YAML/JSON Configuration Files

### R-CONFIG-1: Application Configuration
**Priority**: HIGH
- **R-CONFIG-1.1**: Remove `{{TARGET_DB}}` entries from application config files
- **R-CONFIG-1.2**: Update configuration files (`.yml`, `.yaml`, `.json`, `.ini`) 
- **R-CONFIG-1.3**: Remove database connection sections completely
- **R-CONFIG-1.4**: Update configuration schemas and validation rules
- **R-CONFIG-1.5**: Remove database-specific feature flags and toggles

### R-CONFIG-2: Service Configuration
**Priority**: HIGH
- **R-CONFIG-2.1**: Update microservice configuration files
- **R-CONFIG-2.2**: Remove database references from service registries
- **R-CONFIG-2.3**: Update API gateway configurations
- **R-CONFIG-2.4**: Remove database health check configurations
- **R-CONFIG-2.5**: Update service mesh configurations

**Validation**: Validate JSON/YAML syntax and schema compliance
**Commit Point**: `git commit -m "config: remove {{TARGET_DB}} from app configs" && git tag deprec-app-config`

## Environment Variables and Files

### R-CONFIG-3: Environment Files
**Priority**: HIGH
- **R-CONFIG-3.1**: Remove `{{TARGET_DB}}_*` environment variables from `.env` files
- **R-CONFIG-3.2**: Update `.env.example` and `.env.template` files
- **R-CONFIG-3.3**: Remove database URLs and connection strings
- **R-CONFIG-3.4**: Clean up environment variable documentation
- **R-CONFIG-3.5**: Update environment variable validation scripts

### R-CONFIG-4: Runtime Environment
**Priority**: MEDIUM
- **R-CONFIG-4.1**: Remove database environment variables from container configs
- **R-CONFIG-4.2**: Update environment variable injection in orchestration
- **R-CONFIG-4.3**: Remove database secrets from environment management
- **R-CONFIG-4.4**: Update environment variable defaults and fallbacks

**Validation**: Ensure application starts without removed environment variables
**Commit Point**: `git commit -m "env: remove {{TARGET_DB}} environment variables" && git tag deprec-env`

## Docker and Container Configuration

### R-CONFIG-5: Docker Configuration
**Priority**: HIGH
- **R-CONFIG-5.1**: Remove database-specific Docker Compose services
- **R-CONFIG-5.2**: Update Dockerfile environment variable declarations
- **R-CONFIG-5.3**: Remove database initialization scripts from containers
- **R-CONFIG-5.4**: Update Docker Compose network configurations
- **R-CONFIG-5.5**: Remove database volume mounts and declarations

### R-CONFIG-6: Container Orchestration
**Priority**: MEDIUM
- **R-CONFIG-6.1**: Update Docker Swarm service configurations
- **R-CONFIG-6.2**: Remove database-related container dependencies
- **R-CONFIG-6.3**: Update container health check configurations
- **R-CONFIG-6.4**: Remove database-specific container resource limits

**Validation**: `docker-compose config` validates without errors
**Commit Point**: `git commit -m "docker: remove {{TARGET_DB}} container configs" && git tag deprec-docker`

## CI/CD Configuration

### R-CONFIG-7: Pipeline Configuration
**Priority**: MEDIUM
- **R-CONFIG-7.1**: Remove `{{TARGET_DB}}` from CI/CD pipeline configurations
- **R-CONFIG-7.2**: Update build environment variables in pipelines
- **R-CONFIG-7.3**: Remove database testing and migration steps
- **R-CONFIG-7.4**: Update deployment pipeline configurations
- **R-CONFIG-7.5**: Remove database-specific artifact generation

### R-CONFIG-8: Testing Configuration
**Priority**: MEDIUM
- **R-CONFIG-8.1**: Update test configuration files
- **R-CONFIG-8.2**: Remove database test fixtures and seeds
- **R-CONFIG-8.3**: Update integration test configurations
- **R-CONFIG-8.4**: Remove database-specific test environments

**Validation**: Pipeline dry-run executes successfully
**Commit Point**: `git commit -m "ci: remove {{TARGET_DB}} from pipelines" && git tag deprec-ci-config`

## Setup and Installation Scripts

### R-CONFIG-9: Setup Scripts
**Priority**: MEDIUM
- **R-CONFIG-9.1**: Remove `{{TARGET_DB}}` entries from setup scripts
- **R-CONFIG-9.2**: Update installation and bootstrap scripts
- **R-CONFIG-9.3**: Remove database initialization from setup
- **R-CONFIG-9.4**: Update configuration generation scripts
- **R-CONFIG-9.5**: Remove database-specific setup validations

### R-CONFIG-10: Development Environment
**Priority**: LOW
- **R-CONFIG-10.1**: Update development environment setup
- **R-CONFIG-10.2**: Remove database from local development stacks
- **R-CONFIG-10.3**: Update developer onboarding scripts
- **R-CONFIG-10.4**: Remove database-specific development tools

**Validation**: Setup process works without removed database
**Commit Point**: `git commit -m "setup: remove {{TARGET_DB}} from setup scripts" && git tag deprec-setup`

## Configuration Templates and Examples

### R-CONFIG-11: Template Files
**Priority**: LOW
- **R-CONFIG-11.1**: Update configuration templates
- **R-CONFIG-11.2**: Remove database examples from sample configs
- **R-CONFIG-11.3**: Update configuration generators and scaffolding
- **R-CONFIG-11.4**: Remove database references from configuration documentation

### R-CONFIG-12: Example Configurations
**Priority**: LOW
- **R-CONFIG-12.1**: Update connection string examples and templates
- **R-CONFIG-12.2**: Remove database configuration examples
- **R-CONFIG-12.3**: Update sample environment files
- **R-CONFIG-12.4**: Remove database-specific configuration tutorials

**Validation**: Templates generate valid configurations
**Commit Point**: `git commit -m "templates: remove {{TARGET_DB}} from config templates" && git tag deprec-templates`

## Security and Secrets Configuration

### R-CONFIG-13: Secrets Management
**Priority**: HIGH
- **R-CONFIG-13.1**: Remove database credentials from secret stores
- **R-CONFIG-13.2**: Update secrets management configurations
- **R-CONFIG-13.3**: Remove database-specific encryption keys
- **R-CONFIG-13.4**: Update access control for secrets
- **R-CONFIG-13.5**: Remove database connection certificates

### R-CONFIG-14: Security Configuration
**Priority**: HIGH
- **R-CONFIG-14.1**: Update security policy configurations
- **R-CONFIG-14.2**: Remove database-specific firewall rules
- **R-CONFIG-14.3**: Update authentication configurations
- **R-CONFIG-14.4**: Remove database access control rules

**Validation**: Security configurations remain intact
**Commit Point**: `git commit -m "security: remove {{TARGET_DB}} security configs" && git tag deprec-security-config`

## Monitoring and Logging Configuration

### R-CONFIG-15: Monitoring Configuration
**Priority**: MEDIUM
- **R-CONFIG-15.1**: Remove database monitoring configurations
- **R-CONFIG-15.2**: Update metrics collection configurations
- **R-CONFIG-15.3**: Remove database-specific alerting rules
- **R-CONFIG-15.4**: Update dashboard configurations
- **R-CONFIG-15.5**: Remove database performance monitoring

### R-CONFIG-16: Logging Configuration
**Priority**: MEDIUM
- **R-CONFIG-16.1**: Remove database-specific logging configurations
- **R-CONFIG-16.2**: Update log aggregation rules
- **R-CONFIG-16.3**: Remove database query logging
- **R-CONFIG-16.4**: Update log retention policies for database logs

**Validation**: Monitoring and logging systems function correctly
**Commit Point**: `git commit -m "monitoring: remove {{TARGET_DB}} monitoring configs" && git tag deprec-monitoring-config`

## Quality Gates and Validation

### Pre-Commit Validation
- [ ] Configuration files pass syntax validation
- [ ] Environment variables are properly handled
- [ ] Container configurations are valid
- [ ] Pipeline configurations execute successfully
- [ ] Security configurations remain intact

### Post-Commit Validation
- [ ] Application starts without database configuration
- [ ] CI/CD pipelines execute successfully
- [ ] Development environment setup works
- [ ] Monitoring and logging function correctly

## Emergency Rollback Strategy

```bash
# Rollback configuration changes
git reset --hard deprec-app-config^
git reset --hard deprec-env^
git reset --hard deprec-docker^

# Restore environment files
cp .env.backup .env
cp docker-compose.yml.backup docker-compose.yml

# Restart services with original configuration
docker-compose down && docker-compose up -d
```

## Configuration Testing Checklist

- [ ] Application starts without database environment variables
- [ ] Configuration validation passes
- [ ] Container orchestration works correctly
- [ ] CI/CD pipelines execute without database steps
- [ ] Development environment setup succeeds
- [ ] Security configurations are preserved
- [ ] Monitoring continues to function for remaining services 