"""
WSL2 Configuration Extensions

Extends Script-Server's configuration system to support WSL2 projects.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from ..wsl2.wsl2_types import ProjectInfo, ProjectType, ProjectStatus, HealthCheck

LOGGER = logging.getLogger('config.wsl2')


class WSL2ConfigValidator:
    """Validates WSL2-specific configuration fields"""
    
    @staticmethod
    def validate_wsl2_config(config: Dict[str, Any]) -> List[str]:
        """Validate WSL2-specific configuration fields"""
        errors = []
        
        # Validate WSL instance name
        wsl_instance = config.get('wsl_instance')
        if wsl_instance:
            if not isinstance(wsl_instance, str) or not wsl_instance.strip():
                errors.append("wsl_instance must be a non-empty string")
        
        # Validate project type
        project_type = config.get('project_type')
        if project_type:
            try:
                ProjectType(project_type)
            except ValueError:
                valid_types = [t.value for t in ProjectType]
                errors.append(f"project_type must be one of: {', '.join(valid_types)}")
        
        # Validate ports
        ports = config.get('ports')
        if ports is not None:
            if not isinstance(ports, list):
                errors.append("ports must be a list")
            else:
                for port in ports:
                    if not isinstance(port, int) or port < 1 or port > 65535:
                        errors.append(f"Invalid port number: {port}")
        
        # Validate health check configuration
        health_check = config.get('health_check')
        if health_check:
            hc_errors = WSL2ConfigValidator._validate_health_check(health_check)
            errors.extend(hc_errors)
        
        # Validate environment variables
        environment = config.get('environment')
        if environment is not None:
            if not isinstance(environment, dict):
                errors.append("environment must be a dictionary")
            else:
                for key, value in environment.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        errors.append("environment variables must be string key-value pairs")
        
        # Validate dependencies
        dependencies = config.get('dependencies')
        if dependencies is not None:
            if not isinstance(dependencies, list):
                errors.append("dependencies must be a list")
            else:
                for dep in dependencies:
                    if not isinstance(dep, str):
                        errors.append("dependencies must be a list of strings")
        
        return errors
    
    @staticmethod
    def _validate_health_check(health_check: Dict[str, Any]) -> List[str]:
        """Validate health check configuration"""
        errors = []
        
        hc_type = health_check.get('type')
        if not hc_type:
            errors.append("health_check.type is required")
        elif hc_type not in ['http', 'tcp', 'command']:
            errors.append("health_check.type must be 'http', 'tcp', or 'command'")
        
        if hc_type == 'http':
            url = health_check.get('url')
            if not url or not isinstance(url, str):
                errors.append("health_check.url is required for HTTP health checks")
        
        elif hc_type == 'tcp':
            port = health_check.get('port')
            if not port or not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("health_check.port is required for TCP health checks")
        
        elif hc_type == 'command':
            command = health_check.get('command')
            if not command or not isinstance(command, str):
                errors.append("health_check.command is required for command health checks")
        
        # Validate optional fields
        interval = health_check.get('interval')
        if interval is not None and (not isinstance(interval, int) or interval < 1):
            errors.append("health_check.interval must be a positive integer")
        
        timeout = health_check.get('timeout')
        if timeout is not None and (not isinstance(timeout, int) or timeout < 1):
            errors.append("health_check.timeout must be a positive integer")
        
        retries = health_check.get('retries')
        if retries is not None and (not isinstance(retries, int) or retries < 0):
            errors.append("health_check.retries must be a non-negative integer")
        
        return errors


def enhance_script_config_for_wsl2(config: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance a standard script configuration with WSL2 project information"""
    enhanced_config = config.copy()
    
    # If this is a WSL2 project, modify the script command
    wsl_instance = config.get('wsl_instance')
    if wsl_instance:
        original_script = config.get('script', '')
        
        # If script doesn't already include WSL command, wrap it
        if not original_script.startswith('wsl '):
            working_dir = config.get('working_directory', '')
            
            if working_dir:
                # Convert Windows WSL path to Linux path if needed
                if working_dir.startswith('\\\\wsl$\\'):
                    # Extract Linux path from \\wsl$\instance\path
                    path_parts = working_dir[7:].split('\\')
                    if len(path_parts) > 1:
                        linux_path = '/' + '/'.join(path_parts[1:])
                        enhanced_config['wsl_working_directory'] = linux_path
                
                enhanced_config['script'] = f"wsl -d {wsl_instance} -e bash -c 'cd {enhanced_config.get('wsl_working_directory', working_dir)} && {original_script}'"
            else:
                enhanced_config['script'] = f"wsl -d {wsl_instance} -e bash -c '{original_script}'"
    
    return enhanced_config


