# GraphMCP Database Decommissioning - Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the GraphMCP Database Decommissioning Workflow into your development and production environments.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Integration](#api-integration)
6. [CI/CD Integration](#cicd-integration)
7. [Monitoring Integration](#monitoring-integration)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### 5-Minute Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd graphmcp

# Install dependencies
pip install -r requirements.txt

# Configure secrets
cp secrets.json.example secrets.json
# Edit secrets.json with your API tokens

# Run demo
python demo.py --database test_db
```

### Docker Quick Start

```bash
# Build and run with Docker
docker build -t graphmcp .
docker run -e DATABASE_NAME=test_db graphmcp
```

## Prerequisites

### Required Services

| Service | Purpose | Required Permissions |
|---------|---------|---------------------|
| **GitHub** | Repository access and analysis | `repo`, `read:org` |
| **Slack** | Notifications and status updates | `chat:write`, `channels:read` |
| **OpenAI** | AI-powered pattern discovery | Standard API access |

### System Requirements

- **Python**: 3.8+
- **Memory**: 4GB+ RAM (8GB+ recommended)
- **Storage**: 10GB+ free space
- **Network**: Internet connectivity for APIs

## Installation

### Method 1: pip install (Recommended)

```bash
# Install from PyPI (when published)
pip install graphmcp-db-decommission

# Or install from source
pip install git+https://github.com/your-org/graphmcp.git
```

### Method 2: Local Development

```bash
# Clone repository
git clone https://github.com/your-org/graphmcp.git
cd graphmcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Method 3: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "concrete.db_decommission"]
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Core Configuration
LOG_LEVEL=INFO
DEV_MODE=false
STRUCTURED_LOGGING=true

# Database Configuration
TARGET_DATABASE_NAME=your_database
TARGET_REPO_URLS=https://github.com/your-org/repo1,https://github.com/your-org/repo2

# MCP Configuration
MCP_TIMEOUT=120
MCP_RETRY_COUNT=3

# File Processing
REPOMIX_MAX_FILE_SIZE=1048576
REPOMIX_INCLUDE_PATTERNS=**/*.py,**/*.js,**/*.ts,**/*.yaml,**/*.yml
REPOMIX_EXCLUDE_PATTERNS=node_modules/**,dist/**,build/**
```

### Secrets Configuration

Create `secrets.json`:

```json
{
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token",
    "SLACK_BOT_TOKEN": "your_slack_token",
  "OPENAI_API_KEY": "sk-your-openai-key"
}
```

### MCP Configuration

Create `mcp_config.json`:

```json
{
  "mcpServers": {
    "ovr_github": {
      "command": "python",
      "args": ["-m", "mcp_github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": ""
      }
    },
    "ovr_slack": {
      "command": "python",
      "args": ["-m", "mcp_slack"],
      "env": {
        "SLACK_BOT_TOKEN": ""
      }
    },
    "ovr_repomix": {
      "command": "python",
      "args": ["-m", "mcp_repomix"],
      "env": {}
    }
  }
}
```

## API Integration

### Python SDK Integration

```python
from concrete.db_decommission import create_db_decommission_workflow
from concrete.parameter_service import get_parameter_service

# Initialize workflow
workflow = create_db_decommission_workflow()

# Execute with parameters
result = await workflow.execute(
    database_name="your_database",
    target_repos=["https://github.com/your-org/repo1"],
    slack_channel="#database-ops"
)

print(f"Workflow completed: {result.success}")
print(f"Files processed: {result.files_processed}")
```

### REST API Integration

```python
import requests

# Start workflow
response = requests.post('http://localhost:8000/api/v1/decommission', json={
    "database_name": "your_database",
    "repositories": ["https://github.com/your-org/repo1"],
    "slack_channel": "#database-ops"
})

workflow_id = response.json()['workflow_id']

# Check status
status = requests.get(f'http://localhost:8000/api/v1/workflow/{workflow_id}/status')
print(status.json())
```

### Webhook Integration

```python
from flask import Flask, request
from concrete.db_decommission import create_db_decommission_workflow

app = Flask(__name__)

@app.route('/webhook/decommission', methods=['POST'])
def handle_decommission():
    data = request.json
    
    workflow = create_db_decommission_workflow()
    result = await workflow.execute(
        database_name=data['database_name'],
        target_repos=data['repositories']
    )
    
    return {"status": "completed", "result": result.to_dict()}
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/db-decommission.yml`:

```yaml
name: Database Decommissioning

on:
  workflow_dispatch:
    inputs:
      database_name:
        description: 'Database to decommission'
        required: true
      repositories:
        description: 'Repositories to process (comma-separated)'
        required: true

jobs:
  decommission:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Configure secrets
      run: |
        echo '{
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
          "SLACK_BOT_TOKEN": "${{ secrets.SLACK_BOT_TOKEN }}",
          "OPENAI_API_KEY": "${{ secrets.OPENAI_API_KEY }}"
        }' > secrets.json
    
    - name: Run decommissioning workflow
      run: |
        python demo.py --database "${{ github.event.inputs.database_name }}"
      env:
        TARGET_REPO_URLS: ${{ github.event.inputs.repositories }}
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: decommission-results
        path: logs/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    parameters {
        string(name: 'DATABASE_NAME', description: 'Database to decommission')
        text(name: 'REPOSITORIES', description: 'Repositories to process')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                
                withCredentials([
                    string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN'),
                    string(credentialsId: 'slack-token', variable: 'SLACK_TOKEN'),
                    string(credentialsId: 'openai-key', variable: 'OPENAI_KEY')
                ]) {
                    sh '''
                        echo "{
                            \\"GITHUB_PERSONAL_ACCESS_TOKEN\\": \\"$GITHUB_TOKEN\\",
                            \\"SLACK_BOT_TOKEN\\": \\"$SLACK_TOKEN\\",
                            \\"OPENAI_API_KEY\\": \\"$OPENAI_KEY\\"
                        }" > secrets.json
                    '''
                }
            }
        }
        
        stage('Execute Decommissioning') {
            steps {
                sh "python demo.py --database ${params.DATABASE_NAME}"
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'logs/**/*', fingerprint: true
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'logs',
                reportFiles: '*.json',
                reportName: 'Decommission Report'
            ])
        }
    }
}
```

### Azure DevOps

```yaml
trigger: none

