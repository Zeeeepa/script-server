"""
WSL2 Integration Module

Integrates WSL2 functionality with Script-Server's core systems.
"""

import logging
from typing import Dict, Any, List, Optional
from ..wsl2.wsl2_service import WSL2Service
from ..model.wsl2_model import wsl2_project_model
from ..execution.project_executor import ProjectExecutionService
from ..projects.project_discovery import ProjectDiscovery
from ..monitoring.port_monitor import PortMonitor
from ..monitoring.health_checker import HealthChecker
from ..web.wsl2_handlers import WSL2_URL_PATTERNS
from ..web.wsl2_websocket import WSL2_WEBSOCKET_PATTERN

LOGGER = logging.getLogger('integration.wsl2')


class WSL2Integration:
    """Main integration class for WSL2 functionality"""
    
    def __init__(self):
        self.wsl2_service = WSL2Service()
        self.project_executor = ProjectExecutionService(self.wsl2_service)
        self.project_discovery = ProjectDiscovery(self.wsl2_service)
        self.port_monitor = PortMonitor(self.wsl2_service)
        self.health_checker = HealthChecker(self.wsl2_service)
        self.is_initialized = False
    
    def initialize(self):
        """Initialize WSL2 integration"""
        try:
            LOGGER.info("Initializing WSL2 integration...")
            
            # Initialize services
            self.wsl2_service.initialize()
            
            # Load existing projects
            self._load_existing_projects()
            
            # Start monitoring services
            self.port_monitor.start_monitoring()
            self.health_checker.start_monitoring()
            
            self.is_initialized = True
            LOGGER.info("WSL2 integration initialized successfully")
            
        except Exception as e:
            LOGGER.error(f"Failed to initialize WSL2 integration: {e}")
            raise
    
    def shutdown(self):
        """Shutdown WSL2 integration"""
        try:
            LOGGER.info("Shutting down WSL2 integration...")
            
            # Stop monitoring services
            self.port_monitor.stop_monitoring()
            self.health_checker.stop_monitoring()
            
            self.is_initialized = False
            LOGGER.info("WSL2 integration shut down successfully")
            
        except Exception as e:
            LOGGER.error(f"Error during WSL2 integration shutdown: {e}")
    
    def _load_existing_projects(self):
        """Load existing WSL2 projects from configuration"""
        try:
            # This would typically load from a configuration file or database
            # For now, we'll just ensure the model is ready
            projects = wsl2_project_model.get_all_projects()
            LOGGER.info(f"Loaded {len(projects)} existing WSL2 projects")
            
        except Exception as e:
            LOGGER.error(f"Error loading existing projects: {e}")
    
    def get_url_patterns(self):
        """Get URL patterns for WSL2 handlers"""
        return WSL2_URL_PATTERNS
    
    def get_websocket_pattern(self):
        """Get WebSocket pattern for WSL2 handler"""
        return WSL2_WEBSOCKET_PATTERN
    
    def get_services(self):
        """Get all WSL2 services for dependency injection"""
        return {
            'wsl2_service': self.wsl2_service,
            'project_executor': self.project_executor,
            'project_discovery': self.project_discovery,
            'port_monitor': self.port_monitor,
            'health_checker': self.health_checker
        }
    
    def auto_discover_projects(self, instance_names: List[str] = None) -> List[Dict[str, Any]]:
        """Auto-discover projects in WSL2 instances"""
        try:
            if not instance_names:
                instances = self.wsl2_service.get_instances()
                instance_names = [inst.name for inst in instances if inst.status == 'Running']
            
            all_discovered = []
            for instance_name in instance_names:
                try:
                    discovered = self.project_discovery.discover_projects(instance_name)
                    all_discovered.extend(discovered)
                    LOGGER.info(f"Discovered {len(discovered)} projects in {instance_name}")
                except Exception as e:
                    LOGGER.error(f"Error discovering projects in {instance_name}: {e}")
            
            return [project.to_dict() for project in all_discovered]
            
        except Exception as e:
            LOGGER.error(f"Error in auto-discovery: {e}")
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall WSL2 system status"""
        try:
            instances = self.wsl2_service.get_instances()
            projects = wsl2_project_model.get_all_projects()
            port_usage = self.port_monitor.get_all_port_usage()
            port_conflicts = self.port_monitor.detect_port_conflicts()
            health_status = self.health_checker.check_all_projects_health()
            
            running_projects = [p for p in projects if p.status.value == 'running']
            stopped_projects = [p for p in projects if p.status.value == 'stopped']
            error_projects = [p for p in projects if p.status.value == 'error']
            
            return {
                'instances': {
                    'total': len(instances),
                    'running': len([i for i in instances if i.status == 'Running']),
                    'stopped': len([i for i in instances if i.status == 'Stopped'])
                },
                'projects': {
                    'total': len(projects),
                    'running': len(running_projects),
                    'stopped': len(stopped_projects),
                    'error': len(error_projects)
                },
                'ports': {
                    'total_in_use': sum(len(ports) for ports in port_usage.values()),
                    'conflicts': len(port_conflicts)
                },
                'health': {
                    'healthy': len([p for p in projects if p.status.value == 'running']),
                    'unhealthy': len(health_status.get('unhealthy_projects', []))
                }
            }
            
        except Exception as e:
            LOGGER.error(f"Error getting system status: {e}")
            return {}


# Global WSL2 integration instance
wsl2_integration = WSL2Integration()


def initialize_wsl2_integration():
    """Initialize the global WSL2 integration"""
    wsl2_integration.initialize()


def shutdown_wsl2_integration():
    """Shutdown the global WSL2 integration"""
    wsl2_integration.shutdown()


def get_wsl2_integration() -> WSL2Integration:
    """Get the global WSL2 integration instance"""
    return wsl2_integration
