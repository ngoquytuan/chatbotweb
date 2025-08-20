#utils/monitoring.py
"""
System Performance Monitoring
"""
import time
import psutil
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        
        try:
            # Get CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Get load average (Unix-like systems only)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except (AttributeError, OSError):
                # Windows or other systems that don't support getloadavg
                pass
            
            # Get memory metrics
            memory = psutil.virtual_memory()
            
            # Get disk metrics
            disk = psutil.disk_usage('/')
            
            # Get network metrics
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': load_avg
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': {
                    'total': len(psutil.pids()),
                    'running': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        
        try:
            # Get current process info
            process = psutil.Process()
            
            # Memory info for current process
            memory_info = process.memory_info()
            
            # CPU usage for current process
            cpu_percent = process.cpu_percent()
            
            # File descriptors (Unix only)
            open_files = None
            try:
                open_files = len(process.open_files())
            except (AttributeError, psutil.AccessDenied):
                pass
            
            # Threads
            num_threads = process.num_threads()
            
            return {
                'process': {
                    'pid': process.pid,
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'cpu_percent': cpu_percent,
                    'num_threads': num_threads,
                    'open_files': open_files,
                    'create_time': process.create_time()
                },
                'uptime': time.time() - self.start_time
            }
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {'error': str(e)}
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def get_health_status(self, metrics: Dict[str, Any]) -> str:
        """Determine health status based on metrics"""
        
        try:
            # Check CPU usage
            cpu_usage = metrics.get('cpu', {}).get('usage_percent', 0)
            if cpu_usage > 90:
                return 'critical'
            elif cpu_usage > 75:
                return 'warning'
            
            # Check memory usage
            memory_percent = metrics.get('memory', {}).get('percent', 0)
            if memory_percent > 90:
                return 'critical'
            elif memory_percent > 80:
                return 'warning'
            
            # Check disk usage
            disk_percent = metrics.get('disk', {}).get('percent', 0)
            if disk_percent > 90:
                return 'critical'
            elif disk_percent > 85:
                return 'warning'
            
            return 'healthy'
            
        except Exception as e:
            logger.error(f"Error determining health status: {e}")
            return 'unknown'