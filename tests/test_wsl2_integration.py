"""
Tests for WSL2 Integration

Comprehensive test suite for WSL2 project management functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wsl2.wsl2_service import WSL2Service
from wsl2.wsl2_types import WSL2Instance, ProjectInfo, ProjectType, ProjectStatus
from projects.project_discovery import ProjectDiscovery
from monitoring.port_monitor import PortMonitor
from monitoring.health_checker import HealthChecker
from model.wsl2_model import WSL2ProjectModel


class TestWSL2Service(unittest.TestCase):
    """Test WSL2Service functionality"""
    
    def setUp(self):
        self.wsl2_service = WSL2Service()
    
    @patch('wsl2.wsl2_commands.WSL2Commands.execute_command')
    def test_get_instances(self, mock_execute):
        """Test getting WSL2 instances"""
        mock_execute.return_value = (0, "Ubuntu\nDebian\n", "")
        
        instances = self.wsl2_service.get_instances()
        
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].name, "Ubuntu")
        self.assertEqual(instances[1].name, "Debian")
    
    @patch('wsl2.wsl2_commands.WSL2Commands.execute_command')
    def test_start_instance(self, mock_execute):
        """Test starting WSL2 instance"""
        mock_execute.return_value = (0, "", "")
        
        result = self.wsl2_service.start_instance("Ubuntu")
        
        self.assertTrue(result)
        mock_execute.assert_called_with(['wsl', '-d', 'Ubuntu', '--', 'echo', 'started'])
    
    @patch('wsl2.wsl2_commands.WSL2Commands.execute_command')
    def test_execute_command(self, mock_execute):
        """Test executing command in WSL2 instance"""
        mock_execute.return_value = (0, "Hello World", "")
        
        result = self.wsl2_service.execute_command("Ubuntu", "echo 'Hello World'")
        
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "Hello World")


class TestProjectDiscovery(unittest.TestCase):
    """Test ProjectDiscovery functionality"""
    
    def setUp(self):
        self.wsl2_service = Mock()
        self.project_discovery = ProjectDiscovery(self.wsl2_service)
    
    def test_detect_nodejs_project(self):
        """Test Node.js project detection"""
        # Mock file system responses
        self.wsl2_service.file_exists.return_value = True
        self.wsl2_service.read_file.return_value = '{"name": "test-app", "scripts": {"start": "node index.js"}}'
        
        project_type = self.project_discovery.project_type_detector.detect_project_type("/home/user/app")
        
        self.assertEqual(project_type, ProjectType.NODEJS)
    
    def test_detect_python_project(self):
        """Test Python project detection"""
        self.wsl2_service.file_exists.side_effect = lambda path: path.endswith('requirements.txt')
        self.wsl2_service.read_file.return_value = 'flask==2.0.1\nrequests==2.25.1'
        
        project_type = self.project_discovery.project_type_detector.detect_project_type("/home/user/app")
        
        self.assertEqual(project_type, ProjectType.PYTHON)
    
    def test_discover_projects(self):
        """Test project discovery in WSL2 instance"""
        # Mock directory scanning
        self.wsl2_service.list_directory.return_value = ['/home/user/app1', '/home/user/app2']
        self.wsl2_service.file_exists.return_value = True
        self.wsl2_service.read_file.return_value = '{"name": "test-app"}'
        
        projects = self.project_discovery.discover_projects("Ubuntu", "/home/user")
        
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0].name, "app1")
        self.assertEqual(projects[1].name, "app2")


class TestPortMonitor(unittest.TestCase):
    """Test PortMonitor functionality"""
    
    def setUp(self):
        self.wsl2_service = Mock()
        self.port_monitor = PortMonitor(self.wsl2_service)
    
    def test_scan_port_usage(self):
        """Test port usage scanning"""
        # Mock netstat output
        netstat_output = """
