"""
Project Type Detection and Configuration

Handles detection of different project types and their default configurations.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from ..wsl2.wsl2_types import ProjectType, HealthCheck

LOGGER = logging.getLogger('projects.types')


class ProjectTypeDetector:
    """Detects project types based on file patterns and content"""
    
    # File patterns for project type detection
    TYPE_PATTERNS = {
        ProjectType.NODEJS: [
            'package.json',
            'yarn.lock',
            'package-lock.json',
            'node_modules',
            '.nvmrc'
        ],
        ProjectType.PYTHON: [
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            'Pipfile',
            'environment.yml',
            'conda.yml',
            '.python-version',
            'main.py',
            'app.py',
            'manage.py'  # Django
        ],
        ProjectType.DOCKER: [
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.yaml',
            '.dockerignore'
        ],
        ProjectType.GO: [
            'go.mod',
            'go.sum',
            'main.go',
            'Gopkg.toml',
            'Gopkg.lock'
        ],
        ProjectType.JAVA: [
            'pom.xml',
            'build.gradle',
            'gradle.properties',
            'gradlew',
            'mvnw',
            'src/main/java'
        ],
        ProjectType.DOTNET: [
            '*.csproj',
            '*.sln',
            '*.fsproj',
            '*.vbproj',
            'global.json',
            'nuget.config'
        ]
    }
    
    # Priority order for type detection (higher index = higher priority)
    TYPE_PRIORITY = [
        ProjectType.GENERIC,
        ProjectType.JAVA,
        ProjectType.DOTNET,
        ProjectType.GO,
        ProjectType.PYTHON,
        ProjectType.NODEJS,
        ProjectType.DOCKER  # Docker has highest priority as it can contain other types
    ]
    
    @classmethod
    def detect_project_type(cls, files: List[str], file_contents: Dict[str, str] = None) -> ProjectType:
        """Detect project type based on files and their contents"""
        file_contents = file_contents or {}
        detected_types = []
        
        # Check each project type
        for project_type, patterns in cls.TYPE_PATTERNS.items():
            score = 0
            
            for pattern in patterns:
                if cls._matches_pattern(pattern, files):
                    score += 1
                    
                    # Additional scoring based on file content
                    if project_type == ProjectType.NODEJS and pattern == 'package.json':
                        package_content = file_contents.get('package.json', '')
                        if package_content:
                            score += cls._score_nodejs_package(package_content)
                    
                    elif project_type == ProjectType.PYTHON and pattern in ['requirements.txt', 'setup.py']:
                        score += 2  # Strong indicators
                    
                    elif project_type == ProjectType.DOCKER and pattern in ['Dockerfile', 'docker-compose.yml']:
                        score += 3  # Very strong indicators
            
            if score > 0:
                detected_types.append((project_type, score))
        
        if not detected_types:
            return ProjectType.GENERIC
        
        # Sort by score, then by priority
        detected_types.sort(key=lambda x: (x[1], cls.TYPE_PRIORITY.index(x[0])))
        
        return detected_types[-1][0]  # Return highest scoring type
    
    @staticmethod
    def _matches_pattern(pattern: str, files: List[str]) -> bool:
        """Check if pattern matches any file in the list"""
        if '*' in pattern:
            # Handle wildcard patterns
            import fnmatch
            return any(fnmatch.fnmatch(f, pattern) for f in files)
        else:
            # Exact match or directory check
            return pattern in files or any(f.startswith(pattern + '/') for f in files)
    
    @staticmethod
    def _score_nodejs_package(package_content: str) -> int:
        """Score Node.js project based on package.json content"""
        try:
            package_data = json.loads(package_content)
            score = 0
            
            # Check for common Node.js indicators
            if 'scripts' in package_data:
                scripts = package_data['scripts']
                if 'start' in scripts:
                    score += 2
                if 'dev' in scripts or 'develop' in scripts:
                    score += 1
                if 'build' in scripts:
                    score += 1
            
            # Check for common dependencies
            deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
            
            frameworks = ['express', 'react', 'vue', 'angular', 'next', 'nuxt', 'svelte']
            for framework in frameworks:
                if framework in deps:
                    score += 1
            
            return score
            
        except json.JSONDecodeError:
            return 0


def get_project_type_config(project_type: ProjectType, project_name: str, project_path: str, 
                          file_contents: Dict[str, str] = None) -> Dict[str, Any]:
    """Get default configuration for a project type"""
    file_contents = file_contents or {}
    
    base_config = {
        'name': project_name,
        'project_type': project_type.value,
        'path': project_path,
        'ports': [],
        'environment': {},
        'dependencies': [],
        'auto_restart': False
    }
    
    if project_type == ProjectType.NODEJS:
        return _get_nodejs_config(base_config, file_contents)
    elif project_type == ProjectType.PYTHON:
        return _get_python_config(base_config, file_contents)
    elif project_type == ProjectType.DOCKER:
        return _get_docker_config(base_config, file_contents)
    elif project_type == ProjectType.GO:
        return _get_go_config(base_config, file_contents)
    elif project_type == ProjectType.JAVA:
        return _get_java_config(base_config, file_contents)
    elif project_type == ProjectType.DOTNET:
        return _get_dotnet_config(base_config, file_contents)
    else:
        return _get_generic_config(base_config)


def _get_nodejs_config(base_config: Dict[str, Any], file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Generate Node.js project configuration"""
    config = base_config.copy()
    
    # Parse package.json for configuration hints
    package_content = file_contents.get('package.json', '')
    if package_content:
        try:
            package_data = json.loads(package_content)
            
            # Determine start script
            scripts = package_data.get('scripts', {})
            if 'start' in scripts:
                config['start_script'] = './start.sh'  # We'll generate this
                config['generated_start_script'] = f"npm start"
            elif 'dev' in scripts:
                config['start_script'] = './start.sh'
                config['generated_start_script'] = f"npm run dev"
            
            # Determine ports from common patterns
            start_script = scripts.get('start', scripts.get('dev', ''))
            port = _extract_port_from_script(start_script)
            if port:
                config['ports'] = [port]
            else:
                config['ports'] = [3000]  # Default Node.js port
            
            # Set environment variables
            config['environment'] = {
                'NODE_ENV': 'development',
                'PORT': str(config['ports'][0]) if config['ports'] else '3000'
            }
            
            # Health check configuration
            config['health_check'] = {
                'type': 'http',
                'url': f"http://localhost:{config['ports'][0]}" if config['ports'] else 'http://localhost:3000',
                'interval': 30,
                'timeout': 10
            }
            
        except json.JSONDecodeError:
            LOGGER.warning("Failed to parse package.json")
    
    # Default configuration if package.json not available
    if not config.get('ports'):
        config['ports'] = [3000]
        config['environment'] = {'NODE_ENV': 'development', 'PORT': '3000'}
        config['health_check'] = {
            'type': 'http',
            'url': 'http://localhost:3000',
            'interval': 30
        }
    
    return config


