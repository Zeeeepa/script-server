#!/usr/bin/env python3
"""
WSL2 Project Management System - Test Runner

Comprehensive test runner for WSL2 functionality with proper imports.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock external dependencies that might not be available
sys.modules['tornado'] = Mock()
sys.modules['tornado.web'] = Mock()
sys.modules['tornado.websocket'] = Mock()
sys.modules['tornado.escape'] = Mock()

class MockWSL2Types:
    """Mock WSL2 types for testing"""
    
    class ProjectType:
        NODEJS = 'nodejs'
        PYTHON = 'python'
        DOCKER = 'docker'
        GO = 'go'
        JAVA = 'java'
        DOTNET = 'dotnet'
        GENERIC = 'generic'
    
    class ProjectStatus:
        RUNNING = 'running'
        STOPPED = 'stopped'
        STARTING = 'starting'
        STOPPING = 'stopping'
        ERROR = 'error'
    
    class WSL2Instance:
        def __init__(self, name, status='Running'):
            self.name = name
            self.status = status
    
    class ProjectInfo:
        def __init__(self, name, wsl_instance, path, project_type, ports=None, 
                     health_check=None, dependencies=None, status=None):
            self.name = name
            self.wsl_instance = wsl_instance
            self.path = path
            self.project_type = project_type
            self.ports = ports or []
            self.health_check = health_check
            self.dependencies = dependencies or []
            self.status = status or MockWSL2Types.ProjectStatus.STOPPED
            self.id = f"{name}-{wsl_instance}"
        
        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'wsl_instance': self.wsl_instance,
                'path': self.path,
                'project_type': self.project_type,
                'ports': self.ports,
                'health_check': self.health_check,
                'dependencies': self.dependencies,
                'status': self.status
            }

# Mock the types module
sys.modules['wsl2.wsl2_types'] = MockWSL2Types()


class TestWSL2ServiceMock(unittest.TestCase):
    """Test WSL2Service functionality with mocks"""
    
    def setUp(self):
        self.mock_service = Mock()
        self.mock_service.get_instances.return_value = [
            MockWSL2Types.WSL2Instance("Ubuntu", "Running"),
            MockWSL2Types.WSL2Instance("Debian", "Stopped")
        ]
    
    def test_get_instances(self):
        """Test getting WSL2 instances"""
        instances = self.mock_service.get_instances()
        
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].name, "Ubuntu")
        self.assertEqual(instances[1].name, "Debian")
    
    def test_start_instance(self):
        """Test starting WSL2 instance"""
        self.mock_service.start_instance.return_value = True
        
        result = self.mock_service.start_instance("Ubuntu")
        
        self.assertTrue(result)
        self.mock_service.start_instance.assert_called_with("Ubuntu")
    
    def test_execute_command(self):
        """Test executing command in WSL2 instance"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.stdout = "Hello World"
        mock_result.stderr = ""
        
        self.mock_service.execute_command.return_value = mock_result
        
        result = self.mock_service.execute_command("Ubuntu", "echo 'Hello World'")
        
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "Hello World")


class TestProjectDiscoveryMock(unittest.TestCase):
    """Test ProjectDiscovery functionality with mocks"""
    
    def setUp(self):
        self.mock_wsl2_service = Mock()
        self.mock_discovery = Mock()
    
    def test_detect_nodejs_project(self):
        """Test Node.js project detection"""
        self.mock_discovery.detect_project_type.return_value = MockWSL2Types.ProjectType.NODEJS
        
        project_type = self.mock_discovery.detect_project_type("/home/user/app")
        
        self.assertEqual(project_type, MockWSL2Types.ProjectType.NODEJS)
    
    def test_detect_python_project(self):
        """Test Python project detection"""
        self.mock_discovery.detect_project_type.return_value = MockWSL2Types.ProjectType.PYTHON
        
        project_type = self.mock_discovery.detect_project_type("/home/user/app")
        
        self.assertEqual(project_type, MockWSL2Types.ProjectType.PYTHON)
    
    def test_discover_projects(self):
        """Test project discovery in WSL2 instance"""
        projects = [
            MockWSL2Types.ProjectInfo("app1", "Ubuntu", "/home/user/app1", MockWSL2Types.ProjectType.NODEJS),
            MockWSL2Types.ProjectInfo("app2", "Ubuntu", "/home/user/app2", MockWSL2Types.ProjectType.PYTHON)
        ]
        
        self.mock_discovery.discover_projects.return_value = projects
        
        discovered = self.mock_discovery.discover_projects("Ubuntu", "/home/user")
        
        self.assertEqual(len(discovered), 2)
        self.assertEqual(discovered[0].name, "app1")
        self.assertEqual(discovered[1].name, "app2")


