"""
WSL2 Type Definitions

Defines data structures and enums for WSL2 operations.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import json


class WSL2Status(Enum):
    """WSL2 instance status enumeration"""
    RUNNING = "Running"
    STOPPED = "Stopped"
    INSTALLING = "Installing"
    CONVERTING = "Converting"
    UNKNOWN = "Unknown"


class ProjectStatus(Enum):
    """Project status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class ProjectType(Enum):
    """Supported project types"""
    NODEJS = "nodejs"
    PYTHON = "python"
    DOCKER = "docker"
    GO = "go"
    JAVA = "java"
    DOTNET = "dotnet"
    GENERIC = "generic"


@dataclass
class WSL2Instance:
    """Represents a WSL2 instance"""
    name: str
    status: WSL2Status
    version: int
    default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'version': self.version,
            'default': self.default
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WSL2Instance':
        return cls(
            name=data['name'],
            status=WSL2Status(data['status']),
            version=data['version'],
            default=data.get('default', False)
        )


@dataclass
class HealthCheck:
    """Health check configuration"""
    type: str  # 'http', 'tcp', 'command'
    url: Optional[str] = None
    port: Optional[int] = None
    command: Optional[str] = None
    interval: int = 30
    timeout: int = 10
    retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'url': self.url,
            'port': self.port,
            'command': self.command,
            'interval': self.interval,
            'timeout': self.timeout,
            'retries': self.retries
        }


@dataclass
class ProjectInfo:
    """Represents a project within a WSL2 instance"""
    id: str
    name: str
    wsl_instance: str
    path: str
    project_type: ProjectType
    status: ProjectStatus
    ports: List[int]
    start_script: Optional[str] = None
    stop_script: Optional[str] = None
    health_check: Optional[HealthCheck] = None
    environment: Optional[Dict[str, str]] = None
    dependencies: Optional[List[str]] = None
    auto_restart: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'wsl_instance': self.wsl_instance,
            'path': self.path,
            'project_type': self.project_type.value,
            'status': self.status.value,
            'ports': self.ports,
            'start_script': self.start_script,
            'stop_script': self.stop_script,
            'health_check': self.health_check.to_dict() if self.health_check else None,
            'environment': self.environment or {},
            'dependencies': self.dependencies or [],
            'auto_restart': self.auto_restart
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectInfo':
        health_check = None
        if data.get('health_check'):
            health_check = HealthCheck(**data['health_check'])
        
        return cls(
            id=data['id'],
            name=data['name'],
            wsl_instance=data['wsl_instance'],
            path=data['path'],
            project_type=ProjectType(data['project_type']),
            status=ProjectStatus(data['status']),
            ports=data['ports'],
            start_script=data.get('start_script'),
            stop_script=data.get('stop_script'),
            health_check=health_check,
            environment=data.get('environment', {}),
            dependencies=data.get('dependencies', []),
            auto_restart=data.get('auto_restart', False)
        )


@dataclass
class CommandResult:
    """Result of a WSL2 command execution"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'return_code': self.return_code
        }
