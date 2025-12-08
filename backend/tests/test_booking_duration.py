import requests
import sys
import json
from datetime import datetime, timedelta

class BookingDurationTester:
    def __init__(self, base_url="https://mani-pedi-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_service_id = None
        self.created_booking_id = None

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
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
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
            else:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            
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

    def setup_admin_auth(self):
        """Setup admin authentication"""
        print("\n" + "="*60)
        print("SETUP: ADMIN AUTHENTICATION")
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

    def create_test_service(self):
        """Create a test service with 60 minutes duration"""
        print("\n" + "="*60)
        print("SETUP: CREATE TEST SERVICE (60 MINUTES)")
        print("="*60)
        
        if not self.admin_token:
            print("❌ Cannot create service - no admin token")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        service_data = {
            "name": "Тест Маникюр 60хв",
            "description": "Тестова послуга тривалістю 60 хвилин",
            "duration_minutes": 60,
            "price": 1500,
            "image_url": "https://example.com/test-manicure.jpg"
        }
        
        created_service = self.run_test(
            "Create 60-minute Service",
            "POST",
            "services",
            200,
            data=service_data,
            headers=auth_headers
        )
        
        if created_service and 'id' in created_service:
            self.created_service_id = created_service['id']
            print(f"   Created service ID: {self.created_service_id}")
            print(f"   Service duration: {created_service['duration_minutes']} minutes")
            return True
        
        return False

    def test_timeslots_with_duration_consideration(self):
        """Test timeslots considering duration of existing bookings"""
        print("\n" + "="*60)
        print("TEST 1: TIMESLOTS WITH DURATION CONSIDERATION")
        print("="*60)
        
        if not self.created_service_id:
            print("❌ Cannot test timeslots - no test service created")
            return False
        
        # Get tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"   Testing date: {tomorrow}")
        
        # Step 1: Get initial available timeslots
        print("\n--- Step 1: Get initial available timeslots ---")
        initial_slots = self.run_test(
            "Get Initial Timeslots",
            "GET",
            f"timeslots/{tomorrow}?service_id={self.created_service_id}",
            200
        )
        
        if not initial_slots:
            print("❌ Cannot get initial timeslots")
            return False
        
        available_slots = [slot for slot in initial_slots if slot.get('available', False)]
        print(f"   Initial available slots: {len(available_slots)}")
        
        if len(available_slots) < 3:
            print("❌ Not enough available slots for testing")
            return False
        
        # Find first available slot for booking
        target_slot = available_slots[0]
        target_time = target_slot['time']
        
        print(f"   Using first available slot: {target_time}")
        print(f"   Available slots: {[slot['time'] for slot in available_slots[:5]]}")  # Show first 5
        
        # Step 2: Create booking at target time (should occupy target_time to target_time+60min)
        print(f"\n--- Step 2: Create booking at {target_time} ---")
        booking_data = {
            "service_id": self.created_service_id,
            "date": tomorrow,
            "time": target_time,
            "client_name": "Олена Тестова",
            "client_phone": "+380991234567",
            "client_email": "olena.test@example.com",
            "notes": "Тестовий запис для перевірки тривалості"
        }
        
        created_booking = self.run_test(
            "Create Booking at 10:00",
            "POST",
            "bookings",
            200,
            data=booking_data
        )
        
        if not created_booking or 'id' not in created_booking:
            print("❌ Failed to create booking")
            return False
        
        self.created_booking_id = created_booking['id']
        print(f"   Created booking ID: {self.created_booking_id}")
        print(f"   Booking duration: {created_booking['duration_minutes']} minutes")
        print(f"   Booking time: {created_booking['time']} on {created_booking['date']}")
        
        # Step 3: Check timeslots after booking creation
        print("\n--- Step 3: Check timeslots after booking creation ---")
        updated_slots = self.run_test(
            "Get Updated Timeslots",
            "GET",
            f"timeslots/{tomorrow}?service_id={self.created_service_id}",
            200
        )
        
        if not updated_slots:
            print("❌ Cannot get updated timeslots")
            return False
        
        # Analyze specific time slots
        slot_analysis = {}
        for slot in updated_slots:
            slot_analysis[slot['time']] = slot['available']
        
        print(f"   Total slots returned: {len(updated_slots)}")
        
        # Calculate expected time slots based on actual booking time
        booking_start = datetime.strptime(target_time, "%H:%M")
        booking_end = booking_start + timedelta(minutes=60)
        
        # Find next 30-minute slot after booking start
        next_slot_time = booking_start + timedelta(minutes=30)
        end_slot_time = booking_end
        
        target_time_str = target_time
        next_slot_str = next_slot_time.strftime("%H:%M")
        end_slot_str = end_slot_time.strftime("%H:%M")
        
        print(f"   Booking occupies: {target_time_str} - {end_slot_str}")
        
        # Test expectations
        test_cases = [
            (target_time_str, False, f"should be unavailable (exact booking time)"),
            (next_slot_str, False, f"should be unavailable (conflicts with {target_time_str}-{end_slot_str} booking)"),
            (end_slot_str, True, f"should be available (after booking ends at {end_slot_str})")
        ]
        
        all_passed = True
        for time_slot, expected_available, reason in test_cases:
            actual_available = slot_analysis.get(time_slot, None)
            
            if actual_available is None:
                print(f"   ❌ Slot {time_slot} not found in response")
                all_passed = False
            elif actual_available == expected_available:
                print(f"   ✅ Slot {time_slot}: available={actual_available} ({reason})")
            else:
                print(f"   ❌ Slot {time_slot}: expected available={expected_available}, got available={actual_available} ({reason})")
                all_passed = False
        
        self.log_test("Timeslots Duration Logic", all_passed, 
                     "Duration consideration in timeslots" if all_passed else "Duration logic failed")
        
        return all_passed

    def test_booking_duration_update(self):
        """Test updating booking duration via admin API"""
        print("\n" + "="*60)
        print("TEST 2: BOOKING DURATION UPDATE")
        print("="*60)
        
        if not self.created_booking_id:
            print("❌ Cannot test duration update - no booking created")
            return False
        
        if not self.admin_token:
            print("❌ Cannot test duration update - no admin token")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Step 1: Get current booking details
        print("\n--- Step 1: Get current booking details ---")
        current_booking = self.run_test(
            "Get Current Booking",
            "GET",
            f"bookings/{self.created_booking_id}",
            200
        )
        
        if not current_booking:
            print("❌ Cannot get current booking")
            return False
        
        original_duration = current_booking.get('duration_minutes', 0)
        print(f"   Original duration: {original_duration} minutes")
        
        # Step 2: Update booking duration to 90 minutes
        print("\n--- Step 2: Update booking duration to 90 minutes ---")
        update_data = {
            "duration_minutes": 90,
            "notes": "Тривалість оновлена до 90 хвилин"
        }
        
        updated_booking = self.run_test(
            "Update Booking Duration",
            "PUT",
            f"admin/bookings/{self.created_booking_id}",
            200,
            data=update_data,
            headers=auth_headers
        )
        
        if not updated_booking:
            print("❌ Failed to update booking")
            return False
        
        new_duration = updated_booking.get('duration_minutes', 0)
        print(f"   New duration: {new_duration} minutes")
        
        # Step 3: Verify the update
        print("\n--- Step 3: Verify duration update ---")
        verified_booking = self.run_test(
            "Verify Updated Booking",
            "GET",
            f"bookings/{self.created_booking_id}",
            200
        )
        
        if not verified_booking:
            print("❌ Cannot verify updated booking")
            return False
        
        verified_duration = verified_booking.get('duration_minutes', 0)
        print(f"   Verified duration: {verified_duration} minutes")
        
        # Check if duration was updated correctly
        duration_updated = (new_duration == 90 and verified_duration == 90)
        
        if duration_updated:
            print("   ✅ Duration successfully updated from 60 to 90 minutes")
        else:
            print(f"   ❌ Duration update failed. Expected: 90, Got: {verified_duration}")
        
        self.log_test("Booking Duration Update", duration_updated,
                     "Duration updated successfully" if duration_updated else f"Expected 90, got {verified_duration}")
        
        return duration_updated

    def test_timeslots_after_duration_update(self):
        """Test timeslots after duration update (bonus test)"""
        print("\n" + "="*60)
        print("BONUS TEST: TIMESLOTS AFTER DURATION UPDATE")
        print("="*60)
        
        if not self.created_service_id or not self.created_booking_id:
            print("❌ Cannot test - missing service or booking")
            return False
        
        # Get tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get timeslots after duration update
        updated_slots = self.run_test(
            "Get Timeslots After Duration Update",
            "GET",
            f"timeslots/{tomorrow}?service_id={self.created_service_id}",
            200
        )
        
        if not updated_slots:
            print("❌ Cannot get timeslots after update")
            return False
        
        # Analyze slots - now booking should occupy 10:00-11:30 (90 minutes)
        slot_analysis = {}
        for slot in updated_slots:
            slot_analysis[slot['time']] = slot['available']
        
        # We need to get the actual booking time from the created booking
        # For now, let's check if we can get the booking details
        if not self.created_booking_id:
            print("❌ No booking ID available for analysis")
            return False
        
        # Get the actual booking to see its time
        booking_response = self.run_test(
            "Get Booking for Analysis",
            "GET",
            f"bookings/{self.created_booking_id}",
            200
        )
        
        if not booking_response:
            print("❌ Cannot get booking details")
            return False
        
        booking_time = booking_response.get('time', '')
        booking_duration = booking_response.get('duration_minutes', 90)
        
        # Calculate expected slots based on actual booking
        booking_start = datetime.strptime(booking_time, "%H:%M")
        booking_end = booking_start + timedelta(minutes=booking_duration)
        
        slot1 = booking_start.strftime("%H:%M")
        slot2 = (booking_start + timedelta(minutes=30)).strftime("%H:%M")
        slot3 = (booking_start + timedelta(minutes=60)).strftime("%H:%M")
        slot4 = booking_end.strftime("%H:%M")
        
        print(f"   Booking: {booking_time} for {booking_duration} minutes (ends at {slot4})")
        
        # Test expectations after 90-minute duration
        test_cases = [
            (slot1, False, "should be unavailable (booking start)"),
            (slot2, False, "should be unavailable (within 90-minute booking)"),
            (slot3, False, "should be unavailable (within 90-minute booking)"),
            (slot4, True, "should be available (after 90-minute booking ends)")
        ]
        
        all_passed = True
        for time_slot, expected_available, reason in test_cases:
            actual_available = slot_analysis.get(time_slot, None)
            
            if actual_available is None:
                print(f"   ⚠️  Slot {time_slot} not found in response")
            elif actual_available == expected_available:
                print(f"   ✅ Slot {time_slot}: available={actual_available} ({reason})")
            else:
                print(f"   ❌ Slot {time_slot}: expected available={expected_available}, got available={actual_available} ({reason})")
                all_passed = False
        
        self.log_test("Timeslots After Duration Update", all_passed,
                     "Timeslots correctly reflect updated duration" if all_passed else "Timeslots don't reflect duration update")
        
        return all_passed

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n" + "="*60)
        print("CLEANUP: REMOVING TEST DATA")
        print("="*60)
        
        if not self.admin_token:
            print("❌ Cannot cleanup - no admin token")
            return
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Cancel the test booking
        if self.created_booking_id:
            self.run_test(
                "Cancel Test Booking",
                "PUT",
                f"bookings/{self.created_booking_id}/cancel",
                200,
                data={"cancellation_reason": "Cleanup after testing"}
            )
        
        # Delete the test service
        if self.created_service_id:
            self.run_test(
                "Delete Test Service",
                "DELETE",
                f"services/{self.created_service_id}",
                200,
                headers=auth_headers
            )

    def run_all_tests(self):
        """Run all booking duration tests"""
        print("🚀 Starting Booking Duration Tests")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        
        # Setup
        if not self.setup_admin_auth():
            print("❌ Admin authentication failed - cannot proceed")
            return False
        
        if not self.create_test_service():
            print("❌ Test service creation failed - cannot proceed")
            return False
        
        # Run main tests
        test1_passed = self.test_timeslots_with_duration_consideration()
        test2_passed = self.test_booking_duration_update()
        
        # Bonus test
        bonus_passed = self.test_timeslots_after_duration_update()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "="*60)
        print("BOOKING DURATION TEST SUMMARY")
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
            print("\n✅ ALL TESTS PASSED!")
        
        # Main test results
        main_tests_passed = test1_passed and test2_passed
        print(f"\n📊 MAIN FUNCTIONALITY:")
        print(f"   ✅ Timeslots Duration Logic: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"   ✅ Booking Duration Update: {'PASSED' if test2_passed else 'FAILED'}")
        print(f"   🎯 Bonus - Updated Timeslots: {'PASSED' if bonus_passed else 'FAILED'}")
        
        return main_tests_passed

def main():
    tester = BookingDurationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())