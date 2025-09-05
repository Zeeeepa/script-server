"""
WSL2 Model Extensions

Extends Script-Server's model system to support WSL2 project data structures.
"""

import logging
from typing import Dict, Any, List, Optional
from ..wsl2.wsl2_types import ProjectInfo, ProjectType, ProjectStatus, HealthCheck
from ..config.wsl2_config import create_wsl2_project_config, extract_wsl2_info_from_config

LOGGER = logging.getLogger('model.wsl2')


class WSL2ProjectModel:
    """Model for managing WSL2 project configurations"""
    
    def __init__(self):
        self._projects = {}  # project_id -> ProjectInfo
        self._config_cache = {}  # project_id -> script config
    
    def add_project(self, project_info: ProjectInfo) -> None:
        """Add a project to the model"""
        self._projects[project_info.id] = project_info
        
        # Generate script configuration
        script_config = create_wsl2_project_config(project_info)
        self._config_cache[project_info.id] = script_config
        
        LOGGER.info(f"Added WSL2 project: {project_info.name} ({project_info.id})")
    
    def remove_project(self, project_id: str) -> bool:
        """Remove a project from the model"""
        if project_id in self._projects:
            project = self._projects.pop(project_id)
            self._config_cache.pop(project_id, None)
            LOGGER.info(f"Removed WSL2 project: {project.name} ({project_id})")
            return True
        return False
    
    def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        """Get a project by ID"""
        return self._projects.get(project_id)
    
    def get_project_by_name(self, name: str, instance_name: str = None) -> Optional[ProjectInfo]:
        """Get a project by name and optionally instance"""
        for project in self._projects.values():
            if project.name == name:
                if instance_name is None or project.wsl_instance == instance_name:
                    return project
        return None
    
    def get_all_projects(self) -> List[ProjectInfo]:
        """Get all projects"""
        return list(self._projects.values())
    
    def get_projects_by_instance(self, instance_name: str) -> List[ProjectInfo]:
        """Get all projects for a specific WSL2 instance"""
        return [p for p in self._projects.values() if p.wsl_instance == instance_name]
    
    def get_projects_by_status(self, status: ProjectStatus) -> List[ProjectInfo]:
        """Get all projects with a specific status"""
        return [p for p in self._projects.values() if p.status == status]
    
    def get_projects_by_type(self, project_type: ProjectType) -> List[ProjectInfo]:
        """Get all projects of a specific type"""
        return [p for p in self._projects.values() if p.project_type == project_type]
    
    def update_project_status(self, project_id: str, status: ProjectStatus) -> bool:
        """Update a project's status"""
        if project_id in self._projects:
            self._projects[project_id].status = status
            LOGGER.debug(f"Updated project {project_id} status to {status.value}")
            return True
        return False
    
    def get_script_config(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the Script-Server configuration for a project"""
        return self._config_cache.get(project_id)
    
    def update_project(self, project_info: ProjectInfo) -> bool:
        """Update an existing project"""
        if project_info.id in self._projects:
            self._projects[project_info.id] = project_info
            
            # Regenerate script configuration
            script_config = create_wsl2_project_config(project_info)
            self._config_cache[project_info.id] = script_config
            
            LOGGER.info(f"Updated WSL2 project: {project_info.name} ({project_info.id})")
            return True
        return False
    
    def get_projects_using_port(self, port: int) -> List[ProjectInfo]:
        """Get all projects using a specific port"""
        return [p for p in self._projects.values() if port in p.ports]
    
    def get_instance_summary(self, instance_name: str) -> Dict[str, Any]:
        """Get summary information for an instance"""
        projects = self.get_projects_by_instance(instance_name)
        
        status_counts = {}
        type_counts = {}
        total_ports = set()
        
        for project in projects:
            # Count by status
            status = project.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            project_type = project.project_type.value
            type_counts[project_type] = type_counts.get(project_type, 0) + 1
            
            # Collect ports
            total_ports.update(project.ports)
        
        return {
            'instance_name': instance_name,
            'total_projects': len(projects),
            'status_counts': status_counts,
            'type_counts': type_counts,
            'total_ports': len(total_ports),
            'ports_in_use': sorted(list(total_ports))
        }
    
    def get_global_summary(self) -> Dict[str, Any]:
        """Get global summary of all projects"""
        all_projects = self.get_all_projects()
        
        instance_counts = {}
        status_counts = {}
        type_counts = {}
        total_ports = set()
        
        for project in all_projects:
            # Count by instance
            instance = project.wsl_instance
            instance_counts[instance] = instance_counts.get(instance, 0) + 1
            
            # Count by status
            status = project.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            project_type = project.project_type.value
            type_counts[project_type] = type_counts.get(project_type, 0) + 1
            
            # Collect ports
            total_ports.update(project.ports)
        
        return {
            'total_projects': len(all_projects),
            'total_instances': len(instance_counts),
            'instance_counts': instance_counts,
            'status_counts': status_counts,
            'type_counts': type_counts,
            'total_ports': len(total_ports),
            'ports_in_use': sorted(list(total_ports))
        }
    
    def find_projects(self, **filters) -> List[ProjectInfo]:
        """Find projects matching the given filters"""
        projects = self.get_all_projects()
        
        # Apply filters
        if 'name' in filters:
            name_filter = filters['name'].lower()
            projects = [p for p in projects if name_filter in p.name.lower()]
        
        if 'instance' in filters:
            instance_filter = filters['instance']
            projects = [p for p in projects if p.wsl_instance == instance_filter]
        
        if 'status' in filters:
            status_filter = ProjectStatus(filters['status'])
            projects = [p for p in projects if p.status == status_filter]
        
        if 'type' in filters:
            type_filter = ProjectType(filters['type'])
            projects = [p for p in projects if p.project_type == type_filter]
        
        if 'port' in filters:
            port_filter = int(filters['port'])
            projects = [p for p in projects if port_filter in p.ports]
        
        return projects
    
    def clear_instance_projects(self, instance_name: str) -> int:
        """Remove all projects for a specific instance"""
        projects_to_remove = [p.id for p in self._projects.values() if p.wsl_instance == instance_name]
        
        for project_id in projects_to_remove:
            self.remove_project(project_id)
        
        LOGGER.info(f"Cleared {len(projects_to_remove)} projects from instance {instance_name}")
        return len(projects_to_remove)
    
    def clear_all_projects(self) -> int:
        """Remove all projects"""
        count = len(self._projects)
        self._projects.clear()
        self._config_cache.clear()
        LOGGER.info(f"Cleared all {count} projects")
        return count
    
    def export_projects(self) -> List[Dict[str, Any]]:
        """Export all projects as dictionaries"""
        return [project.to_dict() for project in self._projects.values()]
    
    def import_projects(self, project_data: List[Dict[str, Any]]) -> int:
        """Import projects from dictionaries"""
        imported_count = 0
        
        for data in project_data:
            try:
                project_info = ProjectInfo.from_dict(data)
                self.add_project(project_info)
                imported_count += 1
            except Exception as e:
                LOGGER.error(f"Failed to import project {data.get('name', 'unknown')}: {e}")
        
        LOGGER.info(f"Imported {imported_count} projects")
        return imported_count


# Global instance of the WSL2 project model
wsl2_project_model = WSL2ProjectModel()
