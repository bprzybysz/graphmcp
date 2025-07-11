# Infrastructure Source Type Rules - Database Decommissioning

## Overview
Rules specific to Infrastructure-as-Code components including Terraform, Helm charts, Kubernetes manifests, and cloud resources.

## Priority: **HIGHEST**
**Rationale**: Infrastructure changes cascade to all other components and require coordination/approval

## Pre-Processing Setup
- **Branch Strategy**: Create `deprecate-{{TARGET_DB}}-infra` branch
- **Backup Strategy**: Backup `.tfstate`, `.tfvars`, and Helm release states
- **Dependencies**: Check for dependent resources and services

## Terraform Rules

### R-INFRA-1: Terraform State Management
**Priority**: CRITICAL
- **R-INFRA-1.1**: Backup `.tfstate` files before any modifications
- **R-INFRA-1.2**: Use `terraform state rm "{{TARGET_DB_RESOURCE_ADDRESS}}"` to remove from state without destroying
- **R-INFRA-1.3**: Verify state consistency with `terraform state list | grep {{TARGET_DB}}`
- **R-INFRA-1.4**: Export state backup: `terraform state pull > backup-{{TARGET_DB}}-$(date +%s).tfstate`

### R-INFRA-2: Resource Removal
**Priority**: CRITICAL
- **R-INFRA-2.1**: Remove `{{TARGET_DB}}` resource blocks from Terraform configuration files
- **R-INFRA-2.2**: Remove database-specific data sources and references
- **R-INFRA-2.3**: Update provider configurations that include database-specific settings
- **R-INFRA-2.4**: Remove database-specific outputs from Terraform output blocks

### R-INFRA-3: Variables and Configuration
**Priority**: HIGH
- **R-INFRA-3.1**: Update or remove database-specific variables from `.tfvars` files
- **R-INFRA-3.2**: Remove `{{TARGET_DB}}` references from Terraform modules
- **R-INFRA-3.3**: Update Terraform destroy protection flags (`prevent_destroy = false`)
- **R-INFRA-3.4**: Clean up variable definitions in `variables.tf`

**Validation**: Run `terraform plan` to verify no unintended changes
**Commit Point**: `git commit -m "terraform: remove {{TARGET_DB}} IaC" && git tag deprec-terraform`

## Helm Chart Rules

### R-INFRA-4: Helm Values and Templates
**Priority**: HIGH
- **R-INFRA-4.1**: Remove `{{TARGET_DB}}` entries from `values.yaml` and `values-*.yaml`
- **R-INFRA-4.2**: Update template files to remove database references
- **R-INFRA-4.3**: Remove database-specific ConfigMaps and Secrets
- **R-INFRA-4.4**: Update Chart dependencies in `Chart.yaml`

### R-INFRA-5: Helm Releases
**Priority**: HIGH
- **R-INFRA-5.1**: Check active Helm releases: `helm list -A | grep {{TARGET_DB}}`
- **R-INFRA-5.2**: Uninstall database-specific releases: `helm uninstall {{TARGET_DB}}-*`
- **R-INFRA-5.3**: Clean up Helm secrets and ConfigMaps
- **R-INFRA-5.4**: Update umbrella charts that reference the database

**Validation**: `helm template` and `helm lint` to verify chart integrity
**Commit Point**: `git commit -m "helm: remove {{TARGET_DB}} charts" && git tag deprec-helm`

## Kubernetes Manifest Rules

### R-INFRA-6: Kubernetes Resources
**Priority**: HIGH
- **R-INFRA-6.1**: Remove database Deployments, StatefulSets, and DaemonSets
- **R-INFRA-6.2**: Remove database Services and Ingress resources
- **R-INFRA-6.3**: Clean up database-specific ConfigMaps and Secrets
- **R-INFRA-6.4**: Remove PersistentVolumes and PersistentVolumeClaims
- **R-INFRA-6.5**: Update NetworkPolicies that reference database pods

### R-INFRA-7: RBAC and Security
**Priority**: MEDIUM
- **R-INFRA-7.1**: Remove database-specific ServiceAccounts
- **R-INFRA-7.2**: Clean up ClusterRoles and RoleBindings
- **R-INFRA-7.3**: Remove database-specific SecurityContexts
- **R-INFRA-7.4**: Update Pod Security Policies if applicable

