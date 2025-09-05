"""
WSL2 Command Execution Module

Handles low-level WSL2 command execution and output parsing.
"""

import subprocess
import re
import logging
from typing import List, Dict, Optional, Tuple
from .wsl2_types import WSL2Instance, WSL2Status, CommandResult

LOGGER = logging.getLogger('wsl2.commands')


class WSL2Commands:
    """Low-level WSL2 command execution and parsing"""
    
    @staticmethod
    def execute_command(command: List[str], timeout: int = 30) -> CommandResult:
        """Execute a command and return structured result"""
        try:
            LOGGER.debug(f"Executing command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            success = result.returncode == 0
            
            LOGGER.debug(f"Command result: success={success}, return_code={result.returncode}")
            if result.stdout:
                LOGGER.debug(f"STDOUT: {result.stdout[:200]}...")
            if result.stderr:
                LOGGER.debug(f"STDERR: {result.stderr[:200]}...")
            
            return CommandResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            LOGGER.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1
            )
        except Exception as e:
            LOGGER.error(f"Error executing command: {e}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1
            )
    
    @classmethod
    def list_instances(cls) -> CommandResult:
        """List all WSL2 instances with verbose output"""
        return cls.execute_command(['wsl', '--list', '--verbose'])
    
    @classmethod
    def get_instance_status(cls, instance_name: str) -> CommandResult:
        """Get status of specific WSL2 instance"""
        return cls.execute_command(['wsl', '--list', '--verbose'])
    
    @classmethod
    def start_instance(cls, instance_name: str) -> CommandResult:
        """Start a WSL2 instance"""
        return cls.execute_command(['wsl', '--distribution', instance_name, '--exec', 'echo', 'started'])
    
    @classmethod
    def stop_instance(cls, instance_name: str) -> CommandResult:
        """Stop a WSL2 instance"""
        return cls.execute_command(['wsl', '--terminate', instance_name])
    
    @classmethod
    def execute_in_instance(cls, instance_name: str, command: str, working_dir: Optional[str] = None) -> CommandResult:
        """Execute a command within a specific WSL2 instance"""
        wsl_command = ['wsl', '--distribution', instance_name]
        
        if working_dir:
            # Change to working directory and execute command
            full_command = f"cd '{working_dir}' && {command}"
            wsl_command.extend(['--exec', 'bash', '-c', full_command])
        else:
            wsl_command.extend(['--exec', 'bash', '-c', command])
        
        return cls.execute_command(wsl_command)
    
    @classmethod
    def get_file_content(cls, instance_name: str, file_path: str) -> CommandResult:
        """Get content of a file from WSL2 instance"""
        command = f"cat '{file_path}'"
        return cls.execute_in_instance(instance_name, command)
    
    @classmethod
    def list_directory(cls, instance_name: str, directory_path: str) -> CommandResult:
        """List directory contents in WSL2 instance"""
        command = f"ls -la '{directory_path}'"
        return cls.execute_in_instance(instance_name, command)
    
    @classmethod
    def check_file_exists(cls, instance_name: str, file_path: str) -> CommandResult:
        """Check if file exists in WSL2 instance"""
        command = f"test -f '{file_path}' && echo 'exists' || echo 'not_found'"
        return cls.execute_in_instance(instance_name, command)
    
    @classmethod
    def check_directory_exists(cls, instance_name: str, directory_path: str) -> CommandResult:
        """Check if directory exists in WSL2 instance"""
        command = f"test -d '{directory_path}' && echo 'exists' || echo 'not_found'"
        return cls.execute_in_instance(instance_name, command)
    
    @classmethod
    def get_process_list(cls, instance_name: str) -> CommandResult:
        """Get list of running processes in WSL2 instance"""
        command = "ps aux"
        return cls.execute_in_instance(instance_name, command)
    
    @classmethod
    def check_port_usage(cls, instance_name: str, port: int) -> CommandResult:
        """Check if a port is in use in WSL2 instance"""
        command = f"netstat -tuln | grep ':{port}' || echo 'port_free'"
        return cls.execute_in_instance(instance_name, command)
    
    @classmethod
    def get_system_info(cls, instance_name: str) -> CommandResult:
        """Get system information from WSL2 instance"""
        command = "uname -a && cat /etc/os-release"
        return cls.execute_in_instance(instance_name, command)


class WSL2Parser:
    """Parser for WSL2 command outputs"""
    
    @staticmethod
    def parse_instance_list(output: str) -> List[WSL2Instance]:
        """Parse wsl --list --verbose output into WSL2Instance objects"""
        instances = []
        lines = output.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            
            # Parse line format: "  NAME                   STATE           VERSION"
            # Handle potential Unicode characters and extra spaces
            line = line.strip()
            if not line:
                continue
            
            # Split by whitespace, handling multiple spaces
            parts = re.split(r'\s+', line)
            if len(parts) < 3:
                continue
            
            name = parts[0].strip('*').strip()  # Remove default marker
            status_str = parts[1]
            version_str = parts[2]
            
            # Determine if this is the default instance
            is_default = line.strip().startswith('*')
            
            # Parse status
            try:
                status = WSL2Status(status_str)
            except ValueError:
                LOGGER.warning(f"Unknown WSL2 status: {status_str}")
                status = WSL2Status.UNKNOWN
            
            # Parse version
            try:
                version = int(version_str)
            except ValueError:
                LOGGER.warning(f"Invalid version number: {version_str}")
                version = 2  # Default to WSL2
            
            instances.append(WSL2Instance(
                name=name,
                status=status,
                version=version,
                default=is_default
            ))
        
        return instances
    
    @staticmethod
    def parse_port_check(output: str) -> bool:
        """Parse port check output to determine if port is in use"""
        return 'port_free' not in output.lower()
    
    @staticmethod
    def parse_file_exists(output: str) -> bool:
        """Parse file existence check output"""
        return 'exists' in output.strip()
    
    @staticmethod
    def parse_process_list(output: str) -> List[Dict[str, str]]:
        """Parse ps aux output into process information"""
        processes = []
        lines = output.strip().split('\n')
        
        if len(lines) < 2:
            return processes
        
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            
            # Parse ps aux format
            parts = line.split(None, 10)  # Split into max 11 parts
            if len(parts) >= 11:
                processes.append({
                    'user': parts[0],
                    'pid': parts[1],
                    'cpu': parts[2],
                    'mem': parts[3],
                    'vsz': parts[4],
                    'rss': parts[5],
                    'tty': parts[6],
                    'stat': parts[7],
                    'start': parts[8],
                    'time': parts[9],
                    'command': parts[10]
                })
        
        return processes
