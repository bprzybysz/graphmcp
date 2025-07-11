# Database Reference Quick Search Patterns

## Overview
Comprehensive search patterns for detecting database references across different source types during repository scanning.

## Infrastructure Source Type

### Terraform Files (*.tf, *.tfvars)
```regex
# Resource blocks
resource\s+"azurerm_postgresql_flexible_server"\s+"{{TARGET_DB}}"
resource\s+"aws_rds_instance"\s+"{{TARGET_DB}}"
resource\s+"google_sql_database_instance"\s+"{{TARGET_DB}}"

# Variables and locals
variable\s+"{{TARGET_DB}}_"
local\s+{[^}]*{{TARGET_DB}}[^}]*}

# Data sources
data\s+"azurerm_postgresql_flexible_server"\s+"{{TARGET_DB}}"
```

### Helm Charts (values*.yaml, Chart.yaml, templates/*)
```regex
# Values files
{{TARGET_DB}}:
  name:\s*["']{{TARGET_DB}}["']
  database:\s*["']{{TARGET_DB}}["']

# Chart dependencies
- name:\s*{{TARGET_DB}}
  repository:

# Template references
{{\.Values\.{{TARGET_DB}}}}
{{\.Values\.database\.{{TARGET_DB}}}}
```

### Kubernetes Manifests (*.yaml, *.yml)
```regex
# ConfigMaps and Secrets
name:\s*{{TARGET_DB}}-config
name:\s*{{TARGET_DB}}-secret

# Database references
database:\s*["']{{TARGET_DB}}["']
POSTGRES_DB:\s*["']{{TARGET_DB}}["']
DATABASE_NAME:\s*["']{{TARGET_DB}}["']
```

## Configuration Source Type

### YAML/JSON Configuration Files
```regex
# Database configuration blocks
database:[\s\S]*?{{TARGET_DB}}
databases:[\s\S]*?{{TARGET_DB}}

# Connection strings
"{{TARGET_DB}}_CONNECTION"
"{{TARGET_DB}}_DATABASE_URL"
{{TARGET_DB}}_HOST
{{TARGET_DB}}_PORT
```

### Environment Files (.env, .env.*, docker-compose.yml)
```regex
# Environment variables
{{TARGET_DB}}_DATABASE_URL=
{{TARGET_DB}}_HOST=
{{TARGET_DB}}_USER=
{{TARGET_DB}}_PASSWORD=
POSTGRES_DB={{TARGET_DB}}

# Docker Compose services
{{TARGET_DB}}-db:
{{TARGET_DB}}_database:
```

### CI/CD Configuration (.github/workflows/*, .gitlab-ci.yml, Jenkinsfile)
```regex
# Pipeline variables
{{TARGET_DB}}_DATABASE
DATABASE_NAME.*{{TARGET_DB}}
{{TARGET_DB}}_MIGRATION

# Service definitions
services:[\s\S]*?{{TARGET_DB}}
```

## SQL Source Type

### SQL Dump Files (*.sql, *.dump, *.bak)
```regex
# Database creation
CREATE DATABASE\s+{{TARGET_DB}}
USE\s+{{TARGET_DB}}
\\connect\s+{{TARGET_DB}}

# Table creation with database prefix
CREATE TABLE\s+{{TARGET_DB}}\.
INSERT INTO\s+{{TARGET_DB}}\.

# Comments and documentation
--.*{{TARGET_DB}}
/\*.*{{TARGET_DB}}.*\*/
```

### Migration Files (*migration*, *migrate*, schema/*)
```regex
# Migration file names
.*{{TARGET_DB}}.*migration
.*migrate.*{{TARGET_DB}}

# Migration content
ALTER DATABASE\s+{{TARGET_DB}}
DROP DATABASE\s+{{TARGET_DB}}
```

## Python Source Type

### Python Application Files (*.py)
```regex
# Database connection configurations
DATABASE_CONFIG.*{{TARGET_DB}}
DATABASES.*{{TARGET_DB}}
{{TARGET_DB}}_CONFIG

# ORM Models and connections
class\s+{{TARGET_DB}}.*Model
{{TARGET_DB}}_connection
{{TARGET_DB}}_engine

# Import statements
from\s+.*{{TARGET_DB}}
import\s+.*{{TARGET_DB}}
```

### Python Configuration (settings.py, config.py, *.ini)
```regex
# Django/Flask database settings
DATABASES\s*=\s*{[\s\S]*?{{TARGET_DB}}
DATABASE_URL.*{{TARGET_DB}}

# SQLAlchemy connections
{{TARGET_DB}}_DATABASE_URI
engine.*{{TARGET_DB}}
```

### Requirements Files (requirements.txt, setup.py, pyproject.toml)
```regex
# Database-specific packages
{{TARGET_DB}}-connector
py{{TARGET_DB}}
{{TARGET_DB}}db
```

## Documentation Source Type

### Markdown Files (*.md, *.rst)
```regex
# Headers and titles
#.*{{TARGET_DB}}
##.*{{TARGET_DB}}

# Code blocks and examples
```.*{{TARGET_DB}}
`{{TARGET_DB}}`

# Tables and lists
\|.*{{TARGET_DB}}.*\|
\*.*{{TARGET_DB}}
-.*{{TARGET_DB}}
```

### Configuration Documentation
```regex
# Configuration examples
{{TARGET_DB}}:
  host:
  port:

# Connection examples
postgresql://.*{{TARGET_DB}}
jdbc:postgresql://.*{{TARGET_DB}}
```

## General Cross-Type Patterns

### Case-Insensitive Variants
```regex
# Common variations
{{TARGET_DB}}
{{target_db}}
{{TARGET-DB}}
{{Target_Db}}
{{TARGETDB}}
{{targetdb}}
```

### File Path Patterns
```regex
# Directories and paths
/{{TARGET_DB}}/
/{{TARGET_DB}}_
_{{TARGET_DB}}/
{{TARGET_DB}}-
```

### URL and Connection String Patterns  
```regex
# URLs and connection strings
://.*{{TARGET_DB}}
@.*{{TARGET_DB}}
{{TARGET_DB}}\.example\.com
{{TARGET_DB}}-.*\.amazonaws\.com
```

## Usage Instructions

1. **Replace `{{TARGET_DB}}`** with the actual database name during scanning
2. **Apply source-type filters** based on file extensions and paths
3. **Use case-insensitive matching** for broader coverage
4. **Combine patterns** for comprehensive detection
5. **Validate matches** to reduce false positives

## Pattern Priority

1. **HIGH**: Exact database names in resource definitions
2. **MEDIUM**: Database names in configuration values
3. **LOW**: Database names in comments and documentation

## Examples

For database name `periodic_table`:
- Infrastructure: `resource "azurerm_postgresql_flexible_server" "periodic_table"`
- Configuration: `PERIODIC_TABLE_DATABASE_URL=postgres://...`
- SQL: `CREATE DATABASE periodic_table;`
- Python: `class PeriodicTableModel(Model):`
