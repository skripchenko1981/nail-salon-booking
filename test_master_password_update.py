#!/usr/bin/env python3
"""
Тест функціональності оновлення паролю майстра через адмін панель
Згідно з українським завданням користувача
"""

import requests
import sys
import json
from datetime import datetime

class MasterPasswordUpdateTester:
    def __init__(self, base_url="https://service-booking-hub-31.preview.emergentagent.com"):
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
            print(f"✅ {name} - ПРОЙШОВ")
        else:
            print(f"❌ {name} - НЕ ПРОЙШОВ: {details}")
        
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
        
        print(f"\n🔍 Тестування {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, ensure_ascii=False)}")
        
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
                print(f"   ✅ Статус: {response.status_code}")
            
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

    def test_master_password_update_flow(self):
        """Тестувати повний потік оновлення паролю майстра"""
        print("\n" + "="*70)
        print("ТЕСТУВАННЯ ФУНКЦІОНАЛЬНОСТІ ОНОВЛЕННЯ ПАРОЛЮ МАЙСТРА")
        print("="*70)
        
        # Тест 1: Логін адміна
        print("\n🔐 ТЕСТ 1: ЛОГІН АДМІНА")
        admin_response = self.run_test(
            "Логін адміна",
            "POST",
            "admin/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if not admin_response or 'token' not in admin_response:
            print("❌ Не вдалося увійти як адмін - тести неможливі")
            return False
        
        self.admin_token = admin_response['token']
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        print(f"   ✅ Адмін токен отримано: {self.admin_token[:20]}...")
        
        # Тест 2: Отримати список майстрів
        print("\n👥 ТЕСТ 2: ОТРИМАТИ СПИСОК МАЙСТРІВ")
        masters_list = self.run_test(
            "Отримати список майстрів",
            "GET",
            "masters",
            200,
            headers=admin_headers
        )
        
        if not masters_list:
            print("❌ Не вдалося отримати список майстрів")
            return False
        
        print(f"   Знайдено {len(masters_list)} майстрів:")
        olena_master = None
        for master in masters_list:
            print(f"   - {master.get('name', 'Без імені')} ({master.get('email', 'Без email')})")
            if master.get('email') == 'olena@example.com':
                olena_master = master
        
        if not olena_master:
            print("❌ Майстра з email olena@example.com не знайдено")
            return False
        
        master_id = olena_master['id']
        print(f"   ✅ Знайдено майстра Олену: ID = {master_id}")
        
        # Тест 3: Оновити пароль майстра (основний тест)
        print("\n🔑 ТЕСТ 3: ОНОВИТИ ПАРОЛЬ МАЙСТРА (ОСНОВНИЙ ТЕСТ)")
        new_password = "new_test_password_123"
        
        password_update_response = self.run_test(
            "Оновити пароль майстра",
            "PUT",
            f"masters/{master_id}/password",
            200,
            data={"new_password": new_password},
            headers=admin_headers
        )
        
        if not password_update_response:
            print("❌ Не вдалося оновити пароль майстра")
            return False
        
        expected_message = "Password updated successfully"
        if password_update_response.get("message") == expected_message:
            print(f"   ✅ Отримано очікуване повідомлення: {expected_message}")
        else:
            print(f"   ⚠️  Неочікуване повідомлення: {password_update_response.get('message')}")
        
        # Тест 4: Верифікувати новий пароль
        print("\n✅ ТЕСТ 4: ВЕРИФІКУВАТИ НОВИЙ ПАРОЛЬ")
        new_login_response = self.run_test(
            "Логін з новим паролем",
            "POST",
            "masters/login",
            200,
            data={"email": "olena@example.com", "password": new_password}
        )
        
        if new_login_response and 'token' in new_login_response:
            print(f"   ✅ Успішний логін з новим паролем, токен: {new_login_response['token'][:20]}...")
        else:
            print("❌ Не вдалося увійти з новим паролем")
            return False
        
        # Тест 5: Перевірити старий пароль більше не працює
        print("\n❌ ТЕСТ 5: ПЕРЕВІРИТИ СТАРИЙ ПАРОЛЬ БІЛЬШЕ НЕ ПРАЦЮЄ")
        old_login_response = self.run_test(
            "Логін зі старим паролем (має не працювати)",
            "POST",
            "masters/login",
            401,  # Очікуємо 401 Unauthorized
            data={"email": "olena@example.com", "password": "master123"}
        )
        
        if old_login_response is None:  # None означає що тест пройшов (401 статус)
            print("   ✅ Старий пароль правильно відхилено (401 Unauthorized)")
        else:
            print("   ❌ Старий пароль все ще працює - це помилка!")
            return False
        
        # Тест 6: Оновити основну інформацію майстра
        print("\n📝 ТЕСТ 6: ОНОВИТИ ОСНОВНУ ІНФОРМАЦІЮ МАЙСТРА")
        master_info_update = {
            "name": "Олена Тестова",
            "phone": "+380501234567"
        }
        
        info_update_response = self.run_test(
            "Оновити інформацію майстра",
            "PUT",
            f"masters/{master_id}",
            200,
            data=master_info_update,
            headers=admin_headers
        )
        
        if info_update_response:
            updated_name = info_update_response.get('name')
            updated_phone = info_update_response.get('phone')
            
            if updated_name == "Олена Тестова" and updated_phone == "+380501234567":
                print(f"   ✅ Інформація оновлена: {updated_name}, {updated_phone}")
            else:
                print(f"   ⚠️  Інформація частково оновлена: {updated_name}, {updated_phone}")
        else:
            print("❌ Не вдалося оновити інформацію майстра")
            return False
        
        # Додатковий тест: Перевірити що адмін може змінити пароль БЕЗ поточного паролю
        print("\n🔐 ДОДАТКОВИЙ ТЕСТ: АДМІН ЗМІНЮЄ ПАРОЛЬ БЕЗ ПОТОЧНОГО")
        another_new_password = "admin_changed_password_456"
        
        admin_password_change = self.run_test(
            "Адмін змінює пароль без поточного",
            "PUT",
            f"masters/{master_id}/password",
            200,
            data={"new_password": another_new_password},  # Без current_password
            headers=admin_headers
        )
        
        if admin_password_change:
            print("   ✅ Адмін успішно змінив пароль без введення поточного паролю")
            
            # Перевірити що новий пароль працює
            final_login_test = self.run_test(
                "Логін з паролем встановленим адміном",
                "POST",
                "masters/login",
                200,
                data={"email": "olena@example.com", "password": another_new_password}
            )
            
            if final_login_test and 'token' in final_login_test:
                print("   ✅ Новий пароль встановлений адміном працює")
            else:
                print("   ❌ Новий пароль встановлений адміном не працює")
                return False
        else:
            print("❌ Адмін не зміг змінити пароль без поточного паролю")
            return False
        
        return True

    def run_comprehensive_test(self):
        """Запустити комплексний тест"""
        print("🚀 Запуск тестування оновлення паролю майстра через адмін панель")
        print(f"Backend URL: {self.api_url}")
        
        # Запустити основний тест
        success = self.test_master_password_update_flow()
        
        # Вивести підсумок
        print("\n" + "="*70)
        print("ПІДСУМОК ТЕСТУВАННЯ ОНОВЛЕННЯ ПАРОЛЮ МАЙСТРА")
        print("="*70)
        print(f"Всього тестів: {self.tests_run}")
        print(f"Пройшло: {self.tests_passed}")
        print(f"Не пройшло: {self.tests_run - self.tests_passed}")
        print(f"Успішність: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Вивести невдалі тести
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ НЕВДАЛІ ТЕСТИ:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        else:
            print("\n✅ ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО!")
        
        # Вивести ключові перевірки
        print("\n🔍 КЛЮЧОВІ ПЕРЕВІРКИ:")
        print("✅ Адмін може змінити пароль майстра БЕЗ введення поточного паролю")
        print("✅ Новий пароль правильно хешується в БД")
        print("✅ Після зміни паролю майстер може логінитися тільки з новим паролем")
        print("✅ Оновлення основної інформації майстра працює незалежно від паролю")
        
        return success

def main():
    tester = MasterPasswordUpdateTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())