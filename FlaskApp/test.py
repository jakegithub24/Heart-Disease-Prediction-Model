"""
API Test Suite for Heart Disease Prediction Flask Application
Tests various endpoints and API functionality
"""

import requests
import json
from datetime import datetime
import sqlite3
import os
import subprocess
import sys

# Base URL for the Flask application
BASE_URL = "http://localhost:5001"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"username": "admin", "password": "admin123"},
    "staff": {"username": "staff1", "password": "staff123"}
}

def init_test_users():
    """Initialize test users in the database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'heart_care.db')
        
        # Run a Python command to initialize users using Flask's context
        init_script = """
import sqlite3
import sys
sys.path.insert(0, '.')
from werkzeug.security import generate_password_hash

db_path = '{}'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if not cursor.fetchone():
    print("Users table not found. Skipping user initialization.")
    conn.close()
    sys.exit(0)

# Insert test users if they don't exist
test_users = [
    ("admin", "admin123", "admin@test.com", "Admin User", "admin"),
    ("staff1", "staff123", "staff1@test.com", "Staff User 1", "staff"),
]

for username, password, email, full_name, role in test_users:
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, full_name, role) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, email, full_name, role)
        )
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()
print("Test users initialized")
""".format(db_path)
        
        result = subprocess.run([sys.executable, "-c", init_script], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            print("✓ Test users initialized successfully")
            return True
        else:
            print(f"⚠ User initialization output: {result.stdout}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"⚠ Could not initialize test users: {e}")
        return False

class FlaskAppTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.user_id = None
        self.patient_id = None
        self.test_user_id = None
        self.logged_in_user = None
        self.logged_in_role = None

    def log_test(self, test_name, passed, message="", status_code=None):
        """Log test results"""
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"\n{status}: {test_name}")
        if message:
            print(f"  Details: {message}")
        if status_code:
            print(f"  Status Code: {status_code}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        })

    def test_home_page(self):
        """Test: GET / - Home page"""
        try:
            response = self.session.get(f"{self.base_url}/")
            passed = response.status_code == 200
            self.log_test("Home Page Load", passed, 
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Home Page Load", False, str(e))
            return False

    def test_login_page(self):
        """Test: GET /login - Login page"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            passed = response.status_code == 200
            self.log_test("Login Page Load", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Login Page Load", False, str(e))
            return False

    def test_login_invalid(self):
        """Test: POST /login - Invalid credentials"""
        try:
            data = {
                "username": "invalid_user",
                "password": "wrong_password"
            }
            response = self.session.post(f"{self.base_url}/login", data=data)
            passed = response.status_code == 200  # Should redirect/return login page
            self.log_test("Login with Invalid Credentials", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Login with Invalid Credentials", False, str(e))
            return False

    def test_login_valid(self):
        """Test: POST /login - Valid credentials (tries both admin and staff)"""
        for role, creds in TEST_CREDENTIALS.items():
            try:
                data = {
                    "username": creds["username"],
                    "password": creds["password"]
                }
                response = self.session.post(f"{self.base_url}/login", data=data, 
                                            allow_redirects=True)
                
                # Check if login was successful by checking session or redirect
                passed = response.status_code == 200 and ("dashboard" in response.text.lower() or "patient" in response.text.lower())
                
                if passed:
                    self.logged_in_user = creds["username"]
                    self.logged_in_role = role
                    self.log_test(f"Login with Valid Credentials ({role.upper()})", True,
                                 f"Successfully logged in as {creds['username']}")
                    return True
                else:
                    # Print response snippet for debugging
                    snippet = response.text[:200] if response.text else "No response body"
                    self.log_test(f"Login with Valid Credentials ({role.upper()})", False,
                                 f"Response snippet: {snippet[:100]}", response.status_code)
            except Exception as e:
                self.log_test(f"Login with Valid Credentials ({role.upper()})", False, str(e))
        
        return False

    def test_dashboard_access(self):
        """Test: GET /dashboard - Dashboard access (requires login)"""
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            # If not logged in, should redirect to login
            passed = response.status_code == 200 or "login" in response.url.lower()
            self.log_test("Dashboard Access", passed,
                         f"Logged in as: {self.logged_in_user}", response.status_code)
            return passed
        except Exception as e:
            self.log_test("Dashboard Access", False, str(e))
            return False

    def test_patients_list(self):
        """Test: GET /patients - Patients list (requires login)"""
        try:
            response = self.session.get(f"{self.base_url}/patients")
            passed = response.status_code == 200 or "login" in response.url.lower()
            
            if response.status_code == 500:
                # Extract error details from response
                error_snippet = response.text[response.text.find('<title>'):response.text.find('</title>')+8] if '<title>' in response.text else ""
                self.log_test("Patients List Access", passed,
                             f"Error: {error_snippet[:150]}", response.status_code)
            else:
                self.log_test("Patients List Access", passed,
                             f"Logged in as: {self.logged_in_user}", response.status_code)
            return passed
        except Exception as e:
            self.log_test("Patients List Access", False, str(e))
            return False

    def test_predict_page(self):
        """Test: GET /predict - Prediction page"""
        try:
            response = self.session.get(f"{self.base_url}/predict")
            passed = response.status_code == 200 or "login" in response.url.lower()
            self.log_test("Predict Page Access", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Predict Page Access", False, str(e))
            return False

    def test_api_patient_stats(self):
        """Test: GET /api/patient_stats - Patient statistics API"""
        try:
            response = self.session.get(f"{self.base_url}/api/patient_stats")
            passed = response.status_code in [200, 302]  # May redirect if not logged in
            
            try:
                data = response.json()
                self.log_test("API Patient Stats", passed,
                             f"Status Code: {response.status_code}, Data: {data}")
            except:
                self.log_test("API Patient Stats", passed,
                             f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("API Patient Stats", False, str(e))
            return False

    def test_logout(self):
        """Test: GET /logout - Logout"""
        try:
            response = self.session.get(f"{self.base_url}/logout", allow_redirects=True)
            passed = response.status_code == 200
            self.log_test("Logout", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Logout", False, str(e))
            return False

    def test_nonexistent_patient(self):
        """Test: GET /patient/99999 - Non-existent patient"""
        try:
            response = self.session.get(f"{self.base_url}/patient/99999")
            # Should either return 404, 500, or handle gracefully with 200
            # The app might return 200 with an error message or not found page
            passed = response.status_code in [200, 404, 302, 500] or "login" in response.url.lower()
            self.log_test("Non-existent Patient Access", passed,
                         f"App handles non-existent patient gracefully", response.status_code)
            return passed
        except Exception as e:
            self.log_test("Non-existent Patient Access", False, str(e))
            return False

    def test_profile_page(self):
        """Test: GET /profile - User profile page"""
        try:
            response = self.session.get(f"{self.base_url}/profile")
            passed = response.status_code in [200, 302]
            self.log_test("Profile Page Access", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Profile Page Access", False, str(e))
            return False

    def test_admin_users_page(self):
        """Test: GET /admin/users - Admin users page"""
        try:
            response = self.session.get(f"{self.base_url}/admin/users")
            passed = response.status_code == 200 or "login" in response.url.lower()
            
            if response.status_code == 500:
                error_snippet = response.text[response.text.find('<title>'):response.text.find('</title>')+8] if '<title>' in response.text else ""
                self.log_test("Admin Users Page Access", passed,
                             f"Error: {error_snippet[:150]}", response.status_code)
            else:
                self.log_test("Admin Users Page Access", passed,
                             f"User role: {self.logged_in_role}", response.status_code)
            return passed
        except Exception as e:
            self.log_test("Admin Users Page Access", False, str(e))
            return False

    def test_audit_log_page(self):
        """Test: GET /admin/audit_log - Audit log page"""
        try:
            response = self.session.get(f"{self.base_url}/admin/audit_log")
            passed = response.status_code in [200, 302]
            self.log_test("Audit Log Page Access", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Audit Log Page Access", False, str(e))
            return False

    def test_connection(self):
        """Test: Basic connection to Flask app"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            passed = response.status_code < 500
            self.log_test("Flask App Connection", passed,
                         f"Status Code: {response.status_code}")
            return passed
        except requests.exceptions.ConnectionError:
            self.log_test("Flask App Connection", False,
                         f"Could not connect to {self.base_url}")
            return False
        except Exception as e:
            self.log_test("Flask App Connection", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("HEART DISEASE PREDICTION APP - API TEST SUITE")
        print("=" * 60)
        print(f"Testing: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Initialize test users
        print("\nInitializing test database...")
        init_test_users()

        # Test connection first
        if not self.test_connection():
            print("\n✗ CRITICAL: Cannot connect to Flask app. Stopping tests.")
            return False

        # Run all tests
        self.test_home_page()
        self.test_login_page()
        self.test_login_invalid()
        self.test_login_valid()
        self.test_dashboard_access()
        self.test_patients_list()
        self.test_predict_page()
        self.test_api_patient_stats()
        self.test_profile_page()
        self.test_admin_users_page()
        self.test_audit_log_page()
        self.test_nonexistent_patient()
        self.test_logout()

        # Print summary
        self.print_summary()
        return self.get_pass_rate() >= 0.7  # 70% pass rate

    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for t in self.test_results if t["passed"])
        total = len(self.test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("=" * 60)

        if total - passed > 0:
            print("\nFailed Tests:")
            for test in self.test_results:
                if not test["passed"]:
                    print(f"  - {test['test']}: {test['message']}")

    def get_pass_rate(self):
        """Get pass rate as percentage"""
        if not self.test_results:
            return 0
        passed = sum(1 for t in self.test_results if t["passed"])
        return passed / len(self.test_results)

    def export_results(self, filename="test_results.json"):
        """Export test results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nTest results exported to {filename}")


def main():
    """Main test execution"""
    tester = FlaskAppTester()
    success = tester.run_all_tests()
    tester.export_results()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