def _get_python_config(base_config: Dict[str, Any], file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Generate Python project configuration"""
    config = base_config.copy()
    
    # Detect Python framework
    requirements = file_contents.get('requirements.txt', '')
    
    if 'django' in requirements.lower():
        config['ports'] = [8000]
        config['start_script'] = './start.sh'
        config['generated_start_script'] = 'python manage.py runserver 0.0.0.0:8000'
        config['health_check'] = {
            'type': 'http',
            'url': 'http://localhost:8000',
            'interval': 30
        }
    elif 'flask' in requirements.lower():
        config['ports'] = [5000]
        config['start_script'] = './start.sh'
        config['generated_start_script'] = 'python app.py'
        config['environment'] = {'FLASK_ENV': 'development'}
        config['health_check'] = {
            'type': 'http',
            'url': 'http://localhost:5000',
            'interval': 30
        }
    elif 'fastapi' in requirements.lower():
        config['ports'] = [8000]
        config['start_script'] = './start.sh'
        config['generated_start_script'] = 'uvicorn main:app --host 0.0.0.0 --port 8000'
        config['health_check'] = {
            'type': 'http',
            'url': 'http://localhost:8000/docs',
            'interval': 30
        }
    else:
        # Generic Python application
        config['ports'] = [8000]
        config['start_script'] = './start.sh'
        config['generated_start_script'] = 'python main.py'
    
    return config


def _get_docker_config(base_config: Dict[str, Any], file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Generate Docker project configuration"""
    config = base_config.copy()
    
    # Parse docker-compose.yml for port information
    compose_content = file_contents.get('docker-compose.yml') or file_contents.get('docker-compose.yaml', '')
    
    if compose_content:
        # Simple port extraction from docker-compose
        ports = _extract_ports_from_compose(compose_content)
        config['ports'] = ports if ports else [8080]
    else:
        config['ports'] = [8080]
    
    config['start_script'] = './start.sh'
    config['generated_start_script'] = 'docker-compose up -d'
    config['stop_script'] = './stop.sh'
    config['generated_stop_script'] = 'docker-compose down'
    
    # Health check for first exposed port
    if config['ports']:
        config['health_check'] = {
            'type': 'http',
            'url': f"http://localhost:{config['ports'][0]}",
            'interval': 30
        }
    
    return config


def _get_go_config(base_config: Dict[str, Any], file_contents: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Go project configuration"""
    config = base_config.copy()
    
    config['ports'] = [8080]
    config['start_script'] = './start.sh'
    config['generated_start_script'] = 'go run main.go'
    config['health_check'] = {
        'type': 'http',
        'url': 'http://localhost:8080',
        'interval': 30
    }
    
    return config


def _get_java_config(base_config: Dict[str, Any], file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Generate Java project configuration"""
    config = base_config.copy()
    
    config['ports'] = [8080]
    
    # Detect build system
    if 'pom.xml' in file_contents:
        config['start_script'] = './start.sh'
        config['generated_start_script'] = 'mvn spring-boot:run'
    elif any('build.gradle' in f for f in file_contents.keys()):
        config['start_script'] = './start.sh'
        config['generated_start_script'] = './gradlew bootRun'
    
    config['health_check'] = {
        'type': 'http',
        'url': 'http://localhost:8080',
        'interval': 30
    }
    
    return config


def _get_dotnet_config(base_config: Dict[str, Any], file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Generate .NET project configuration"""
    config = base_config.copy()
    
    config['ports'] = [5000]
    config['start_script'] = './start.sh'
    config['generated_start_script'] = 'dotnet run'
    config['health_check'] = {
        'type': 'http',
        'url': 'http://localhost:5000',
        'interval': 30
    }
    
    return config


def _get_generic_config(base_config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate generic project configuration"""
    config = base_config.copy()
    
    config['ports'] = []
    config['start_script'] = './start.sh'
    config['generated_start_script'] = 'echo "Please configure start script"'
    
    return config


def _extract_port_from_script(script: str) -> Optional[int]:
    """Extract port number from script command"""
    import re
    
    # Look for port patterns in script
    port_patterns = [
        r'--port[=\s]+(\d+)',
        r'-p[=\s]+(\d+)',
        r'PORT[=\s]+(\d+)',
        r':(\d+)',
        r'localhost:(\d+)'
    ]
    
    for pattern in port_patterns:
        match = re.search(pattern, script)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    return None


def _extract_ports_from_compose(compose_content: str) -> List[int]:
    """Extract port mappings from docker-compose content"""
    import re
    
    ports = []
    
    # Simple regex to find port mappings like "3000:3000" or "- 3000:3000"
    port_patterns = [
        r'["\']?(\d+):\d+["\']?',  # "3000:3000" or 3000:3000
        r'-\s+(\d+):\d+',          # - 3000:3000
    ]
    
    for pattern in port_patterns:
        matches = re.findall(pattern, compose_content)
        for match in matches:
            try:
                port = int(match)
                if port not in ports:
                    ports.append(port)
            except ValueError:
                continue
    
    return sorted(ports)
