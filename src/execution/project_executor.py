"""
Project Execution Integration

Integrates WSL2 project execution with Script-Server's execution service.
"""

import logging
from typing import Dict, Any, Optional
from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, ProjectStatus
from ..model.wsl2_model import wsl2_project_model
from .wsl2_executor import WSL2ProjectExecutor
from ..config.wsl2_config import is_wsl2_config, extract_wsl2_info_from_config

LOGGER = logging.getLogger('execution.project')


class ProjectExecutionService:
    """Service that integrates WSL2 project execution with Script-Server"""
    
    def __init__(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self.wsl2_executor = WSL2ProjectExecutor(wsl2_service)
        
    def can_handle_config(self, config: Dict[str, Any]) -> bool:
        """Check if this service can handle the given configuration"""
        return is_wsl2_config(config)
    
    def start_project_from_config(self, config: Dict[str, Any], user_name: str = None) -> Dict[str, Any]:
        """Start a project from a Script-Server configuration"""
        try:
            # Extract WSL2 information from config
            wsl2_info = extract_wsl2_info_from_config(config)
            if not wsl2_info:
                return {
                    'success': False,
                    'message': 'Configuration is not a WSL2 project',
                    'error': 'Missing WSL2 configuration fields'
                }
            
            # Find or create project info
            project_info = self._get_project_from_config(config)
            if not project_info:
                return {
                    'success': False,
                    'message': 'Failed to create project from configuration',
                    'error': 'Invalid project configuration'
                }
            
            # Start the project
            return self.wsl2_executor.start_project(project_info, user_name)
            
        except Exception as e:
            LOGGER.error(f"Error starting project from config: {e}")
            return {
                'success': False,
                'message': f'Error starting project: {str(e)}',
                'error': str(e)
            }
    
    def stop_project_from_config(self, config: Dict[str, Any], user_name: str = None) -> Dict[str, Any]:
        """Stop a project from a Script-Server configuration"""
        try:
            # Find project info
            project_info = self._get_project_from_config(config)
            if not project_info:
                return {
                    'success': False,
                    'message': 'Project not found',
                    'error': 'Cannot find project from configuration'
                }
            
            # Stop the project
            return self.wsl2_executor.stop_project(project_info, user_name)
            
        except Exception as e:
            LOGGER.error(f"Error stopping project from config: {e}")
            return {
                'success': False,
                'message': f'Error stopping project: {str(e)}',
                'error': str(e)
            }
    
    def get_project_status_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get project status from a Script-Server configuration"""
        try:
            # Find project info
            project_info = self._get_project_from_config(config)
            if not project_info:
                return {
                    'success': False,
                    'message': 'Project not found',
                    'error': 'Cannot find project from configuration'
                }
            
            # Get project status
            return self.wsl2_executor.get_project_status(project_info)
            
        except Exception as e:
            LOGGER.error(f"Error getting project status from config: {e}")
            return {
                'success': False,
                'message': f'Error getting project status: {str(e)}',
                'error': str(e)
            }
    
    def _get_project_from_config(self, config: Dict[str, Any]) -> Optional[ProjectInfo]:
        """Get or create ProjectInfo from Script-Server configuration"""
        try:
            # Try to find existing project by name and instance
            project_name = config.get('name')
            wsl_instance = config.get('wsl_instance')
            
            if not project_name or not wsl_instance:
                LOGGER.error("Missing project name or WSL instance in configuration")
                return None
            
            # Look for existing project
            existing_project = wsl2_project_model.get_project_by_name(project_name, wsl_instance)
            if existing_project:
                return existing_project
            
            # Create new project from configuration
            return self._create_project_from_config(config)
            
        except Exception as e:
            LOGGER.error(f"Error getting project from config: {e}")
            return None
    
    def _create_project_from_config(self, config: Dict[str, Any]) -> Optional[ProjectInfo]:
        """Create a new ProjectInfo from Script-Server configuration"""
        try:
            from ..wsl2.wsl2_types import ProjectType, HealthCheck
            import uuid
            
            # Extract required fields
            project_name = config.get('name')
            wsl_instance = config.get('wsl_instance')
            working_directory = config.get('working_directory', '/tmp')
            
            if not all([project_name, wsl_instance]):
                LOGGER.error("Missing required fields for project creation")
                return None
            
            # Extract optional fields
            project_type_str = config.get('project_type', 'generic')
            try:
                project_type = ProjectType(project_type_str)
            except ValueError:
                project_type = ProjectType.GENERIC
            
            ports = config.get('ports', [])
            environment = config.get('environment', {})
            dependencies = config.get('dependencies', [])
            auto_restart = config.get('auto_restart', False)
            
            # Create health check if configured
            health_check = None
            hc_config = config.get('health_check')
            if hc_config:
                health_check = HealthCheck(
                    type=hc_config.get('type', 'http'),
                    url=hc_config.get('url'),
                    port=hc_config.get('port'),
                    command=hc_config.get('command'),
                    interval=hc_config.get('interval', 30),
                    timeout=hc_config.get('timeout', 10),
                    retries=hc_config.get('retries', 3)
                )
            
            # Generate project ID
            project_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{wsl_instance}:{working_directory}"))
            
            # Create ProjectInfo
            project_info = ProjectInfo(
                id=project_id,
                name=project_name,
                wsl_instance=wsl_instance,
                path=working_directory,
                project_type=project_type,
                status=ProjectStatus.STOPPED,
                ports=ports,
                start_script=config.get('script', './start.sh'),
                stop_script=config.get('stop_script'),
                health_check=health_check,
                environment=environment,
                dependencies=dependencies,
                auto_restart=auto_restart
            )
            
            # Add to model
            wsl2_project_model.add_project(project_info)
            
            LOGGER.info(f"Created new project from config: {project_name}")
            return project_info
            
        except Exception as e:
            LOGGER.error(f"Error creating project from config: {e}")
            return None
    
    def get_all_project_statuses(self) -> Dict[str, Any]:
        """Get status of all WSL2 projects"""
        try:
            all_projects = wsl2_project_model.get_all_projects()
            project_statuses = {}
            
            for project in all_projects:
                status_info = self.wsl2_executor.get_project_status(project)
                project_statuses[project.id] = status_info
            
            return {
                'success': True,
                'total_projects': len(all_projects),
                'projects': project_statuses
            }
            
        except Exception as e:
            LOGGER.error(f"Error getting all project statuses: {e}")
            return {
                'success': False,
                'message': f'Error getting project statuses: {str(e)}',
                'error': str(e)
            }
    
    def bulk_start_projects(self, instance_name: str = None, project_type: str = None) -> Dict[str, Any]:
        """Start multiple projects based on filters"""
        try:
            # Get projects to start
            filters = {}
            if instance_name:
                filters['instance'] = instance_name
            if project_type:
                filters['type'] = project_type
            
            projects = wsl2_project_model.find_projects(**filters)
            
            # Filter to only stopped projects
            stopped_projects = [p for p in projects if p.status == ProjectStatus.STOPPED]
            
            results = {}
            success_count = 0
            
            for project in stopped_projects:
                result = self.wsl2_executor.start_project(project)
                results[project.id] = result
                if result['success']:
                    success_count += 1
            
            return {
                'success': True,
                'message': f'Started {success_count} of {len(stopped_projects)} projects',
                'total_projects': len(stopped_projects),
                'successful_starts': success_count,
                'results': results
            }
            
        except Exception as e:
            LOGGER.error(f"Error bulk starting projects: {e}")
            return {
                'success': False,
                'message': f'Error bulk starting projects: {str(e)}',
                'error': str(e)
            }
    
    def bulk_stop_projects(self, instance_name: str = None, project_type: str = None) -> Dict[str, Any]:
        """Stop multiple projects based on filters"""
        try:
            # Get projects to stop
            filters = {}
            if instance_name:
                filters['instance'] = instance_name
            if project_type:
                filters['type'] = project_type
            
            projects = wsl2_project_model.find_projects(**filters)
            
            # Filter to only running projects
            running_projects = [p for p in projects if p.status == ProjectStatus.RUNNING]
            
            results = {}
            success_count = 0
            
            for project in running_projects:
                result = self.wsl2_executor.stop_project(project)
                results[project.id] = result
                if result['success']:
                    success_count += 1
            
            return {
                'success': True,
                'message': f'Stopped {success_count} of {len(running_projects)} projects',
                'total_projects': len(running_projects),
                'successful_stops': success_count,
                'results': results
            }
            
        except Exception as e:
            LOGGER.error(f"Error bulk stopping projects: {e}")
            return {
                'success': False,
                'message': f'Error bulk stopping projects: {str(e)}',
                'error': str(e)
            }
    
    def restart_failed_projects(self) -> Dict[str, Any]:
        """Restart projects that are in error state"""
        try:
            error_projects = wsl2_project_model.get_projects_by_status(ProjectStatus.ERROR)
            
            results = {}
            success_count = 0
            
            for project in error_projects:
                result = self.wsl2_executor.restart_project(project)
                results[project.id] = result
                if result['success']:
                    success_count += 1
            
            return {
                'success': True,
                'message': f'Restarted {success_count} of {len(error_projects)} failed projects',
                'total_projects': len(error_projects),
                'successful_restarts': success_count,
                'results': results
            }
            
        except Exception as e:
            LOGGER.error(f"Error restarting failed projects: {e}")
            return {
                'success': False,
                'message': f'Error restarting failed projects: {str(e)}',
                'error': str(e)
            }
