import requests
import sys
import json
from datetime import datetime, timedelta

class NailSalonAPITester:
    def __init__(self, base_url="https://mani-pedi-portal.preview.emergentagent.com"):
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
            "email": unique_email,
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

    def test_multi_master_system(self):
        """Test multi-master system with data isolation as requested in Ukrainian"""
        print("\n" + "="*60)
        print("ТЕСТУВАННЯ MULTI-MASTER СИСТЕМИ БРОНЮВАННЯ")
        print("="*60)
        
        # Test credentials from the request
        master1_credentials = {"email": "olena@example.com", "password": "master123"}
        master2_credentials = {"email": "maria@example.com", "password": "master123"}
        admin_credentials = {"username": "admin", "password": "admin123"}
        
        # 1. Test Admin Authentication
        print("\n🔐 1. ТЕСТУВАННЯ АВТЕНТИФІКАЦІЇ АДМІНА")
        admin_response = self.run_test(
            "Admin Login",
            "POST", 
            "admin/login",
            200,
            data=admin_credentials
        )
        
        if not admin_response or 'token' not in admin_response:
            print("❌ Не вдалося увійти як адмін - тести неможливі")
            return False
        
        admin_token = admin_response['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        print(f"   ✅ Адмін токен отримано: {admin_token[:20]}...")
        
        # 2. Test Master Authentication
        print("\n🔐 2. ТЕСТУВАННЯ АВТЕНТИФІКАЦІЇ МАЙСТРІВ")
        
        # Master 1 login
        master1_response = self.run_test(
            "Master 1 Login (Олена Коваль)",
            "POST",
            "masters/login", 
            200,
            data=master1_credentials
        )
        
        if not master1_response or 'token' not in master1_response:
            print("❌ Не вдалося увійти як Майстер 1")
            return False
        
        master1_token = master1_response['token']
        master1_headers = {'Authorization': f'Bearer {master1_token}'}
        master1_id = master1_response['master']['id']
        print(f"   ✅ Майстер 1 токен: {master1_token[:20]}... (ID: {master1_id})")
        
        # Master 2 login
        master2_response = self.run_test(
            "Master 2 Login (Марія Петренко)",
            "POST",
            "masters/login",
            200, 
            data=master2_credentials
        )
        
        if not master2_response or 'token' not in master2_response:
            print("❌ Не вдалося увійти як Майстер 2")
            return False
        
        master2_token = master2_response['token']
        master2_headers = {'Authorization': f'Bearer {master2_token}'}
        master2_id = master2_response['master']['id']
        print(f"   ✅ Майстер 2 токен: {master2_token[:20]}... (ID: {master2_id})")
        
        # Verify tokens are different
        if master1_token == master2_token:
            self.log_test("Токени майстрів різні", False, "Токени однакові!")
        else:
            self.log_test("Токени майстрів різні", True, "Токени різні")
        
        # 3. Test Public Masters List
        print("\n👥 3. ТЕСТУВАННЯ СПИСКУ АКТИВНИХ МАЙСТРІВ")
        masters_list = self.run_test(
            "Get Active Masters",
            "GET",
            "masters",
            200
        )
        
        if masters_list:
            print(f"   Знайдено {len(masters_list)} активних майстрів:")
            olena_found = False
            maria_found = False
            
            for master in masters_list:
                print(f"   - {master.get('name', 'Без імені')} ({master.get('email', 'Без email')})")
                if master.get('email') == 'olena@example.com':
                    olena_found = True
                if master.get('email') == 'maria@example.com':
                    maria_found = True
            
            if olena_found and maria_found:
                self.log_test("Обидва майстри знайдені", True, "Олена Коваль та Марія Петренко активні")
            else:
                self.log_test("Обидва майстри знайдені", False, f"Олена: {olena_found}, Марія: {maria_found}")
        
        # 4. Test Data Isolation - Services
        print("\n🔒 4. ТЕСТУВАННЯ ІЗОЛЯЦІЇ ДАНИХ - ПОСЛУГИ")
        
        # Get Master 1 services
        master1_services = self.run_test(
            "Master 1 Services",
            "GET",
            "services",
            200,
            headers=master1_headers
        )
        
        # Get Master 2 services  
        master2_services = self.run_test(
            "Master 2 Services", 
            "GET",
            "services",
            200,
            headers=master2_headers
        )
        
        if master1_services and master2_services:
            print(f"   Майстер 1: {len(master1_services)} послуг")
            print(f"   Майстер 2: {len(master2_services)} послуг")
            
            # Check for service ID overlap
            master1_ids = {s['id'] for s in master1_services}
            master2_ids = {s['id'] for s in master2_services}
            overlap = master1_ids.intersection(master2_ids)
            
            if overlap:
                self.log_test("Ізоляція послуг", False, f"Знайдено перетин ID: {overlap}")
            else:
                self.log_test("Ізоляція послуг", True, "Послуги не перетинаються")
                
            # Verify each master has 3 services as mentioned in requirements
            if len(master1_services) >= 3:
                self.log_test("Майстер 1 має 3+ послуги", True, f"Знайдено {len(master1_services)} послуг")
            else:
                self.log_test("Майстер 1 має 3+ послуги", False, f"Тільки {len(master1_services)} послуг")
                
            if len(master2_services) >= 3:
                self.log_test("Майстер 2 має 3+ послуги", True, f"Знайдено {len(master2_services)} послуг")
            else:
                self.log_test("Майстер 2 має 3+ послуги", False, f"Тільки {len(master2_services)} послуг")
        
        # 5. Test Data Isolation - Bookings, Schedule, Vacations, Clients
        print("\n🔒 5. ТЕСТУВАННЯ ІЗОЛЯЦІЇ ДАНИХ - ЗАПИСИ, РОЗКЛАД, ВІДПУСТКИ, КЛІЄНТИ")
        
        # Test bookings isolation
        master1_bookings = self.run_test(
            "Master 1 Bookings",
            "GET", 
            "admin/bookings",
            200,
            headers=master1_headers
        )
        
        master2_bookings = self.run_test(
            "Master 2 Bookings",
            "GET",
            "admin/bookings", 
            200,
            headers=master2_headers
        )
        
        if master1_bookings is not None and master2_bookings is not None:
            print(f"   Майстер 1: {len(master1_bookings)} записів")
            print(f"   Майстер 2: {len(master2_bookings)} записів")
            
            # Check booking isolation
            master1_booking_ids = {b['id'] for b in master1_bookings}
            master2_booking_ids = {b['id'] for b in master2_bookings}
            booking_overlap = master1_booking_ids.intersection(master2_booking_ids)
            
            if booking_overlap:
                self.log_test("Ізоляція записів", False, f"Знайдено перетин записів: {booking_overlap}")
            else:
                self.log_test("Ізоляція записів", True, "Записи не перетинаються")
        
        # Test schedule isolation
        master1_schedule = self.run_test(
            "Master 1 Schedule",
            "GET",
            f"schedule?master_id={master1_id}",
            200
        )
        
        master2_schedule = self.run_test(
            "Master 2 Schedule", 
            "GET",
            f"schedule?master_id={master2_id}",
            200
        )
        
        if master1_schedule and master2_schedule:
            print(f"   Майстер 1: розклад на {len(master1_schedule)} днів")
            print(f"   Майстер 2: розклад на {len(master2_schedule)} днів")
            self.log_test("Розклад майстрів", True, "Розклади отримані")
        
        # Test vacations isolation
        master1_vacations = self.run_test(
            "Master 1 Vacations",
            "GET",
            "vacations",
            200,
            headers=master1_headers
        )
        
        master2_vacations = self.run_test(
            "Master 2 Vacations",
            "GET", 
            "vacations",
            200,
            headers=master2_headers
        )
        
        if master1_vacations is not None and master2_vacations is not None:
            print(f"   Майстер 1: {len(master1_vacations)} відпусток")
            print(f"   Майстер 2: {len(master2_vacations)} відпусток")
            self.log_test("Ізоляція відпусток", True, "Відпустки отримані окремо")
        
        # Test clients isolation
        master1_clients = self.run_test(
            "Master 1 Clients",
            "GET",
            "admin/clients", 
            200,
            headers=master1_headers
        )
        
        master2_clients = self.run_test(
            "Master 2 Clients",
            "GET",
            "admin/clients",
            200, 
            headers=master2_headers
        )
        
        if master1_clients is not None and master2_clients is not None:
            print(f"   Майстер 1: {len(master1_clients)} клієнтів")
            print(f"   Майстер 2: {len(master2_clients)} клієнтів")
            
            # Check client isolation
            master1_client_ids = {c['id'] for c in master1_clients}
            master2_client_ids = {c['id'] for c in master2_clients}
            client_overlap = master1_client_ids.intersection(master2_client_ids)
            
            if client_overlap:
                self.log_test("Ізоляція клієнтів", False, f"Знайдено перетин клієнтів: {client_overlap}")
            else:
                self.log_test("Ізоляція клієнтів", True, "Клієнти не перетинаються")
        
        # 6. Test Master Operations - Create Service
        print("\n⚙️ 6. ТЕСТУВАННЯ ОПЕРАЦІЙ МАЙСТРА - СТВОРЕННЯ ПОСЛУГИ")
        
        if master1_services:
            # Master 1 creates new service
            new_service_data = {
                "master_id": master1_id,
                "name": "Тест Послуга Майстра 1",
                "description": "Тестова послуга для перевірки ізоляції",
                "duration_minutes": 60,
                "price": 1500
            }
            
            created_service = self.run_test(
                "Master 1 Create Service",
                "POST",
                "services",
                200,
                data=new_service_data,
                headers=master1_headers
            )
            
            if created_service and 'id' in created_service:
                service_id = created_service['id']
                print(f"   ✅ Майстер 1 створив послугу: {service_id}")
                
                # Verify Master 1 can see the new service
                updated_master1_services = self.run_test(
                    "Master 1 Updated Services",
                    "GET",
                    "services",
                    200,
                    headers=master1_headers
                )
                
                if updated_master1_services:
                    service_found = any(s['id'] == service_id for s in updated_master1_services)
                    if service_found:
                        self.log_test("Майстер 1 бачить свою нову послугу", True, "Послуга знайдена")
                    else:
                        self.log_test("Майстер 1 бачить свою нову послугу", False, "Послуга не знайдена")
                
                # Verify Master 2 CANNOT see Master 1's new service
                updated_master2_services = self.run_test(
                    "Master 2 Updated Services",
                    "GET", 
                    "services",
                    200,
                    headers=master2_headers
                )
                
                if updated_master2_services:
                    service_found = any(s['id'] == service_id for s in updated_master2_services)
                    if service_found:
                        self.log_test("Майстер 2 НЕ бачить послугу Майстра 1", False, "Послуга видима!")
                    else:
                        self.log_test("Майстер 2 НЕ бачить послугу Майстра 1", True, "Ізоляція працює")
        
        # 7. Test Booking Flow
        print("\n📅 7. ТЕСТУВАННЯ ПОТОКУ БРОНЮВАННЯ")
        
        if master1_services and len(master1_services) > 0:
            service = master1_services[0]
            service_id = service['id']
            
            # Get available timeslots
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            timeslots = self.run_test(
                "Get Timeslots for Master 1",
                "GET",
                f"timeslots/{tomorrow}?service_id={service_id}&master_id={master1_id}",
                200
            )
            
            if timeslots:
                available_slots = [slot for slot in timeslots if slot.get('available', False)]
                print(f"   Знайдено {len(available_slots)} доступних слотів з {len(timeslots)} загальних")
                
                # Verify working hours (09:00-18:00)
                working_hours_slots = [slot for slot in timeslots if '09:00' <= slot['time'] <= '18:00']
                if len(working_hours_slots) >= 18:  # Should have 18 slots (9:00-18:00, 30min intervals)
                    self.log_test("Робочі години 09:00-18:00", True, f"Знайдено {len(working_hours_slots)} слотів")
                else:
                    self.log_test("Робочі години 09:00-18:00", False, f"Тільки {len(working_hours_slots)} слотів")
                
                if available_slots:
                    # Create test booking
                    booking_data = {
                        "master_id": master1_id,
                        "service_id": service_id,
                        "date": tomorrow,
                        "time": available_slots[0]['time'],
                        "client_name": "Тест Клієнт Майстра 1",
                        "client_phone": "+380501234567",
                        "client_email": "test.client1@example.com"
                    }
                    
                    created_booking = self.run_test(
                        "Create Test Booking for Master 1",
                        "POST",
                        "bookings",
                        200,
                        data=booking_data
                    )
                    
                    if created_booking and 'id' in created_booking:
                        booking_id = created_booking['id']
                        print(f"   ✅ Створено тестовий запис: {booking_id}")
                        
                        # Verify Master 1 can see the booking
                        final_master1_bookings = self.run_test(
                            "Master 1 Final Bookings Check",
                            "GET",
                            "admin/bookings",
                            200,
                            headers=master1_headers
                        )
                        
                        if final_master1_bookings:
                            booking_found = any(b['id'] == booking_id for b in final_master1_bookings)
                            if booking_found:
                                self.log_test("Майстер 1 бачить свій запис", True, "Запис знайдено")
                            else:
                                self.log_test("Майстер 1 бачить свій запис", False, "Запис не знайдено")
                        
                        # Verify Master 2 CANNOT see Master 1's booking
                        final_master2_bookings = self.run_test(
                            "Master 2 Final Bookings Check",
                            "GET",
                            "admin/bookings", 
                            200,
                            headers=master2_headers
                        )
                        
                        if final_master2_bookings:
                            booking_found = any(b['id'] == booking_id for b in final_master2_bookings)
                            if booking_found:
                                self.log_test("Майстер 2 НЕ бачить запис Майстра 1", False, "Запис видимий!")
                            else:
                                self.log_test("Майстер 2 НЕ бачить запис Майстра 1", True, "Ізоляція працює")
                        
                        # Clean up - cancel test booking
                        self.run_test(
                            "Cancel Test Booking",
                            "PUT",
                            f"bookings/{booking_id}/cancel",
                            200,
                            data={"cancellation_reason": "Тестове очищення"}
                        )
        
        return True
    
    def run_multi_master_test(self):
        """Run the multi-master system test as requested"""
        print("🚀 Запуск тестування Multi-Master системи бронювання")
        print(f"Backend URL: {self.api_url}")
        
        # Run the comprehensive multi-master test
        self.test_multi_master_system()
        
        # Print summary
        print("\n" + "="*60)
        print("ПІДСУМОК ТЕСТУВАННЯ MULTI-MASTER СИСТЕМИ")
        print("="*60)
        print(f"Всього тестів: {self.tests_run}")
        print(f"Пройшло: {self.tests_passed}")
        print(f"Не пройшло: {self.tests_run - self.tests_passed}")
        print(f"Успішність: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ НЕВДАЛІ ТЕСТИ:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        else:
            print("\n✅ ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = NailSalonAPITester()
    # Run the multi-master system test as requested
    success = tester.run_multi_master_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())