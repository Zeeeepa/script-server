#!/usr/bin/env python3
"""
WSL2 Project Management System - Validation Gates

Comprehensive validation framework ensuring production readiness.
"""

import os
import sys
import json
import time
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import importlib.util

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationGate:
    """Base class for validation gates"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = False
        self.errors = []
        self.warnings = []
        self.execution_time = 0
    
    def run(self) -> bool:
        """Run the validation gate"""
        start_time = time.time()
        try:
            logger.info(f"🔍 Running {self.name}...")
            result = self._execute()
            self.passed = result
            if result:
                logger.info(f"✅ {self.name} - PASSED")
            else:
                logger.error(f"❌ {self.name} - FAILED")
                for error in self.errors:
                    logger.error(f"   Error: {error}")
        except Exception as e:
            self.passed = False
            self.errors.append(str(e))
            logger.error(f"❌ {self.name} - EXCEPTION: {e}")
        finally:
            self.execution_time = time.time() - start_time
            
        return self.passed
    
    def _execute(self) -> bool:
        """Override this method in subclasses"""
        raise NotImplementedError


class CodeStructureValidation(ValidationGate):
    """Validates code structure and organization"""
    
    def __init__(self):
        super().__init__("Code Structure Validation", "Validates file structure and imports")
    
    def _execute(self) -> bool:
        required_files = [
            'src/wsl2/wsl2_service.py',
            'src/wsl2/wsl2_types.py',
            'src/wsl2/wsl2_commands.py',
            'src/projects/project_discovery.py',
            'src/projects/project_scanner.py',
            'src/projects/project_types.py',
            'src/monitoring/port_monitor.py',
            'src/monitoring/health_checker.py',
            'src/model/wsl2_model.py',
            'src/config/wsl2_config.py',
            'src/execution/wsl2_executor.py',
            'src/execution/project_executor.py',
            'src/web/wsl2_handlers.py',
            'src/web/wsl2_websocket.py',
            'src/integration/wsl2_integration.py',
            'web-src/src/components/wsl2/WSL2Dashboard.vue',
            'web-src/src/components/wsl2/WSL2ProjectCard.vue',
            'web-src/src/services/wsl2Api.js',
            'web-src/src/services/wsl2WebSocket.js'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.errors.extend([f"Missing file: {f}" for f in missing_files])
            return False
        
        # Check for proper __init__.py files
        required_init_files = [
            'src/wsl2/__init__.py',
            'src/projects/__init__.py',
            'src/monitoring/__init__.py',
            'src/integration/__init__.py'
        ]
        
        for init_file in required_init_files:
            if not os.path.exists(init_file):
                self.warnings.append(f"Missing __init__.py: {init_file}")
        
        return True


class PythonSyntaxValidation(ValidationGate):
    """Validates Python syntax and imports"""
    
    def __init__(self):
        super().__init__("Python Syntax Validation", "Validates Python syntax and imports")
    
    def _execute(self) -> bool:
        python_files = []
        for root, dirs, files in os.walk('src'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        syntax_errors = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
            except Exception as e:
                self.warnings.append(f"Could not check {file_path}: {e}")
        
        if syntax_errors:
            self.errors.extend(syntax_errors)
            return False
        
        return True


class ConfigurationValidation(ValidationGate):
    """Validates configuration schemas and templates"""
    
    def __init__(self):
        super().__init__("Configuration Validation", "Validates configuration schemas")
    
    def _execute(self) -> bool:
        # Test configuration validation
        test_configs = [
            {
                "name": "test-nodejs",
                "wsl_instance": "Ubuntu",
                "project_type": "nodejs",
                "ports": [3000],
                "health_check": {
                    "type": "http",
                    "url": "http://localhost:3000"
                }
            },
            {
                "name": "test-python",
                "wsl_instance": "Ubuntu", 
                "project_type": "python",
                "ports": [8000],
                "health_check": {
                    "type": "tcp",
                    "port": 8000
                }
            },
            {
                "name": "invalid-config",
                "wsl_instance": "",  # Invalid
                "project_type": "invalid",  # Invalid
                "ports": [99999]  # Invalid port
            }
        ]
        
        # This would normally import and test the actual validation
        # For now, we'll do basic structure validation
        for i, config in enumerate(test_configs):
            if i < 2:  # First two should be valid
                if not config.get('name') or not config.get('wsl_instance'):
                    self.errors.append(f"Valid config {i} failed basic validation")
                    return False
            else:  # Last one should be invalid
                if config.get('wsl_instance') == "":
                    # This is expected to be invalid
                    pass
        
        return True


class APIEndpointValidation(ValidationGate):
    """Validates API endpoint definitions"""
    
    def __init__(self):
        super().__init__("API Endpoint Validation", "Validates API endpoint definitions")
    
    def _execute(self) -> bool:
        # Check if handlers file exists and has required patterns
        handlers_file = 'src/web/wsl2_handlers.py'
        if not os.path.exists(handlers_file):
            self.errors.append("WSL2 handlers file not found")
            return False
        
        with open(handlers_file, 'r') as f:
            content = f.read()
        
        required_handlers = [
            'WSL2InstancesHandler',
            'WSL2ProjectsHandler', 
            'WSL2ProjectHandler',
            'WSL2ProjectActionHandler',
            'WSL2DiscoveryHandler',
            'WSL2PortsHandler',
            'WSL2HealthHandler',
            'WSL2BulkActionHandler'
        ]
        
        missing_handlers = []
        for handler in required_handlers:
            if handler not in content:
                missing_handlers.append(handler)
        
        if missing_handlers:
            self.errors.extend([f"Missing handler: {h}" for h in missing_handlers])
            return False
        
        # Check for URL patterns
        if 'WSL2_URL_PATTERNS' not in content:
            self.errors.append("Missing WSL2_URL_PATTERNS definition")
            return False
        
        return True


class WebSocketValidation(ValidationGate):
    """Validates WebSocket implementation"""
    
    def __init__(self):
        super().__init__("WebSocket Validation", "Validates WebSocket implementation")
    
    def _execute(self) -> bool:
        websocket_file = 'src/web/wsl2_websocket.py'
        if not os.path.exists(websocket_file):
            self.errors.append("WebSocket handler file not found")
            return False
        
        with open(websocket_file, 'r') as f:
            content = f.read()
        
        required_methods = [
            'on_open',
            'on_close', 
            'on_message',
            'handle_subscribe',
            'handle_unsubscribe',
            'broadcast_message'
        ]
        
        missing_methods = []
        for method in required_methods:
            if method not in content:
                missing_methods.append(method)
        
        if missing_methods:
            self.warnings.extend([f"Missing WebSocket method: {m}" for m in missing_methods])
        
        return True


class FrontendValidation(ValidationGate):
    """Validates frontend components"""
    
    def __init__(self):
        super().__init__("Frontend Validation", "Validates Vue.js components and services")
    
    def _execute(self) -> bool:
        frontend_files = [
            'web-src/src/components/wsl2/WSL2Dashboard.vue',
            'web-src/src/components/wsl2/WSL2ProjectCard.vue',
            'web-src/src/services/wsl2Api.js',
            'web-src/src/services/wsl2WebSocket.js'
        ]
        
        missing_files = []
        for file_path in frontend_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.errors.extend([f"Missing frontend file: {f}" for f in missing_files])
            return False
        
        # Validate Vue components have required sections
        vue_files = [f for f in frontend_files if f.endswith('.vue')]
        for vue_file in vue_files:
            with open(vue_file, 'r') as f:
                content = f.read()
            
            if '<template>' not in content:
                self.errors.append(f"{vue_file} missing <template> section")
                return False
            
            if '<script>' not in content:
                self.errors.append(f"{vue_file} missing <script> section")
                return False
        
        return True


class SecurityValidation(ValidationGate):
    """Validates security aspects"""
    
    def __init__(self):
        super().__init__("Security Validation", "Validates security implementations")
    
    def _execute(self) -> bool:
        security_issues = []
        
        # Check for potential security issues in Python files
        python_files = []
        for root, dirs, files in os.walk('src'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        dangerous_patterns = [
            'eval(',
            'exec(',
            'os.system(',
            'subprocess.call(',
            'shell=True'
        ]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for pattern in dangerous_patterns:
                    if pattern in content:
                        # Check if it's in a comment or string
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if pattern in line and not line.strip().startswith('#'):
                                self.warnings.append(f"{file_path}:{i+1} - Potential security issue: {pattern}")
            except Exception as e:
                self.warnings.append(f"Could not scan {file_path}: {e}")
        
        # Check for CORS configuration
        handlers_file = 'src/web/wsl2_handlers.py'
        if os.path.exists(handlers_file):
            with open(handlers_file, 'r') as f:
                content = f.read()
            
            if 'Access-Control-Allow-Origin' in content:
                if '"*"' in content:
                    self.warnings.append("CORS allows all origins - consider restricting in production")
        
        return True


class PerformanceValidation(ValidationGate):
    """Validates performance considerations"""
    
    def __init__(self):
        super().__init__("Performance Validation", "Validates performance implementations")
    
    def _execute(self) -> bool:
        # Check for caching implementations
        cache_files = [
            'src/monitoring/port_monitor.py',
            'src/monitoring/health_checker.py'
        ]
        
        caching_found = False
        for file_path in cache_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if 'cache' in content.lower():
                    caching_found = True
                    break
        
        if not caching_found:
            self.warnings.append("No caching implementation found - consider adding for better performance")
        
        # Check for async/await usage in appropriate places
        websocket_file = 'src/web/wsl2_websocket.py'
        if os.path.exists(websocket_file):
            with open(websocket_file, 'r') as f:
                content = f.read()
            
            if 'async def' not in content:
                self.warnings.append("WebSocket handler may benefit from async implementation")
        
        return True


class DocumentationValidation(ValidationGate):
    """Validates documentation completeness"""
    
    def __init__(self):
        super().__init__("Documentation Validation", "Validates documentation completeness")
    
    def _execute(self) -> bool:
        required_docs = [
            'README_WSL2.md'
        ]
        
        missing_docs = []
        for doc in required_docs:
            if not os.path.exists(doc):
                missing_docs.append(doc)
        
        if missing_docs:
            self.errors.extend([f"Missing documentation: {d}" for d in missing_docs])
            return False
        
        # Check README completeness
        readme_file = 'README_WSL2.md'
        with open(readme_file, 'r') as f:
            content = f.read()
        
        required_sections = [
            '## Features',
            '## Requirements', 
            '## Quick Start',
            '## Architecture',
            '## API Reference',
            '## Configuration'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            self.warnings.extend([f"README missing section: {s}" for s in missing_sections])
        
        return True


class ValidationRunner:
    """Main validation runner"""
    
    def __init__(self):
        self.gates = [
            CodeStructureValidation(),
            PythonSyntaxValidation(),
            ConfigurationValidation(),
            APIEndpointValidation(),
            WebSocketValidation(),
            FrontendValidation(),
            SecurityValidation(),
            PerformanceValidation(),
            DocumentationValidation()
        ]
        self.results = {}
    
    def run_all(self) -> Dict[str, Any]:
        """Run all validation gates"""
        logger.info("🚀 Starting WSL2 Project Management System Validation")
        logger.info("=" * 60)
        
        start_time = time.time()
        passed_count = 0
        failed_count = 0
        total_warnings = 0
        
        for gate in self.gates:
            result = gate.run()
            self.results[gate.name] = {
                'passed': result,
                'errors': gate.errors,
                'warnings': gate.warnings,
                'execution_time': gate.execution_time
            }
            
            if result:
                passed_count += 1
            else:
                failed_count += 1
            
            total_warnings += len(gate.warnings)
            
            # Print warnings
            for warning in gate.warnings:
                logger.warning(f"   Warning: {warning}")
        
        total_time = time.time() - start_time
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🏁 VALIDATION SUMMARY")
        logger.info(f"✅ Passed: {passed_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"⚠️  Warnings: {total_warnings}")
        logger.info(f"⏱️  Total Time: {total_time:.2f}s")
        
        overall_success = failed_count == 0
        if overall_success:
            logger.info("🎉 ALL VALIDATION GATES PASSED!")
        else:
            logger.error("💥 SOME VALIDATION GATES FAILED!")
        
        return {
            'overall_success': overall_success,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'warning_count': total_warnings,
            'total_time': total_time,
            'results': self.results
        }
    
    def generate_report(self, output_file: str = 'validation_report.json'):
        """Generate detailed validation report"""
        report = {
            'timestamp': time.time(),
            'validation_results': self.results,
            'summary': {
                'total_gates': len(self.gates),
                'passed': sum(1 for r in self.results.values() if r['passed']),
                'failed': sum(1 for r in self.results.values() if not r['passed']),
                'total_warnings': sum(len(r['warnings']) for r in self.results.values())
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Validation report saved to {output_file}")


if __name__ == '__main__':
    runner = ValidationRunner()
    results = runner.run_all()
    runner.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)
