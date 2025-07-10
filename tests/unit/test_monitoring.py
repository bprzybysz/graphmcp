"""
Unit tests for the Monitoring System

Tests the monitoring system functionality including:
- Health checks
- Metrics collection
- Alert system
- Monitoring dashboard
- Metrics export
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from concrete.monitoring import (
    get_monitoring_system,
    reset_monitoring_system,
    MonitoringSystem,
    SystemMetrics,
    WorkflowMetrics,
    HealthStatus,
    AlertSeverity,
    HealthCheckResult
)

class DiskMetrics:
    """Custom class for disk metrics that properly implements division."""
    def __init__(self, total, used, free):
        self.total = total
        self.used = used
        self.free = free
        
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return float(self.used) / float(other)
        return 0.0
        
    def __float__(self):
        return float(self.used)

@pytest.fixture
def monitoring_system():
    """Create a fresh monitoring system for each test."""
    reset_monitoring_system()
    system = get_monitoring_system()
    yield system
    reset_monitoring_system()

@pytest.fixture
def mock_psutil():
    """Mock psutil functions."""
    with patch('concrete.monitoring.psutil') as mock:
        # CPU
        mock.cpu_percent.return_value = 45.2
        
        # Memory
        mock_memory = MagicMock()
        mock_memory.percent = 62.5
        mock_memory.available = 8589934592  # 8GB
        mock_memory.total = 17179869184  # 16GB
        mock.virtual_memory.return_value = mock_memory
        
        # Disk
        mock_disk = DiskMetrics(
            total=1000000000000,  # 1TB
            used=600000000000,    # 600GB
            free=400000000000     # 400GB
        )
        mock.disk_usage.return_value = mock_disk
        
        # Network
        mock.net_connections.return_value = [1, 2, 3]  # 3 connections
        
        # Process
        mock.pids.return_value = [1, 2, 3, 4]  # 4 processes
        
        # System info
        mock.LINUX = "Linux"
        mock.sys = MagicMock()
        mock.sys.version_info = MagicMock()
        mock.sys.version_info.major = 3
        mock.sys.version_info.minor = 11
        mock.os = MagicMock()
        mock.os.getpid.return_value = 12345
        
        yield mock

class TestSystemMetrics:
    """Test cases for system metrics collection."""
    
    def test_system_metrics_creation(self):
        """Test creating SystemMetrics object."""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            network_connections=5,
            process_count=10,
            uptime_seconds=3600.0,
            timestamp=datetime.utcnow()
        )
        
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_percent == 70.0
        assert metrics.network_connections == 5
        assert metrics.process_count == 10
        assert metrics.uptime_seconds == 3600.0
        
    def test_system_metrics_to_dict(self):
        """Test converting SystemMetrics to dictionary."""
        timestamp = datetime.utcnow()
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            network_connections=5,
            process_count=10,
            uptime_seconds=3600.0,
            timestamp=timestamp
        )
        
        metrics_dict = metrics.to_dict()
        assert metrics_dict['cpu_percent'] == 50.0
        assert metrics_dict['memory_percent'] == 60.0
        assert metrics_dict['disk_percent'] == 70.0
        assert metrics_dict['network_connections'] == 5
        assert metrics_dict['process_count'] == 10
        assert metrics_dict['uptime_seconds'] == 3600.0
        assert metrics_dict['timestamp'] == timestamp.isoformat()

class TestWorkflowMetrics:
    """Test cases for workflow metrics."""
    
    def test_workflow_metrics_creation(self):
        """Test creating WorkflowMetrics object."""
        metrics = WorkflowMetrics(
            total_workflows=10,
            successful_workflows=8,
            failed_workflows=2,
            average_duration_seconds=120.0,
            repositories_processed=5,
            files_processed=100,
            error_rate=0.2
        )
        
        assert metrics.total_workflows == 10
        assert metrics.successful_workflows == 8
        assert metrics.failed_workflows == 2
        assert metrics.average_duration_seconds == 120.0
        assert metrics.repositories_processed == 5
        assert metrics.files_processed == 100
        assert metrics.error_rate == 0.2
        
    def test_workflow_metrics_to_dict(self):
        """Test converting WorkflowMetrics to dictionary."""
        last_execution = datetime.utcnow()
        metrics = WorkflowMetrics(
            total_workflows=10,
            successful_workflows=8,
            failed_workflows=2,
            average_duration_seconds=120.0,
            repositories_processed=5,
            files_processed=100,
            error_rate=0.2,
            last_execution=last_execution
        )
        
        metrics_dict = metrics.to_dict()
        assert metrics_dict['total_workflows'] == 10
        assert metrics_dict['successful_workflows'] == 8
        assert metrics_dict['failed_workflows'] == 2
        assert metrics_dict['average_duration_seconds'] == 120.0
        assert metrics_dict['repositories_processed'] == 5
        assert metrics_dict['files_processed'] == 100
        assert metrics_dict['error_rate'] == 0.2
        assert metrics_dict['last_execution'] == last_execution.isoformat()

class TestHealthChecks:
    """Test cases for health check functionality."""
    
    @pytest.mark.asyncio
    async def test_system_resources_check(self, monitoring_system, mock_psutil):
        """Test system resources health check."""
        result = await monitoring_system.perform_health_check("system_resources")
        
        assert isinstance(result, HealthCheckResult)
        assert result.name == "system_resources"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert result.duration_ms >= 0
        
    @pytest.mark.asyncio
    async def test_memory_usage_check(self, monitoring_system, mock_psutil):
        """Test memory usage health check."""
        result = await monitoring_system.perform_health_check("memory_usage")
        
        assert isinstance(result, HealthCheckResult)
        assert result.name == "memory_usage"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert result.duration_ms >= 0
        
    @pytest.mark.asyncio
    async def test_disk_space_check(self, monitoring_system, mock_psutil):
        """Test disk space health check."""
        result = await monitoring_system.perform_health_check("disk_space")
        
        assert isinstance(result, HealthCheckResult)
        assert result.name == "disk_space"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert result.duration_ms >= 0
        
    @pytest.mark.asyncio
    async def test_network_connectivity_check(self, monitoring_system):
        """Test network connectivity health check."""
        result = await monitoring_system.perform_health_check("network_connectivity")
        
        assert isinstance(result, HealthCheckResult)
        assert result.name == "network_connectivity"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert result.duration_ms >= 0
        
    @pytest.mark.asyncio
    async def test_perform_health_check_error_handling(self, monitoring_system, mock_psutil):
        """Test error handling during a specific health check."""
        # Make _check_system_resources raise an exception
        mock_psutil.cpu_percent.side_effect = Exception("CPU check failed")
        
        result = await monitoring_system.perform_health_check("system_resources")
        
        assert isinstance(result, HealthCheckResult)
        assert result.name == "system_resources"
        assert result.status == HealthStatus.CRITICAL
        assert "Health check error: CPU check failed" in result.message
        assert result.duration_ms >= 0
        assert result.timestamp is not None
        
    @pytest.mark.asyncio
    async def test_all_health_checks(self, monitoring_system):
        """Test running all health checks."""
        results = await monitoring_system.perform_health_check()
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        for name, result in results.items():
            assert isinstance(result, HealthCheckResult)
            assert result.name == name
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
            assert result.duration_ms >= 0

class TestMetricsCollection:
    """Test cases for metrics collection."""
    
    def test_collect_system_metrics(self, monitoring_system, mock_psutil):
        """Test collecting system metrics."""
        metrics = monitoring_system.collect_system_metrics()
        
        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent == 45.2
        assert metrics.memory_percent == 62.5
        assert metrics.disk_percent == 60.0  # (600/1000) * 100
        assert metrics.network_connections == 3
        assert metrics.process_count == 4
        assert metrics.uptime_seconds > 0
        assert isinstance(metrics.timestamp, datetime)
        
    def test_update_workflow_metrics(self, monitoring_system):
        """Test updating workflow metrics."""
        monitoring_system.update_workflow_metrics(
            workflow_result={"success": True},
            duration_seconds=60.0,
            repositories_processed=2,
            files_processed=50
        )
        
        metrics = monitoring_system.workflow_metrics
        assert metrics.total_workflows == 1
        assert metrics.successful_workflows == 1
        assert metrics.failed_workflows == 0
        assert metrics.average_duration_seconds == 60.0
        assert metrics.repositories_processed == 2
        assert metrics.files_processed == 50
        assert metrics.error_rate == 0.0
        assert isinstance(metrics.last_execution, datetime)

class TestAlertSystem:
    """Test cases for alert system."""
    
    @pytest.mark.asyncio
    async def test_send_alert_webhook(self, monitoring_system):
        """Test sending alert via webhook."""
        monitoring_system.alert_webhook_url = "http://test.webhook"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            
            await monitoring_system.send_alert(
                severity=AlertSeverity.WARNING,
                title="Test Alert",
                message="This is a test alert",
                metadata={"test": True}
            )
            
            assert len(monitoring_system.alert_history) == 1
            alert = monitoring_system.alert_history[0]
            assert alert["severity"] == AlertSeverity.WARNING.value
            assert alert["title"] == "Test Alert"
            assert alert["message"] == "This is a test alert"
            assert alert["metadata"] == {"test": True}
            
            mock_post.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_send_alert_slack(self, monitoring_system):
        """Test sending alert via Slack."""
        monitoring_system.slack_webhook_url = "http://slack.webhook"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            
            await monitoring_system.send_alert(
                severity=AlertSeverity.CRITICAL,
                title="Critical Alert",
                message="This is a critical alert",
                metadata={"critical": True}
            )
            
            assert len(monitoring_system.alert_history) == 1
            alert = monitoring_system.alert_history[0]
            assert alert["severity"] == AlertSeverity.CRITICAL.value
            assert alert["title"] == "Critical Alert"
            assert alert["message"] == "This is a critical alert"
            assert alert["metadata"] == {"critical": True}
            
            mock_post.assert_called_once()

class TestMonitoringDashboard:
    """Test cases for monitoring dashboard."""
    
    def test_get_monitoring_dashboard(self, monitoring_system, mock_psutil):
        """Test getting monitoring dashboard data."""
        dashboard = monitoring_system.get_monitoring_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard["status"] == "operational"
        assert isinstance(dashboard["timestamp"], str)
        assert dashboard["uptime_seconds"] > 0
        assert isinstance(dashboard["system_metrics"], dict)
        assert isinstance(dashboard["workflow_metrics"], dict)
        assert isinstance(dashboard["recent_alerts"], list)
        assert isinstance(dashboard["health_checks_available"], list)
        assert len(dashboard["health_checks_available"]) > 0

class TestMetricsExport:
    """Test cases for metrics export functionality."""
    
    @pytest.mark.asyncio
    async def test_export_metrics(self, monitoring_system, tmp_path, mock_psutil):
        """Test exporting metrics to file."""
        # Mock net_connections to avoid permission issues
        mock_psutil.net_connections.return_value = [1, 2, 3]  # 3 connections
        
        output_path = tmp_path / "metrics_export.json"
        
        await monitoring_system.export_metrics(str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
            
        assert isinstance(data["export_timestamp"], str)
        assert isinstance(data["monitoring_dashboard"], dict)
        assert isinstance(data["health_check_results"], dict)
        assert isinstance(data["alert_history"], list)
        assert isinstance(data["system_info"], dict)

class TestGlobalInstance:
    """Test cases for global monitoring system instance."""
    
    def test_get_monitoring_system(self):
        """Test getting global monitoring system instance."""
        reset_monitoring_system()
        
        system1 = get_monitoring_system()
        system2 = get_monitoring_system()
        
        assert system1 is system2
        assert isinstance(system1, MonitoringSystem)
        
    def test_reset_monitoring_system(self):
        """Test resetting global monitoring system instance."""
        system1 = get_monitoring_system()
        reset_monitoring_system()
        system2 = get_monitoring_system()
        
        assert system1 is not system2 