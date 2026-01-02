"""
Project Discovery Engine

Main orchestrator for discovering and configuring projects in WSL2 instances.
"""

import logging
import uuid
from typing import List, Dict, Optional, Any
from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, ProjectStatus, ProjectType, HealthCheck
from .project_scanner import ProjectScanner
from .project_types import ProjectTypeDetector, get_project_type_config

LOGGER = logging.getLogger('projects.discovery')


class ProjectDiscovery:
    """Main project discovery and configuration engine"""
    
    def __init__(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self.scanner = ProjectScanner(wsl2_service)
        self.type_detector = ProjectTypeDetector()
        
    def discover_projects(self, instance_name: str, force_rescan: bool = False) -> List[ProjectInfo]:
        """Discover all projects in a WSL2 instance"""
        LOGGER.info(f"Starting project discovery for WSL2 instance: {instance_name}")
        
        # Check if instance is available
        if not self.wsl2_service.is_instance_running(instance_name):
            LOGGER.warning(f"WSL2 instance '{instance_name}' is not running, attempting to start")
            if not self.wsl2_service.start_instance(instance_name):
                LOGGER.error(f"Failed to start WSL2 instance '{instance_name}'")
                return []
        
        # Scan for potential projects
        raw_projects = self.scanner.scan_instance(instance_name)
        
        if not raw_projects:
            LOGGER.info(f"No projects found in WSL2 instance '{instance_name}'")
            return []
        
        # Convert raw project data to ProjectInfo objects
        projects = []
        for raw_project in raw_projects:
            try:
                project_info = self._create_project_info(raw_project)
                if project_info:
                    projects.append(project_info)
            except Exception as e:
                LOGGER.error(f"Error processing project {raw_project.get('name', 'unknown')}: {e}")
        
        LOGGER.info(f"Successfully discovered {len(projects)} projects in '{instance_name}'")
        return projects
    
    def _create_project_info(self, raw_project: Dict[str, Any]) -> Optional[ProjectInfo]:
        """Convert raw project data to ProjectInfo object"""
        try:
            # Detect project type
            files = raw_project.get('files', [])
            file_contents = raw_project.get('file_contents', {})
            project_type = self.type_detector.detect_project_type(files, file_contents)
            
            # Generate project configuration
            project_config = get_project_type_config(
                project_type=project_type,
                project_name=raw_project['name'],
                project_path=raw_project['path'],
                file_contents=file_contents
            )
            
            # Create health check object
            health_check = None
            if project_config.get('health_check'):
                hc_config = project_config['health_check']
                health_check = HealthCheck(
                    type=hc_config['type'],
                    url=hc_config.get('url'),
                    port=hc_config.get('port'),
                    command=hc_config.get('command'),
                    interval=hc_config.get('interval', 30),
                    timeout=hc_config.get('timeout', 10),
                    retries=hc_config.get('retries', 3)
                )
            
            # Generate unique project ID
            project_id = self._generate_project_id(raw_project['instance'], raw_project['path'])
            
            # Determine initial project status
            initial_status = self._determine_project_status(raw_project['instance'], project_config)
            
            # Create ProjectInfo object
            project_info = ProjectInfo(
                id=project_id,
                name=raw_project['name'],
                wsl_instance=raw_project['instance'],
                path=raw_project['path'],
                project_type=project_type,
                status=initial_status,
                ports=project_config.get('ports', []),
                start_script=project_config.get('start_script'),
                stop_script=project_config.get('stop_script'),
                health_check=health_check,
                environment=project_config.get('environment', {}),
                dependencies=project_config.get('dependencies', []),
                auto_restart=project_config.get('auto_restart', False)
            )
            
            # Store generated scripts if any
            if project_config.get('generated_start_script'):
                project_info._generated_start_script = project_config['generated_start_script']
            if project_config.get('generated_stop_script'):
                project_info._generated_stop_script = project_config['generated_stop_script']
            
            return project_info
            
        except Exception as e:
            LOGGER.error(f"Error creating ProjectInfo for {raw_project.get('name', 'unknown')}: {e}")
            return None
    
    def _generate_project_id(self, instance_name: str, project_path: str) -> str:
        """Generate a unique project ID"""
        # Create a deterministic ID based on instance and path
        base_string = f"{instance_name}:{project_path}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, base_string))
    
    def _determine_project_status(self, instance_name: str, project_config: Dict[str, Any]) -> ProjectStatus:
        """Determine the current status of a project"""
        try:
            # Check if any of the project's ports are in use
            ports = project_config.get('ports', [])
            
            for port in ports:
                if self.wsl2_service.is_port_in_use(instance_name, port):
                    return ProjectStatus.RUNNING
            
            # If no ports are in use, assume stopped
            return ProjectStatus.STOPPED
            
        except Exception as e:
            LOGGER.error(f"Error determining project status: {e}")
            return ProjectStatus.UNKNOWN
    
    def refresh_project_status(self, project: ProjectInfo) -> ProjectStatus:
        """Refresh the status of a specific project"""
        try:
            # Check port usage
            if project.ports:
                for port in project.ports:
                    if self.wsl2_service.is_port_in_use(project.wsl_instance, port):
                        return ProjectStatus.RUNNING
            
            # Check health endpoint if available
            if project.health_check and project.health_check.type == 'http':
                # This would require HTTP client implementation
                # For now, rely on port checking
                pass
            
            return ProjectStatus.STOPPED
            
        except Exception as e:
            LOGGER.error(f"Error refreshing project status for {project.name}: {e}")
            return ProjectStatus.UNKNOWN
    
    def validate_project(self, project: ProjectInfo) -> Dict[str, Any]:
        """Validate a project configuration and structure"""
        validation = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Validate project path exists
            if not self.wsl2_service.directory_exists(project.wsl_instance, project.path):
                validation['valid'] = False
                validation['issues'].append(f"Project directory does not exist: {project.path}")
                return validation
            
            # Validate start script if specified
            if project.start_script:
                script_path = f"{project.path.rstrip('/')}/{project.start_script}"
                if not self.wsl2_service.file_exists(project.wsl_instance, script_path):
                    validation['warnings'].append(f"Start script not found: {project.start_script}")
                    validation['recommendations'].append("Create start script or update configuration")
            
            # Validate stop script if specified
            if project.stop_script:
                script_path = f"{project.path.rstrip('/')}/{project.stop_script}"
                if not self.wsl2_service.file_exists(project.wsl_instance, script_path):
                    validation['warnings'].append(f"Stop script not found: {project.stop_script}")
                    validation['recommendations'].append("Create stop script or update configuration")
            
            # Validate port configuration
            if not project.ports:
                validation['warnings'].append("No ports configured for project")
                validation['recommendations'].append("Configure ports for proper monitoring")
            
            # Check for port conflicts with other projects
            # This would require a project registry to check against
            
            # Validate health check configuration
            if project.health_check:
                if project.health_check.type == 'http' and not project.health_check.url:
                    validation['issues'].append("HTTP health check configured but no URL provided")
                    validation['valid'] = False
                elif project.health_check.type == 'tcp' and not project.health_check.port:
                    validation['issues'].append("TCP health check configured but no port provided")
                    validation['valid'] = False
            
            # Use scanner to validate project structure
            structure_validation = self.scanner.validate_project_structure(
                project.wsl_instance, 
                project.path
            )
            
            if structure_validation.get('issues'):
                validation['issues'].extend(structure_validation['issues'])
            
            if structure_validation.get('recommendations'):
                validation['recommendations'].extend(structure_validation['recommendations'])
            
            if not structure_validation.get('valid', True):
                validation['valid'] = False
            
        except Exception as e:
            validation['valid'] = False
            validation['issues'].append(f"Error validating project: {e}")
        
        return validation
    
    def generate_project_scripts(self, project: ProjectInfo) -> Dict[str, str]:
        """Generate start/stop scripts for a project"""
        scripts = {}
        
        try:
            # Generate start script
            if hasattr(project, '_generated_start_script'):
                start_content = self._create_start_script(
                    project._generated_start_script,
                    project.environment
                )
                scripts['start.sh'] = start_content
            
            # Generate stop script
            if hasattr(project, '_generated_stop_script'):
                stop_content = self._create_stop_script(
                    project._generated_stop_script,
                    project.ports
                )
                scripts['stop.sh'] = stop_content
            elif project.ports:
                # Generate generic stop script based on ports
                stop_content = self._create_generic_stop_script(project.ports)
                scripts['stop.sh'] = stop_content
            
        except Exception as e:
            LOGGER.error(f"Error generating scripts for project {project.name}: {e}")
        
        return scripts
    
    def _create_start_script(self, command: str, environment: Dict[str, str]) -> str:
        """Create a start script with environment variables"""
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated start script",
            "",
            "set -e",  # Exit on error
            ""
        ]
        
        # Add environment variables
        for key, value in environment.items():
            script_lines.append(f"export {key}='{value}'")
        
        if environment:
            script_lines.append("")
        
        # Add the main command
        script_lines.extend([
            "echo 'Starting project...'",
            f"{command}",
            ""
        ])
        
        return "\n".join(script_lines)
    
    def _create_stop_script(self, command: str, ports: List[int]) -> str:
        """Create a stop script"""
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated stop script",
            "",
            "set -e",
            "",
            "echo 'Stopping project...'",
            f"{command}",
            ""
        ]
        
        return "\n".join(script_lines)
    
    def _create_generic_stop_script(self, ports: List[int]) -> str:
        """Create a generic stop script that kills processes on specified ports"""
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated generic stop script",
            "",
            "echo 'Stopping project by killing processes on ports...'",
            ""
        ]
        
        for port in ports:
            script_lines.extend([
                f"# Kill process on port {port}",
                f"PID=$(lsof -ti:{port} 2>/dev/null || true)",
                "if [ ! -z \"$PID\" ]; then",
                f"    echo 'Killing process on port {port} (PID: $PID)'",
                "    kill $PID",
                "    sleep 1",
                "    # Force kill if still running",
                f"    if kill -0 $PID 2>/dev/null; then",
                "        echo 'Force killing process'",
                "        kill -9 $PID",
                "    fi",
                "else",
                f"    echo 'No process found on port {port}'",
                "fi",
                ""
            ])
        
        script_lines.append("echo 'Project stopped'")
        
        return "\n".join(script_lines)
    
    def get_discovery_summary(self, instance_name: str) -> Dict[str, Any]:
        """Get a summary of project discovery results"""
        try:
            projects = self.discover_projects(instance_name)
            
            # Count projects by type
            type_counts = {}
            status_counts = {}
            
            for project in projects:
                project_type = project.project_type.value
                type_counts[project_type] = type_counts.get(project_type, 0) + 1
                
                status = project.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'instance_name': instance_name,
                'total_projects': len(projects),
                'project_types': type_counts,
                'project_statuses': status_counts,
                'projects': [p.to_dict() for p in projects]
            }
            
        except Exception as e:
            LOGGER.error(f"Error generating discovery summary for {instance_name}: {e}")
            return {
                'instance_name': instance_name,
                'total_projects': 0,
                'error': str(e)
            }
