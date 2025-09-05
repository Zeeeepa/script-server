"""
Project Scanner

Scans WSL2 instances for project directories and files.
"""

import logging
import os
from typing import List, Dict, Set, Optional, Tuple
from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import WSL2Instance

LOGGER = logging.getLogger('projects.scanner')


class ProjectScanner:
    """Scans WSL2 instances for potential project directories"""
    
    # Common project root directories to scan
    SCAN_DIRECTORIES = [
        '/home',
        '/opt',
        '/var/www',
        '/srv',
        '/workspace',
        '/projects',
        '/code',
        '/app',
        '/src'
    ]
    
    # Directories to skip during scanning
    SKIP_DIRECTORIES = {
        '.git', '.svn', '.hg',  # Version control
        'node_modules', '__pycache__', '.pytest_cache',  # Dependencies/cache
        '.venv', 'venv', 'env', '.env',  # Virtual environments
        'build', 'dist', 'target', 'bin', 'obj',  # Build outputs
        '.idea', '.vscode', '.vs',  # IDE files
        'logs', 'log', 'tmp', 'temp',  # Temporary files
        '.docker', '.cache'  # Other cache directories
    }
    
    # Files that indicate a project root
    PROJECT_INDICATORS = {
        'package.json', 'yarn.lock', 'package-lock.json',  # Node.js
        'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile',  # Python
        'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',  # Docker
        'go.mod', 'go.sum',  # Go
        'pom.xml', 'build.gradle', 'gradlew',  # Java
        '*.csproj', '*.sln', 'global.json',  # .NET
        'Makefile', 'CMakeLists.txt',  # C/C++
        'Cargo.toml',  # Rust
        'composer.json',  # PHP
        'Gemfile',  # Ruby
        'mix.exs',  # Elixir
        'pubspec.yaml',  # Dart/Flutter
        '.gitignore', 'README.md', 'README.txt'  # General indicators
    }
    
    def __init__(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        
    def scan_instance(self, instance_name: str, max_depth: int = 3) -> List[Dict[str, any]]:
        """Scan a WSL2 instance for projects"""
        LOGGER.info(f"Scanning WSL2 instance '{instance_name}' for projects")
        
        if not self.wsl2_service.is_instance_running(instance_name):
            LOGGER.warning(f"WSL2 instance '{instance_name}' is not running")
            return []
        
        projects = []
        
        # Scan each root directory
        for scan_dir in self.SCAN_DIRECTORIES:
            if self.wsl2_service.directory_exists(instance_name, scan_dir):
                LOGGER.debug(f"Scanning directory: {scan_dir}")
                found_projects = self._scan_directory(instance_name, scan_dir, max_depth)
                projects.extend(found_projects)
        
        # Remove duplicates and sort by path
        unique_projects = self._deduplicate_projects(projects)
        unique_projects.sort(key=lambda x: x['path'])
        
        LOGGER.info(f"Found {len(unique_projects)} potential projects in '{instance_name}'")
        return unique_projects
    
    def _scan_directory(self, instance_name: str, directory: str, max_depth: int, current_depth: int = 0) -> List[Dict[str, any]]:
        """Recursively scan a directory for projects"""
        if current_depth >= max_depth:
            return []
        
        projects = []
        
        try:
            # Get directory contents
            files = self.wsl2_service.list_directory(instance_name, directory)
            if not files:
                return []
            
            # Check if current directory is a project
            project_info = self._analyze_directory(instance_name, directory, files)
            if project_info:
                projects.append(project_info)
                # If we found a project, don't scan subdirectories (avoid nested projects for now)
                return projects
            
            # Scan subdirectories
            for file in files:
                if file.startswith('.') and file not in {'.', '..'}:
                    continue  # Skip hidden files/directories except . and ..
                
                if file in {'.', '..'}:
                    continue
                
                if file in self.SKIP_DIRECTORIES:
                    continue
                
                # Check if it's a directory (simple heuristic)
                subdir_path = f"{directory.rstrip('/')}/{file}"
                
                if self.wsl2_service.directory_exists(instance_name, subdir_path):
                    sub_projects = self._scan_directory(instance_name, subdir_path, max_depth, current_depth + 1)
                    projects.extend(sub_projects)
        
        except Exception as e:
            LOGGER.error(f"Error scanning directory {directory} in {instance_name}: {e}")
        
        return projects
    
    def _analyze_directory(self, instance_name: str, directory: str, files: List[str]) -> Optional[Dict[str, any]]:
        """Analyze a directory to determine if it's a project"""
        # Count project indicators
        indicator_count = 0
        found_indicators = []
        
        for file in files:
            if file in self.PROJECT_INDICATORS:
                indicator_count += 1
                found_indicators.append(file)
            elif any(file.endswith(ext) for ext in ['.csproj', '.sln', '.fsproj', '.vbproj']):
                indicator_count += 2  # .NET project files are strong indicators
                found_indicators.append(file)
        
        # Require at least 1 strong indicator or 2 weak indicators
        if indicator_count < 1:
            return None
        
        # Get additional file information for project type detection
        file_contents = {}
        important_files = ['package.json', 'requirements.txt', 'docker-compose.yml', 'docker-compose.yaml']
        
        for important_file in important_files:
            if important_file in files:
                content = self.wsl2_service.get_file_content(instance_name, f"{directory}/{important_file}")
                if content:
                    file_contents[important_file] = content[:2048]  # Limit content size
        
        # Extract project name from directory
        project_name = os.path.basename(directory.rstrip('/'))
        if not project_name or project_name in {'.', '..'}:
            project_name = f"project-{hash(directory) % 10000}"
        
        return {
            'name': project_name,
            'path': directory,
            'instance': instance_name,
            'files': files,
            'indicators': found_indicators,
            'file_contents': file_contents,
            'indicator_count': indicator_count
        }
    
    def _deduplicate_projects(self, projects: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Remove duplicate projects based on path"""
        seen_paths = set()
        unique_projects = []
        
        for project in projects:
            path = project['path']
            if path not in seen_paths:
                seen_paths.add(path)
                unique_projects.append(project)
        
        return unique_projects
    
    def get_project_files(self, instance_name: str, project_path: str, file_patterns: List[str] = None) -> Dict[str, str]:
        """Get content of specific files from a project"""
        file_patterns = file_patterns or ['package.json', 'requirements.txt', 'docker-compose.yml', 'Dockerfile']
        
        file_contents = {}
        
        for pattern in file_patterns:
            file_path = f"{project_path.rstrip('/')}/{pattern}"
            if self.wsl2_service.file_exists(instance_name, file_path):
                content = self.wsl2_service.get_file_content(instance_name, file_path)
                if content:
                    file_contents[pattern] = content
        
        return file_contents
    
    def validate_project_structure(self, instance_name: str, project_path: str) -> Dict[str, any]:
        """Validate and analyze project structure"""
        validation = {
            'valid': False,
            'issues': [],
            'recommendations': [],
            'structure_score': 0
        }
        
        try:
            # Check if project directory exists
            if not self.wsl2_service.directory_exists(instance_name, project_path):
                validation['issues'].append(f"Project directory does not exist: {project_path}")
                return validation
            
            # Get project files
            files = self.wsl2_service.list_directory(instance_name, project_path)
            if not files:
                validation['issues'].append("Project directory is empty")
                return validation
            
            # Check for project indicators
            indicators_found = []
            for file in files:
                if file in self.PROJECT_INDICATORS:
                    indicators_found.append(file)
                    validation['structure_score'] += 1
            
            if not indicators_found:
                validation['issues'].append("No project indicators found")
            else:
                validation['valid'] = True
            
            # Check for common project structure issues
            if 'node_modules' in files and 'package.json' not in files:
                validation['issues'].append("Found node_modules but no package.json")
            
            if '__pycache__' in files and 'requirements.txt' not in files and 'setup.py' not in files:
                validation['recommendations'].append("Consider adding requirements.txt for Python dependencies")
            
            # Check for start/stop scripts
            script_files = [f for f in files if f.endswith('.sh') or f in ['start', 'stop', 'run']]
            if script_files:
                validation['structure_score'] += 1
            else:
                validation['recommendations'].append("Consider adding start/stop scripts for easier management")
            
            # Check for documentation
            doc_files = [f for f in files if f.lower().startswith('readme')]
            if doc_files:
                validation['structure_score'] += 1
            else:
                validation['recommendations'].append("Consider adding a README file")
            
            validation['indicators_found'] = indicators_found
            validation['script_files'] = script_files
            validation['doc_files'] = doc_files
            
        except Exception as e:
            validation['issues'].append(f"Error validating project structure: {e}")
        
        return validation
    
    def estimate_scan_time(self, instance_name: str) -> int:
        """Estimate scan time in seconds"""
        # Simple estimation based on directory count
        base_time = 5  # Base time in seconds
        
        try:
            total_dirs = 0
            for scan_dir in self.SCAN_DIRECTORIES:
                if self.wsl2_service.directory_exists(instance_name, scan_dir):
                    total_dirs += 1
            
            # Estimate 2 seconds per directory
            estimated_time = base_time + (total_dirs * 2)
            return min(estimated_time, 60)  # Cap at 60 seconds
            
        except Exception:
            return base_time
