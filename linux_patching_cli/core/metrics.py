"""
Metrics collection and monitoring for Linux Patching Automation
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pathlib import Path

from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from prometheus_client.core import CollectorRegistry
import psutil

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Prometheus metrics
REGISTRY = CollectorRegistry()

# Counters
PATCHING_JOBS_TOTAL = Counter(
    'patching_jobs_total',
    'Total number of patching jobs',
    ['status', 'environment', 'quarter'],
    registry=REGISTRY
)

PATCHING_JOBS_FAILED = Counter(
    'patching_jobs_failed_total',
    'Total number of failed patching jobs',
    ['reason', 'environment', 'quarter'],
    registry=REGISTRY
)

SERVER_PATCHES_APPLIED = Counter(
    'server_patches_applied_total',
    'Total number of patches applied to servers',
    ['server', 'environment', 'patch_type'],
    registry=REGISTRY
)

SSH_CONNECTIONS = Counter(
    'ssh_connections_total',
    'Total number of SSH connections',
    ['server', 'status'],
    registry=REGISTRY
)

API_REQUESTS = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

EMAIL_NOTIFICATIONS = Counter(
    'email_notifications_total',
    'Total number of email notifications sent',
    ['type', 'status'],
    registry=REGISTRY
)

# Histograms
PATCHING_DURATION = Histogram(
    'patching_job_duration_seconds',
    'Time spent on patching jobs',
    ['environment', 'job_type'],
    registry=REGISTRY
)

SSH_RESPONSE_TIME = Histogram(
    'ssh_response_time_seconds',
    'SSH connection response time',
    ['server'],
    registry=REGISTRY
)

API_REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Gauges
ACTIVE_PATCHING_JOBS = Gauge(
    'active_patching_jobs',
    'Number of currently active patching jobs',
    registry=REGISTRY
)

PENDING_APPROVALS = Gauge(
    'patching_approvals_pending',
    'Number of pending approval requests',
    registry=REGISTRY
)

SERVER_STATUS = Gauge(
    'server_status',
    'Server status (1=online, 0=offline)',
    ['server', 'environment'],
    registry=REGISTRY
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=REGISTRY
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage',
    registry=REGISTRY
)

QUEUE_SIZE = Gauge(
    'queue_size',
    'Current queue size',
    ['queue_type'],
    registry=REGISTRY
)

# Info metrics
APPLICATION_INFO = Info(
    'application_info',
    'Application information',
    registry=REGISTRY
)

class MetricType(Enum):
    """Metric types for categorization"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    INFO = "info"

@dataclass
class MetricData:
    """Data structure for metric information"""
    name: str
    type: MetricType
    value: Any
    labels: Dict[str, str]
    timestamp: float
    description: Optional[str] = None

