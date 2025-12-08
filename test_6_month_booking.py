#!/usr/bin/env python3
"""
Швидкий тест для перевірки функціональності бронювання на 6 місяців
"""

import requests
import sys
from datetime import datetime, timedelta

class SixMonthBookingTester:
    def __init__(self, base_url="https://mani-pedi-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_passed = 0
        self.tests_total = 0

    def log_result(self, test_name, success, details=""):
        """Логування результату тесту"""
        self.tests_total += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {details}")

    def test_6_month_booking_functionality(self):
        """Тест функціональності бронювання на 6 місяців"""
        print("🚀 Тестування бронювання на 6 місяців")
        print("=" * 60)
        
        # Тест 1: Отримати список послуг
        print("\n📋 Тест 1: Отримання списку послуг")
        try:
            response = requests.get(f"{self.api_url}/services")
            if response.status_code == 200:
                services = response.json()
                if services:
                    service = services[0]
                    service_id = service['id']
                    print(f"   Використовуємо послугу: {service['name']} (ID: {service_id})")
                    self.log_result("GET /api/services", True)
                else:
                    self.log_result("GET /api/services", False, "Немає доступних послуг")
                    return False
            else:
                self.log_result("GET /api/services", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("GET /api/services", False, f"Exception: {str(e)}")
            return False

        # Тест 2: Перевірка слотів на дату через 150 днів
        print("\n📅 Тест 2: Перевірка слотів на дату через 150 днів")
        date_150_days = (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d')
        print(f"   Дата: {date_150_days}")
        
        try:
            url = f"{self.api_url}/timeslots/{date_150_days}?service_id={service_id}&master_id=admin"
            response = requests.get(url)
            
            if response.status_code == 200:
                timeslots = response.json()
                print(f"   Отримано {len(timeslots)} слотів")
                self.log_result("Слоти на 150 днів вперед", True, f"Знайдено {len(timeslots)} слотів")
            else:
                self.log_result("Слоти на 150 днів вперед", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Слоти на 150 днів вперед", False, f"Exception: {str(e)}")
            return False

        # Тест 3: Створення бронювання на дату через 100 днів
        print("\n📝 Тест 3: Створення бронювання на дату через 100 днів")
        date_100_days = (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d')
        print(f"   Дата: {date_100_days}")
        
        # Спочатку отримаємо доступні слоти
        try:
            url = f"{self.api_url}/timeslots/{date_100_days}?service_id={service_id}&master_id=admin"
            response = requests.get(url)
            
            if response.status_code == 200:
                timeslots = response.json()
                available_slots = [slot for slot in timeslots if slot.get('available', False)]
                
                if available_slots:
                    time_slot = available_slots[0]['time']
                    print(f"   Використовуємо слот: {time_slot}")
                    self.log_result("Отримання слотів на 100 днів", True, f"Доступно {len(available_slots)} слотів")
                else:
                    # Якщо немає доступних слотів, використаємо перший слот для тесту
                    if timeslots:
                        time_slot = timeslots[0]['time']
                        print(f"   Використовуємо слот (може бути зайнятий): {time_slot}")
                        self.log_result("Отримання слотів на 100 днів", True, f"Знайдено {len(timeslots)} слотів (можливо зайняті)")
                    else:
                        self.log_result("Отримання слотів на 100 днів", False, "Немає слотів")
                        return False
            else:
                self.log_result("Отримання слотів на 100 днів", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Отримання слотів на 100 днів", False, f"Exception: {str(e)}")
            return False

        # Створення бронювання
        booking_data = {
            "master_id": "admin",
            "service_id": service_id,
            "date": date_100_days,
            "time": time_slot,
            "client_name": "Тест Клієнт",
            "client_phone": "+380501234567"
        }
        
        try:
            response = requests.post(f"{self.api_url}/bookings", json=booking_data)
            
            if response.status_code == 200:
                booking = response.json()
                booking_id = booking.get('id')
                print(f"   Створено бронювання: {booking_id}")
                self.log_result("Створення бронювання на 100 днів", True, f"ID: {booking_id}")
                
                # Скасуємо тестове бронювання
                try:
                    cancel_response = requests.put(
                        f"{self.api_url}/bookings/{booking_id}/cancel",
                        json={"cancellation_reason": "Тестове бронювання"}
                    )
                    if cancel_response.status_code == 200:
                        print(f"   Тестове бронювання скасовано")
                        self.log_result("Скасування тестового бронювання", True)
                    else:
                        self.log_result("Скасування тестового бронювання", False, f"Status: {cancel_response.status_code}")
                except Exception as e:
                    self.log_result("Скасування тестового бронювання", False, f"Exception: {str(e)}")
                
                return True
            else:
                error_msg = f"Status: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f", Response: {error_data}"
                except:
                    error_msg += f", Text: {response.text[:200]}"
                self.log_result("Створення бронювання на 100 днів", False, error_msg)
                return False
        except Exception as e:
            self.log_result("Створення бронювання на 100 днів", False, f"Exception: {str(e)}")
            return False

    def run_test(self):
        """Запуск тесту"""
        success = self.test_6_month_booking_functionality()
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
        print("=" * 60)
        print(f"Тестів пройдено: {self.tests_passed}/{self.tests_total}")
        print(f"Успішність: {(self.tests_passed/self.tests_total)*100:.1f}%")
        
        if success and self.tests_passed == self.tests_total:
            print("\n✅ ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО!")
            print("Функціональність бронювання на 6 місяців працює коректно.")
            return True
        else:
            print("\n❌ ДЕЯКІ ТЕСТИ НЕ ПРОЙШЛИ")
            return False

def main():
    tester = SixMonthBookingTester()
    success = tester.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())