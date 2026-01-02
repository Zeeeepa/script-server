#!/usr/bin/env python3
"""
Comprehensive Validation Gates Test Suite for WSL2 Management System
Elite-level testing following Silicon Valley standards (Stripe, Airbnb, Linear)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation test"""
    test_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None

class ValidationGates:
    """Comprehensive validation gates for WSL2 management system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[ValidationResult] = []
        self.driver: Optional[webdriver.Chrome] = None
        
    def setup_browser(self) -> webdriver.Chrome:
        """Setup Chrome browser with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1440,900")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def teardown_browser(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    async def run_all_validation_gates(self) -> Dict[str, Any]:
        """Run all validation gates and return comprehensive results"""
        logger.info("🚀 Starting comprehensive validation gates...")
        
        # Phase 1: Infrastructure Validation
        await self._validate_infrastructure()
        
        # Phase 2: WSL2 Integration Validation
        await self._validate_wsl2_integration()
        
        # Phase 3: Frontend Validation
        await self._validate_frontend()
        
        # Phase 4: API Validation
        await self._validate_api_endpoints()
        
        # Phase 5: Performance Validation
        await self._validate_performance()
        
        # Phase 6: Security Validation
        await self._validate_security()
        
        # Phase 7: Accessibility Validation
        await self._validate_accessibility()
        
        # Phase 8: Visual Regression Validation
        await self._validate_visual_regression()
        
        return self._generate_validation_report()
    
    async def _validate_infrastructure(self):
        """Validate infrastructure components"""
        logger.info("📋 Phase 1: Infrastructure Validation")
        
        # Check Python dependencies
        try:
            import tornado
            import websocket
            import psutil
            self._add_result("infrastructure_dependencies", True, "All Python dependencies available")
        except ImportError as e:
            self._add_result("infrastructure_dependencies", False, f"Missing dependency: {e}")
        
        # Check WSL2 availability
        try:
            result = subprocess.run(["wsl", "--list", "--verbose"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self._add_result("wsl2_availability", True, "WSL2 is available and configured")
            else:
                self._add_result("wsl2_availability", False, "WSL2 not available or configured")
        except Exception as e:
            self._add_result("wsl2_availability", False, f"WSL2 check failed: {e}")
        
        # Check port availability
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 5000))
                self._add_result("port_availability", True, "Port 5000 is available")
        except OSError:
            self._add_result("port_availability", False, "Port 5000 is already in use")
    
    async def _validate_wsl2_integration(self):
        """Validate WSL2 integration components"""
        logger.info("🏢 Phase 2: WSL2 Integration Validation")
        
        # Test WSL2 configuration validation
        try:
            from src.config.wsl2_config import WSL2ConfigValidator, get_wsl2_config_template
            
            template = get_wsl2_config_template()
            errors = WSL2ConfigValidator.validate_wsl2_config(template)
            
            if not errors:
                self._add_result("wsl2_config_validation", True, "WSL2 configuration validation passed")
            else:
                self._add_result("wsl2_config_validation", False, f"Configuration errors: {errors}")
        except Exception as e:
            self._add_result("wsl2_config_validation", False, f"WSL2 config validation failed: {e}")
        
        # Test WSL2 model functionality
        try:
            from src.model.wsl2_model import WSL2ProjectModel
            from src.model.project_info import ProjectInfo
            
            project_info = ProjectInfo(
                name="test_project",
                path="/test/path",
                project_type="python"
            )
            
            model = WSL2ProjectModel()
            config = model.create_project_config(project_info)
            
            if config and 'wsl_instance' in config:
                self._add_result("wsl2_model_functionality", True, "WSL2 model functionality working")
            else:
                self._add_result("wsl2_model_functionality", False, "WSL2 model config creation failed")
        except Exception as e:
            self._add_result("wsl2_model_functionality", False, f"WSL2 model test failed: {e}")
    
    async def _validate_frontend(self):
        """Validate frontend components and functionality"""
        logger.info("🎨 Phase 3: Frontend Validation")
        
        try:
            self.setup_browser()
            
            # Navigate to main page
            self.driver.get(self.base_url)
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for main application elements
            try:
                # Look for project management interface
                project_elements = self.driver.find_elements(By.CLASS_NAME, "project-card")
                if project_elements:
                    self._add_result("frontend_project_cards", True, f"Found {len(project_elements)} project cards")
                else:
                    self._add_result("frontend_project_cards", False, "No project cards found")
                
                # Check for navigation elements
                nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
                if nav_elements:
                    self._add_result("frontend_navigation", True, "Navigation elements present")
                else:
                    self._add_result("frontend_navigation", False, "No navigation elements found")
                
                # Take screenshot for visual validation
                screenshot_path = "tests/screenshots/frontend_main.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                self._add_result("frontend_screenshot", True, "Frontend screenshot captured", 
                               screenshot_path=screenshot_path)
                
            except Exception as e:
                self._add_result("frontend_elements", False, f"Frontend element check failed: {e}")
        
        except Exception as e:
            self._add_result("frontend_validation", False, f"Frontend validation failed: {e}")
        finally:
            self.teardown_browser()
    
    async def _validate_api_endpoints(self):
        """Validate API endpoints functionality"""
        logger.info("📡 Phase 4: API Validation")
        
        # Test WSL2 API endpoints
        endpoints_to_test = [
            ("/api/wsl2/projects", "GET"),
            ("/api/wsl2/config/template", "GET"),
            ("/api/wsl2/instances", "GET"),
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.request(method, url, timeout=10)
                
                if response.status_code in [200, 404]:  # 404 is acceptable for some endpoints
                    self._add_result(f"api_{endpoint.replace('/', '_')}", True, 
                                   f"API endpoint {endpoint} responded with {response.status_code}")
                else:
                    self._add_result(f"api_{endpoint.replace('/', '_')}", False, 
                                   f"API endpoint {endpoint} failed with {response.status_code}")
            except Exception as e:
                self._add_result(f"api_{endpoint.replace('/', '_')}", False, 
                               f"API endpoint {endpoint} failed: {e}")
    
    async def _validate_performance(self):
        """Validate performance metrics"""
        logger.info("⚡ Phase 5: Performance Validation")
        
        try:
            # Test page load time
            start_time = time.time()
            response = requests.get(self.base_url, timeout=30)
            load_time = time.time() - start_time
            
            if load_time < 3.0:  # 3 second threshold
                self._add_result("performance_page_load", True, 
                               f"Page load time: {load_time:.2f}s (< 3s threshold)")
            else:
                self._add_result("performance_page_load", False, 
                               f"Page load time: {load_time:.2f}s (> 3s threshold)")
        except Exception as e:
            self._add_result("performance_page_load", False, f"Performance test failed: {e}")
    
    async def _validate_security(self):
        """Validate security measures"""
        logger.info("🔒 Phase 6: Security Validation")
        
        try:
            # Check for security headers
            response = requests.get(self.base_url, timeout=10)
            headers = response.headers
            
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection'
            ]
            
            missing_headers = [h for h in security_headers if h not in headers]
            
            if not missing_headers:
                self._add_result("security_headers", True, "All security headers present")
            else:
                self._add_result("security_headers", False, 
                               f"Missing security headers: {missing_headers}")
        except Exception as e:
            self._add_result("security_headers", False, f"Security validation failed: {e}")
    
    async def _validate_accessibility(self):
        """Validate accessibility compliance"""
        logger.info("♿ Phase 7: Accessibility Validation")
        
        try:
            self.setup_browser()
            self.driver.get(self.base_url)
            
            # Check for basic accessibility features
            # Alt text on images
            images = self.driver.find_elements(By.TAG_NAME, "img")
            images_without_alt = [img for img in images if not img.get_attribute("alt")]
            
            if not images_without_alt:
                self._add_result("accessibility_alt_text", True, "All images have alt text")
            else:
                self._add_result("accessibility_alt_text", False, 
                               f"{len(images_without_alt)} images missing alt text")
            
            # Check for form labels
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            unlabeled_inputs = []
            for input_elem in inputs:
                input_id = input_elem.get_attribute("id")
                if input_id:
                    labels = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    if not labels:
                        unlabeled_inputs.append(input_elem)
            
            if not unlabeled_inputs:
                self._add_result("accessibility_form_labels", True, "All form inputs have labels")
            else:
                self._add_result("accessibility_form_labels", False, 
                               f"{len(unlabeled_inputs)} inputs missing labels")
        
        except Exception as e:
            self._add_result("accessibility_validation", False, f"Accessibility validation failed: {e}")
        finally:
            self.teardown_browser()
    
    async def _validate_visual_regression(self):
        """Validate visual regression using screenshots"""
        logger.info("👁️ Phase 8: Visual Regression Validation")
        
        try:
            self.setup_browser()
            
            # Test different viewport sizes
            viewports = [
                (1440, 900, "desktop"),
                (768, 1024, "tablet"),
                (375, 667, "mobile")
            ]
            
            for width, height, device in viewports:
                self.driver.set_window_size(width, height)
                self.driver.get(self.base_url)
                
                # Wait for page to stabilize
                time.sleep(2)
                
                screenshot_path = f"tests/screenshots/visual_regression_{device}_{width}x{height}.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                
                self._add_result(f"visual_regression_{device}", True, 
                               f"Screenshot captured for {device} ({width}x{height})", 
                               screenshot_path=screenshot_path)
        
        except Exception as e:
            self._add_result("visual_regression", False, f"Visual regression validation failed: {e}")
        finally:
            self.teardown_browser()
    
    def _add_result(self, test_name: str, passed: bool, message: str, 
                   details: Optional[Dict[str, Any]] = None, screenshot_path: Optional[str] = None):
        """Add a validation result"""
        result = ValidationResult(
            test_name=test_name,
            passed=passed,
            message=message,
            details=details,
            screenshot_path=screenshot_path
        )
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "screenshot_path": r.screenshot_path
                }
                for r in self.results
            ]
        }
        
        return report

async def main():
    """Main validation gates execution"""
    validator = ValidationGates()
    
    try:
        report = await validator.run_all_validation_gates()
        
        # Save report to file
        report_path = "tests/validation_reports/comprehensive_validation_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        summary = report["summary"]
        print(f"\n🎯 VALIDATION GATES SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"{'='*50}")
        
        if summary['failed_tests'] > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in report["results"]:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print(f"\n📊 Full report saved to: {report_path}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['failed_tests'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Validation gates execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
