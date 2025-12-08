import requests
import sys
import json
from datetime import datetime, timedelta

class NailSalonAPITester:
    def __init__(self, base_url="https://nail-studio-20.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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
        print("\n" + "="*50)
        print("TESTING ADMIN AUTHENTICATION")
        print("="*50)
        
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

    def test_services_api(self):
        """Test services CRUD operations"""
        print("\n" + "="*50)
        print("TESTING SERVICES API")
        print("="*50)
        
        # Get services
        services = self.run_test("Get Services", "GET", "services", 200)
        
        if not services:
            print("❌ Cannot proceed with services tests - GET failed")
            return False
        
        print(f"   Found {len(services)} services")
        
        if not self.admin_token:
            print("❌ Cannot test admin services operations - no token")
            return False
        
        # Create new service
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        new_service_data = {
            "name": "Тест Маникюр",
            "description": "Тестовая услуга маникюра",
            "duration_minutes": 90,
            "price": 2500,
            "image_url": "https://example.com/test.jpg"
        }
        
        created_service = self.run_test(
            "Create Service",
            "POST",
            "services",
            200,
            data=new_service_data,
            headers=auth_headers
        )
        
        if created_service and 'id' in created_service:
            service_id = created_service['id']
            print(f"   Created service ID: {service_id}")
            
            # Update service
            update_data = {"price": 3000}
            self.run_test(
                "Update Service",
                "PUT",
                f"services/{service_id}",
                200,
                data=update_data,
                headers=auth_headers
            )
            
            # Delete service
            self.run_test(
                "Delete Service",
                "DELETE",
                f"services/{service_id}",
                200,
                headers=auth_headers
            )
        
        return True

    def test_schedule_api(self):
        """Test schedule API"""
        print("\n" + "="*50)
        print("TESTING SCHEDULE API")
        print("="*50)
        
        # Get schedule
        schedule = self.run_test("Get Schedule", "GET", "schedule", 200)
        
        if schedule:
            print(f"   Found schedule for {len(schedule)} days")
            
            if self.admin_token:
                # Update schedule for Monday (day 0)
                auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
                schedule_data = {
                    "day_of_week": 0,
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "is_working": True
                }
                
                self.run_test(
                    "Update Schedule",
                    "POST",
                    "schedule",
                    200,
                    data=schedule_data,
                    headers=auth_headers
                )
        
        return True

    def test_booking_flow(self):
        """Test complete booking flow"""
        print("\n" + "="*50)
        print("TESTING BOOKING FLOW")
        print("="*50)
        
        # Get services first
        services = self.run_test("Get Services for Booking", "GET", "services", 200)
        
        if not services or len(services) == 0:
            print("❌ No services available for booking test")
            return False
        
        service = services[0]
        service_id = service['id']
        print(f"   Using service: {service['name']} (ID: {service_id})")
        
        # Get available time slots for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        time_slots = self.run_test(
            "Get Time Slots",
            "GET",
            f"timeslots/{tomorrow}?service_id={service_id}",
            200
        )
        
        if not time_slots:
            print("❌ No time slots available")
            return False
        
        available_slots = [slot for slot in time_slots if slot.get('available', False)]
        if not available_slots:
            print("❌ No available time slots")
            return False
        
        time_slot = available_slots[0]['time']
        print(f"   Using time slot: {time_slot} on {tomorrow}")
        
        # Create booking
        booking_data = {
            "service_id": service_id,
            "date": tomorrow,
            "time": time_slot,
            "client_name": "Тест Клиент",
            "client_phone": "+7 (999) 123-45-67",
            "client_email": "test@example.com",
            "notes": "Тестовая запись"
        }
        
        created_booking = self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            200,
            data=booking_data
        )
        
        if created_booking and 'id' in created_booking:
            booking_id = created_booking['id']
            print(f"   Created booking ID: {booking_id}")
            
            # Get client bookings
            phone = "+7 (999) 123-45-67"
            client_bookings = self.run_test(
                "Get Client Bookings",
                "GET",
                f"bookings/client/{requests.utils.quote(phone)}",
                200
            )
            
            if client_bookings:
                print(f"   Found {len(client_bookings)} bookings for client")
            
            # Get specific booking
            self.run_test(
                "Get Specific Booking",
                "GET",
                f"bookings/{booking_id}",
                200
            )
            
            # Cancel booking
            self.run_test(
                "Cancel Booking",
                "PUT",
                f"bookings/{booking_id}/cancel",
                200,
                data={"cancellation_reason": "Test cancellation"}
            )
            
            return True
        
        return False

    def test_admin_operations(self):
        """Test admin-specific operations"""
        print("\n" + "="*50)
        print("TESTING ADMIN OPERATIONS")
        print("="*50)
        
        if not self.admin_token:
            print("❌ Cannot test admin operations - no token")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get all bookings
        all_bookings = self.run_test(
            "Get All Bookings (Admin)",
            "GET",
            "admin/bookings",
            200,
            headers=auth_headers
        )
        
        if all_bookings:
            print(f"   Found {len(all_bookings)} total bookings")
            
            # Update booking status if any bookings exist
            if len(all_bookings) > 0:
                booking_id = all_bookings[0]['id']
                self.run_test(
                    "Update Booking Status",
                    "PUT",
                    f"admin/bookings/{booking_id}",
                    200,
                    data={"status": "confirmed"},
                    headers=auth_headers
                )
        
        # Get stats
        self.run_test(
            "Get Admin Stats",
            "GET",
            "admin/stats",
            200,
            headers=auth_headers
        )
        
        return True

    def test_6_month_booking_limit(self):
        """Test 6-month booking limit functionality"""
        print("\n" + "="*50)
        print("TESTING 6-MONTH BOOKING LIMIT")
        print("="*50)
        
        # Get services first
        services = self.run_test("Get Services for 6-month test", "GET", "services", 200)
        
        if not services or len(services) == 0:
            print("❌ No services available for 6-month booking test")
            return False
        
        service = services[0]
        service_id = service['id']
        print(f"   Using service: {service['name']} (ID: {service_id})")
        
        # Test 1: Get timeslots for date 150 days from today (should work)
        date_150_days = (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d')
        print(f"   Testing date 150 days from now: {date_150_days}")
        
        time_slots_150 = self.run_test(
            "Get Timeslots 150 days ahead",
            "GET",
            f"timeslots/{date_150_days}?service_id={service_id}&master_id=admin",
            200
        )
        
        if time_slots_150 is not None:
            print(f"   ✅ Found {len(time_slots_150)} timeslots for 150 days ahead")
        else:
            print("   ❌ Failed to get timeslots for 150 days ahead")
            return False
        
        # Test 2: Create booking for date 100 days from today (should work)
        date_100_days = (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d')
        print(f"   Testing booking creation for date 100 days from now: {date_100_days}")
        
        # Get available slots for 100 days ahead
        time_slots_100 = self.run_test(
            "Get Timeslots 100 days ahead",
            "GET",
            f"timeslots/{date_100_days}?service_id={service_id}&master_id=admin",
            200
        )
        
        if not time_slots_100:
            print("   ❌ No time slots available for 100 days ahead")
            return False
        
        available_slots = [slot for slot in time_slots_100 if slot.get('available', False)]
        if not available_slots:
            print("   ❌ No available time slots for 100 days ahead")
            return False
        
        time_slot = available_slots[0]['time']
        print(f"   Using time slot: {time_slot} on {date_100_days}")
        
        # Create booking for 100 days ahead
        booking_data = {
            "master_id": "admin",
            "service_id": service_id,
            "date": date_100_days,
            "time": time_slot,
            "client_name": "Тест Клієнт",
            "client_phone": "+380501234567"
        }
        
        created_booking = self.run_test(
            "Create Booking 100 days ahead",
            "POST",
            "bookings",
            200,
            data=booking_data
        )
        
        if created_booking and 'id' in created_booking:
            booking_id = created_booking['id']
            print(f"   ✅ Created booking ID: {booking_id} for 100 days ahead")
            
            # Clean up - cancel the test booking
            self.run_test(
                "Cancel Test Booking",
                "PUT",
                f"bookings/{booking_id}/cancel",
                200,
                data={"cancellation_reason": "Test cleanup"}
            )
            
            return True
        else:
            print("   ❌ Failed to create booking for 100 days ahead")
            return False

    def test_master_system(self):
        """Test master system functionality as requested"""
        print("\n" + "="*50)
        print("TESTING MASTER SYSTEM FUNCTIONALITY")
        print("="*50)
        
        if not self.admin_token:
            print("❌ Cannot test master system - no admin token")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Generate unique email with timestamp
        import time
        timestamp = int(time.time())
        unique_email = f"test.master.{timestamp}@example.com"
        
        # 1. Create a master
        master_data = {
            "name": "Тестовий Майстер",
            "email": unique_email,
            "phone": "+380501111111",
            "password": "test123"
        }
        
        created_master = self.run_test(
            "Create Master",
            "POST",
            "masters",
            200,
            data=master_data,
            headers=auth_headers
        )
        
        if not created_master or 'id' not in created_master:
            print("❌ Failed to create master - cannot continue with master tests")
            return False
        
        master_id = created_master['id']
        print(f"   Created master ID: {master_id}")
        
        # 2. Get list of masters
        masters_list = self.run_test(
            "Get Masters List",
            "GET",
            "masters",
            200,
            headers=auth_headers
        )
        
        if masters_list:
            print(f"   Found {len(masters_list)} masters in the system")
            
            # 3. Check that created master is in the list
            master_found = False
            for master in masters_list:
                if master.get('email') == unique_email:
                    master_found = True
                    print(f"   ✅ Created master found in list: {master.get('name')}")
                    break
            
            if not master_found:
                self.log_test("Master in List Check", False, "Created master not found in masters list")
            else:
                self.log_test("Master in List Check", True, "Created master found in masters list")
        
        # 4. Try to login as the created master
        master_login_data = {
            "email": "test.master@example.com",
            "password": "test123"
        }
        
        master_login_response = self.run_test(
            "Master Login",
            "POST",
            "masters/login",
            200,
            data=master_login_data
        )
        
        if master_login_response and 'token' in master_login_response:
            master_token = master_login_response['token']
            print(f"   ✅ Master login successful, token obtained: {master_token[:20]}...")
            
            # 5. Test booking filtering with new authorization
            master_auth_headers = {'Authorization': f'Bearer {master_token}'}
            
            # Get bookings as master (should only see own bookings)
            master_bookings = self.run_test(
                "Get Bookings as Master",
                "GET",
                "admin/bookings",
                200,
                headers=master_auth_headers
            )
            
            if master_bookings is not None:
                print(f"   ✅ Master can access bookings API, found {len(master_bookings)} bookings")
            
            # Get bookings as admin (should see all bookings)
            admin_bookings = self.run_test(
                "Get Bookings as Admin",
                "GET",
                "admin/bookings",
                200,
                headers=auth_headers
            )
            
            if admin_bookings is not None:
                print(f"   ✅ Admin can access bookings API, found {len(admin_bookings)} bookings")
        
        return True

    def test_error_cases(self):
        """Test error handling"""
        print("\n" + "="*50)
        print("TESTING ERROR CASES")
        print("="*50)
        
        # Test invalid service ID
        self.run_test(
            "Invalid Service ID",
            "GET",
            "timeslots/2025-01-01?service_id=invalid-id",
            404
        )
        
        # Test invalid booking ID
        self.run_test(
            "Invalid Booking ID",
            "GET",
            "bookings/invalid-id",
            404
        )
        
        # Test invalid admin credentials
        self.run_test(
            "Invalid Admin Login",
            "POST",
            "admin/login",
            401,
            data={"username": "wrong", "password": "wrong"}
        )
        
        # Test unauthorized admin access
        self.run_test(
            "Unauthorized Admin Access",
            "GET",
            "admin/stats",
            401
        )

    def run_master_system_test(self):
        """Run focused master system test as requested"""
        print("🚀 Starting Master System API Test")
        print(f"Base URL: {self.base_url}")
        
        # Test admin login first
        if not self.test_admin_login():
            print("❌ Admin login failed - cannot proceed with master tests")
            return False
        
        # Run master system test
        self.test_master_system()
        
        # Print summary
        print("\n" + "="*50)
        print("MASTER SYSTEM TEST SUMMARY")
        print("="*50)
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
        
        return self.tests_passed == self.tests_run

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Nail Salon API Tests")
        print(f"Base URL: {self.base_url}")
        
        # Test admin login first
        if not self.test_admin_login():
            print("❌ Admin login failed - some tests will be skipped")
        
        # Run all test suites
        self.test_services_api()
        self.test_schedule_api()
        self.test_booking_flow()
        self.test_6_month_booking_limit()
        self.test_master_system()
        self.test_admin_operations()
        self.test_error_cases()
        
        # Print summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
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
        
        return self.tests_passed == self.tests_run

def main():
    tester = NailSalonAPITester()
    # Run focused master system test as requested
    success = tester.run_master_system_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())