parameters:
- name: databaseName
  displayName: Database Name
  type: string
- name: repositories
  displayName: Repositories
  type: string

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.9'

- script: |
    pip install -r requirements.txt
  displayName: 'Install dependencies'

- task: AzureKeyVault@2
  inputs:
    azureSubscription: 'your-subscription'
    KeyVaultName: 'your-keyvault'
    SecretsFilter: 'github-token,slack-token,openai-key'
    RunAsPreJob: true

- script: |
    echo '{
      "GITHUB_PERSONAL_ACCESS_TOKEN": "$(github-token)",
      "SLACK_BOT_TOKEN": "$(slack-token)",
      "OPENAI_API_KEY": "$(openai-key)"
    }' > secrets.json
  displayName: 'Configure secrets'

- script: |
    python demo.py --database "${{ parameters.databaseName }}"
  displayName: 'Run decommissioning'
  env:
    TARGET_REPO_URLS: ${{ parameters.repositories }}

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: 'logs'
    artifactName: 'decommission-results'
```

## Monitoring Integration

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
WORKFLOW_RUNS = Counter('db_decommission_runs_total', 'Total workflow runs')
WORKFLOW_DURATION = Histogram('db_decommission_duration_seconds', 'Workflow duration')
ACTIVE_WORKFLOWS = Gauge('db_decommission_active_workflows', 'Active workflows')

# In your workflow code
@WORKFLOW_DURATION.time()
def run_workflow():
    WORKFLOW_RUNS.inc()
    ACTIVE_WORKFLOWS.inc()
    try:
        # Your workflow logic
        pass
    finally:
        ACTIVE_WORKFLOWS.dec()

# Start metrics server
start_http_server(8000)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Database Decommissioning",
    "panels": [
      {
        "title": "Workflow Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(db_decommission_runs_total[5m])"
          }
        ]
      },
      {
        "title": "Average Duration",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(db_decommission_duration_seconds)"
          }
        ]
      }
    ]
  }
}
```

### Custom Health Checks

```python
from concrete.monitoring import get_monitoring_system

# Add custom health check
monitoring = get_monitoring_system()

@monitoring.add_health_check("database_connectivity")
async def check_database():
    try:
        # Your database check logic
        return HealthCheckResult.healthy("Database accessible")
    except Exception as e:
        return HealthCheckResult.critical(f"Database error: {e}")
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

```bash
# Problem: GitHub authentication failed
# Solution: Check token permissions
curl -H "Authorization: token your_github_token" https://api.github.com/user

# Problem: Slack authentication failed  
# Solution: Verify bot token and permissions
curl -X POST -H 'Authorization: Bearer your_slack_token' \
  -H 'Content-type: application/json' \
  --data '{"channel":"#test","text":"Test"}' \
  https://slack.com/api/chat.postMessage
```

#### 2. Memory Issues

```python
# Monitor memory usage
from concrete.monitoring import get_monitoring_system

monitoring = get_monitoring_system()
health = await monitoring.perform_health_check("memory_usage")
print(f"Memory status: {health.status}")
```

#### 3. Network Timeouts

```python
# Adjust timeout settings
import os
os.environ['MCP_TIMEOUT'] = '300'  # 5 minutes
os.environ['MCP_RETRY_COUNT'] = '5'
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export MCP_DEBUG=true

# Run with verbose output
python demo.py --database test_db --verbose
```

### Log Analysis

```bash
# Check workflow logs
tail -f logs/db_decommission_*.json | jq .

# Find errors
grep -i error logs/*.log

# Monitor system resources
python -c "
from concrete.monitoring import get_monitoring_system
import asyncio

async def main():
    monitoring = get_monitoring_system()
    health = await monitoring.perform_health_check()
    for name, result in health.items():
        print(f'{name}: {result.status.value} - {result.message}')

asyncio.run(main())
"
```

## Support

### Documentation

- [API Reference](API_REFERENCE.md)
- [Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Contributing Guide](CONTRIBUTING.md)

### Community

- GitHub Issues: [Report bugs and feature requests](https://github.com/your-org/graphmcp/issues)
- Slack Channel: `#graphmcp-support`
- Email: graphmcp-support@your-org.com

### Professional Support

For enterprise support, training, and custom integrations, contact our professional services team. 