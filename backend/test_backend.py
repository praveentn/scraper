# backend/test_backend.py
"""
Comprehensive backend testing script for Blitz Web Scraping Platform

Run this script while the Flask app is running to test all functionality.
Usage: python test_backend.py
"""
import requests
import json
import time
import sys
import os
from datetime import datetime


class BlitzTester:
    def __init__(self, base_url="http://localhost:5232"):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
        self.auth_token = None
        self.admin_token = None
        self.test_data = {}
        self.passed_tests = 0
        self.failed_tests = 0
        
        print("🧪 Blitz Backend Testing Suite")
        print("=" * 50)
        print(f"Target URL: {base_url}")
        print(f"Started at: {datetime.now().isoformat()}")
        print()
    
    def log_test(self, test_name, success, message="", data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if message:
            print(f"   💬 {message}")
        
        if data and not success:
            print(f"   📄 Response: {json.dumps(data, indent=2)}")
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        print()
    
    def make_request(self, method, endpoint, data=None, use_auth=True, admin=False):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if use_auth:
            token = self.admin_token if admin and self.admin_token else self.auth_token
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            try:
                return response, response.json()
            except:
                return response, {'message': response.text}
                
        except requests.exceptions.RequestException as e:
            return None, {'error': str(e)}
    
    def test_health_check(self):
        """Test health endpoint"""
        response, data = self.make_request('GET', '/health', use_auth=False)
        
        if response and response.status_code == 200 and data.get('status') == 'healthy':
            self.log_test("Health Check", True, "Server is healthy")
            return True
        else:
            self.log_test("Health Check", False, "Server health check failed", data)
            return False
    
    def test_api_info(self):
        """Test API info endpoint"""
        response, data = self.make_request('GET', '/api/info', use_auth=False)
        
        if response and response.status_code == 200 and 'endpoints' in data:
            self.log_test("API Info", True, f"API version: {data.get('version')}")
            return True
        else:
            self.log_test("API Info", False, "API info endpoint failed", data)
            return False
    
    def test_email_validation_debug(self):
        """Debug email validation"""
        test_email = "testuser123@example.com"
        
        # Test the debug endpoint if available
        debug_data = {"email": test_email}
        response, data = self.make_request('POST', '/api/debug/validate-email', debug_data, use_auth=False)
        
        if response and response.status_code == 200:
            is_valid = data.get('valid', False)
            self.log_test("Email Validation Debug", True, f"Email '{test_email}' -> {is_valid}")
        else:
            self.log_test("Email Validation Debug", False, "Debug endpoint not available", data)
    
    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "email": f"testuser{int(time.time())}@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response, data = self.make_request('POST', '/api/auth/register', user_data, use_auth=False)
        
        if response and response.status_code == 201 and data.get('success'):
            self.test_data['user_email'] = user_data['email']
            self.test_data['user_password'] = user_data['password']
            self.test_data['user_id'] = data['user']['id']
            self.log_test("User Registration", True, f"User created: {user_data['email']}")
            return True
        else:
            self.log_test("User Registration", False, "Failed to register user", data)
            return False
    
    def test_admin_registration(self):
        """Test admin user registration"""
        admin_data = {
            "email": f"admin{int(time.time())}@example.com",
            "password": "adminpassword123",
            "first_name": "Admin",
            "last_name": "User"
        }
        
        response, data = self.make_request('POST', '/api/auth/register', admin_data, use_auth=False)
        
        if response and response.status_code == 201:
            # Manually set admin role (in real app, this would be done through admin panel)
            self.test_data['admin_email'] = admin_data['email']
            self.test_data['admin_password'] = admin_data['password']
            self.log_test("Admin Registration", True, f"Admin user created: {admin_data['email']}")
            return True
        else:
            self.log_test("Admin Registration", False, "Failed to register admin", data)
            return False
    
    def test_user_login(self):
        """Test user login"""
        if 'user_email' not in self.test_data:
            self.log_test("User Login", False, "No test user available")
            return False
        
        login_data = {
            "email": self.test_data['user_email'],
            "password": self.test_data['user_password']
        }
        
        response, data = self.make_request('POST', '/api/auth/login', login_data, use_auth=False)
        
        if response and response.status_code == 200 and data.get('success'):
            self.auth_token = data['tokens']['access_token']
            self.log_test("User Login", True, "User logged in successfully")
            return True
        else:
            self.log_test("User Login", False, "Login failed", data)
            return False
    
    def test_admin_login(self):
        """Test admin login"""
        if 'admin_email' not in self.test_data:
            self.log_test("Admin Login", False, "No admin user available")
            return False
        
        login_data = {
            "email": self.test_data['admin_email'],
            "password": self.test_data['admin_password']
        }
        
        response, data = self.make_request('POST', '/api/auth/login', login_data, use_auth=False)
        
        if response and response.status_code == 200 and data.get('success'):
            self.admin_token = data['tokens']['access_token']
            self.log_test("Admin Login", True, "Admin logged in successfully")
            return True
        else:
            self.log_test("Admin Login", False, "Admin login failed", data)
            return False
    
    def test_get_profile(self):
        """Test get user profile"""
        response, data = self.make_request('GET', '/api/auth/profile')
        
        if response and response.status_code == 200 and data.get('success'):
            self.log_test("Get Profile", True, f"Profile: {data['user']['email']}")
            return True
        else:
            self.log_test("Get Profile", False, "Failed to get profile", data)
            return False
    
    def test_create_project(self):
        """Test project creation"""
        project_data = {
            "name": f"Test Project {int(time.time())}",
            "description": "A test project for automated testing",
            "tags": ["test", "automation"],
            "industry": "Technology",
            "priority": "high"
        }
        
        response, data = self.make_request('POST', '/api/projects', project_data)
        
        if response and response.status_code == 201 and data.get('success'):
            self.test_data['project_id'] = data['project']['id']
            self.log_test("Create Project", True, f"Project created: {project_data['name']}")
            return True
        else:
            self.log_test("Create Project", False, "Failed to create project", data)
            return False
    
    def test_get_projects(self):
        """Test get projects"""
        response, data = self.make_request('GET', '/api/projects')
        
        if response and response.status_code == 200 and data.get('success'):
            project_count = len(data.get('projects', []))
            self.log_test("Get Projects", True, f"Found {project_count} projects")
            return True
        else:
            self.log_test("Get Projects", False, "Failed to get projects", data)
            return False
    
    def test_update_project(self):
        """Test project update"""
        if 'project_id' not in self.test_data:
            self.log_test("Update Project", False, "No test project available")
            return False
        
        update_data = {
            "description": "Updated description for automated testing",
            "priority": "medium"
        }
        
        response, data = self.make_request('PUT', f'/api/projects/{self.test_data["project_id"]}', update_data)
        
        if response and response.status_code == 200 and data.get('success'):
            self.log_test("Update Project", True, "Project updated successfully")
            return True
        else:
            self.log_test("Update Project", False, "Failed to update project", data)
            return False
    
    def test_create_website(self):
        """Test website creation"""
        if 'project_id' not in self.test_data:
            self.log_test("Create Website", False, "No test project available")
            return False
        
        website_data = {
            "project_id": self.test_data['project_id'],
            "url": "https://httpbin.org",
            "name": "HTTPBin Test Site",
            "description": "Test website for scraping",
            "crawl_depth": 2,
            "follow_external_links": False,
            "rate_limit_delay": 1.0
        }
        
        response, data = self.make_request('POST', '/api/websites', website_data)
        
        if response and response.status_code == 201 and data.get('success'):
            self.test_data['website_id'] = data['website']['id']
            self.log_test("Create Website", True, f"Website created: {website_data['url']}")
            return True
        else:
            self.log_test("Create Website", False, "Failed to create website", data)
            return False
    
    def test_scrape_single_page(self):
        """Test single page scraping"""
        if 'website_id' not in self.test_data:
            self.log_test("Scrape Single Page", False, "No test website available")
            return False
        
        scrape_data = {
            "website_id": self.test_data['website_id'],
            "single_page": True,
            "url": "https://httpbin.org/html",
            "use_selenium": False
        }
        
        response, data = self.make_request('POST', '/api/scraping/run', scrape_data)
        
        if response and response.status_code == 200 and data.get('success'):
            if 'page' in data and data['page']:
                self.test_data['page_id'] = data['page']['id']
            self.log_test("Scrape Single Page", True, "Page scraped successfully")
            return True
        else:
            self.log_test("Scrape Single Page", False, "Failed to scrape page", data)
            return False
    
    def test_get_scraping_status(self):
        """Test scraping status"""
        if 'website_id' not in self.test_data:
            self.log_test("Get Scraping Status", False, "No test website available")
            return False
        
        response, data = self.make_request('GET', f'/api/scraping/status/{self.test_data["website_id"]}')
        
        if response and response.status_code == 200 and data.get('success'):
            status = data.get('status', {})
            self.log_test("Get Scraping Status", True, f"Status: {status.get('status', 'unknown')}")
            return True
        else:
            self.log_test("Get Scraping Status", False, "Failed to get scraping status", data)
            return False
    
    def test_create_extraction_rule(self):
        """Test extraction rule creation"""
        if 'project_id' not in self.test_data:
            self.log_test("Create Extraction Rule", False, "No test project available")
            return False
        
        rule_data = {
            "project_id": self.test_data['project_id'],
            "name": "Test Title Extraction",
            "description": "Extract page titles",
            "rule_type": "css",
            "selector": "h1, h2, h3",
            "attribute": "text",
            "transform": "clean",
            "multiple": True
        }
        
        response, data = self.make_request('POST', '/api/content/rules', rule_data)
        
        if response and response.status_code == 201 and data.get('success'):
            self.test_data['rule_id'] = data['rule']['id']
            self.log_test("Create Extraction Rule", True, f"Rule created: {rule_data['name']}")
            return True
        else:
            self.log_test("Create Extraction Rule", False, "Failed to create extraction rule", data)
            return False
    
    def test_extract_content(self):
        """Test content extraction"""
        if 'page_id' not in self.test_data:
            self.log_test("Extract Content", False, "No test page available")
            return False
        
        extract_data = {
            "page_id": self.test_data['page_id']
        }
        
        response, data = self.make_request('POST', '/api/content/extract', extract_data)
        
        if response and response.status_code == 200 and data.get('success'):
            snippet_count = len(data.get('snippets', []))
            self.log_test("Extract Content", True, f"Extracted {snippet_count} snippets")
            return True
        else:
            self.log_test("Extract Content", False, "Failed to extract content", data)
            return False
    
    def test_get_snippets(self):
        """Test get snippets"""
        response, data = self.make_request('GET', '/api/content/snippets')
        
        if response and response.status_code == 200 and data.get('success'):
            snippet_count = len(data.get('snippets', []))
            self.log_test("Get Snippets", True, f"Retrieved {snippet_count} snippets")
            
            # Store first snippet for approval test
            if data.get('snippets'):
                self.test_data['snippet_id'] = data['snippets'][0]['id']
            
            return True
        else:
            self.log_test("Get Snippets", False, "Failed to get snippets", data)
            return False
    
    def test_approve_snippet(self):
        """Test snippet approval"""
        if 'snippet_id' not in self.test_data:
            self.log_test("Approve Snippet", False, "No test snippet available")
            return False
        
        approval_data = {
            "status": "approved",
            "review_notes": "Approved by automated test"
        }
        
        response, data = self.make_request('PUT', f'/api/content/snippets/{self.test_data["snippet_id"]}/approve', approval_data)
        
        if response and response.status_code == 200 and data.get('success'):
            self.log_test("Approve Snippet", True, "Snippet approved successfully")
            return True
        else:
            self.log_test("Approve Snippet", False, "Failed to approve snippet", data)
            return False
    
    def test_search_content(self):
        """Test content search"""
        response, data = self.make_request('GET', '/api/content/search?q=test')
        
        if response and response.status_code == 200 and data.get('success'):
            result_count = len(data.get('results', []))
            self.log_test("Search Content", True, f"Found {result_count} search results")
            return True
        else:
            self.log_test("Search Content", False, "Failed to search content", data)
            return False
    
    def test_create_export(self):
        """Test export creation"""
        export_data = {
            "export_type": "csv",
            "filters": {
                "data_type": "snippets",
                "status": "approved"
            }
        }
        
        response, data = self.make_request('POST', '/api/reports/export', export_data)
        
        if response and response.status_code == 201 and data.get('success'):
            self.test_data['export_id'] = data['export']['id']
            self.log_test("Create Export", True, f"Export created: {data['export']['filename']}")
            return True
        else:
            self.log_test("Create Export", False, "Failed to create export", data)
            return False
    
    def test_get_exports(self):
        """Test get exports"""
        response, data = self.make_request('GET', '/api/reports/exports')
        
        if response and response.status_code == 200 and data.get('success'):
            export_count = len(data.get('exports', []))
            self.log_test("Get Exports", True, f"Found {export_count} exports")
            return True
        else:
            self.log_test("Get Exports", False, "Failed to get exports", data)
            return False
    
    def test_admin_sql_executor(self):
        """Test admin SQL executor"""
        if not self.admin_token:
            self.log_test("Admin SQL Executor", False, "No admin token available")
            return False
        
        sql_data = {
            "sql": "SELECT COUNT(*) as total_users FROM users",
            "page": 1,
            "per_page": 10
        }
        
        response, data = self.make_request('POST', '/api/admin/sql/execute', sql_data, admin=True)
        
        if response and response.status_code == 200 and data.get('success'):
            row_count = len(data.get('rows', []))
            self.log_test("Admin SQL Executor", True, f"SQL executed, {row_count} rows returned")
            return True
        else:
            self.log_test("Admin SQL Executor", False, "Failed to execute SQL", data)
            return False
    
    def test_admin_get_users(self):
        """Test admin get users"""
        if not self.admin_token:
            self.log_test("Admin Get Users", False, "No admin token available")
            return False
        
        response, data = self.make_request('GET', '/api/admin/users', admin=True)
        
        if response and response.status_code == 200 and data.get('success'):
            user_count = len(data.get('users', []))
            self.log_test("Admin Get Users", True, f"Retrieved {user_count} users")
            return True
        else:
            self.log_test("Admin Get Users", False, "Failed to get users", data)
            return False
    
    def test_admin_system_status(self):
        """Test admin system status"""
        if not self.admin_token:
            self.log_test("Admin System Status", False, "No admin token available")
            return False
        
        response, data = self.make_request('GET', '/api/admin/system/status', admin=True)
        
        if response and response.status_code == 200 and data.get('success'):
            table_stats = data.get('status', {}).get('table_statistics', {})
            self.log_test("Admin System Status", True, f"Tables: {', '.join(table_stats.keys())}")
            return True
        else:
            self.log_test("Admin System Status", False, "Failed to get system status", data)
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        # Delete test project (cascades to websites, pages, etc.)
        if 'project_id' in self.test_data:
            response, data = self.make_request('DELETE', f'/api/projects/{self.test_data["project_id"]}')
            if response and response.status_code == 200:
                print("   ✅ Test project deleted")
            else:
                print("   ❌ Failed to delete test project")
        
        print()
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting comprehensive backend tests...\n")
        
        # Basic connectivity tests
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return
        
        self.test_api_info()
        
        # Debug email validation
        self.test_email_validation_debug()
        
        # Authentication tests
        self.test_user_registration()
        self.test_admin_registration()
        self.test_user_login()
        self.test_admin_login()
        self.test_get_profile()
        
        # Project management tests
        self.test_create_project()
        self.test_get_projects()
        self.test_update_project()
        
        # Website and scraping tests
        self.test_create_website()
        self.test_scrape_single_page()
        self.test_get_scraping_status()
        
        # Content extraction tests
        self.test_create_extraction_rule()
        self.test_extract_content()
        self.test_get_snippets()
        self.test_approve_snippet()
        self.test_search_content()
        
        # Export tests
        self.test_create_export()
        self.test_get_exports()
        
        # Admin tests
        self.test_admin_sql_executor()
        self.test_admin_get_users()
        self.test_admin_system_status()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Final results
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("=" * 50)
        print("🏁 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Completed at: {datetime.now().isoformat()}")
        
        if self.failed_tests == 0:
            print("\n🎉 All tests passed! Backend is working correctly.")
        else:
            print(f"\n⚠️  {self.failed_tests} test(s) failed. Check the logs above.")
        
        return self.failed_tests == 0


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Blitz Backend API')
    parser.add_argument('--url', default='http://localhost:5232', help='Base URL for API')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    tester = BlitzTester(args.url)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()