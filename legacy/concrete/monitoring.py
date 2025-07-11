"""
Production Monitoring System for Database Decommissioning Workflow.

This module provides comprehensive monitoring, health checks, metrics collection,
and alerting capabilities for production deployment of the database decommissioning workflow.
"""

import asyncio
import time
import json
import psutil
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass 
class SystemMetrics:
    """System performance metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int
    process_count: int
    uptime_seconds: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class WorkflowMetrics:
    """Workflow-specific performance metrics."""
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    average_duration_seconds: float
    repositories_processed: int
    files_processed: int
    error_rate: float
    last_execution: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        if self.last_execution:
            result['last_execution'] = self.last_execution.isoformat()
        return result

class MonitoringSystem:
    """Comprehensive monitoring system for production deployment."""
    
    def __init__(self, 
                 config: Dict[str, Any] = None,
                 alert_webhook_url: str = None,
                 slack_webhook_url: str = None):
        self.config = config or {}
        self.alert_webhook_url = alert_webhook_url
        self.slack_webhook_url = slack_webhook_url
        self.start_time = time.time()
        self.health_checks = {}
        self.metrics_history = []
        self.alert_history = []
        self.workflow_metrics = WorkflowMetrics(
            total_workflows=0,
            successful_workflows=0,
            failed_workflows=0,
            average_duration_seconds=0.0,
            repositories_processed=0,
            files_processed=0,
            error_rate=0.0
        )
        
        # Initialize health checks
        self._register_health_checks()
        
    def _register_health_checks(self):
        """Register all health check functions."""
        self.health_checks = {
            "system_resources": self._check_system_resources,
            "disk_space": self._check_disk_space,
            "memory_usage": self._check_memory_usage,
            "network_connectivity": self._check_network_connectivity,
            "mcp_services": self._check_mcp_services,
            "environment_config": self._check_environment_config,
            "log_files": self._check_log_files
        }

    async def perform_health_check(self, check_name: str = None) -> Union[HealthCheckResult, Dict[str, HealthCheckResult]]:
        """
        Perform health check(s).
        
        Args:
            check_name: Specific check to run, or None for all checks
            
        Returns:
            Single result if check_name specified, otherwise dict of all results
        """
        if check_name:
            if check_name not in self.health_checks:
                return HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Unknown health check: {check_name}",
                    duration_ms=0.0,
                    timestamp=datetime.utcnow()
                )
            
            start_time = time.time()
            try:
                result = await self.health_checks[check_name]()
                duration_ms = (time.time() - start_time) * 1000
                result.duration_ms = duration_ms
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Health check {check_name} failed: {e}")
                return HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check error: {str(e)}",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow()
                )
        else:
            # Run all health checks
            results = {}
            for name in self.health_checks:
                results[name] = await self.perform_health_check(name)
            return results

    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        status = HealthStatus.HEALTHY
        message = f"CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%"
        
        if cpu_percent > 90 or memory.percent > 90:
            status = HealthStatus.CRITICAL
            message += " - HIGH RESOURCE USAGE"
        elif cpu_percent > 75 or memory.percent > 75:
            status = HealthStatus.WARNING
            message += " - Elevated resource usage"
            
        return HealthCheckResult(
            name="system_resources",
            status=status,
            message=message,
            duration_ms=0.0,
            timestamp=datetime.utcnow(),
            metadata={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3)
            }
        )

    async def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        available_gb = disk.free / (1024**3)
        
        status = HealthStatus.HEALTHY
        message = f"Disk usage: {disk_percent:.1f}%, Available: {available_gb:.1f}GB"
        
        if disk_percent > 95:
            status = HealthStatus.CRITICAL
            message += " - CRITICAL DISK SPACE"
        elif disk_percent > 85:
            status = HealthStatus.WARNING
            message += " - Low disk space"
            
        return HealthCheckResult(
            name="disk_space",
            status=status,
            message=message,
            duration_ms=0.0,
            timestamp=datetime.utcnow(),
            metadata={
                "disk_percent": disk_percent,
                "available_gb": available_gb,
                "total_gb": disk.total / (1024**3)
            }
        )

    async def _check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage details."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        status = HealthStatus.HEALTHY
        message = f"Memory: {memory.percent:.1f}%, Swap: {swap.percent:.1f}%"
        
        if memory.percent > 95 or (swap.total > 0 and swap.percent > 50):
            status = HealthStatus.CRITICAL
            message += " - MEMORY PRESSURE"
        elif memory.percent > 85 or (swap.total > 0 and swap.percent > 25):
            status = HealthStatus.WARNING
            message += " - High memory usage"
        
        # Build metadata with cross-platform compatibility
        metadata = {
            "memory_percent": memory.percent,
            "swap_percent": swap.percent,
            "available_gb": memory.available / (1024**3),
            "total_gb": memory.total / (1024**3)
        }
        
        # Add platform-specific memory details if available
        try:
            if hasattr(memory, 'buffers'):
                metadata["buffers_gb"] = memory.buffers / (1024**3)
            if hasattr(memory, 'cached'):
                metadata["cached_gb"] = memory.cached / (1024**3)
            if hasattr(memory, 'shared'):
                metadata["shared_gb"] = memory.shared / (1024**3)
        except AttributeError:
            # macOS doesn't have all Linux memory fields, which is fine
            pass
            
        return HealthCheckResult(
            name="memory_usage",
            status=status,
            message=message,
            duration_ms=0.0,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )

    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity to external services."""
        test_urls = [
            "https://api.github.com",
            "https://hooks.slack.com",
            "https://httpbin.org/status/200"
        ]
        
        successful_connections = 0
        connection_details = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for url in test_urls:
                try:
                    start_time = time.time()
                    async with session.get(url) as response:
                        duration = (time.time() - start_time) * 1000
                        if response.status < 400:
                            successful_connections += 1
                            connection_details.append({
                                "url": url,
                                "status": "success",
                                "response_code": response.status,
                                "duration_ms": duration
                            })
                        else:
                            connection_details.append({
                                "url": url,
                                "status": "error",
                                "response_code": response.status,
                                "duration_ms": duration
                            })
                except Exception as e:
                    connection_details.append({
                        "url": url,
                        "status": "failed",
                        "error": str(e),
                        "duration_ms": 0
                    })
        
        success_rate = successful_connections / len(test_urls)
        
        if success_rate == 1.0:
            status = HealthStatus.HEALTHY
            message = "All network connectivity tests passed"
        elif success_rate >= 0.5:
            status = HealthStatus.WARNING
            message = f"Partial network connectivity: {successful_connections}/{len(test_urls)} passed"
        else:
            status = HealthStatus.CRITICAL
            message = f"Network connectivity issues: {successful_connections}/{len(test_urls)} passed"
            
        return HealthCheckResult(
            name="network_connectivity",
            status=status,
            message=message,
            duration_ms=0.0,
            timestamp=datetime.utcnow(),
            metadata={
                "success_rate": success_rate,
                "connection_details": connection_details
            }
        )

    async def _check_mcp_services(self) -> HealthCheckResult:
        """Check MCP service configurations and availability."""
        try:
            from concrete.parameter_service import get_parameter_service
            param_service = get_parameter_service()
            
            # Check required configuration
            required_params = [
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "SLACK_BOT_TOKEN", 
                "MCP_CONFIG_PATH"
            ]
            
            missing_params = []
            for param in required_params:
                if not param_service.get_parameter(param):
                    missing_params.append(param)
            
            if missing_params:
                status = HealthStatus.CRITICAL
                message = f"Missing required parameters: {', '.join(missing_params)}"
            else:
                status = HealthStatus.HEALTHY
                message = "All MCP service parameters configured"
                
            return HealthCheckResult(
                name="mcp_services",
                status=status,
                message=message,
                duration_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "missing_parameters": missing_params,
                    "total_parameters": len(param_service.get_all_parameters())
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="mcp_services",
                status=HealthStatus.CRITICAL,
                message=f"MCP service check failed: {str(e)}",
                duration_ms=0.0,
                timestamp=datetime.utcnow()
            )

    async def _check_environment_config(self) -> HealthCheckResult:
        """Check environment configuration and secrets."""
        config_issues = []
        
        # Check for .env file
        env_file = Path(".env")
        if not env_file.exists():
            config_issues.append(".env file not found")
        
        # Check for secrets.json
        secrets_file = Path("secrets.json")
        if not secrets_file.exists():
            config_issues.append("secrets.json file not found")
        
        # Check MCP config
        mcp_config = Path("mcp_config.json")
        if not mcp_config.exists():
            config_issues.append("mcp_config.json file not found")
            
        if config_issues:
            status = HealthStatus.WARNING
            message = f"Configuration issues: {', '.join(config_issues)}"
        else:
            status = HealthStatus.HEALTHY
            message = "All configuration files present"
            
        return HealthCheckResult(
            name="environment_config",
            status=status,
            message=message,
            duration_ms=0.0,
            timestamp=datetime.utcnow(),
            metadata={"issues": config_issues}
        )

    async def _check_log_files(self) -> HealthCheckResult:
        """Check log file accessibility and disk usage."""
        log_dir = Path("logs")
        
        if not log_dir.exists():
            return HealthCheckResult(
                name="log_files",
                status=HealthStatus.WARNING,
                message="Logs directory does not exist",
                duration_ms=0.0,
                timestamp=datetime.utcnow()
            )
        
        try:
            log_files = list(log_dir.glob("*.json"))
            total_size_mb = sum(f.stat().st_size for f in log_files) / (1024**2)
            
            status = HealthStatus.HEALTHY
            message = f"Log files: {len(log_files)}, Total size: {total_size_mb:.1f}MB"
            
            if total_size_mb > 1000:  # 1GB
                status = HealthStatus.WARNING
                message += " - Large log files detected"
                
            return HealthCheckResult(
                name="log_files",
                status=status,
                message=message,
                duration_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "log_file_count": len(log_files),
                    "total_size_mb": total_size_mb
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="log_files",
                status=HealthStatus.CRITICAL,
                message=f"Cannot access log files: {str(e)}",
                duration_ms=0.0,
                timestamp=datetime.utcnow()
            )

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network_connections = len(psutil.net_connections())
        process_count = len(psutil.pids())
        uptime_seconds = time.time() - self.start_time
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100,
            network_connections=network_connections,
            process_count=process_count,
            uptime_seconds=uptime_seconds,
            timestamp=datetime.utcnow()
        )

    def update_workflow_metrics(self, 
                               workflow_result: Dict[str, Any],
                               duration_seconds: float,
                               repositories_processed: int = 0,
                               files_processed: int = 0):
        """Update workflow execution metrics."""
        self.workflow_metrics.total_workflows += 1
        
        if workflow_result.get("success", False):
            self.workflow_metrics.successful_workflows += 1
        else:
            self.workflow_metrics.failed_workflows += 1
            
        # Update averages
        total_duration = (self.workflow_metrics.average_duration_seconds * 
                         (self.workflow_metrics.total_workflows - 1) + duration_seconds)
        self.workflow_metrics.average_duration_seconds = total_duration / self.workflow_metrics.total_workflows
        
        self.workflow_metrics.repositories_processed += repositories_processed
        self.workflow_metrics.files_processed += files_processed
        self.workflow_metrics.error_rate = (
            self.workflow_metrics.failed_workflows / self.workflow_metrics.total_workflows
        )
        self.workflow_metrics.last_execution = datetime.utcnow()

    async def send_alert(self, 
                        severity: AlertSeverity,
                        title: str,
                        message: str,
                        metadata: Dict[str, Any] = None):
        """Send alert via configured channels."""
        alert = {
            "severity": severity.value,
            "title": title,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.alert_history.append(alert)
        
        # Send to webhook if configured
        if self.alert_webhook_url:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(self.alert_webhook_url, json=alert)
                logger.info(f"Alert sent to webhook: {title}")
            except Exception as e:
                logger.error(f"Failed to send alert to webhook: {e}")
        
        # Send to Slack if configured  
        if self.slack_webhook_url:
            try:
                slack_message = {
                    "text": f"🚨 {title}",
                    "attachments": [{
                        "color": "danger" if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY] else "warning",
                        "fields": [
                            {"title": "Severity", "value": severity.value.upper(), "short": True},
                            {"title": "Time", "value": alert["timestamp"], "short": True},
                            {"title": "Message", "value": message, "short": False}
                        ]
                    }]
                }
                
                async with aiohttp.ClientSession() as session:
                    await session.post(self.slack_webhook_url, json=slack_message)
                logger.info(f"Alert sent to Slack: {title}")
            except Exception as e:
                logger.error(f"Failed to send alert to Slack: {e}")

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        system_metrics = self.collect_system_metrics()
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": system_metrics.uptime_seconds,
            "system_metrics": system_metrics.to_dict(),
            "workflow_metrics": self.workflow_metrics.to_dict(),
            "recent_alerts": self.alert_history[-10:],  # Last 10 alerts
            "health_checks_available": list(self.health_checks.keys())
        }

    async def export_metrics(self, output_path: str):
        """Export all monitoring data to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform all health checks
            health_results = await self.perform_health_check()
            
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "monitoring_dashboard": self.get_monitoring_dashboard(),
                "health_check_results": {
                    name: result.to_dict() if hasattr(result, 'to_dict') else result
                    for name, result in health_results.items()
                },
                "alert_history": self.alert_history,
                "system_info": {
                    "platform": psutil.LINUX if hasattr(psutil, 'LINUX') else "unknown",
                    "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
                    "process_id": psutil.os.getpid()
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Monitoring data exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export monitoring data: {e}")
            raise

# Global monitoring instance
_monitoring_system = None

def get_monitoring_system(config: Dict[str, Any] = None) -> MonitoringSystem:
    """Get or create global monitoring system instance."""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem(config)
    return _monitoring_system

def reset_monitoring_system():
    """Reset global monitoring system (for testing)."""
    global _monitoring_system
    _monitoring_system = None 