class MetricsCollector:
    """Centralized metrics collection and management"""
    
    def __init__(self, port: int = 8004):
        self.port = port
        self.registry = REGISTRY
        self.metrics_data: List[MetricData] = []
        self.start_time = time.time()
        self._setup_application_info()
        
    def _setup_application_info(self):
        """Setup application information metrics"""
        APPLICATION_INFO.info({
            'version': '1.0.0',
            'build_date': '2024-01-01',
            'environment': 'production',
            'python_version': '3.9+',
        })
        
    def start_metrics_server(self):
        """Start the Prometheus metrics server"""
        try:
            start_http_server(self.port, registry=self.registry)
            logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            
    def record_patching_job(self, status: str, environment: str, quarter: str, 
                          duration: Optional[float] = None, job_type: str = "standard"):
        """Record patching job metrics"""
        PATCHING_JOBS_TOTAL.labels(
            status=status,
            environment=environment,
            quarter=quarter
        ).inc()
        
        if duration:
            PATCHING_DURATION.labels(
                environment=environment,
                job_type=job_type
            ).observe(duration)
            
        if status == "failed":
            PATCHING_JOBS_FAILED.labels(
                reason="execution_error",
                environment=environment,
                quarter=quarter
            ).inc()
            
    def record_server_patch(self, server: str, environment: str, patch_type: str):
        """Record server patch application"""
        SERVER_PATCHES_APPLIED.labels(
            server=server,
            environment=environment,
            patch_type=patch_type
        ).inc()
        
    def record_ssh_connection(self, server: str, status: str, response_time: Optional[float] = None):
        """Record SSH connection metrics"""
        SSH_CONNECTIONS.labels(
            server=server,
            status=status
        ).inc()
        
        if response_time:
            SSH_RESPONSE_TIME.labels(server=server).observe(response_time)
            
    def record_api_request(self, method: str, endpoint: str, status: str, duration: float):
        """Record API request metrics"""
        API_REQUESTS.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        API_REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    def record_email_notification(self, notification_type: str, status: str):
        """Record email notification metrics"""
        EMAIL_NOTIFICATIONS.labels(
            type=notification_type,
            status=status
        ).inc()
        
    def update_active_jobs(self, count: int):
        """Update active patching jobs count"""
        ACTIVE_PATCHING_JOBS.set(count)
        
    def update_pending_approvals(self, count: int):
        """Update pending approvals count"""
        PENDING_APPROVALS.set(count)
        
    def update_server_status(self, server: str, environment: str, is_online: bool):
        """Update server status"""
        SERVER_STATUS.labels(
            server=server,
            environment=environment
        ).set(1 if is_online else 0)
        
    def update_queue_size(self, queue_type: str, size: int):
        """Update queue size"""
        QUEUE_SIZE.labels(queue_type=queue_type).set(size)
        
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            logger.debug(f"System metrics collected: CPU={cpu_percent}%, Memory={memory.percent}%")
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "metrics_collected": len(self.metrics_data),
            "active_jobs": ACTIVE_PATCHING_JOBS._value.get(),
            "pending_approvals": PENDING_APPROVALS._value.get(),
            "system_cpu_usage": SYSTEM_CPU_USAGE._value.get(),
            "system_memory_usage": SYSTEM_MEMORY_USAGE._value.get(),
            "timestamp": time.time()
        }
        
    def export_metrics(self, file_path: str):
        """Export metrics to a JSON file"""
        try:
            metrics_summary = self.get_metrics_summary()
            
            with open(file_path, 'w') as f:
                json.dump(metrics_summary, f, indent=2)
                
            logger.info(f"Metrics exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            
    def reset_metrics(self):
        """Reset all metrics (use with caution)"""
        logger.warning("Resetting all metrics")
        
        # Clear counters would require recreating them
        # This is typically not done in production
        ACTIVE_PATCHING_JOBS.set(0)
        PENDING_APPROVALS.set(0)
        SYSTEM_CPU_USAGE.set(0)
        SYSTEM_MEMORY_USAGE.set(0)
        
        self.metrics_data.clear()

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector

# Convenience functions
def record_patching_job_start(job_id: str, environment: str, quarter: str):
    """Record the start of a patching job"""
    metrics_collector.record_patching_job("started", environment, quarter)
    logger.info(f"Patching job started: {job_id}")

def record_patching_job_completion(job_id: str, environment: str, quarter: str, 
                                 duration: float, success: bool):
    """Record the completion of a patching job"""
    status = "completed" if success else "failed"
    metrics_collector.record_patching_job(status, environment, quarter, duration)
    logger.info(f"Patching job {status}: {job_id} (duration: {duration:.2f}s)")

def record_server_connectivity(server: str, is_connected: bool, response_time: Optional[float] = None):
    """Record server connectivity status"""
    status = "connected" if is_connected else "disconnected"
    metrics_collector.record_ssh_connection(server, status, response_time)

def start_metrics_collection():
    """Start the metrics collection service"""
    metrics_collector.start_metrics_server()
    logger.info("Metrics collection service started")

if __name__ == "__main__":
    # Example usage
    start_metrics_collection()
    
    # Simulate some metrics
    record_patching_job_start("job-001", "production", "Q1")
    record_server_connectivity("web-01", True, 0.123)
    metrics_collector.collect_system_metrics()
    
    print("Metrics collection demo completed")