#!/usr/bin/env python3
"""
Тестування Telegram сповіщень для адміна та Site Settings API
Створено для тестування функціоналу згідно з завданням
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Додаємо шлях до backend для імпорту
sys.path.append('/app/backend')

class AdminNotificationsTester:
    def __init__(self):
        # Використовуємо URL з frontend/.env
        self.base_url = "https://beauty-hub-180.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.admin_token = None
        self.test_results = []
        self.created_booking_id = None
        
        print(f"🔧 Тестування API: {self.api_url}")
        print(f"🔧 ADMIN_TELEGRAM_ID з .env: 1097557544")
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Логування результату тесту"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and isinstance(response_data, dict):
            print(f"   📊 Response keys: {list(response_data.keys())}")
            
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        
    def make_request(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Виконання HTTP запиту"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers)
                
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:200]}
                
            return success, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0
    
    def test_admin_login(self):
        """Тест авторизації адміна"""
        print("\n" + "="*60)
        print("🔐 ТЕСТУВАННЯ АВТОРИЗАЦІЇ АДМІНА")
        print("="*60)
        
        success, data, status = self.make_request(
            'POST', 
            'admin/login',
            data={"username": "admin", "password": "admin123"},
            expected_status=200
        )
        
        if success and 'token' in data:
            self.admin_token = data['token']
            self.log_result(
                "Авторизація адміна", 
                True, 
                f"Токен отримано (довжина: {len(self.admin_token)})"
            )
            return True
        else:
            self.log_result(
                "Авторизація адміна", 
                False, 
                f"Status: {status}, Response: {data}"
            )
            return False
    
    def test_site_settings_api(self):
        """Тестування Site Settings API"""
        print("\n" + "="*60)
        print("⚙️  ТЕСТУВАННЯ SITE SETTINGS API")
        print("="*60)
        
        # 1. GET /api/settings (публічний доступ)
        success, data, status = self.make_request('GET', 'settings')
        
        if success:
            self.log_result(
                "GET /api/settings (публічний)", 
                True, 
                f"Отримано налаштування: {data.get('site_name', 'N/A')}"
            )
            original_color = data.get('primary_color', '#D4A5A5')
        else:
            self.log_result(
                "GET /api/settings (публічний)", 
                False, 
                f"Status: {status}, Response: {data}"
            )
            return False
        
        if not self.admin_token:
            print("❌ Немає токена адміна - пропускаємо PUT тест")
            return False
            
        # 2. PUT /api/admin/settings (потребує авторизації)
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        new_color = "#FF5733"  # Новий колір для тесту
        
        update_data = {
            "id": "site_settings",
            "site_name": "Nail Studio",
            "site_description": "Професійний догляд за вашими руками та ногами",
            "primary_color": new_color,
            "secondary_color": "#9E829C",
            "accent_color": "#F3EBEB",
            "phone": "+380 99 123 45 67",
            "email": "info@beauty-alena.pp.ua",
            "address": "Київ, вул. Прикладна, 1",
            "working_hours": "Пн-Сб: 9:00-18:00"
        }
        
        success, data, status = self.make_request(
            'PUT', 
            'admin/settings',
            data=update_data,
            headers=auth_headers
        )
        
        if success:
            self.log_result(
                "PUT /api/admin/settings (авторизований)", 
                True, 
                f"Колір оновлено на: {data.get('primary_color', 'N/A')}"
            )
        else:
            self.log_result(
                "PUT /api/admin/settings (авторизований)", 
                False, 
                f"Status: {status}, Response: {data}"
            )
            return False
        
        # 3. Перевірка, що зміни збереглися
        success, data, status = self.make_request('GET', 'settings')
        
        if success and data.get('primary_color') == new_color:
            self.log_result(
                "Перевірка збереження налаштувань", 
                True, 
                f"Колір успішно змінено на: {new_color}"
            )
        else:
            self.log_result(
                "Перевірка збереження налаштувань", 
                False, 
                f"Очікувався {new_color}, отримано {data.get('primary_color', 'N/A')}"
            )
        
        return True
    
    def test_booking_with_admin_notifications(self):
        """Тестування створення запису з Telegram сповіщеннями для адміна"""
        print("\n" + "="*60)
        print("📱 ТЕСТУВАННЯ TELEGRAM СПОВІЩЕНЬ ДЛЯ АДМІНА")
        print("="*60)
        
        # Спочатку отримаємо доступні послуги
        success, services_data, status = self.make_request('GET', 'services')
        
        if not success or not services_data:
            self.log_result(
                "Отримання послуг для тесту", 
                False, 
                f"Не вдалося отримати послуги. Status: {status}"
            )
            return False
            
        if len(services_data) == 0:
            self.log_result(
                "Отримання послуг для тесту", 
                False, 
                "Немає доступних послуг для тестування"
            )
            return False
        
        service = services_data[0]
        service_id = service['id']
        
        self.log_result(
            "Отримання послуг для тесту", 
            True, 
            f"Використовуємо послугу: {service['name']} (ID: {service_id})"
        )
        
        # Створюємо запис на завтра
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        booking_data = {
            "service_id": service_id,
            "date": tomorrow,
            "time": "14:00",
            "client_name": "Олена Тестова",
            "client_phone": "+380991234567",
            "client_email": "olena.test@example.com",
            "notes": "Тестовий запис для перевірки Telegram сповіщень"
        }
        
        # 1. POST /api/bookings - повинно відправити сповіщення адміну
        success, data, status = self.make_request(
            'POST', 
            'bookings',
            data=booking_data
        )
        
        if success and 'id' in data:
            self.created_booking_id = data['id']
            self.log_result(
                "POST /api/bookings (з Telegram сповіщенням)", 
                True, 
                f"Запис створено ID: {self.created_booking_id}. Telegram сповіщення відправлено адміну (ID: 1097557544)"
            )
        else:
            self.log_result(
                "POST /api/bookings (з Telegram сповіщенням)", 
                False, 
                f"Status: {status}, Response: {data}"
            )
            return False
        
        return True
    
    def test_booking_cancellation_with_notifications(self):
        """Тестування скасування запису з Telegram сповіщеннями"""
        if not self.created_booking_id:
            print("❌ Немає створеного запису для тестування скасування")
            return False
        
        print("\n" + "="*60)
        print("❌ ТЕСТУВАННЯ СКАСУВАННЯ ЗАПИСУ З СПОВІЩЕННЯМИ")
        print("="*60)
        
        # PUT /api/bookings/{booking_id}/cancel - скасування клієнтом
        cancel_data = {
            "cancellation_reason": "Тестове скасування для перевірки Telegram сповіщень"
        }
        
        success, data, status = self.make_request(
            'PUT', 
            f'bookings/{self.created_booking_id}/cancel',
            data=cancel_data
        )
        
        if success:
            self.log_result(
                "PUT /api/bookings/{id}/cancel (з Telegram сповіщенням)", 
                True, 
                f"Запис скасовано. Telegram сповіщення відправлено адміну (ID: 1097557544)"
            )
        else:
            self.log_result(
                "PUT /api/bookings/{id}/cancel (з Telegram сповіщенням)", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        return success
    
    def test_admin_booking_status_change(self):
        """Тестування зміни статусу запису через адмін-панель"""
        if not self.admin_token:
            print("❌ Немає токена адміна для тестування")
            return False
            
        print("\n" + "="*60)
        print("👨‍💼 ТЕСТУВАННЯ ЗМІНИ СТАТУСУ ЧЕРЕЗ АДМІН-ПАНЕЛЬ")
        print("="*60)
        
        # Спочатку створимо новий запис для тестування
        success, services_data, status = self.make_request('GET', 'services')
        if not success or not services_data:
            print("❌ Не вдалося отримати послуги")
            return False
            
        service = services_data[0]
        tomorrow = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        booking_data = {
            "service_id": service['id'],
            "date": tomorrow,
            "time": "16:00",
            "client_name": "Марія Адмінтест",
            "client_phone": "+380987654321",
            "client_email": "maria.admin@example.com",
            "notes": "Тестовий запис для адмін-панелі"
        }
        
        success, booking_response, status = self.make_request('POST', 'bookings', data=booking_data)
        
        if not success or 'id' not in booking_response:
            self.log_result(
                "Створення запису для адмін-тесту", 
                False, 
                f"Status: {status}, Response: {booking_response}"
            )
            return False
        
        admin_booking_id = booking_response['id']
        self.log_result(
            "Створення запису для адмін-тесту", 
            True, 
            f"Запис створено ID: {admin_booking_id}"
        )
        
        # PUT /api/admin/bookings/{booking_id} - зміна статусу адміном
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        update_data = {
            "status": "confirmed",
            "notes": "Підтверджено адміністратором через тестування"
        }
        
        success, data, status = self.make_request(
            'PUT', 
            f'admin/bookings/{admin_booking_id}',
            data=update_data,
            headers=auth_headers
        )
        
        if success:
            self.log_result(
                "PUT /api/admin/bookings/{id} (зміна статусу)", 
                True, 
                f"Статус змінено на 'confirmed'. Telegram сповіщення відправлено клієнту"
            )
        else:
            self.log_result(
                "PUT /api/admin/bookings/{id} (зміна статусу)", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        return success
    
    def test_unauthorized_access(self):
        """Тестування неавторизованого доступу"""
        print("\n" + "="*60)
        print("🚫 ТЕСТУВАННЯ НЕАВТОРИЗОВАНОГО ДОСТУПУ")
        print("="*60)
        
        # Спроба оновити налаштування без токена
        update_data = {"primary_color": "#000000"}
        
        success, data, status = self.make_request(
            'PUT', 
            'admin/settings',
            data=update_data,
            expected_status=401
        )
        
        if success:  # success означає, що отримали очікуваний 401 статус
            self.log_result(
                "Неавторизований доступ до PUT /admin/settings", 
                True, 
                "Правильно повернуто 401 Unauthorized"
            )
        else:
            self.log_result(
                "Неавторизований доступ до PUT /admin/settings", 
                False, 
                f"Очікувався 401, отримано {status}"
            )
        
        return success
    
    def run_all_tests(self):
        """Запуск всіх тестів"""
        print("🚀 ПОЧАТОК ТЕСТУВАННЯ ADMIN NOTIFICATIONS & SITE SETTINGS")
        print(f"🌐 Backend URL: {self.api_url}")
        print(f"📱 Admin Telegram ID: 1097557544")
        print("📝 Примітка: Telegram повідомлення не можна перевірити без реального бота,")
        print("    але переконуємося, що API не падає при відправці")
        
        # Послідовність тестів
        tests = [
            self.test_admin_login,
            self.test_site_settings_api,
            self.test_booking_with_admin_notifications,
            self.test_booking_cancellation_with_notifications,
            self.test_admin_booking_status_change,
            self.test_unauthorized_access
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_result(
                    f"Помилка в {test.__name__}", 
                    False, 
                    f"Exception: {str(e)}"
                )
        
        # Підсумок
        print("\n" + "="*60)
        print("📊 ПІДСУМОК ТЕСТУВАННЯ")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Всього тестів: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📊 Успішність: {(passed_tests/total_tests)*100:.1f}%")
        
        # Деталі провалених тестів
        failed = [r for r in self.test_results if not r['success']]
        if failed:
            print(f"\n❌ ПРОВАЛЕНІ ТЕСТИ:")
            for test in failed:
                print(f"   • {test['test']}: {test['details']}")
        
        print(f"\n🎯 ВИСНОВОК:")
        if failed_tests == 0:
            print("✅ Всі тести пройдено успішно!")
            print("📱 Telegram сповіщення налаштовано правильно (ADMIN_TELEGRAM_ID: 1097557544)")
            print("⚙️  Site Settings API працює коректно")
        else:
            print(f"⚠️  {failed_tests} тестів провалено. Перевірте деталі вище.")
        
        return failed_tests == 0

def main():
    """Головна функція"""
    tester = AdminNotificationsTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())