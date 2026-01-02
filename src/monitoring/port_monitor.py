"""
Port Monitor

Tracks port usage across WSL2 instances and detects conflicts.
"""

import logging
import time
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict
from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, WSL2Instance
from ..model.wsl2_model import wsl2_project_model

LOGGER = logging.getLogger('monitoring.port')


class PortMonitor:
    """Monitors port usage across WSL2 instances"""
    
    def __init__(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self._port_cache = {}  # instance -> {port -> usage_info}
        self._cache_timeout = 30  # seconds
        self._reserved_ports = set()  # Ports reserved by system/other services
        
        # Common system ports to avoid
        self._system_ports = {
            22, 23, 25, 53, 80, 110, 143, 443, 993, 995,  # Common services
            135, 139, 445, 1433, 1521, 3306, 5432,  # Windows/DB services
            8080, 8443, 9000, 9001  # Common dev ports
        }
    
    def scan_port_usage(self, instance_name: str, force_refresh: bool = False) -> Dict[int, Dict[str, Any]]:
        """Scan port usage for a specific WSL2 instance"""
        cache_key = instance_name
        current_time = time.time()
        
        # Check cache
        if not force_refresh and cache_key in self._port_cache:
            cached_data, timestamp = self._port_cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                LOGGER.debug(f"Returning cached port data for {instance_name}")
                return cached_data
        
        LOGGER.info(f"Scanning port usage for WSL2 instance: {instance_name}")
        
        if not self.wsl2_service.is_instance_running(instance_name):
            LOGGER.warning(f"WSL2 instance {instance_name} is not running")
            return {}
        
        port_usage = {}
        
        try:
            # Get all projects for this instance
            projects = wsl2_project_model.get_projects_by_instance(instance_name)
            
            # Check each project's ports
            for project in projects:
                for port in project.ports:
                    usage_info = self._check_port_usage(instance_name, port, project)
                    if usage_info:
                        port_usage[port] = usage_info
            
            # Also scan for unexpected port usage
            unexpected_ports = self._scan_unexpected_ports(instance_name, port_usage.keys())
            port_usage.update(unexpected_ports)
            
            # Update cache
            self._port_cache[cache_key] = (port_usage, current_time)
            
            LOGGER.info(f"Found {len(port_usage)} ports in use on {instance_name}")
            return port_usage
            
        except Exception as e:
            LOGGER.error(f"Error scanning port usage for {instance_name}: {e}")
            return {}
    
    def _check_port_usage(self, instance_name: str, port: int, project: ProjectInfo) -> Optional[Dict[str, Any]]:
        """Check usage of a specific port"""
        try:
            is_in_use = self.wsl2_service.is_port_in_use(instance_name, port)
            
            if is_in_use:
                # Get process information
                processes = self._get_port_processes(instance_name, port)
                
                return {
                    'port': port,
                    'in_use': True,
                    'project_id': project.id,
                    'project_name': project.name,
                    'instance': instance_name,
                    'processes': processes,
                    'last_checked': time.time()
                }
            else:
                return {
                    'port': port,
                    'in_use': False,
                    'project_id': project.id,
                    'project_name': project.name,
                    'instance': instance_name,
                    'processes': [],
                    'last_checked': time.time()
                }
                
        except Exception as e:
            LOGGER.error(f"Error checking port {port} usage: {e}")
            return None
    
    def _get_port_processes(self, instance_name: str, port: int) -> List[Dict[str, str]]:
        """Get processes using a specific port"""
        try:
            # Use netstat to find processes using the port
            result = self.wsl2_service.execute_command(
                instance_name,
                f"netstat -tulpn | grep ':{port}' || true"
            )
            
            if not result.success:
                return []
            
            processes = []
            for line in result.stdout.strip().split('\n'):
                if line and str(port) in line:
                    # Parse netstat output
                    parts = line.split()
                    if len(parts) >= 7:
                        protocol = parts[0]
                        local_address = parts[3]
                        state = parts[5] if len(parts) > 5 else 'UNKNOWN'
                        process_info = parts[6] if len(parts) > 6 else 'unknown'
                        
                        # Extract PID and process name
                        pid = 'unknown'
                        process_name = 'unknown'
                        if '/' in process_info:
                            pid, process_name = process_info.split('/', 1)
                        
                        processes.append({
                            'protocol': protocol,
                            'local_address': local_address,
                            'state': state,
                            'pid': pid,
                            'process_name': process_name
                        })
            
            return processes
            
        except Exception as e:
            LOGGER.error(f"Error getting processes for port {port}: {e}")
            return []
    
    def _scan_unexpected_ports(self, instance_name: str, known_ports: Set[int]) -> Dict[int, Dict[str, Any]]:
        """Scan for ports in use that aren't associated with known projects"""
        try:
            # Get all listening ports
            result = self.wsl2_service.execute_command(
                instance_name,
                "netstat -tuln | grep LISTEN || true"
            )
            
            if not result.success:
                return {}
            
            unexpected_ports = {}
            
            for line in result.stdout.strip().split('\n'):
                if line and 'LISTEN' in line:
                    # Extract port from netstat output
                    parts = line.split()
                    if len(parts) >= 4:
                        local_address = parts[3]
                        if ':' in local_address:
                            try:
                                port = int(local_address.split(':')[-1])
                                
                                # Skip known ports and system ports
                                if port not in known_ports and port not in self._system_ports:
                                    processes = self._get_port_processes(instance_name, port)
                                    
                                    unexpected_ports[port] = {
                                        'port': port,
                                        'in_use': True,
                                        'project_id': None,
                                        'project_name': 'Unknown',
                                        'instance': instance_name,
                                        'processes': processes,
                                        'unexpected': True,
                                        'last_checked': time.time()
                                    }
                                    
                            except ValueError:
                                continue
            
            if unexpected_ports:
                LOGGER.info(f"Found {len(unexpected_ports)} unexpected ports in use on {instance_name}")
            
            return unexpected_ports
            
        except Exception as e:
            LOGGER.error(f"Error scanning unexpected ports: {e}")
            return {}
    
    def get_all_port_usage(self) -> Dict[str, Dict[int, Dict[str, Any]]]:
        """Get port usage for all WSL2 instances"""
        all_usage = {}
        
        try:
            instances = self.wsl2_service.get_instances()
            
            for instance in instances:
                if instance.status.value == 'Running':
                    usage = self.scan_port_usage(instance.name)
                    if usage:
                        all_usage[instance.name] = usage
            
            return all_usage
            
        except Exception as e:
            LOGGER.error(f"Error getting all port usage: {e}")
            return {}
    
    def detect_port_conflicts(self) -> List[Dict[str, Any]]:
        """Detect port conflicts across instances and projects"""
        conflicts = []
        
        try:
            all_usage = self.get_all_port_usage()
            port_assignments = defaultdict(list)  # port -> [(instance, project_info)]
            
            # Collect all port assignments
            for instance_name, ports in all_usage.items():
                for port, usage_info in ports.items():
                    port_assignments[port].append((instance_name, usage_info))
            
            # Find conflicts (same port used by multiple projects)
            for port, assignments in port_assignments.items():
                if len(assignments) > 1:
                    # Check if it's actually a conflict (different projects)
                    project_ids = set()
                    for instance, usage_info in assignments:
                        project_id = usage_info.get('project_id')
                        if project_id:
                            project_ids.add(project_id)
                    
                    if len(project_ids) > 1:
                        conflicts.append({
                            'port': port,
                            'conflict_type': 'multiple_projects',
                            'assignments': assignments,
                            'severity': 'high'
                        })
            
            return conflicts
            
        except Exception as e:
            LOGGER.error(f"Error detecting port conflicts: {e}")
            return []
    
    def suggest_alternative_ports(self, requested_port: int, instance_name: str, count: int = 3) -> List[int]:
        """Suggest alternative ports if the requested port is in use"""
        try:
            current_usage = self.scan_port_usage(instance_name)
            used_ports = set(current_usage.keys())
            used_ports.update(self._system_ports)
            used_ports.update(self._reserved_ports)
            
            suggestions = []
            
            # Try ports near the requested port first
            for offset in range(1, 100):
                for candidate in [requested_port + offset, requested_port - offset]:
                    if (1024 <= candidate <= 65535 and 
                        candidate not in used_ports and 
                        candidate not in suggestions):
                        suggestions.append(candidate)
                        if len(suggestions) >= count:
                            return suggestions
            
            # If we couldn't find nearby ports, try common development port ranges
            dev_ranges = [
                (3000, 3100),  # Node.js common range
                (8000, 8100),  # Python/Django common range
                (9000, 9100),  # Various services
                (4000, 4100),  # Alternative range
            ]
            
            for start, end in dev_ranges:
                for candidate in range(start, end):
                    if (candidate not in used_ports and 
                        candidate not in suggestions):
                        suggestions.append(candidate)
                        if len(suggestions) >= count:
                            return suggestions
            
            return suggestions
            
        except Exception as e:
            LOGGER.error(f"Error suggesting alternative ports: {e}")
            return []
    
    def reserve_port(self, port: int, reason: str = "Manual reservation") -> bool:
        """Reserve a port to prevent automatic assignment"""
        try:
            self._reserved_ports.add(port)
            LOGGER.info(f"Reserved port {port}: {reason}")
            return True
        except Exception as e:
            LOGGER.error(f"Error reserving port {port}: {e}")
            return False
    
    def release_port(self, port: int) -> bool:
        """Release a reserved port"""
        try:
            if port in self._reserved_ports:
                self._reserved_ports.remove(port)
                LOGGER.info(f"Released reserved port {port}")
                return True
            return False
        except Exception as e:
            LOGGER.error(f"Error releasing port {port}: {e}")
            return False
    
    def get_port_statistics(self) -> Dict[str, Any]:
        """Get port usage statistics"""
        try:
            all_usage = self.get_all_port_usage()
            
            total_ports = 0
            ports_in_use = 0
            ports_by_instance = {}
            ports_by_project_type = defaultdict(int)
            
            for instance_name, ports in all_usage.items():
                instance_port_count = len(ports)
                ports_by_instance[instance_name] = instance_port_count
                total_ports += instance_port_count
                
                for port, usage_info in ports.items():
                    if usage_info.get('in_use'):
                        ports_in_use += 1
                    
                    # Count by project type if available
                    project_id = usage_info.get('project_id')
                    if project_id:
                        project = wsl2_project_model.get_project(project_id)
                        if project:
                            ports_by_project_type[project.project_type.value] += 1
            
            conflicts = self.detect_port_conflicts()
            
            return {
                'total_monitored_ports': total_ports,
                'ports_in_use': ports_in_use,
                'ports_available': total_ports - ports_in_use,
                'ports_by_instance': ports_by_instance,
                'ports_by_project_type': dict(ports_by_project_type),
                'port_conflicts': len(conflicts),
                'reserved_ports': len(self._reserved_ports),
                'system_ports_avoided': len(self._system_ports)
            }
            
        except Exception as e:
            LOGGER.error(f"Error getting port statistics: {e}")
            return {}
    
    def clear_cache(self):
        """Clear the port usage cache"""
        self._port_cache.clear()
        LOGGER.debug("Port monitor cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on port monitoring system"""
        health = {
            'port_monitor_healthy': True,
            'cache_size': len(self._port_cache),
            'reserved_ports': len(self._reserved_ports),
            'issues': []
        }
        
        try:
            # Test basic functionality
            instances = self.wsl2_service.get_instances()
            running_instances = [i for i in instances if i.status.value == 'Running']
            
            if not running_instances:
                health['issues'].append('No running WSL2 instances found')
            
            # Test port scanning on first running instance
            if running_instances:
                test_instance = running_instances[0].name
                try:
                    self.scan_port_usage(test_instance, force_refresh=True)
                except Exception as e:
                    health['port_monitor_healthy'] = False
                    health['issues'].append(f'Port scanning failed: {str(e)}')
            
        except Exception as e:
            health['port_monitor_healthy'] = False
            health['issues'].append(f'Health check failed: {str(e)}')
        
        return health
