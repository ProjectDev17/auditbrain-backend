"""
QA API Testing Script for AuditBrain Backend
Comprehensive testing of all API endpoints with detailed reporting
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TestStatus(Enum):
    PASSED = "✓ PASSED"
    FAILED = "✗ FAILED"
    WARNING = "⚠ WARNING"
    SKIPPED = "○ SKIPPED"


@dataclass
class TestResult:
    endpoint: str
    method: str
    status: TestStatus = TestStatus.PASSED
    response_code: Optional[int] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.refresh_token = None
        self.results: List[TestResult] = []
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def add_result(self, result: TestResult):
        """Add test result to collection"""
        self.results.append(result)
        status_symbol = result.status.value.split()[0]
        self.log(f"{status_symbol} {result.method} {result.endpoint} - {result.message}")
    
    def set_auth_header(self):
        """Set authorization header with JWT token"""
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def clear_auth_header(self):
        """Clear authorization header"""
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
    
    # ==================== AUTHENTICATION TESTS ====================
    
    def test_login_valid(self, username: str, password: str) -> TestResult:
        """Test login with valid credentials"""
        endpoint = "/api/auth/login/"
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "email": username,  # El sistema usa email como USERNAME_FIELD
            "password": password
        }
        
        try:
            response = self.session.post(url, json=payload)
            result = TestResult(endpoint=endpoint, method="POST", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                if "access" in data and "refresh" in data:
                    self.token = data["access"]
                    self.refresh_token = data["refresh"]
                    result.status = TestStatus.PASSED
                    result.message = "Login successful, tokens received"
                    result.details = {"has_access_token": True, "has_refresh_token": True}
                else:
                    result.status = TestStatus.FAILED
                    result.message = "Login response missing tokens"
                    result.errors.append("Response does not contain 'access' or 'refresh' tokens")
            else:
                result.status = TestStatus.FAILED
                result.message = f"Login failed with status {response.status_code}"
                result.errors.append(f"Expected 200, got {response.status_code}")
                try:
                    result.details = response.json()
                except:
                    result.details = {"raw_response": response.text}
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="POST",
                status=TestStatus.FAILED,
                message=f"Exception during login: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_login_invalid(self) -> TestResult:
        """Test login with invalid credentials"""
        endpoint = "/api/auth/login/"
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "email": "invalid@test.com",
            "password": "wrong_password"
        }
        
        try:
            response = self.session.post(url, json=payload)
            result = TestResult(endpoint=endpoint, method="POST", response_code=response.status_code)
            
            if response.status_code == 401:
                result.status = TestStatus.PASSED
                result.message = "Correctly rejected invalid credentials"
            elif response.status_code == 400:
                result.status = TestStatus.PASSED
                result.message = "Correctly rejected invalid credentials (400)"
                result.warnings.append("Consider using 401 instead of 400 for authentication failures")
            else:
                result.status = TestStatus.FAILED
                result.message = f"Unexpected status code: {response.status_code}"
                result.errors.append(f"Expected 401, got {response.status_code}")
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="POST",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_token_verify(self) -> TestResult:
        """Test token verification"""
        endpoint = "/api/auth/token/verify/"
        url = f"{self.base_url}{endpoint}"
        
        if not self.token:
            return TestResult(
                endpoint=endpoint,
                method="POST",
                status=TestStatus.SKIPPED,
                message="No token available to verify"
            )
        
        payload = {"token": self.token}
        
        try:
            response = self.session.post(url, json=payload)
            result = TestResult(endpoint=endpoint, method="POST", response_code=response.status_code)
            
            if response.status_code == 200:
                result.status = TestStatus.PASSED
                result.message = "Token verified successfully"
            else:
                result.status = TestStatus.FAILED
                result.message = f"Token verification failed: {response.status_code}"
                result.errors.append(f"Expected 200, got {response.status_code}")
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="POST",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_token_refresh(self) -> TestResult:
        """Test token refresh"""
        endpoint = "/api/auth/token/refresh/"
        url = f"{self.base_url}{endpoint}"
        
        if not self.refresh_token:
            return TestResult(
                endpoint=endpoint,
                method="POST",
                status=TestStatus.SKIPPED,
                message="No refresh token available"
            )
        
        payload = {"refresh": self.refresh_token}
        
        try:
            response = self.session.post(url, json=payload)
            result = TestResult(endpoint=endpoint, method="POST", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                if "access" in data:
                    self.token = data["access"]
                    result.status = TestStatus.PASSED
                    result.message = "Token refreshed successfully"
                else:
                    result.status = TestStatus.WARNING
                    result.message = "Token refresh succeeded but no access token in response"
                    result.warnings.append("Response should contain new 'access' token")
            else:
                result.status = TestStatus.FAILED
                result.message = f"Token refresh failed: {response.status_code}"
                result.errors.append(f"Expected 200, got {response.status_code}")
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="POST",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_profile_get(self) -> TestResult:
        """Test getting user profile"""
        endpoint = "/api/auth/profile/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "username", "email"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if not missing_fields:
                    result.status = TestStatus.PASSED
                    result.message = "Profile retrieved successfully"
                    result.details = {"fields": list(data.keys())}
                else:
                    result.status = TestStatus.WARNING
                    result.message = "Profile retrieved but missing expected fields"
                    result.warnings.append(f"Missing fields: {', '.join(missing_fields)}")
            elif response.status_code == 401:
                result.status = TestStatus.FAILED
                result.message = "Authentication failed"
                result.errors.append("Token may be invalid or expired")
            else:
                result.status = TestStatus.FAILED
                result.message = f"Unexpected status: {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    # ==================== USERS VIEWSET TESTS ====================
    
    def test_users_list(self) -> TestResult:
        """Test listing users with pagination"""
        endpoint = "/api/auth/users/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check pagination structure
                if "results" in data:
                    result.status = TestStatus.PASSED
                    result.message = f"Users list retrieved ({len(data['results'])} users)"
                    result.details = {
                        "count": data.get("count", 0),
                        "has_pagination": True,
                        "has_next": data.get("next") is not None,
                        "has_previous": data.get("previous") is not None
                    }
                else:
                    result.status = TestStatus.WARNING
                    result.message = "Users retrieved but no pagination structure"
                    result.warnings.append("Response should use pagination with 'results' key")
            elif response.status_code == 403:
                result.status = TestStatus.WARNING
                result.message = "Permission denied - user may not have access"
                result.warnings.append("Check if user has permission to list users")
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_users_list_with_filters(self) -> TestResult:
        """Test users list with query filters"""
        endpoint = "/api/auth/users/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        test_cases = [
            {"params": {"page": 1}, "description": "pagination"},
            {"params": {"ordering": "username"}, "description": "ordering"},
            {"params": {"search": "admin"}, "description": "search"},
        ]
        
        result = TestResult(endpoint=endpoint, method="GET", status=TestStatus.PASSED)
        result.details["filter_tests"] = []
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            try:
                response = self.session.get(url, params=test_case["params"])
                test_result = {
                    "description": test_case["description"],
                    "params": test_case["params"],
                    "status_code": response.status_code,
                    "passed": response.status_code == 200
                }
                result.details["filter_tests"].append(test_result)
                
                if response.status_code == 200:
                    passed += 1
                else:
                    failed += 1
                    result.errors.append(f"Filter '{test_case['description']}' failed: {response.status_code}")
            
            except Exception as e:
                failed += 1
                result.errors.append(f"Filter '{test_case['description']}' exception: {str(e)}")
        
        if failed == 0:
            result.status = TestStatus.PASSED
            result.message = f"All {passed} filter tests passed"
        elif passed > 0:
            result.status = TestStatus.WARNING
            result.message = f"{passed} passed, {failed} failed"
        else:
            result.status = TestStatus.FAILED
            result.message = f"All {failed} filter tests failed"
        
        return result
    
    # ==================== AUDITS TESTS ====================
    
    def test_audits_list(self) -> TestResult:
        """Test listing audits"""
        endpoint = "/api/audits/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                result.status = TestStatus.PASSED
                result.message = f"Audits retrieved successfully"
                
                if "results" in data:
                    result.details = {
                        "count": data.get("count", 0),
                        "has_pagination": True
                    }
                else:
                    result.details = {"count": len(data) if isinstance(data, list) else 0}
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_audit_types_list(self) -> TestResult:
        """Test listing audit types"""
        endpoint = "/api/audit-types/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                result.status = TestStatus.PASSED
                result.message = "Audit types retrieved successfully"
                
                if "results" in data:
                    result.details = {"count": data.get("count", 0)}
                else:
                    result.details = {"count": len(data) if isinstance(data, list) else 0}
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_events_list(self) -> TestResult:
        """Test listing global events"""
        endpoint = "/api/events/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                result.status = TestStatus.PASSED
                result.message = "Events retrieved successfully"
                
                if "results" in data:
                    result.details = {"count": data.get("count", 0)}
                else:
                    result.details = {"count": len(data) if isinstance(data, list) else 0}
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_evidences_list(self) -> TestResult:
        """Test listing global evidences"""
        endpoint = "/api/evidences/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                result.status = TestStatus.PASSED
                result.message = "Evidences retrieved successfully"
                
                if "results" in data:
                    result.details = {"count": data.get("count", 0)}
                else:
                    result.details = {"count": len(data) if isinstance(data, list) else 0}
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    # ==================== REPORTS TESTS ====================
    
    def test_audit_summary(self) -> TestResult:
        """Test audit summary report"""
        endpoint = "/api/reports/audits/summary/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                result.status = TestStatus.PASSED
                result.message = "Audit summary retrieved"
                result.details = {"response_keys": list(data.keys()) if isinstance(data, dict) else []}
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_audit_by_period(self) -> TestResult:
        """Test audit by period report"""
        endpoint = "/api/reports/audits/by-period/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        # Test with and without date parameters
        test_cases = [
            {"params": {}, "description": "without parameters"},
            {"params": {"start_date": "2024-01-01", "end_date": "2024-12-31"}, "description": "with date range"},
        ]
        
        result = TestResult(endpoint=endpoint, method="GET", status=TestStatus.PASSED)
        result.details["tests"] = []
        passed = 0
        
        for test_case in test_cases:
            try:
                response = self.session.get(url, params=test_case["params"])
                test_result = {
                    "description": test_case["description"],
                    "status_code": response.status_code,
                    "passed": response.status_code == 200
                }
                result.details["tests"].append(test_result)
                
                if response.status_code == 200:
                    passed += 1
            except Exception as e:
                result.errors.append(f"Test '{test_case['description']}' failed: {str(e)}")
        
        if passed == len(test_cases):
            result.status = TestStatus.PASSED
            result.message = "All period report tests passed"
        elif passed > 0:
            result.status = TestStatus.WARNING
            result.message = f"{passed}/{len(test_cases)} tests passed"
        else:
            result.status = TestStatus.FAILED
            result.message = "All period report tests failed"
        
        return result
    
    def test_audit_by_user(self) -> TestResult:
        """Test audit by user report"""
        endpoint = "/api/reports/audits/by-user/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                result.status = TestStatus.PASSED
                result.message = "Audit by user report retrieved"
                result.details = {"response_type": type(data).__name__}
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_events_summary(self) -> TestResult:
        """Test events summary report"""
        endpoint = "/api/reports/events/summary/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                result.status = TestStatus.PASSED
                result.message = "Events summary retrieved"
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    def test_evidences_summary(self) -> TestResult:
        """Test evidences summary report"""
        endpoint = "/api/reports/evidences/summary/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 200:
                result.status = TestStatus.PASSED
                result.message = "Evidences summary retrieved"
            else:
                result.status = TestStatus.FAILED
                result.message = f"Failed with status {response.status_code}"
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_unauthorized_access(self) -> TestResult:
        """Test accessing protected endpoint without authentication"""
        endpoint = "/api/audits/"
        url = f"{self.base_url}{endpoint}"
        
        self.clear_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 401:
                result.status = TestStatus.PASSED
                result.message = "Correctly returns 401 for unauthenticated request"
            else:
                result.status = TestStatus.FAILED
                result.message = f"Expected 401, got {response.status_code}"
                result.errors.append("Protected endpoints should return 401 without authentication")
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        # Restore auth header
        self.set_auth_header()
        
        return result
    
    def test_not_found(self) -> TestResult:
        """Test 404 error for non-existent resource"""
        endpoint = "/api/audits/99999999/"
        url = f"{self.base_url}{endpoint}"
        
        self.set_auth_header()
        
        try:
            response = self.session.get(url)
            result = TestResult(endpoint=endpoint, method="GET", response_code=response.status_code)
            
            if response.status_code == 404:
                result.status = TestStatus.PASSED
                result.message = "Correctly returns 404 for non-existent resource"
            else:
                result.status = TestStatus.WARNING
                result.message = f"Expected 404, got {response.status_code}"
                result.warnings.append("Non-existent resources should return 404")
        
        except Exception as e:
            result = TestResult(
                endpoint=endpoint,
                method="GET",
                status=TestStatus.FAILED,
                message=f"Exception: {str(e)}",
                errors=[str(e)]
            )
        
        return result
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self, username: str, password: str):
        """Run all API tests"""
        self.log("=" * 80, "INFO")
        self.log("Starting AuditBrain API QA Tests", "INFO")
        self.log("=" * 80, "INFO")
        
        # Phase 1: Authentication Tests
        self.log("\n=== PHASE 1: Authentication Tests ===", "INFO")
        self.add_result(self.test_login_invalid())
        self.add_result(self.test_login_valid(username, password))
        self.add_result(self.test_token_verify())
        self.add_result(self.test_token_refresh())
        self.add_result(self.test_profile_get())
        
        # Phase 2: User Management Tests
        self.log("\n=== PHASE 2: User Management Tests ===", "INFO")
        self.add_result(self.test_users_list())
        self.add_result(self.test_users_list_with_filters())
        
        # Phase 3: Audits Tests
        self.log("\n=== PHASE 3: Audits Tests ===", "INFO")
        self.add_result(self.test_audits_list())
        self.add_result(self.test_audit_types_list())
        self.add_result(self.test_events_list())
        self.add_result(self.test_evidences_list())
        
        # Phase 4: Reports Tests
        self.log("\n=== PHASE 4: Reports Tests ===", "INFO")
        self.add_result(self.test_audit_summary())
        self.add_result(self.test_audit_by_period())
        self.add_result(self.test_audit_by_user())
        self.add_result(self.test_events_summary())
        self.add_result(self.test_evidences_summary())
        
        # Phase 5: Error Handling Tests
        self.log("\n=== PHASE 5: Error Handling Tests ===", "INFO")
        self.add_result(self.test_unauthorized_access())
        self.add_result(self.test_not_found())
        
        self.log("\n" + "=" * 80, "INFO")
        self.log("All tests completed", "INFO")
        self.log("=" * 80, "INFO")
    
    def generate_report(self, output_file: str = "qa_test_results.md"):
        """Generate detailed markdown report"""
        
        # Calculate statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == TestStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        # Collect all errors and suggestions
        all_errors = []
        all_warnings = []
        all_suggestions = []
        
        for result in self.results:
            for error in result.errors:
                all_errors.append(f"**{result.method} {result.endpoint}**: {error}")
            for warning in result.warnings:
                all_warnings.append(f"**{result.method} {result.endpoint}**: {warning}")
            for suggestion in result.suggestions:
                all_suggestions.append(f"**{result.method} {result.endpoint}**: {suggestion}")
        
        # Generate report
        report = f"""# AuditBrain API QA Test Results

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Base URL**: {self.base_url}

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✓ Passed | {passed} | {(passed/total*100):.1f}% |
| ✗ Failed | {failed} | {(failed/total*100):.1f}% |
| ⚠ Warnings | {warnings} | {(warnings/total*100):.1f}% |
| ○ Skipped | {skipped} | {(skipped/total*100):.1f}% |
| **Total** | **{total}** | **100%** |