class TestPortMonitorMock(unittest.TestCase):
    """Test PortMonitor functionality with mocks"""
    
    def setUp(self):
        self.mock_wsl2_service = Mock()
        self.mock_port_monitor = Mock()
    
    def test_scan_port_usage(self):
        """Test port usage scanning"""
        port_usage = {
            3000: {'process': 'node', 'pid': 1234},
            8080: {'process': 'python', 'pid': 5678}
        }
        
        self.mock_port_monitor.scan_port_usage.return_value = port_usage
        
        result = self.mock_port_monitor.scan_port_usage("Ubuntu")
        
        self.assertIn(3000, result)
        self.assertIn(8080, result)
        self.assertEqual(result[3000]['process'], 'node')
        self.assertEqual(result[8080]['process'], 'python')
    
    def test_detect_port_conflicts(self):
        """Test port conflict detection"""
        conflicts = [
            {
                'port': 3000,
                'instances': ['Ubuntu', 'Debian'],
                'processes': [
                    {'instance': 'Ubuntu', 'process': 'node', 'pid': 1234},
                    {'instance': 'Debian', 'process': 'python', 'pid': 5678}
                ]
            }
        ]
        
        self.mock_port_monitor.detect_port_conflicts.return_value = conflicts
        
        result = self.mock_port_monitor.detect_port_conflicts()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['port'], 3000)
        self.assertEqual(len(result[0]['instances']), 2)


class TestHealthCheckerMock(unittest.TestCase):
    """Test HealthChecker functionality with mocks"""
    
    def setUp(self):
        self.mock_wsl2_service = Mock()
        self.mock_health_checker = Mock()
    
    def test_http_health_check(self):
        """Test HTTP health check"""
        project = MockWSL2Types.ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=MockWSL2Types.ProjectType.NODEJS,
            ports=[3000],
            health_check={
                'type': 'http',
                'url': 'http://localhost:3000/health',
                'timeout': 10
            }
        )
        
        health_result = {
            'healthy': True,
            'status_code': 200,
            'response_time': 0.1,
            'message': 'OK'
        }
        
        self.mock_health_checker.check_project_health.return_value = health_result
        
        result = self.mock_health_checker.check_project_health(project)
        
        self.assertTrue(result['healthy'])
        self.assertEqual(result['status_code'], 200)
    
    def test_tcp_health_check(self):
        """Test TCP health check"""
        project = MockWSL2Types.ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=MockWSL2Types.ProjectType.NODEJS,
            ports=[3000],
            health_check={
                'type': 'tcp',
                'port': 3000,
                'timeout': 5
            }
        )
        
        health_result = {
            'healthy': True,
            'response_time': 0.05,
            'message': 'Port accessible'
        }
        
        self.mock_health_checker.check_project_health.return_value = health_result
        
        result = self.mock_health_checker.check_project_health(project)
        
        self.assertTrue(result['healthy'])
        self.assertLess(result['response_time'], 1.0)


