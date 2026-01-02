"""
WSL2 Project Executor

Extends Script-Server's execution system to handle WSL2 project lifecycle operations.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, ProjectStatus, CommandResult
from ..model.wsl2_model import wsl2_project_model
from ..projects.project_discovery import ProjectDiscovery

LOGGER = logging.getLogger('execution.wsl2')


class WSL2ProjectExecutor:
    """Handles WSL2 project execution operations"""
    
    def __init__(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self.project_discovery = ProjectDiscovery(wsl2_service)
        self._active_executions = {}  # execution_id -> project_info
        
    def start_project(self, project_info: ProjectInfo, user_name: str = None) -> Dict[str, Any]:
        """Start a WSL2 project"""
        LOGGER.info(f"Starting WSL2 project: {project_info.name} in {project_info.wsl_instance}")
        
        try:
            # Update project status
            project_info.status = ProjectStatus.STARTING
            wsl2_project_model.update_project(project_info)
            
            # Ensure WSL2 instance is running
            if not self.wsl2_service.is_instance_running(project_info.wsl_instance):
                LOGGER.info(f"Starting WSL2 instance: {project_info.wsl_instance}")
                if not self.wsl2_service.start_instance(project_info.wsl_instance):
                    raise Exception(f"Failed to start WSL2 instance: {project_info.wsl_instance}")
            
            # Start dependencies first
            if project_info.dependencies:
                self._start_dependencies(project_info)
            
            # Check if project is already running
            if self._is_project_running(project_info):
                LOGGER.info(f"Project {project_info.name} is already running")
                project_info.status = ProjectStatus.RUNNING
                wsl2_project_model.update_project(project_info)
                return {
                    'success': True,
                    'message': f'Project {project_info.name} is already running',
                    'project_id': project_info.id,
                    'status': project_info.status.value
                }
            
            # Generate start script if needed
            if not project_info.start_script or not self.wsl2_service.file_exists(
                project_info.wsl_instance, 
                f"{project_info.path}/{project_info.start_script}"
            ):
                self._generate_start_script(project_info)
            
            # Execute start command
            start_command = self._get_start_command(project_info)
            result = self.wsl2_service.execute_command(
                project_info.wsl_instance,
                start_command,
                project_info.path
            )
            
            if result.success:
                # Wait a moment for the process to start
                time.sleep(2)
                
                # Verify the project started successfully
                if self._is_project_running(project_info):
                    project_info.status = ProjectStatus.RUNNING
                    LOGGER.info(f"Successfully started project: {project_info.name}")
                    
                    # Generate execution ID for tracking
                    execution_id = f"wsl2-{project_info.id}-{int(time.time())}"
                    self._active_executions[execution_id] = project_info
                    
                    return {
                        'success': True,
                        'message': f'Project {project_info.name} started successfully',
                        'project_id': project_info.id,
                        'execution_id': execution_id,
                        'status': project_info.status.value,
                        'ports': project_info.ports,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
                else:
                    project_info.status = ProjectStatus.ERROR
                    return {
                        'success': False,
                        'message': f'Project {project_info.name} failed to start properly',
                        'project_id': project_info.id,
                        'status': project_info.status.value,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                project_info.status = ProjectStatus.ERROR
                LOGGER.error(f"Failed to start project {project_info.name}: {result.stderr}")
                return {
                    'success': False,
                    'message': f'Failed to start project {project_info.name}',
                    'project_id': project_info.id,
                    'status': project_info.status.value,
                    'error': result.stderr,
                    'stdout': result.stdout
                }
                
        except Exception as e:
            project_info.status = ProjectStatus.ERROR
            LOGGER.error(f"Error starting project {project_info.name}: {e}")
            return {
                'success': False,
                'message': f'Error starting project {project_info.name}: {str(e)}',
                'project_id': project_info.id,
                'status': project_info.status.value,
                'error': str(e)
            }
        finally:
            wsl2_project_model.update_project(project_info)
    
    def stop_project(self, project_info: ProjectInfo, user_name: str = None) -> Dict[str, Any]:
        """Stop a WSL2 project"""
        LOGGER.info(f"Stopping WSL2 project: {project_info.name} in {project_info.wsl_instance}")
        
        try:
            # Update project status
            project_info.status = ProjectStatus.STOPPING
            wsl2_project_model.update_project(project_info)
            
            # Check if project is actually running
            if not self._is_project_running(project_info):
                LOGGER.info(f"Project {project_info.name} is not running")
                project_info.status = ProjectStatus.STOPPED
                wsl2_project_model.update_project(project_info)
                return {
                    'success': True,
                    'message': f'Project {project_info.name} is already stopped',
                    'project_id': project_info.id,
                    'status': project_info.status.value
                }
            
            # Execute stop command
            stop_command = self._get_stop_command(project_info)
            result = self.wsl2_service.execute_command(
                project_info.wsl_instance,
                stop_command,
                project_info.path
            )
            
            # Wait a moment for the process to stop
            time.sleep(2)
            
            # Verify the project stopped
            if not self._is_project_running(project_info):
                project_info.status = ProjectStatus.STOPPED
                LOGGER.info(f"Successfully stopped project: {project_info.name}")
                
                # Remove from active executions
                execution_ids_to_remove = [
                    eid for eid, proj in self._active_executions.items() 
                    if proj.id == project_info.id
                ]
                for eid in execution_ids_to_remove:
                    del self._active_executions[eid]
                
                return {
                    'success': True,
                    'message': f'Project {project_info.name} stopped successfully',
                    'project_id': project_info.id,
                    'status': project_info.status.value,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                # Force kill if still running
                LOGGER.warning(f"Project {project_info.name} still running, attempting force stop")
                force_result = self._force_stop_project(project_info)
                
                if force_result['success']:
                    project_info.status = ProjectStatus.STOPPED
                    return force_result
                else:
                    project_info.status = ProjectStatus.ERROR
                    return force_result
                    
        except Exception as e:
            project_info.status = ProjectStatus.ERROR
            LOGGER.error(f"Error stopping project {project_info.name}: {e}")
            return {
                'success': False,
                'message': f'Error stopping project {project_info.name}: {str(e)}',
                'project_id': project_info.id,
                'status': project_info.status.value,
                'error': str(e)
            }
        finally:
            wsl2_project_model.update_project(project_info)
    
    def restart_project(self, project_info: ProjectInfo, user_name: str = None) -> Dict[str, Any]:
        """Restart a WSL2 project"""
        LOGGER.info(f"Restarting WSL2 project: {project_info.name}")
        
        # Stop the project first
        stop_result = self.stop_project(project_info, user_name)
        
        if not stop_result['success']:
            return {
                'success': False,
                'message': f'Failed to stop project {project_info.name} for restart',
                'project_id': project_info.id,
                'stop_result': stop_result
            }
        
        # Wait a moment between stop and start
        time.sleep(1)
        
        # Start the project
        start_result = self.start_project(project_info, user_name)
        
        return {
            'success': start_result['success'],
            'message': f'Project {project_info.name} restart {"successful" if start_result["success"] else "failed"}',
            'project_id': project_info.id,
            'status': project_info.status.value,
            'stop_result': stop_result,
            'start_result': start_result
        }
    
    def get_project_status(self, project_info: ProjectInfo) -> Dict[str, Any]:
        """Get current status of a WSL2 project"""
        try:
            # Refresh project status
            current_status = self.project_discovery.refresh_project_status(project_info)
            project_info.status = current_status
            wsl2_project_model.update_project(project_info)
            
            # Get additional status information
            port_status = {}
            for port in project_info.ports:
                port_status[port] = self.wsl2_service.is_port_in_use(project_info.wsl_instance, port)
            
            # Get process information
            processes = self._get_project_processes(project_info)
            
            return {
                'project_id': project_info.id,
                'name': project_info.name,
                'status': current_status.value,
                'instance': project_info.wsl_instance,
                'ports': project_info.ports,
                'port_status': port_status,
                'processes': processes,
                'health_check': project_info.health_check.to_dict() if project_info.health_check else None
            }
            
        except Exception as e:
            LOGGER.error(f"Error getting project status for {project_info.name}: {e}")
            return {
                'project_id': project_info.id,
                'name': project_info.name,
                'status': ProjectStatus.ERROR.value,
                'error': str(e)
            }
    
    def _is_project_running(self, project_info: ProjectInfo) -> bool:
        """Check if a project is currently running"""
        try:
            # Check if any of the project's ports are in use
            for port in project_info.ports:
                if self.wsl2_service.is_port_in_use(project_info.wsl_instance, port):
                    return True
            
            # If no ports configured, check for processes
            if not project_info.ports:
                processes = self._get_project_processes(project_info)
                return len(processes) > 0
            
            return False
            
        except Exception as e:
            LOGGER.error(f"Error checking if project {project_info.name} is running: {e}")
            return False
    
    def _get_start_command(self, project_info: ProjectInfo) -> str:
        """Get the command to start a project"""
        if project_info.start_script:
            # Make script executable and run it
            script_path = f"{project_info.path}/{project_info.start_script}"
            return f"chmod +x '{script_path}' && '{script_path}'"
        elif hasattr(project_info, '_generated_start_script'):
            # Use generated start command
            return project_info._generated_start_script
        else:
            # Default start command
            return "echo 'No start script configured'"
    
    def _get_stop_command(self, project_info: ProjectInfo) -> str:
        """Get the command to stop a project"""
        if project_info.stop_script:
            # Make script executable and run it
            script_path = f"{project_info.path}/{project_info.stop_script}"
            return f"chmod +x '{script_path}' && '{script_path}'"
        elif hasattr(project_info, '_generated_stop_script'):
            # Use generated stop command
            return project_info._generated_stop_script
        else:
            # Default: kill processes on project ports
            if project_info.ports:
                kill_commands = []
                for port in project_info.ports:
                    kill_commands.append(f"lsof -ti:{port} | xargs -r kill -9")
                return " && ".join(kill_commands)
            else:
                return "echo 'No stop script configured'"
    
    def _force_stop_project(self, project_info: ProjectInfo) -> Dict[str, Any]:
        """Force stop a project by killing processes on its ports"""
        try:
            if not project_info.ports:
                return {
                    'success': False,
                    'message': 'Cannot force stop project without configured ports',
                    'project_id': project_info.id
                }
            
            kill_commands = []
            for port in project_info.ports:
                kill_commands.append(f"lsof -ti:{port} | xargs -r kill -9")
            
            force_command = " && ".join(kill_commands)
            result = self.wsl2_service.execute_command(
                project_info.wsl_instance,
                force_command,
                project_info.path
            )
            
            # Wait and check if stopped
            time.sleep(2)
            
            if not self._is_project_running(project_info):
                return {
                    'success': True,
                    'message': f'Project {project_info.name} force stopped successfully',
                    'project_id': project_info.id,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to force stop project {project_info.name}',
                    'project_id': project_info.id,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error force stopping project {project_info.name}: {str(e)}',
                'project_id': project_info.id,
                'error': str(e)
            }
    
    def _start_dependencies(self, project_info: ProjectInfo):
        """Start project dependencies"""
        for dep_name in project_info.dependencies:
            try:
                # Find dependency project
                dep_project = wsl2_project_model.get_project_by_name(dep_name, project_info.wsl_instance)
                
                if dep_project and dep_project.status != ProjectStatus.RUNNING:
                    LOGGER.info(f"Starting dependency: {dep_name}")
                    self.start_project(dep_project)
                    
            except Exception as e:
                LOGGER.error(f"Failed to start dependency {dep_name}: {e}")
    
    def _generate_start_script(self, project_info: ProjectInfo):
        """Generate start script for a project"""
        try:
            scripts = self.project_discovery.generate_project_scripts(project_info)
            
            if 'start.sh' in scripts:
                script_path = f"{project_info.path}/start.sh"
                
                # Write the script to the project directory
                # This would require implementing file writing to WSL2
                # For now, we'll use the generated command directly
                LOGGER.info(f"Generated start script for {project_info.name}")
                
        except Exception as e:
            LOGGER.error(f"Failed to generate start script for {project_info.name}: {e}")
    
    def _get_project_processes(self, project_info: ProjectInfo) -> List[Dict[str, str]]:
        """Get processes related to a project"""
        try:
            all_processes = self.wsl2_service.get_running_processes(project_info.wsl_instance)
            
            # Filter processes that might be related to this project
            project_processes = []
            
            for process in all_processes:
                command = process.get('command', '').lower()
                
                # Check if process is using project ports
                for port in project_info.ports:
                    if str(port) in command:
                        project_processes.append(process)
                        break
                
                # Check if process is running from project directory
                if project_info.path.lower() in command:
                    project_processes.append(process)
            
            return project_processes
            
        except Exception as e:
            LOGGER.error(f"Error getting project processes for {project_info.name}: {e}")
            return []
    
    def get_active_executions(self) -> Dict[str, ProjectInfo]:
        """Get all active project executions"""
        return self._active_executions.copy()
    
    def cleanup_execution(self, execution_id: str) -> bool:
        """Clean up a finished execution"""
        if execution_id in self._active_executions:
            del self._active_executions[execution_id]
            return True
        return False