## Test Results by Phase

"""
        
        # Group results by phase
        phases = {
            "Authentication": [],
            "User Management": [],
            "Audits": [],
            "Reports": [],
            "Error Handling": []
        }
        
        for result in self.results:
            if "/auth/" in result.endpoint:
                phases["Authentication"].append(result)
            elif "/reports/" in result.endpoint:
                phases["Reports"].append(result)
            elif result.endpoint in ["/api/audits/99999999/", "/api/audits/"]:
                if "99999999" in result.endpoint:
                    phases["Error Handling"].append(result)
                else:
                    phases["Audits"].append(result)
            elif "/api/" in result.endpoint:
                if "users" in result.endpoint:
                    phases["User Management"].append(result)
                else:
                    phases["Audits"].append(result)
            else:
                phases["Error Handling"].append(result)
        
        for phase, results in phases.items():
            if results:
                report += f"\n### {phase}\n\n"
                report += "| Status | Method | Endpoint | Message |\n"
                report += "|--------|--------|----------|----------|\n"
                
                for result in results:
                    status_icon = result.status.value.split()[0]
                    report += f"| {status_icon} | {result.method} | `{result.endpoint}` | {result.message} |\n"
        
        # Add errors section
        if all_errors:
            report += "\n## ❌ Errors Found\n\n"
            for i, error in enumerate(all_errors, 1):
                report += f"{i}. {error}\n"
        
        # Add warnings section
        if all_warnings:
            report += "\n## ⚠️ Warnings\n\n"
            for i, warning in enumerate(all_warnings, 1):
                report += f"{i}. {warning}\n"
        
        # Add suggestions section
        if all_suggestions:
            report += "\n## 💡 Suggestions\n\n"
            for i, suggestion in enumerate(all_suggestions, 1):
                report += f"{i}. {suggestion}\n"
        
        # Write report
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        self.log(f"\nReport generated: {output_file}", "INFO")
        
        return report


def main():
    """Main entry point"""
    import sys
    
    # Configuration
    BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
    USERNAME = os.environ.get("API_USERNAME", "admin@auditbrain.com")
    PASSWORD = os.environ.get("API_PASSWORD", "admin123")
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    if len(sys.argv) > 2:
        USERNAME = sys.argv[2]
    if len(sys.argv) > 3:
        PASSWORD = sys.argv[3]
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Username: {USERNAME}")
    print(f"  Password: {'*' * len(PASSWORD)}\n")
    
    # Run tests
    tester = APITester(base_url=BASE_URL)
    tester.run_all_tests(username=USERNAME, password=PASSWORD)
    
    # Generate report
    report_path = os.path.join(os.path.dirname(__file__), "qa_test_results.md")
    tester.generate_report(output_file=report_path)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = len(tester.results)
    passed = sum(1 for r in tester.results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in tester.results if r.status == TestStatus.FAILED)
    warnings = sum(1 for r in tester.results if r.status == TestStatus.WARNING)
    
    print(f"Total Tests: {total}")
    print(f"✓ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"✗ Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"⚠ Warnings: {warnings} ({warnings/total*100:.1f}%)")
    print("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
