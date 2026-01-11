import requests
import sys
import json
from datetime import datetime, timedelta
import os

class VacationAPITester:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = "https://beauty-hub-180.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_vacation_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_admin_login(self):
        """Test admin login"""
        print("\n" + "="*60)
        print("TESTING ADMIN AUTHENTICATION FOR VACATIONS")
        print("="*60)
        
        response_data = self.run_test(
            "Admin Login",
            "POST",
            "admin/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if response_data and 'token' in response_data:
            self.admin_token = response_data['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_vacation_crud_operations(self):
        """Test vacation CRUD operations"""
        print("\n" + "="*60)
        print("TESTING VACATION CRUD OPERATIONS")
        print("="*60)
        
        if not self.admin_token:
            print("❌ Cannot test vacation operations - no admin token")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # 1. Create vacation (7 days from now to 10 days from now)
        start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        vacation_data = {
            "master_id": "admin",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "Тестова відпустка"
        }
        
        created_vacation = self.run_test(
            "Create Vacation",
            "POST",
            "vacations",
            200,
            data=vacation_data,
            headers=auth_headers
        )
        
        if not created_vacation or 'id' not in created_vacation:
            print("❌ Cannot proceed with vacation tests - creation failed")
            return False
        
        self.created_vacation_id = created_vacation['id']
        print(f"   Created vacation ID: {self.created_vacation_id}")
        
        # 2. Get all vacations
        vacations = self.run_test(
            "Get All Vacations",
            "GET",
            "vacations",
            200,
            headers=auth_headers
        )
        
        if vacations:
            print(f"   Found {len(vacations)} vacations")
            # Verify our vacation is in the list
            found_vacation = any(v['id'] == self.created_vacation_id for v in vacations)
            if found_vacation:
                print("   ✅ Created vacation found in list")
            else:
                print("   ❌ Created vacation not found in list")
        
        # 3. Get vacation by ID
        vacation_by_id = self.run_test(
            "Get Vacation by ID",
            "GET",
            f"vacations/{self.created_vacation_id}",
            200,
            headers=auth_headers
        )
        
        if vacation_by_id:
            print(f"   Retrieved vacation: {vacation_by_id.get('reason', 'No reason')}")
        
        # 4. Update vacation (change reason)
        update_data = {
            "reason": "Оновлена тестова відпустка"
        }
        
        updated_vacation = self.run_test(
            "Update Vacation",
            "PUT",
            f"vacations/{self.created_vacation_id}",
            200,
            data=update_data,
            headers=auth_headers
        )
        
        if updated_vacation:
            print(f"   Updated reason: {updated_vacation.get('reason', 'No reason')}")
        
        return True

    def test_timeslots_with_vacation(self):
        """Test timeslots considering vacation periods"""
        print("\n" + "="*60)
        print("TESTING TIMESLOTS WITH VACATION CONSIDERATION")
        print("="*60)
        
        if not self.admin_token:
            print("❌ Cannot test timeslots - no admin token")
            return False
        
        # Get services first
        services = self.run_test("Get Services for Timeslots", "GET", "services", 200)
        
        if not services or len(services) == 0:
            print("❌ No services available for timeslots test")
            return False
        
        service = services[0]
        service_id = service['id']
        print(f"   Using service: {service['name']} (ID: {service_id})")
        
        # Test date during vacation (8 days from now)
        vacation_date = (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d')
        
        # 1. Check timeslots during vacation - should be empty
        vacation_timeslots = self.run_test(
            "Get Timeslots During Vacation",
            "GET",
            f"timeslots/{vacation_date}?service_id={service_id}&master_id=admin",
            200
        )
        
        if vacation_timeslots is not None:
            if len(vacation_timeslots) == 0:
                print("   ✅ No timeslots available during vacation (correct)")
            else:
                print(f"   ❌ Found {len(vacation_timeslots)} timeslots during vacation (should be 0)")
        
        # 2. Check timeslots after vacation (15 days from now)
        after_vacation_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
        
        after_vacation_timeslots = self.run_test(
            "Get Timeslots After Vacation",
            "GET",
            f"timeslots/{after_vacation_date}?service_id={service_id}&master_id=admin",
            200
        )
        
        if after_vacation_timeslots is not None:
            available_slots = [slot for slot in after_vacation_timeslots if slot.get('available', False)]
            print(f"   Found {len(available_slots)} available timeslots after vacation")
            if len(available_slots) > 0:
                print("   ✅ Timeslots available after vacation (correct)")
            else:
                print("   ❌ No timeslots available after vacation")
        
        return True

    def test_six_month_booking_limit(self):
        """Test 6-month booking limit"""
        print("\n" + "="*60)
        print("TESTING 6-MONTH BOOKING LIMIT")
        print("="*60)
        
        # Get services first
        services = self.run_test("Get Services for Booking Limit", "GET", "services", 200)
        
        if not services or len(services) == 0:
            print("❌ No services available for booking limit test")
            return False
        
        service = services[0]
        service_id = service['id']
        print(f"   Using service: {service['name']} (ID: {service_id})")
        
        # 1. Test booking beyond 6 months (190 days from now)
        far_future_date = (datetime.now() + timedelta(days=190)).strftime('%Y-%m-%d')
        
        far_future_response = self.run_test(
            "Get Timeslots Beyond 6 Months",
            "GET",
            f"timeslots/{far_future_date}?service_id={service_id}&master_id=admin",
            400  # Should return 400 error
        )
        
        # 2. Test booking within 6 months (150 days from now)
        within_limit_date = (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d')
        
        within_limit_response = self.run_test(
            "Get Timeslots Within 6 Months",
            "GET",
            f"timeslots/{within_limit_date}?service_id={service_id}&master_id=admin",
            200  # Should return 200 success
        )
        
        if within_limit_response is not None:
            print(f"   Found {len(within_limit_response)} timeslots within 6-month limit")
        
        return True

    def test_vacation_validation(self):
        """Test vacation validation rules"""
        print("\n" + "="*60)
        print("TESTING VACATION VALIDATION")
        print("="*60)
        
        if not self.admin_token:
            print("❌ Cannot test vacation validation - no admin token")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # 1. Test invalid date format
        invalid_date_data = {
            "master_id": "admin",
            "start_date": "invalid-date",
            "end_date": "2025-02-01",
            "reason": "Test invalid date"
        }
        
        self.run_test(
            "Invalid Date Format",
            "POST",
            "vacations",
            400,  # Should return 400 error
            data=invalid_date_data,
            headers=auth_headers
        )
        
        # 2. Test end date before start date
        invalid_order_data = {
            "master_id": "admin",
            "start_date": "2025-02-10",
            "end_date": "2025-02-05",
            "reason": "Test invalid order"
        }
        
        self.run_test(
            "End Date Before Start Date",
            "POST",
            "vacations",
            400,  # Should return 400 error
            data=invalid_order_data,
            headers=auth_headers
        )
        
        return True

    def cleanup_vacation(self):
        """Clean up created vacation"""
        if self.created_vacation_id and self.admin_token:
            print(f"\n🧹 Cleaning up vacation {self.created_vacation_id}...")
            auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            self.run_test(
                "Delete Test Vacation",
                "DELETE",
                f"vacations/{self.created_vacation_id}",
                200,
                headers=auth_headers
            )

    def run_all_tests(self):
        """Run all vacation tests"""
        print("🚀 Starting Vacation API Tests")
        print(f"Base URL: {self.base_url}")
        
        try:
            # Test admin login first
            if not self.test_admin_login():
                print("❌ Admin login failed - vacation tests cannot proceed")
                return False
            
            # Run all test suites
            self.test_vacation_crud_operations()
            self.test_timeslots_with_vacation()
            self.test_six_month_booking_limit()
            self.test_vacation_validation()
            
        finally:
            # Always cleanup
            self.cleanup_vacation()
        
        # Print summary
        print("\n" + "="*60)
        print("VACATION TESTS SUMMARY")
        print("="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        else:
            print("\n✅ ALL VACATION TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = VacationAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())