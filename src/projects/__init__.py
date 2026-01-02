"""
Project Management Module for WSL2

This module provides project discovery, configuration, and management capabilities:
- Automatic project detection in WSL2 instances
- Project type classification and configuration generation
- Project lifecycle management and monitoring
"""

from .project_discovery import ProjectDiscovery
from .project_types import ProjectTypeDetector, get_project_type_config
from .project_scanner import ProjectScanner

__all__ = ['ProjectDiscovery', 'ProjectTypeDetector', 'ProjectScanner', 'get_project_type_config']
