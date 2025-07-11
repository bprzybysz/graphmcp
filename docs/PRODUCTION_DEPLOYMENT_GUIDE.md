# Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the GraphMCP Database Decommissioning Workflow to production environments. The workflow includes enterprise-grade monitoring, health checks, alerting, and comprehensive error handling.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration Management](#configuration-management)
4. [Deployment Process](#deployment-process)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Health Checks](#health-checks)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)
10. [Performance Tuning](#performance-tuning)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ or CentOS 8+) or macOS 10.15+
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM, Recommended 8GB+
- **Storage**: Minimum 20GB free disk space
- **Network**: Internet connectivity for GitHub, Slack, and Repomix APIs

### Required Services

- **GitHub**: Personal Access Token with repository permissions
- **Slack**: Bot token with channel access permissions
- **Repomix**: Service access for repository analysis

### Dependencies

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git curl jq

# Install monitoring dependencies
pip install psutil aiohttp

# Install optional monitoring tools
pip install prometheus-client grafana-client
```

## Environment Setup

### 1. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash graphmcp
sudo usermod -aG sudo graphmcp

# Switch to application user
sudo su - graphmcp
```

### 2. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-org/graphmcp.git
cd graphmcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Directory Structure

```bash
# Create production directories
mkdir -p /opt/graphmcp/{config,logs,data,backups}
mkdir -p /var/log/graphmcp
mkdir -p /etc/graphmcp

# Set proper permissions
sudo chown -R graphmcp:graphmcp /opt/graphmcp
sudo chown -R graphmcp:graphmcp /var/log/graphmcp
sudo chown -R graphmcp:graphmcp /etc/graphmcp
```

## Configuration Management

### 1. Environment Variables

Create `/etc/graphmcp/environment`:

```bash
# Core Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Application Settings
AUTO_RELOAD=false
DEV_MODE=false
STRUCTURED_LOGGING=true
ENABLE_PROFILING=false

# Timeout and Retry Settings
MCP_TIMEOUT=120
MCP_RETRY_COUNT=3
TEST_TIMEOUT=300

# File Processing
REPOMIX_MAX_FILE_SIZE=1048576
REPOMIX_INCLUDE_PATTERNS=**/*.py,**/*.js,**/*.ts,**/*.yaml,**/*.yml,**/*.md
REPOMIX_EXCLUDE_PATTERNS=node_modules/**,dist/**,build/**,**/.git/**,**/.env

# Monitoring
ENABLE_MONITORING=true
HEALTH_CHECK_INTERVAL=300
METRICS_EXPORT_INTERVAL=3600
```

### 2. Secrets Management

Create `/etc/graphmcp/secrets.json`:

```json
{
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here",
    "SLACK_BOT_TOKEN": "your_slack_bot_token",
  "OPENAI_API_KEY": "sk-your-openai-api-key",
  "ALERT_WEBHOOK_URL": "https://your-alerting-webhook.com",
  "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
}
```

**Security:** Ensure proper file permissions:
```bash
sudo chmod 600 /etc/graphmcp/secrets.json
sudo chown graphmcp:graphmcp /etc/graphmcp/secrets.json
```

### 3. MCP Configuration

Create `/etc/graphmcp/mcp_config.json`:

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

## Deployment Process

### 1. Systemd Service Configuration

Create `/etc/systemd/system/graphmcp.service`:

```ini
[Unit]
Description=GraphMCP Database Decommissioning Workflow
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=graphmcp
Group=graphmcp
WorkingDirectory=/opt/graphmcp
ExecStart=/opt/graphmcp/venv/bin/python -m don_concrete.db_decommission
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30
Restart=always
RestartSec=10

# Environment
Environment=PYTHONPATH=/opt/graphmcp
EnvironmentFile=/etc/graphmcp/environment

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/graphmcp /var/log/graphmcp
CapabilityBoundingSet=

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### 2. Log Rotation

Create `/etc/logrotate.d/graphmcp`:

```bash
/var/log/graphmcp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 graphmcp graphmcp
    postrotate
        systemctl reload graphmcp
    endscript
}

/opt/graphmcp/logs/*.json {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 644 graphmcp graphmcp
}
```

### 3. Deployment Script

Create `/opt/graphmcp/deploy.sh`:

```bash
#!/bin/bash

set -euo pipefail

DEPLOY_DIR="/opt/graphmcp"
BACKUP_DIR="/opt/graphmcp/backups"
SERVICE_NAME="graphmcp"

echo "Starting GraphMCP deployment..."

# Create backup
BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
echo "Creating backup: $BACKUP_NAME"
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$DEPLOY_DIR" . \
    --exclude=backups --exclude=logs --exclude=.git

# Stop service
echo "Stopping service..."
sudo systemctl stop $SERVICE_NAME

# Update code
echo "Updating application code..."
git pull origin main

# Install/update dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Run health checks
echo "Running pre-deployment health checks..."
python -c "
import asyncio
from don_concrete.monitoring import get_monitoring_system

async def main():
    monitoring = get_monitoring_system()
    results = await monitoring.perform_health_check()
    
    critical_issues = [
        name for name, result in results.items() 
        if result.status.value == 'critical'
    ]
    
    if critical_issues:
        print(f'DEPLOYMENT ABORTED: Critical health issues: {critical_issues}')
        exit(1)
    
    print('Health checks passed')

asyncio.run(main())
"

# Start service
echo "Starting service..."
sudo systemctl start $SERVICE_NAME

# Verify deployment
sleep 10
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Deployment successful"
    
    # Send success notification
    python -c "
import asyncio
from don_concrete.monitoring import get_monitoring_system, AlertSeverity

async def main():
    monitoring = get_monitoring_system()
    await monitoring.send_alert(
        AlertSeverity.INFO,
        'GraphMCP Deployment Successful',
        f'GraphMCP has been successfully deployed at $(date)',
        {'deployment_id': '$BACKUP_NAME'}
    )

asyncio.run(main())
    "
else
    echo "❌ Deployment failed - rolling back..."
    
    # Rollback
    sudo systemctl stop $SERVICE_NAME
    cd "$DEPLOY_DIR"
    tar -xzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    sudo systemctl start $SERVICE_NAME
    
    echo "Rollback completed"
    exit 1
fi
```

## Monitoring and Alerting

### 1. Health Check Endpoint

The application exposes health checks via the monitoring system:

```python
# Health check script
import asyncio
from don_concrete.monitoring import get_monitoring_system

async def health_check():
    monitoring = get_monitoring_system()
    results = await monitoring.perform_health_check()
    
    for name, result in results.items():
        print(f"{name}: {result.status.value} - {result.message}")
    
    return all(r.status.value in ['healthy', 'warning'] for r in results.values())

if __name__ == "__main__":
    success = asyncio.run(health_check())
    exit(0 if success else 1)
```

### 2. Metrics Collection

Set up automated metrics export:

```bash
# Add to crontab
crontab -e

# Export metrics every hour
0 * * * * /opt/graphmcp/venv/bin/python -c "
import asyncio
from don_concrete.monitoring import get_monitoring_system
from datetime import datetime

async def export_metrics():
    monitoring = get_monitoring_system()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    await monitoring.export_metrics(f'/var/log/graphmcp/metrics_{timestamp}.json')

asyncio.run(export_metrics())
"
```

### 3. Alerting Configuration

Configure alerts for critical events:

- **System Resource Alerts**: CPU > 90%, Memory > 90%, Disk > 95%
- **Application Alerts**: Health check failures, workflow errors
- **Security Alerts**: Authentication failures, unauthorized access

## Health Checks

The system includes comprehensive health checks:

1. **System Resources**: CPU, memory, disk usage
2. **Disk Space**: Available storage and log file growth
3. **Network Connectivity**: External API availability
4. **MCP Services**: Service configuration and availability
5. **Environment Config**: Configuration file presence and validity
6. **Log Files**: Log accessibility and size monitoring

### Manual Health Check

```bash
# Run comprehensive health check
python -c "
import asyncio
from don_concrete.monitoring import get_monitoring_system

async def main():
    monitoring = get_monitoring_system()
    results = await monitoring.perform_health_check()
    
    print('Health Check Results:')
    print('=' * 50)
    
    for name, result in results.items():
        status_icon = '✅' if result.status.value == 'healthy' else '⚠️' if result.status.value == 'warning' else '❌'
        print(f'{status_icon} {name}: {result.message}')
        if result.metadata:
            for key, value in result.metadata.items():
                print(f'   {key}: {value}')
    
    dashboard = monitoring.get_monitoring_dashboard()
    print(f'\nSystem Uptime: {dashboard[\"uptime_seconds\"]:.0f} seconds')
    print(f'Workflow Success Rate: {dashboard[\"workflow_metrics\"][\"error_rate\"]:.2%}')

asyncio.run(main())
"
```

## Backup and Recovery

### 1. Automated Backups

Create `/opt/graphmcp/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/graphmcp/backups"
RETENTION_DAYS=30

# Create backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/graphmcp_backup_$TIMESTAMP.tar.gz"

echo "Creating backup: $BACKUP_FILE"

tar -czf "$BACKUP_FILE" \
    --exclude=backups \
    --exclude=venv \
    --exclude=.git \
    -C /opt/graphmcp .

# Backup configuration
tar -czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" \
    -C /etc/graphmcp .

# Clean old backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

### 2. Recovery Procedures

```bash
# Emergency recovery script
#!/bin/bash

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Stopping service..."
sudo systemctl stop graphmcp

echo "Restoring from backup: $BACKUP_FILE"
cd /opt/graphmcp
tar -xzf "$BACKUP_FILE"

echo "Restoring configuration..."
sudo tar -xzf "/opt/graphmcp/backups/config_backup_$(basename $BACKUP_FILE .tar.gz | cut -d_ -f3-).tar.gz" -C /etc/graphmcp

echo "Starting service..."
sudo systemctl start graphmcp

echo "Recovery completed"
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check service status
   sudo systemctl status graphmcp
   
   # Check logs
   journalctl -u graphmcp -f
   
   # Check configuration
   python -c "from don_concrete.parameter_service import get_parameter_service; print('Config OK')"
   ```

2. **High Resource Usage**
   ```bash
   # Check system resources
   python -c "
   import asyncio
   from don_concrete.monitoring import get_monitoring_system
   
   async def check():
       monitoring = get_monitoring_system()
       result = await monitoring.perform_health_check('system_resources')
       print(result.message)
       print(result.metadata)
   
   asyncio.run(check())
   "
   ```

3. **API Connection Issues**
   ```bash
   # Test network connectivity
   python -c "
   import asyncio
   from don_concrete.monitoring import get_monitoring_system
   
   async def check():
       monitoring = get_monitoring_system()
       result = await monitoring.perform_health_check('network_connectivity')
       print(result.message)
       print(result.metadata)
   
   asyncio.run(check())
   "
   ```

### Log Analysis

```bash
# View recent errors
grep -i error /var/log/graphmcp/*.log | tail -20

# Check workflow execution logs
ls -la /opt/graphmcp/logs/db_decommission_*.json | tail -5

# Monitor live logs
tail -f /var/log/graphmcp/application.log | jq .
```

## Security Considerations

### 1. File Permissions

```bash
# Set secure permissions
sudo chmod 755 /opt/graphmcp
sudo chmod 644 /opt/graphmcp/*.py
sudo chmod 600 /etc/graphmcp/secrets.json
sudo chmod 644 /etc/graphmcp/environment
sudo chmod 700 /opt/graphmcp/backups
```

### 2. Network Security

- Use HTTPS for all external API calls
- Implement API rate limiting
- Monitor for suspicious activity
- Regular security audits

### 3. Secrets Management

- Rotate API tokens regularly
- Use environment-specific tokens
- Monitor token usage
- Implement token expiration

## Performance Tuning

### 1. System Optimization

```bash
# Increase file descriptor limits
echo "graphmcp soft nofile 65536" >> /etc/security/limits.conf
echo "graphmcp hard nofile 65536" >> /etc/security/limits.conf

# Optimize Python settings
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=random
```

### 2. Application Tuning

```python
# Performance monitoring
import asyncio
from don_concrete.monitoring import get_monitoring_system

async def performance_check():
    monitoring = get_monitoring_system()
    metrics = monitoring.collect_system_metrics()
    
    print(f"CPU Usage: {metrics.cpu_percent}%")
    print(f"Memory Usage: {metrics.memory_percent}%")
    print(f"Network Connections: {metrics.network_connections}")
    
    if metrics.cpu_percent > 80:
        print("⚠️ High CPU usage detected")
    
    if metrics.memory_percent > 80:
        print("⚠️ High memory usage detected")

asyncio.run(performance_check())
```

### 3. Monitoring Dashboard

Access the monitoring dashboard programmatically:

```python
from don_concrete.monitoring import get_monitoring_system

monitoring = get_monitoring_system()
dashboard = monitoring.get_monitoring_dashboard()

print(f"Status: {dashboard['status']}")
print(f"Uptime: {dashboard['uptime_seconds']} seconds")
print(f"Workflow Metrics: {dashboard['workflow_metrics']}")
```

## Production Checklist

Before going live:

- [ ] All configuration files in place
- [ ] Secrets properly configured and secured
- [ ] Service starts automatically
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Alerting tested
- [ ] Backup procedures tested
- [ ] Recovery procedures documented
- [ ] Log rotation configured
- [ ] Security permissions set
- [ ] Performance baselines established
- [ ] Documentation updated

## Support and Maintenance

- **Regular Updates**: Check for updates monthly
- **Security Patches**: Apply immediately
- **Performance Monitoring**: Review metrics weekly
- **Log Analysis**: Check for errors daily
- **Backup Verification**: Test backups monthly
- **Health Checks**: Automated every 5 minutes
- **Capacity Planning**: Review quarterly

For support, contact the GraphMCP team or create an issue in the repository. 