**Validation**: `kubectl dry-run=client` to verify manifest validity
**Commit Point**: `git commit -m "k8s: remove {{TARGET_DB}} manifests" && git tag deprec-k8s`

## Cloud Provider Specific Rules

### R-INFRA-8: AWS Resources
**Priority**: HIGH (if using AWS)
- **R-INFRA-8.1**: Remove RDS instances and parameter groups
- **R-INFRA-8.2**: Clean up VPC security groups specific to database
- **R-INFRA-8.3**: Remove database-specific IAM roles and policies
- **R-INFRA-8.4**: Clean up CloudWatch alarms and log groups
- **R-INFRA-8.5**: Remove database-specific backup policies and snapshots

### R-INFRA-9: Azure Resources
**Priority**: HIGH (if using Azure)
- **R-INFRA-9.1**: Remove PostgreSQL/MySQL Flexible Server instances
- **R-INFRA-9.2**: Clean up Azure Key Vault secrets for database credentials
- **R-INFRA-9.3**: Remove database-specific Network Security Groups
- **R-INFRA-9.4**: Clean up Azure Monitor alerts and dashboards
- **R-INFRA-9.5**: Remove database-specific Resource Groups if dedicated

### R-INFRA-10: GCP Resources
**Priority**: HIGH (if using GCP)
- **R-INFRA-10.1**: Remove Cloud SQL instances and replicas
- **R-INFRA-10.2**: Clean up GCP IAM bindings for database access
- **R-INFRA-10.3**: Remove database-specific VPC firewall rules
- **R-INFRA-10.4**: Clean up Cloud Monitoring dashboards and alerts
- **R-INFRA-10.5**: Remove database-specific Cloud Storage buckets for backups

## Monitoring and Observability Rules

### R-INFRA-11: Monitoring Infrastructure
**Priority**: MEDIUM
- **R-INFRA-11.1**: Remove database-specific Prometheus monitoring rules
- **R-INFRA-11.2**: Clean up Grafana dashboards for database metrics
- **R-INFRA-11.3**: Remove Datadog/New Relic monitors for database
- **R-INFRA-11.4**: Clean up ELK stack configurations for database logs
- **R-INFRA-11.5**: Remove database-specific alerting rules

### R-INFRA-12: Backup Infrastructure
**Priority**: MEDIUM
- **R-INFRA-12.1**: Remove database-specific backup jobs and CronJobs
- **R-INFRA-12.2**: Clean up backup storage (S3 buckets, Azure Storage, etc.)
- **R-INFRA-12.3**: Remove backup monitoring and alerting
- **R-INFRA-12.4**: Update backup retention policies

## Network and Security Rules

### R-INFRA-13: Network Configuration
**Priority**: MEDIUM
- **R-INFRA-13.1**: Remove database-specific DNS records
- **R-INFRA-13.2**: Clean up load balancer configurations
- **R-INFRA-13.3**: Remove database-specific network ACLs
- **R-INFRA-13.4**: Update service mesh configurations (Istio, Linkerd)

### R-INFRA-14: Security Configuration
**Priority**: HIGH
- **R-INFRA-14.1**: Remove database-specific SSL certificates
- **R-INFRA-14.2**: Clean up database access keys and credentials
- **R-INFRA-14.3**: Remove database-specific authentication providers
- **R-INFRA-14.4**: Update security scanning configurations

## Quality Gates and Validation

### Pre-Commit Validation
- [ ] Terraform plan shows only expected removals
- [ ] Helm charts validate without errors
- [ ] Kubernetes manifests pass dry-run validation
- [ ] No orphaned resources remain in cloud provider

### Post-Commit Validation
- [ ] Infrastructure state is consistent
- [ ] No broken dependencies remain
- [ ] Monitoring systems updated
- [ ] Security configurations intact

## Emergency Rollback Strategy

```bash
# Rollback Terraform changes
git reset --hard deprec-terraform^
terraform state push backup-{{TARGET_DB}}-*.tfstate

# Rollback Helm changes
git reset --hard deprec-helm^
helm upgrade {{TARGET_DB}} ./charts --install

# Rollback Kubernetes changes
git reset --hard deprec-k8s^
kubectl apply -f k8s/
```

## Documentation Requirements

- [ ] Update infrastructure documentation
- [ ] Update deployment runbooks
- [ ] Update disaster recovery procedures
- [ ] Update capacity planning documents 