"""
WSL2 WebSocket Handler

Real-time updates for WSL2 project status and monitoring.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Set, Optional
from tornado.websocket import WebSocketHandler
from tornado.escape import json_encode, json_decode

from ..wsl2.wsl2_service import WSL2Service
from ..wsl2.wsl2_types import ProjectInfo, ProjectStatus
from ..model.wsl2_model import wsl2_project_model
from ..monitoring.port_monitor import PortMonitor
from ..monitoring.health_checker import HealthChecker

LOGGER = logging.getLogger('web.wsl2_websocket')


class WSL2WebSocketHandler(WebSocketHandler):
    """WebSocket handler for real-time WSL2 updates"""
    
    # Class-level set to track all connected clients
    clients: Set['WSL2WebSocketHandler'] = set()
    
    def initialize(self, wsl2_service: WSL2Service):
        self.wsl2_service = wsl2_service
        self.port_monitor = PortMonitor(wsl2_service)
        self.health_checker = HealthChecker(wsl2_service)
        self.subscriptions = set()  # What this client is subscribed to
        self.update_task = None
        
    def check_origin(self, origin):
        """Allow connections from any origin (configure as needed for security)"""
        return True
    
    def open(self):
        """Handle new WebSocket connection"""
        WSL2WebSocketHandler.clients.add(self)
        LOGGER.info(f"WSL2 WebSocket client connected. Total clients: {len(self.clients)}")
        
        # Send initial status
        self.send_message({
            'type': 'connection_established',
            'message': 'Connected to WSL2 WebSocket',
            'timestamp': self._get_timestamp()
        })
    
    def on_open(self):
        """Alias for open method for compatibility"""
        return self.open()
        
        # Start periodic updates
        self.start_periodic_updates()
    
    def on_close(self):
        """Handle WebSocket connection close"""
        WSL2WebSocketHandler.clients.discard(self)
        if self.update_task:
            self.update_task.cancel()
        LOGGER.info(f"WSL2 WebSocket client disconnected. Total clients: {len(self.clients)}")
    
    def on_message(self, message):
        """Handle incoming WebSocket message"""
        try:
            data = json_decode(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                self.handle_subscribe(data)
            elif message_type == 'unsubscribe':
                self.handle_unsubscribe(data)
            elif message_type == 'get_status':
                self.handle_get_status(data)
            elif message_type == 'project_action':
                self.handle_project_action(data)
            else:
                self.send_error(f"Unknown message type: {message_type}")
                
        except Exception as e:
            LOGGER.error(f"Error handling WebSocket message: {e}")
            self.send_error(f"Error processing message: {str(e)}")
    
    def handle_subscribe(self, data: Dict[str, Any]):
        """Handle subscription requests"""
        subscription_type = data.get('subscription_type')
        
        if subscription_type == 'project_status':
            project_id = data.get('project_id')
            if project_id:
                self.subscriptions.add(f"project_status:{project_id}")
            else:
                self.subscriptions.add("project_status:all")
                
        elif subscription_type == 'port_monitoring':
            instance_name = data.get('instance_name')
            if instance_name:
                self.subscriptions.add(f"port_monitoring:{instance_name}")
            else:
                self.subscriptions.add("port_monitoring:all")
                
        elif subscription_type == 'health_monitoring':
            self.subscriptions.add("health_monitoring")
            
        elif subscription_type == 'instance_status':
            self.subscriptions.add("instance_status")
            
        else:
            self.send_error(f"Unknown subscription type: {subscription_type}")
            return
        
        self.send_message({
            'type': 'subscription_confirmed',
            'subscription_type': subscription_type,
            'subscriptions': list(self.subscriptions),
            'timestamp': self._get_timestamp()
        })
    
    def handle_unsubscribe(self, data: Dict[str, Any]):
        """Handle unsubscription requests"""
        subscription_type = data.get('subscription_type')
        
        # Remove matching subscriptions
        to_remove = [sub for sub in self.subscriptions if sub.startswith(subscription_type)]
        for sub in to_remove:
            self.subscriptions.discard(sub)
        
        self.send_message({
            'type': 'unsubscription_confirmed',
            'subscription_type': subscription_type,
            'subscriptions': list(self.subscriptions),
            'timestamp': self._get_timestamp()
        })
    
    def handle_get_status(self, data: Dict[str, Any]):
        """Handle immediate status requests"""
        status_type = data.get('status_type')
        
        try:
            if status_type == 'projects':
                projects = wsl2_project_model.get_all_projects()
                projects_data = [project.to_dict() for project in projects]
                
                self.send_message({
                    'type': 'status_response',
                    'status_type': 'projects',
                    'data': projects_data,
                    'timestamp': self._get_timestamp()
                })
                
            elif status_type == 'instances':
                instances = self.wsl2_service.get_instances()
                instances_data = [instance.to_dict() for instance in instances]
                
                self.send_message({
                    'type': 'status_response',
                    'status_type': 'instances',
                    'data': instances_data,
                    'timestamp': self._get_timestamp()
                })
                
            elif status_type == 'ports':
                port_usage = self.port_monitor.get_all_port_usage()
                conflicts = self.port_monitor.detect_port_conflicts()
                
                self.send_message({
                    'type': 'status_response',
                    'status_type': 'ports',
                    'data': {
                        'port_usage': port_usage,
                        'conflicts': conflicts
                    },
                    'timestamp': self._get_timestamp()
                })
                
            else:
                self.send_error(f"Unknown status type: {status_type}")
                
        except Exception as e:
            LOGGER.error(f"Error getting status: {e}")
            self.send_error(f"Error getting status: {str(e)}")
    
    def handle_project_action(self, data: Dict[str, Any]):
        """Handle project action requests via WebSocket"""
        try:
            project_id = data.get('project_id')
            action = data.get('action')
            
            if not project_id or not action:
                self.send_error("project_id and action are required")
                return
            
            project = wsl2_project_model.get_project(project_id)
            if not project:
                self.send_error(f"Project {project_id} not found")
                return
            
            # This would typically be handled by the execution service
            # For now, just acknowledge the request
            self.send_message({
                'type': 'action_acknowledged',
                'project_id': project_id,
                'action': action,
                'message': f"Action {action} requested for project {project.name}",
                'timestamp': self._get_timestamp()
            })
            
        except Exception as e:
            LOGGER.error(f"Error handling project action: {e}")
            self.send_error(f"Error handling project action: {str(e)}")
    
    def send_message(self, message: Dict[str, Any]):
        """Send message to this WebSocket client"""
        try:
            self.write_message(json_encode(message))
        except Exception as e:
            LOGGER.error(f"Error sending WebSocket message: {e}")
    
    def send_error(self, error_message: str):
        """Send error message to client"""
        self.send_message({
            'type': 'error',
            'error': error_message,
            'timestamp': self._get_timestamp()
        })
    
    def start_periodic_updates(self):
        """Start periodic status updates"""
        async def update_loop():
            while True:
                try:
                    await asyncio.sleep(5)  # Update every 5 seconds
                    await self.send_periodic_updates()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    LOGGER.error(f"Error in periodic update loop: {e}")
        
        self.update_task = asyncio.create_task(update_loop())
    
    async def send_periodic_updates(self):
        """Send periodic updates based on subscriptions"""
        try:
            # Project status updates
            if any(sub.startswith('project_status') for sub in self.subscriptions):
                await self.send_project_status_updates()
            
            # Port monitoring updates
            if any(sub.startswith('port_monitoring') for sub in self.subscriptions):
                await self.send_port_monitoring_updates()
            
            # Health monitoring updates
            if 'health_monitoring' in self.subscriptions:
                await self.send_health_monitoring_updates()
            
            # Instance status updates
            if 'instance_status' in self.subscriptions:
                await self.send_instance_status_updates()
                
        except Exception as e:
            LOGGER.error(f"Error sending periodic updates: {e}")
    
    async def send_project_status_updates(self):
        """Send project status updates"""
        try:
            projects = wsl2_project_model.get_all_projects()
            
            for project in projects:
                # Check if client is subscribed to this project or all projects
                if (f"project_status:{project.id}" in self.subscriptions or 
                    "project_status:all" in self.subscriptions):
                    
                    # Get current status (this could be cached for performance)
                    status_info = {
                        'project_id': project.id,
                        'name': project.name,
                        'status': project.status.value,
                        'instance': project.wsl_instance,
                        'ports': project.ports
                    }
                    
                    self.send_message({
                        'type': 'project_status_update',
                        'project': status_info,
                        'timestamp': self._get_timestamp()
                    })
                    
        except Exception as e:
            LOGGER.error(f"Error sending project status updates: {e}")
    
    async def send_port_monitoring_updates(self):
        """Send port monitoring updates"""
        try:
            # Get port usage for subscribed instances
            for subscription in self.subscriptions:
                if subscription.startswith('port_monitoring:'):
                    instance_name = subscription.split(':', 1)[1]
                    
                    if instance_name == 'all':
                        port_usage = self.port_monitor.get_all_port_usage()
                        conflicts = self.port_monitor.detect_port_conflicts()
                        
                        self.send_message({
                            'type': 'port_monitoring_update',
                            'scope': 'all',
                            'port_usage': port_usage,
                            'conflicts': conflicts,
                            'timestamp': self._get_timestamp()
                        })
                    else:
                        port_usage = self.port_monitor.scan_port_usage(instance_name)
                        
                        self.send_message({
                            'type': 'port_monitoring_update',
                            'scope': 'instance',
                            'instance_name': instance_name,
                            'port_usage': port_usage,
                            'timestamp': self._get_timestamp()
                        })
                        
        except Exception as e:
            LOGGER.error(f"Error sending port monitoring updates: {e}")
    
    async def send_health_monitoring_updates(self):
        """Send health monitoring updates"""
        try:
            # Get unhealthy projects
            unhealthy_projects = self.health_checker.get_unhealthy_projects()
            
            if unhealthy_projects:
                self.send_message({
                    'type': 'health_monitoring_update',
                    'unhealthy_projects': unhealthy_projects,
                    'timestamp': self._get_timestamp()
                })
                
        except Exception as e:
            LOGGER.error(f"Error sending health monitoring updates: {e}")
    
    async def send_instance_status_updates(self):
        """Send WSL2 instance status updates"""
        try:
            instances = self.wsl2_service.get_instances()
            instances_data = [instance.to_dict() for instance in instances]
            
            self.send_message({
                'type': 'instance_status_update',
                'instances': instances_data,
                'timestamp': self._get_timestamp()
            })
            
        except Exception as e:
            LOGGER.error(f"Error sending instance status updates: {e}")
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    @classmethod
    def broadcast_message(cls, message: Dict[str, Any], filter_func=None):
        """Broadcast message to all connected clients"""
        for client in cls.clients.copy():  # Copy to avoid modification during iteration
            try:
                if filter_func is None or filter_func(client):
                    client.send_message(message)
            except Exception as e:
                LOGGER.error(f"Error broadcasting to client: {e}")
                cls.clients.discard(client)
    
    @classmethod
    def broadcast_project_status_change(cls, project: ProjectInfo, old_status: ProjectStatus, new_status: ProjectStatus):
        """Broadcast project status change to relevant clients"""
        message = {
            'type': 'project_status_changed',
            'project_id': project.id,
            'project_name': project.name,
            'old_status': old_status.value,
            'new_status': new_status.value,
            'timestamp': cls._get_current_timestamp()
        }
        
        def should_receive(client):
            return (f"project_status:{project.id}" in client.subscriptions or 
                   "project_status:all" in client.subscriptions)
        
        cls.broadcast_message(message, should_receive)
    
    @classmethod
    def broadcast_port_conflict(cls, conflict_info: Dict[str, Any]):
        """Broadcast port conflict detection to relevant clients"""
        message = {
            'type': 'port_conflict_detected',
            'conflict': conflict_info,
            'timestamp': cls._get_current_timestamp()
        }
        
        def should_receive(client):
            return any(sub.startswith('port_monitoring') for sub in client.subscriptions)
        
        cls.broadcast_message(message, should_receive)
    
    @classmethod
    def broadcast_health_alert(cls, project: ProjectInfo, health_status: Dict[str, Any]):
        """Broadcast health alert to relevant clients"""
        message = {
            'type': 'health_alert',
            'project_id': project.id,
            'project_name': project.name,
            'health_status': health_status,
            'timestamp': cls._get_current_timestamp()
        }
        
        def should_receive(client):
            return 'health_monitoring' in client.subscriptions
        
        cls.broadcast_message(message, should_receive)
    
    @staticmethod
    def _get_current_timestamp() -> float:
        """Get current timestamp (static method for class methods)"""
        import time
        return time.time()


# WebSocket URL pattern
WSL2_WEBSOCKET_PATTERN = (r"/ws/wsl2", WSL2WebSocketHandler)
