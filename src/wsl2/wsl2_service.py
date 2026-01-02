"""
WSL2 Service Layer

High-level WSL2 operations and instance management.
"""

import logging
import os
import time
from typing import List, Dict, Optional, Tuple
from .wsl2_commands import WSL2Commands, WSL2Parser
from .wsl2_types import WSL2Instance, WSL2Status, ProjectInfo, ProjectStatus, CommandResult

LOGGER = logging.getLogger('wsl2.service')


class WSL2Service:
    """High-level WSL2 service for instance and project management"""
    
    def __init__(self):
        self.commands = WSL2Commands()
        self.parser = WSL2Parser()
        self._instance_cache = {}
        self._cache_timeout = 30  # seconds
        
    def get_instances(self, use_cache: bool = True) -> List[WSL2Instance]:
        """Get list of all WSL2 instances"""
        cache_key = 'instances'
        current_time = time.time()
        
        # Check cache
        if use_cache and cache_key in self._instance_cache:
            cached_data, timestamp = self._instance_cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                LOGGER.debug("Returning cached WSL2 instances")
                return cached_data
        
        LOGGER.info("Fetching WSL2 instances")
        result = self.commands.list_instances()
        
        if not result.success:
            LOGGER.error(f"Failed to list WSL2 instances: {result.stderr}")
            return []
        
        instances = self.parser.parse_instance_list(result.stdout)
        
        # Update cache
        self._instance_cache[cache_key] = (instances, current_time)
        
        LOGGER.info(f"Found {len(instances)} WSL2 instances")
        return instances
    
    def get_instance(self, name: str) -> Optional[WSL2Instance]:
        """Get specific WSL2 instance by name"""
        instances = self.get_instances()
        for instance in instances:
            if instance.name == name:
                return instance
        return None
    
    def is_instance_running(self, name: str) -> bool:
        """Check if WSL2 instance is running"""
        instance = self.get_instance(name)
        return instance is not None and instance.status == WSL2Status.RUNNING
    
    def start_instance(self, name: str) -> bool:
        """Start a WSL2 instance"""
        LOGGER.info(f"Starting WSL2 instance: {name}")
        
        # Check if already running
        if self.is_instance_running(name):
            LOGGER.info(f"WSL2 instance {name} is already running")
            return True
        
        result = self.commands.start_instance(name)
        
        if result.success:
            LOGGER.info(f"Successfully started WSL2 instance: {name}")
            # Clear cache to force refresh
            self._instance_cache.clear()
            return True
        else:
            LOGGER.error(f"Failed to start WSL2 instance {name}: {result.stderr}")
            return False
    
    def stop_instance(self, name: str) -> bool:
        """Stop a WSL2 instance"""
        LOGGER.info(f"Stopping WSL2 instance: {name}")
        
        result = self.commands.stop_instance(name)
        
        if result.success:
            LOGGER.info(f"Successfully stopped WSL2 instance: {name}")
            # Clear cache to force refresh
            self._instance_cache.clear()
            return True
        else:
            LOGGER.error(f"Failed to stop WSL2 instance {name}: {result.stderr}")
            return False
    
    def execute_command(self, instance_name: str, command: str, working_dir: Optional[str] = None) -> CommandResult:
        """Execute a command in a WSL2 instance"""
        LOGGER.debug(f"Executing command in {instance_name}: {command}")
        
        # Ensure instance is running
        if not self.is_instance_running(instance_name):
            LOGGER.warning(f"WSL2 instance {instance_name} is not running, attempting to start")
            if not self.start_instance(instance_name):
                return CommandResult(
                    success=False,
                    stdout="",
                    stderr=f"Failed to start WSL2 instance {instance_name}",
                    return_code=-1
                )
        
        return self.commands.execute_in_instance(instance_name, command, working_dir)
    
    def get_file_content(self, instance_name: str, file_path: str) -> Optional[str]:
        """Get content of a file from WSL2 instance"""
        result = self.commands.get_file_content(instance_name, file_path)
        
        if result.success:
            return result.stdout
        else:
            LOGGER.error(f"Failed to get file content from {instance_name}:{file_path}: {result.stderr}")
            return None
    
    def file_exists(self, instance_name: str, file_path: str) -> bool:
        """Check if file exists in WSL2 instance"""
        result = self.commands.check_file_exists(instance_name, file_path)
        
        if result.success:
            return self.parser.parse_file_exists(result.stdout)
        else:
            LOGGER.error(f"Failed to check file existence {instance_name}:{file_path}: {result.stderr}")
            return False
    
    def directory_exists(self, instance_name: str, directory_path: str) -> bool:
        """Check if directory exists in WSL2 instance"""
        result = self.commands.check_directory_exists(instance_name, directory_path)
        
        if result.success:
            return self.parser.parse_file_exists(result.stdout)
        else:
            LOGGER.error(f"Failed to check directory existence {instance_name}:{directory_path}: {result.stderr}")
            return False
    
    def list_directory(self, instance_name: str, directory_path: str) -> List[str]:
        """List directory contents in WSL2 instance"""
        result = self.commands.list_directory(instance_name, directory_path)
        
        if result.success:
            # Parse ls -la output
            lines = result.stdout.strip().split('\n')
            files = []
            for line in lines[1:]:  # Skip total line
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = ' '.join(parts[8:])  # Handle filenames with spaces
                        files.append(filename)
            return files
        else:
            LOGGER.error(f"Failed to list directory {instance_name}:{directory_path}: {result.stderr}")
            return []
    
    def is_port_in_use(self, instance_name: str, port: int) -> bool:
        """Check if port is in use in WSL2 instance"""
        result = self.commands.check_port_usage(instance_name, port)
        
        if result.success:
            return self.parser.parse_port_check(result.stdout)
        else:
            LOGGER.error(f"Failed to check port usage {instance_name}:{port}: {result.stderr}")
            return False
    
    def get_running_processes(self, instance_name: str) -> List[Dict[str, str]]:
        """Get list of running processes in WSL2 instance"""
        result = self.commands.get_process_list(instance_name)
        
        if result.success:
            return self.parser.parse_process_list(result.stdout)
        else:
            LOGGER.error(f"Failed to get process list from {instance_name}: {result.stderr}")
            return []
    
    def get_system_info(self, instance_name: str) -> Dict[str, str]:
        """Get system information from WSL2 instance"""
        result = self.commands.get_system_info(instance_name)
        
        if result.success:
            info = {}
            lines = result.stdout.strip().split('\n')
            
            # Parse uname output (first line)
            if lines:
                info['uname'] = lines[0]
            
            # Parse os-release (remaining lines)
            for line in lines[1:]:
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key.lower()] = value.strip('"')
            
            return info
        else:
            LOGGER.error(f"Failed to get system info from {instance_name}: {result.stderr}")
            return {}
    
    def get_wsl_path(self, instance_name: str, linux_path: str) -> str:
        """Convert Linux path to Windows WSL path"""
        # Convert /home/user/project to \\wsl$\instance\home\user\project
        linux_path = linux_path.lstrip('/')
        return f"\\\\wsl$\\{instance_name}\\{linux_path.replace('/', '\\')}"
    
    def get_linux_path(self, wsl_path: str) -> Tuple[str, str]:
        """Convert Windows WSL path to instance name and Linux path"""
        # Convert \\wsl$\instance\home\user\project to ('instance', '/home/user/project')
        if not wsl_path.startswith('\\\\wsl$\\'):
            raise ValueError(f"Invalid WSL path: {wsl_path}")
        
        path_parts = wsl_path[7:].split('\\')  # Remove \\wsl$\ prefix
        if len(path_parts) < 1:
            raise ValueError(f"Invalid WSL path: {wsl_path}")
        
        instance_name = path_parts[0]
        linux_path = '/' + '/'.join(path_parts[1:]) if len(path_parts) > 1 else '/'
        
        return instance_name, linux_path
    
    def clear_cache(self):
        """Clear the instance cache"""
        self._instance_cache.clear()
        LOGGER.debug("WSL2 instance cache cleared")
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on WSL2 service"""
        health = {
            'wsl_available': False,
            'instances_accessible': False
        }
        
        try:
            # Check if WSL is available
            result = self.commands.execute_command(['wsl', '--help'], timeout=10)
            health['wsl_available'] = result.success
            
            if health['wsl_available']:
                # Check if we can list instances
                instances = self.get_instances(use_cache=False)
                health['instances_accessible'] = True
                health['instance_count'] = len(instances)
                
        except Exception as e:
            LOGGER.error(f"WSL2 health check failed: {e}")
        
        return health
