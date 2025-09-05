"""
Health Checker

Performs health checks on WSL2 projects using multiple protocols.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, HealthCheck, ProjectStatus
from ..model.wsl2_model import wsl2_project_model

LOGGER = logging.getLogger('monitoring.health')


class HealthChecker:
    """Performs health checks on WSL2 projects"""
    
    def __init__(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self._health_cache = {}  # project_id -> health_result
        self._cache_timeout = 30  # seconds
    
    def check_project_health(self, project: ProjectInfo, force_refresh: bool = False) -> Dict[str, Any]:
        """Check health of a specific project"""
        cache_key = project.id
        current_time = time.time()
        
        # Check cache
        if not force_refresh and cache_key in self._health_cache:
            cached_result, timestamp = self._health_cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                return cached_result
        
        LOGGER.debug(f"Checking health for project: {project.name}")
        
        health_result = {
            'project_id': project.id,
            'project_name': project.name,
            'healthy': False,
            'checks': [],
            'overall_status': 'unknown',
            'last_checked': current_time
        }
        
        try:
            # Basic status check
            basic_check = self._check_basic_status(project)
            health_result['checks'].append(basic_check)
            
            # Port checks
            if project.ports:
                port_checks = self._check_ports(project)
                health_result['checks'].extend(port_checks)
            
            # Health check if configured
            if project.health_check:
                hc_result = self._perform_health_check(project, project.health_check)
                health_result['checks'].append(hc_result)
            
            # Determine overall health
            health_result['healthy'] = self._determine_overall_health(health_result['checks'])
            health_result['overall_status'] = 'healthy' if health_result['healthy'] else 'unhealthy'
            
            # Update cache
            self._health_cache[cache_key] = (health_result, current_time)
            
            return health_result
            
        except Exception as e:
            LOGGER.error(f"Error checking health for project {project.name}: {e}")
            health_result['overall_status'] = 'error'
            health_result['error'] = str(e)
            return health_result
    
    def _check_basic_status(self, project: ProjectInfo) -> Dict[str, Any]:
        """Perform basic status check"""
        try:
            # Check if WSL2 instance is running
            instance_running = self.wsl2_service.is_instance_running(project.wsl_instance)
            
            # Check if project directory exists
            dir_exists = self.wsl2_service.directory_exists(project.wsl_instance, project.path)
            
            return {
                'check_type': 'basic_status',
                'passed': instance_running and dir_exists,
                'details': {
                    'instance_running': instance_running,
                    'directory_exists': dir_exists
                },
                'message': 'Basic status check',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'check_type': 'basic_status',
                'passed': False,
                'error': str(e),
                'message': 'Basic status check failed',
                'timestamp': time.time()
            }
    
    def _check_ports(self, project: ProjectInfo) -> List[Dict[str, Any]]:
        """Check if project ports are accessible"""
        port_checks = []
        
        for port in project.ports:
            try:
                is_in_use = self.wsl2_service.is_port_in_use(project.wsl_instance, port)
                
                port_checks.append({
                    'check_type': 'port_check',
                    'port': port,
                    'passed': is_in_use,
                    'message': f'Port {port} {"is accessible" if is_in_use else "is not accessible"}',
                    'timestamp': time.time()
                })
                
            except Exception as e:
                port_checks.append({
                    'check_type': 'port_check',
                    'port': port,
                    'passed': False,
                    'error': str(e),
                    'message': f'Port {port} check failed',
                    'timestamp': time.time()
                })
        
        return port_checks
    
    def _perform_health_check(self, project: ProjectInfo, health_check: HealthCheck) -> Dict[str, Any]:
        """Perform configured health check"""
        try:
            if health_check.type == 'http':
                return self._http_health_check(project, health_check)
            elif health_check.type == 'tcp':
                return self._tcp_health_check(project, health_check)
            elif health_check.type == 'command':
                return self._command_health_check(project, health_check)
            else:
                return {
                    'check_type': 'health_check',
                    'passed': False,
                    'error': f'Unknown health check type: {health_check.type}',
                    'timestamp': time.time()
                }
                
        except Exception as e:
            return {
                'check_type': 'health_check',
                'passed': False,
                'error': str(e),
                'message': 'Health check failed',
                'timestamp': time.time()
            }
    
    def _http_health_check(self, project: ProjectInfo, health_check: HealthCheck) -> Dict[str, Any]:
        """Perform HTTP health check"""
        try:
            # Use curl to check HTTP endpoint
            curl_command = f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout {health_check.timeout} '{health_check.url}'"
            
            result = self.wsl2_service.execute_command(
                project.wsl_instance,
                curl_command,
                project.path
            )
            
            if result.success:
                http_code = result.stdout.strip()
                passed = http_code.startswith('2')  # 2xx status codes
                
                return {
                    'check_type': 'http_health_check',
                    'passed': passed,
                    'http_code': http_code,
                    'url': health_check.url,
                    'message': f'HTTP health check returned {http_code}',
                    'timestamp': time.time()
                }
            else:
                return {
                    'check_type': 'http_health_check',
                    'passed': False,
                    'url': health_check.url,
                    'error': result.stderr,
                    'message': 'HTTP health check failed',
                    'timestamp': time.time()
                }
                
        except Exception as e:
            return {
                'check_type': 'http_health_check',
                'passed': False,
                'url': health_check.url,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _tcp_health_check(self, project: ProjectInfo, health_check: HealthCheck) -> Dict[str, Any]:
        """Perform TCP health check"""
        try:
            # Use netcat to check TCP port
            nc_command = f"timeout {health_check.timeout} nc -z localhost {health_check.port}"
            
            result = self.wsl2_service.execute_command(
                project.wsl_instance,
                nc_command,
                project.path
            )
            
            return {
                'check_type': 'tcp_health_check',
                'passed': result.success,
                'port': health_check.port,
                'message': f'TCP health check on port {health_check.port}',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'check_type': 'tcp_health_check',
                'passed': False,
                'port': health_check.port,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _command_health_check(self, project: ProjectInfo, health_check: HealthCheck) -> Dict[str, Any]:
        """Perform command-based health check"""
        try:
            result = self.wsl2_service.execute_command(
                project.wsl_instance,
                health_check.command,
                project.path
            )
            
            return {
                'check_type': 'command_health_check',
                'passed': result.success,
                'command': health_check.command,
                'stdout': result.stdout[:200],  # Limit output
                'stderr': result.stderr[:200],
                'return_code': result.return_code,
                'message': f'Command health check: {health_check.command}',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'check_type': 'command_health_check',
                'passed': False,
                'command': health_check.command,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _determine_overall_health(self, checks: List[Dict[str, Any]]) -> bool:
        """Determine overall health from individual checks"""
        if not checks:
            return False
        
        # All checks must pass for overall health
        return all(check.get('passed', False) for check in checks)
    
    def check_all_projects_health(self) -> Dict[str, Any]:
        """Check health of all projects"""
        try:
            all_projects = wsl2_project_model.get_all_projects()
            health_results = {}
            
            healthy_count = 0
            unhealthy_count = 0
            error_count = 0
            
            for project in all_projects:
                health_result = self.check_project_health(project)
                health_results[project.id] = health_result
                
                if health_result['overall_status'] == 'healthy':
                    healthy_count += 1
                elif health_result['overall_status'] == 'unhealthy':
                    unhealthy_count += 1
                else:
                    error_count += 1
            
            return {
                'total_projects': len(all_projects),
                'healthy_projects': healthy_count,
                'unhealthy_projects': unhealthy_count,
                'error_projects': error_count,
                'health_results': health_results,
                'overall_health_percentage': (healthy_count / len(all_projects) * 100) if all_projects else 0
            }
            
        except Exception as e:
            LOGGER.error(f"Error checking all projects health: {e}")
            return {
                'error': str(e),
                'total_projects': 0
            }
    
    def get_unhealthy_projects(self) -> List[Dict[str, Any]]:
        """Get list of unhealthy projects"""
        try:
            all_health = self.check_all_projects_health()
            unhealthy_projects = []
            
            for project_id, health_result in all_health.get('health_results', {}).items():
                if not health_result.get('healthy', False):
                    project = wsl2_project_model.get_project(project_id)
                    if project:
                        unhealthy_projects.append({
                            'project': project.to_dict(),
                            'health_result': health_result
                        })
            
            return unhealthy_projects
            
        except Exception as e:
            LOGGER.error(f"Error getting unhealthy projects: {e}")
            return []
    
    def clear_cache(self):
        """Clear health check cache"""
        self._health_cache.clear()
        LOGGER.debug("Health checker cache cleared")