def create_wsl2_project_config(project_info: ProjectInfo) -> Dict[str, Any]:
    """Create a Script-Server configuration from ProjectInfo"""
    config = {
        'name': project_info.name,
        'script': project_info.start_script or './start.sh',
        'description': f"WSL2 project: {project_info.name} ({project_info.project_type.value})",
        'working_directory': project_info.path,
        
        # WSL2-specific fields
        'wsl_instance': project_info.wsl_instance,
        'project_type': project_info.project_type.value,
        'ports': project_info.ports,
        'environment': project_info.environment,
        'dependencies': project_info.dependencies,
        'auto_restart': project_info.auto_restart,
        
        # Script-Server specific fields
        'requires_terminal': True,  # WSL2 projects typically need terminal
        'include_script_folder': True,
        'allowed_users': [],  # Can be configured per project
        'admin_users': [],
        
        # Output configuration
        'output_files': [],
        'bash_formatting': True,
        'ansi_enabled': True
    }
    
    # Add health check configuration
    if project_info.health_check:
        config['health_check'] = project_info.health_check.to_dict()
    
    # Add stop script if available
    if project_info.stop_script:
        config['stop_script'] = project_info.stop_script
    
    # Set parameters for environment variables
    if project_info.environment:
        parameters = []
        for key, default_value in project_info.environment.items():
            parameters.append({
                'name': key,
                'description': f'Environment variable: {key}',
                'type': 'text',
                'default': default_value,
                'required': False
            })
        config['parameters'] = parameters
    
    return config


def extract_wsl2_info_from_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract WSL2-specific information from a configuration"""
    wsl2_info = {}
    
    # Check if this is a WSL2 configuration
    if not config.get('wsl_instance'):
        return None
    
    wsl2_fields = [
        'wsl_instance', 'project_type', 'ports', 'health_check',
        'environment', 'dependencies', 'auto_restart'
    ]
    
    for field in wsl2_fields:
        if field in config:
            wsl2_info[field] = config[field]
    
    return wsl2_info if wsl2_info else None


def is_wsl2_config(config: Dict[str, Any]) -> bool:
    """Check if a configuration is for a WSL2 project"""
    return bool(config.get('wsl_instance'))


def get_wsl2_config_template() -> Dict[str, Any]:
    """Get a template for WSL2 project configuration"""
    return {
        'name': 'My WSL2 Project',
        'description': 'WSL2 project description',
        'script': './start.sh',
        'working_directory': '/home/user/project',
        
        # WSL2-specific fields
        'wsl_instance': 'Ubuntu',
        'project_type': 'nodejs',
        'ports': [3000],
        'environment': {
            'NODE_ENV': 'development',
            'PORT': '3000'
        },
        'dependencies': [],
        'auto_restart': False,
        'health_check': {
            'type': 'http',
            'url': 'http://localhost:3000',
            'interval': 30,
            'timeout': 10,
            'retries': 3
        },
        
        # Script-Server fields
        'requires_terminal': True,
        'include_script_folder': True,
        'bash_formatting': True,
        'ansi_enabled': True,
        'parameters': [
            {
                'name': 'NODE_ENV',
                'description': 'Node.js environment',
                'type': 'list',
                'values': ['development', 'production', 'test'],
                'default': 'development'
            }
        ]
    }


class WSL2ConfigMigrator:
    """Handles migration of existing configurations to WSL2 format"""
    
    @staticmethod
    def can_migrate_to_wsl2(config: Dict[str, Any]) -> bool:
        """Check if a configuration can be migrated to WSL2 format"""
        script = config.get('script', '')
        working_dir = config.get('working_directory', '')
        
        # Check if script already uses WSL
        if script.startswith('wsl '):
            return True
        
        # Check if working directory is a WSL path
        if working_dir.startswith('\\\\wsl$\\'):
            return True
        
        return False
    
    @staticmethod
    def migrate_to_wsl2(config: Dict[str, Any], wsl_instance: str) -> Dict[str, Any]:
        """Migrate an existing configuration to WSL2 format"""
        migrated_config = config.copy()
        
        # Add WSL2 fields
        migrated_config['wsl_instance'] = wsl_instance
        migrated_config['project_type'] = 'generic'
        migrated_config['ports'] = []
        migrated_config['environment'] = {}
        migrated_config['dependencies'] = []
        migrated_config['auto_restart'] = False
        
        # Extract WSL instance from existing script if present
        script = config.get('script', '')
        if script.startswith('wsl -d '):
            # Extract instance name from existing WSL command
            parts = script.split()
            if len(parts) >= 3:
                existing_instance = parts[2]
                migrated_config['wsl_instance'] = existing_instance
        
        # Convert working directory if it's a WSL path
        working_dir = config.get('working_directory', '')
        if working_dir.startswith('\\\\wsl$\\'):
            # Convert to Linux path
            path_parts = working_dir[7:].split('\\')
            if len(path_parts) > 1:
                linux_path = '/' + '/'.join(path_parts[1:])
                migrated_config['working_directory'] = linux_path
        
        return migrated_config