tcp        0      0 0.0.0.0:3000            0.0.0.0:*               LISTEN      1234/node
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      5678/python
        """
        
        command_result = Mock()
        command_result.success = True
        command_result.stdout = netstat_output
        
        self.wsl2_service.execute_command.return_value = command_result
        
        port_usage = self.port_monitor.scan_port_usage("Ubuntu")
        
        self.assertIn(3000, port_usage)
        self.assertIn(8080, port_usage)
        self.assertEqual(port_usage[3000]['process'], 'node')
        self.assertEqual(port_usage[8080]['process'], 'python')
    
    def test_detect_port_conflicts(self):
        """Test port conflict detection"""
        # Mock port usage data
        self.port_monitor.port_usage_cache = {
            'Ubuntu': {3000: {'process': 'node', 'pid': 1234}},
            'Debian': {3000: {'process': 'python', 'pid': 5678}}
        }
        
        conflicts = self.port_monitor.detect_port_conflicts()
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['port'], 3000)
        self.assertEqual(len(conflicts[0]['instances']), 2)


class TestHealthChecker(unittest.TestCase):
    """Test HealthChecker functionality"""
    
    def setUp(self):
        self.wsl2_service = Mock()
        self.health_checker = HealthChecker(self.wsl2_service)
    
    def test_http_health_check(self):
        """Test HTTP health check"""
        project = ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=ProjectType.NODEJS,
            ports=[3000],
            health_check={
                'type': 'http',
                'url': 'http://localhost:3000/health',
                'timeout': 10
            }
        )
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'healthy'}
            mock_get.return_value = mock_response
            
            result = self.health_checker.check_project_health(project)
            
            self.assertTrue(result['healthy'])
            self.assertEqual(result['status_code'], 200)
    
    def test_tcp_health_check(self):
        """Test TCP health check"""
        project = ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=ProjectType.NODEJS,
            ports=[3000],
            health_check={
                'type': 'tcp',
                'port': 3000,
                'timeout': 5
            }
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 0  # Success
            
            result = self.health_checker.check_project_health(project)
            
            self.assertTrue(result['healthy'])
            self.assertEqual(result['response_time'], 0)


class TestWSL2ProjectModel(unittest.TestCase):
    """Test WSL2ProjectModel functionality"""
    
    def setUp(self):
        self.model = WSL2ProjectModel()
    
    def test_add_project(self):
        """Test adding a project"""
        project = ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=ProjectType.NODEJS,
            ports=[3000]
        )
        
        self.model.add_project(project)
        
        self.assertEqual(len(self.model.projects), 1)
        self.assertEqual(self.model.projects[0].name, "test-app")
    
    def test_find_projects(self):
        """Test finding projects with filters"""
        project1 = ProjectInfo(
            name="node-app",
            wsl_instance="Ubuntu",
            path="/home/user/node-app",
            project_type=ProjectType.NODEJS,
            ports=[3000]
        )
        
        project2 = ProjectInfo(
            name="python-app",
            wsl_instance="Ubuntu",
            path="/home/user/python-app",
            project_type=ProjectType.PYTHON,
            ports=[8000]
        )
        
        self.model.add_project(project1)
        self.model.add_project(project2)
        
        # Test filtering by type
        nodejs_projects = self.model.find_projects(type='nodejs')
        self.assertEqual(len(nodejs_projects), 1)
        self.assertEqual(nodejs_projects[0].name, "node-app")
        
        # Test filtering by instance
        ubuntu_projects = self.model.find_projects(instance='Ubuntu')
        self.assertEqual(len(ubuntu_projects), 2)
    
    def test_get_project_summary(self):
        """Test getting project summary"""
        project = ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=ProjectType.NODEJS,
            ports=[3000],
            status=ProjectStatus.RUNNING
        )
        
        self.model.add_project(project)
        
        summary = self.model.get_project_summary()
        
        self.assertEqual(summary['total_projects'], 1)
        self.assertEqual(summary['running_projects'], 1)
        self.assertEqual(summary['stopped_projects'], 0)
        self.assertEqual(summary['project_types']['nodejs'], 1)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""
    
    def setUp(self):
        self.wsl2_service = Mock()
        self.project_discovery = ProjectDiscovery(self.wsl2_service)
        self.port_monitor = PortMonitor(self.wsl2_service)
        self.health_checker = HealthChecker(self.wsl2_service)
    
    def test_full_project_lifecycle(self):
        """Test complete project lifecycle"""
        # 1. Discover project
        self.wsl2_service.list_directory.return_value = ['/home/user/myapp']
        self.wsl2_service.file_exists.return_value = True
        self.wsl2_service.read_file.return_value = '{"name": "myapp", "scripts": {"start": "npm start"}}'
        
        projects = self.project_discovery.discover_projects("Ubuntu", "/home/user")
        self.assertEqual(len(projects), 1)
        
        project = projects[0]
        
        # 2. Check port usage
        command_result = Mock()
        command_result.success = True
        command_result.stdout = "tcp 0.0.0.0:3000 LISTEN 1234/node"
        self.wsl2_service.execute_command.return_value = command_result
        
        port_usage = self.port_monitor.scan_port_usage("Ubuntu")
        self.assertIn(3000, port_usage)
        
        # 3. Health check
        project.health_check = {'type': 'http', 'url': 'http://localhost:3000'}
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            health = self.health_checker.check_project_health(project)
            self.assertTrue(health['healthy'])


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestWSL2Service))
    test_suite.addTest(unittest.makeSuite(TestProjectDiscovery))
    test_suite.addTest(unittest.makeSuite(TestPortMonitor))
    test_suite.addTest(unittest.makeSuite(TestHealthChecker))
    test_suite.addTest(unittest.makeSuite(TestWSL2ProjectModel))
    test_suite.addTest(unittest.makeSuite(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