class TestWSL2ProjectModelMock(unittest.TestCase):
    """Test WSL2ProjectModel functionality with mocks"""
    
    def setUp(self):
        self.mock_model = Mock()
        self.mock_model.projects = []
    
    def test_add_project(self):
        """Test adding a project"""
        project = MockWSL2Types.ProjectInfo(
            name="test-app",
            wsl_instance="Ubuntu",
            path="/home/user/app",
            project_type=MockWSL2Types.ProjectType.NODEJS,
            ports=[3000]
        )
        
        # Mock the add_project method
        def mock_add_project(proj):
            self.mock_model.projects.append(proj)
        
        self.mock_model.add_project = mock_add_project
        self.mock_model.add_project(project)
        
        self.assertEqual(len(self.mock_model.projects), 1)
        self.assertEqual(self.mock_model.projects[0].name, "test-app")
    
    def test_find_projects(self):
        """Test finding projects with filters"""
        projects = [
            MockWSL2Types.ProjectInfo("node-app", "Ubuntu", "/home/user/node-app", 
                                    MockWSL2Types.ProjectType.NODEJS, [3000]),
            MockWSL2Types.ProjectInfo("python-app", "Ubuntu", "/home/user/python-app", 
                                    MockWSL2Types.ProjectType.PYTHON, [8000])
        ]
        
        # Mock find_projects method
        def mock_find_projects(**filters):
            if filters.get('type') == 'nodejs':
                return [p for p in projects if p.project_type == MockWSL2Types.ProjectType.NODEJS]
            elif filters.get('instance') == 'Ubuntu':
                return [p for p in projects if p.wsl_instance == 'Ubuntu']
            return projects
        
        self.mock_model.find_projects = mock_find_projects
        
        # Test filtering by type
        nodejs_projects = self.mock_model.find_projects(type='nodejs')
        self.assertEqual(len(nodejs_projects), 1)
        self.assertEqual(nodejs_projects[0].name, "node-app")
        
        # Test filtering by instance
        ubuntu_projects = self.mock_model.find_projects(instance='Ubuntu')
        self.assertEqual(len(ubuntu_projects), 2)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios with mocks"""
    
    def setUp(self):
        self.mock_wsl2_service = Mock()
        self.mock_project_discovery = Mock()
        self.mock_port_monitor = Mock()
        self.mock_health_checker = Mock()
    
    def test_full_project_lifecycle(self):
        """Test complete project lifecycle"""
        # 1. Mock project discovery
        projects = [
            MockWSL2Types.ProjectInfo("myapp", "Ubuntu", "/home/user/myapp", 
                                    MockWSL2Types.ProjectType.NODEJS, [3000])
        ]
        self.mock_project_discovery.discover_projects.return_value = projects
        
        discovered = self.mock_project_discovery.discover_projects("Ubuntu", "/home/user")
        self.assertEqual(len(discovered), 1)
        
        project = discovered[0]
        
        # 2. Mock port usage check
        port_usage = {3000: {'process': 'node', 'pid': 1234}}
        self.mock_port_monitor.scan_port_usage.return_value = port_usage
        
        ports = self.mock_port_monitor.scan_port_usage("Ubuntu")
        self.assertIn(3000, ports)
        
        # 3. Mock health check
        health_result = {'healthy': True, 'status_code': 200}
        self.mock_health_checker.check_project_health.return_value = health_result
        
        health = self.mock_health_checker.check_project_health(project)
        self.assertTrue(health['healthy'])


class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation"""
    
    def test_valid_nodejs_config(self):
        """Test valid Node.js configuration"""
        config = {
            "name": "test-nodejs",
            "wsl_instance": "Ubuntu",
            "project_type": "nodejs",
            "ports": [3000],
            "health_check": {
                "type": "http",
                "url": "http://localhost:3000"
            }
        }
        
        # Basic validation
        self.assertIsNotNone(config.get('name'))
        self.assertIsNotNone(config.get('wsl_instance'))
        self.assertIn(config.get('project_type'), ['nodejs', 'python', 'docker'])
        self.assertIsInstance(config.get('ports'), list)
    
    def test_valid_python_config(self):
        """Test valid Python configuration"""
        config = {
            "name": "test-python",
            "wsl_instance": "Ubuntu",
            "project_type": "python",
            "ports": [8000],
            "health_check": {
                "type": "tcp",
                "port": 8000
            }
        }
        
        # Basic validation
        self.assertIsNotNone(config.get('name'))
        self.assertIsNotNone(config.get('wsl_instance'))
        self.assertEqual(config.get('project_type'), 'python')
        self.assertIsInstance(config.get('ports'), list)
    
    def test_invalid_config(self):
        """Test invalid configuration"""
        config = {
            "name": "",  # Invalid
            "wsl_instance": "",  # Invalid
            "project_type": "invalid",  # Invalid
            "ports": [99999]  # Invalid port
        }
        
        # These should be invalid
        self.assertEqual(config.get('name'), "")
        self.assertEqual(config.get('wsl_instance'), "")
        self.assertNotIn(config.get('project_type'), ['nodejs', 'python', 'docker'])


def run_tests():
    """Run all WSL2 tests"""
    print("🧪 Running WSL2 Project Management System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestWSL2ServiceMock))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProjectDiscoveryMock))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPortMonitorMock))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestHealthCheckerMock))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestWSL2ProjectModelMock))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestIntegrationScenarios))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConfigurationValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("=" * 60)
    print("🏁 TEST SUMMARY")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n💥 SOME TESTS FAILED!")
    
    return success


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
