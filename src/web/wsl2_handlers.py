"""
WSL2 Web API Handlers

REST API endpoints for WSL2 project management functionality.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from tornado.web import RequestHandler
from tornado.escape import json_decode, json_encode

from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, ProjectStatus, ProjectType
from ..model.wsl2_model import wsl2_project_model
from ..execution.project_executor import ProjectExecutionService
from ..projects.project_discovery import ProjectDiscovery
from ..monitoring.port_monitor import PortMonitor
from ..monitoring.health_checker import HealthChecker
from ..config.wsl2_config import WSL2ConfigValidator, get_wsl2_config_template

LOGGER = logging.getLogger('web.wsl2')


class BaseWSL2Handler(RequestHandler):
    """Base handler for WSL2 API endpoints"""
    
    def initialize(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self.project_executor = ProjectExecutionService(wsl2_service)
        self.project_discovery = ProjectDiscovery(wsl2_service)
        self.port_monitor = PortMonitor(wsl2_service)
        self.health_checker = HealthChecker(wsl2_service)
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def write_json(self, data: Dict[str, Any]):
        """Write JSON response"""
        self.set_header("Content-Type", "application/json")
        self.write(json_encode(data))
    
    def get_json_body(self) -> Dict[str, Any]:
        """Parse JSON request body"""
        try:
            return json_decode(self.request.body) if self.request.body else {}
        except Exception as e:
            raise ValueError(f"Invalid JSON: {e}")


class WSL2InstancesHandler(BaseWSL2Handler):
    """Handler for WSL2 instances management"""
    
    def get(self):
        """Get all WSL2 instances"""
        try:
            instances = self.wsl2_service.get_instances()
            instances_data = [instance.to_dict() for instance in instances]
            
            self.write_json({
                'success': True,
                'instances': instances_data,
                'total': len(instances_data)
            })
            
        except Exception as e:
            LOGGER.error(f"Error getting WSL2 instances: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })
    
    def post(self):
        """Start/stop WSL2 instance"""
        try:
            data = self.get_json_body()
            instance_name = data.get('instance_name')
            action = data.get('action')  # 'start' or 'stop'
            
            if not instance_name or not action:
                self.set_status(400)
                self.write_json({
                    'success': False,
                    'error': 'instance_name and action are required'
                })
                return
            
            if action == 'start':
                success = self.wsl2_service.start_instance(instance_name)
                message = f"Instance {instance_name} {'started' if success else 'failed to start'}"
            elif action == 'stop':
                success = self.wsl2_service.stop_instance(instance_name)
                message = f"Instance {instance_name} {'stopped' if success else 'failed to stop'}"
            else:
                self.set_status(400)
                self.write_json({
                    'success': False,
                    'error': 'action must be "start" or "stop"'
                })
                return
            
            self.write_json({
                'success': success,
                'message': message,
                'instance_name': instance_name,
                'action': action
            })
            
        except Exception as e:
            LOGGER.error(f"Error managing WSL2 instance: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2ProjectsHandler(BaseWSL2Handler):
    """Handler for WSL2 projects management"""
    
    def get(self):
        """Get all WSL2 projects with optional filtering"""
        try:
            # Parse query parameters
            instance_name = self.get_argument('instance', None)
            project_type = self.get_argument('type', None)
            status = self.get_argument('status', None)
            
            # Build filters
            filters = {}
            if instance_name:
                filters['instance'] = instance_name
            if project_type:
                filters['type'] = project_type
            if status:
                filters['status'] = status
            
            # Get projects
            if filters:
                projects = wsl2_project_model.find_projects(**filters)
            else:
                projects = wsl2_project_model.get_all_projects()
            
            projects_data = [project.to_dict() for project in projects]
            
            self.write_json({
                'success': True,
                'projects': projects_data,
                'total': len(projects_data),
                'filters': filters
            })
            
        except Exception as e:
            LOGGER.error(f"Error getting WSL2 projects: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })
    
    def post(self):
        """Create or update a WSL2 project"""
        try:
            data = self.get_json_body()
            
            # Validate required fields
            required_fields = ['name', 'wsl_instance', 'path', 'project_type']
            for field in required_fields:
                if field not in data:
                    self.set_status(400)
                    self.write_json({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    })
                    return
            
            # Create ProjectInfo from data
            project_info = ProjectInfo.from_dict(data)
            
            # Add or update project
            existing_project = wsl2_project_model.get_project_by_name(
                project_info.name, project_info.wsl_instance
            )
            
            if existing_project:
                # Update existing project
                project_info.id = existing_project.id
                wsl2_project_model.update_project(project_info)
                action = 'updated'
            else:
                # Add new project
                wsl2_project_model.add_project(project_info)
                action = 'created'
            
            self.write_json({
                'success': True,
                'message': f'Project {project_info.name} {action} successfully',
                'project': project_info.to_dict(),
                'action': action
            })
            
        except Exception as e:
            LOGGER.error(f"Error creating/updating WSL2 project: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2ProjectHandler(BaseWSL2Handler):
    """Handler for individual WSL2 project operations"""
    
    def get(self, project_id: str):
        """Get specific project details"""
        try:
            project = wsl2_project_model.get_project(project_id)
            if not project:
                self.set_status(404)
                self.write_json({
                    'success': False,
                    'error': f'Project {project_id} not found'
                })
                return
            
            # Get additional status information
            status_info = self.project_executor.wsl2_executor.get_project_status(project)
            
            self.write_json({
                'success': True,
                'project': project.to_dict(),
                'status_info': status_info
            })
            
        except Exception as e:
            LOGGER.error(f"Error getting project {project_id}: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })
    
    def delete(self, project_id: str):
        """Delete a WSL2 project"""
        try:
            success = wsl2_project_model.remove_project(project_id)
            
            if success:
                self.write_json({
                    'success': True,
                    'message': f'Project {project_id} deleted successfully'
                })
            else:
                self.set_status(404)
                self.write_json({
                    'success': False,
                    'error': f'Project {project_id} not found'
                })
                
        except Exception as e:
            LOGGER.error(f"Error deleting project {project_id}: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2ProjectActionHandler(BaseWSL2Handler):
    """Handler for WSL2 project actions (start/stop/restart)"""
    
    def post(self, project_id: str, action: str):
        """Execute project action"""
        try:
            project = wsl2_project_model.get_project(project_id)
            if not project:
                self.set_status(404)
                self.write_json({
                    'success': False,
                    'error': f'Project {project_id} not found'
                })
                return
            
            # Execute action
            if action == 'start':
                result = self.project_executor.wsl2_executor.start_project(project)
            elif action == 'stop':
                result = self.project_executor.wsl2_executor.stop_project(project)
            elif action == 'restart':
                result = self.project_executor.wsl2_executor.restart_project(project)
            else:
                self.set_status(400)
                self.write_json({
                    'success': False,
                    'error': f'Invalid action: {action}. Must be start, stop, or restart'
                })
                return
            
            self.write_json(result)
            
        except Exception as e:
            LOGGER.error(f"Error executing {action} on project {project_id}: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2DiscoveryHandler(BaseWSL2Handler):
    """Handler for project discovery operations"""
    
    def post(self):
        """Discover projects in WSL2 instances"""
        try:
            data = self.get_json_body()
            instance_name = data.get('instance_name')
            scan_path = data.get('scan_path', '/home')
            max_depth = data.get('max_depth', 3)
            
            if not instance_name:
                self.set_status(400)
                self.write_json({
                    'success': False,
                    'error': 'instance_name is required'
                })
                return
            
            # Discover projects
            discovered_projects = self.project_discovery.discover_projects(
                instance_name, scan_path, max_depth
            )
            
            # Convert to dict format
            projects_data = [project.to_dict() for project in discovered_projects]
            
            self.write_json({
                'success': True,
                'discovered_projects': projects_data,
                'total': len(projects_data),
                'instance_name': instance_name,
                'scan_path': scan_path
            })
            
        except Exception as e:
            LOGGER.error(f"Error discovering projects: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2PortsHandler(BaseWSL2Handler):
    """Handler for port monitoring operations"""
    
    def get(self):
        """Get port usage information"""
        try:
            instance_name = self.get_argument('instance', None)
            
            if instance_name:
                # Get port usage for specific instance
                port_usage = self.port_monitor.scan_port_usage(instance_name)
                result = {
                    'success': True,
                    'instance_name': instance_name,
                    'port_usage': port_usage
                }
            else:
                # Get port usage for all instances
                all_usage = self.port_monitor.get_all_port_usage()
                conflicts = self.port_monitor.detect_port_conflicts()
                statistics = self.port_monitor.get_port_statistics()
                
                result = {
                    'success': True,
                    'all_port_usage': all_usage,
                    'conflicts': conflicts,
                    'statistics': statistics
                }
            
            self.write_json(result)
            
        except Exception as e:
            LOGGER.error(f"Error getting port information: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2HealthHandler(BaseWSL2Handler):
    """Handler for health monitoring operations"""
    
    def get(self):
        """Get health information"""
        try:
            project_id = self.get_argument('project_id', None)
            
            if project_id:
                # Get health for specific project
                project = wsl2_project_model.get_project(project_id)
                if not project:
                    self.set_status(404)
                    self.write_json({
                        'success': False,
                        'error': f'Project {project_id} not found'
                    })
                    return
                
                health_result = self.health_checker.check_project_health(project)
                self.write_json({
                    'success': True,
                    'project_id': project_id,
                    'health': health_result
                })
            else:
                # Get health for all projects
                all_health = self.health_checker.check_all_projects_health()
                self.write_json({
                    'success': True,
                    'all_health': all_health
                })
                
        except Exception as e:
            LOGGER.error(f"Error getting health information: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2BulkActionHandler(BaseWSL2Handler):
    """Handler for bulk operations on multiple projects"""
    
    def post(self, action: str):
        """Execute bulk action on projects"""
        try:
            data = self.get_json_body()
            instance_name = data.get('instance_name')
            project_type = data.get('project_type')
            project_ids = data.get('project_ids', [])
            
            if action == 'start':
                if project_ids:
                    # Start specific projects
                    results = {}
                    for project_id in project_ids:
                        project = wsl2_project_model.get_project(project_id)
                        if project:
                            result = self.project_executor.wsl2_executor.start_project(project)
                            results[project_id] = result
                    
                    self.write_json({
                        'success': True,
                        'action': 'bulk_start',
                        'results': results
                    })
                else:
                    # Start projects by filters
                    result = self.project_executor.bulk_start_projects(instance_name, project_type)
                    self.write_json(result)
                    
            elif action == 'stop':
                if project_ids:
                    # Stop specific projects
                    results = {}
                    for project_id in project_ids:
                        project = wsl2_project_model.get_project(project_id)
                        if project:
                            result = self.project_executor.wsl2_executor.stop_project(project)
                            results[project_id] = result
                    
                    self.write_json({
                        'success': True,
                        'action': 'bulk_stop',
                        'results': results
                    })
                else:
                    # Stop projects by filters
                    result = self.project_executor.bulk_stop_projects(instance_name, project_type)
                    self.write_json(result)
                    
            else:
                self.set_status(400)
                self.write_json({
                    'success': False,
                    'error': f'Invalid bulk action: {action}'
                })
                
        except Exception as e:
            LOGGER.error(f"Error executing bulk action {action}: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


class WSL2ConfigTemplateHandler(BaseWSL2Handler):
    """Handler for configuration templates"""
    
    def get(self):
        """Get WSL2 configuration template"""
        try:
            template = get_wsl2_config_template()
            
            self.write_json({
                'success': True,
                'template': template
            })
            
        except Exception as e:
            LOGGER.error(f"Error getting config template: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })
    
    def post(self):
        """Validate WSL2 configuration"""
        try:
            config = self.get_json_body()
            
            # Validate configuration
            errors = WSL2ConfigValidator.validate_wsl2_config(config)
            
            self.write_json({
                'success': len(errors) == 0,
                'valid': len(errors) == 0,
                'errors': errors,
                'config': config
            })
            
        except Exception as e:
            LOGGER.error(f"Error validating config: {e}")
            self.set_status(500)
            self.write_json({
                'success': False,
                'error': str(e)
            })


# URL routing patterns for WSL2 API endpoints
WSL2_URL_PATTERNS = [
    (r"/api/wsl2/instances", WSL2InstancesHandler),
    (r"/api/wsl2/projects", WSL2ProjectsHandler),
    (r"/api/wsl2/projects/([^/]+)", WSL2ProjectHandler),
    (r"/api/wsl2/projects/([^/]+)/(start|stop|restart)", WSL2ProjectActionHandler),
    (r"/api/wsl2/discovery", WSL2DiscoveryHandler),
    (r"/api/wsl2/ports", WSL2PortsHandler),
    (r"/api/wsl2/health", WSL2HealthHandler),
    (r"/api/wsl2/bulk/(start|stop)", WSL2BulkActionHandler),
    (r"/api/wsl2/config/template", WSL2ConfigTemplateHandler),
]
