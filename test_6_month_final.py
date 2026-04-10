#!/usr/bin/env python3
"""
Фінальний тест для перевірки функціональності бронювання на 6 місяців
Відповідно до завдання користувача
"""

import requests
import sys
from datetime import datetime, timedelta

def test_6_month_booking():
    """Тест бронювання на 6 місяців згідно з завданням"""
    base_url = "https://service-booking-hub-31.preview.emergentagent.com/api"
    
    print("🚀 ШВИДКИЙ ТЕСТ БРОНЮВАННЯ НА 6 МІСЯЦІВ")
    print("=" * 60)
    
    # Тест 1: Отримати список послуг GET /api/services
    print("\n📋 Тест 1: Отримання списку послуг")
    try:
        response = requests.get(f"{base_url}/services")
        if response.status_code == 200:
            services = response.json()
            if services:
                service = services[0]
                service_id = service['id']
                print(f"✅ Отримано {len(services)} послуг")
                print(f"   Використовуємо: {service['name']} (ID: {service_id})")
            else:
                print("❌ Немає доступних послуг")
                return False
        else:
            print(f"❌ Помилка отримання послуг: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Виняток при отриманні послуг: {str(e)}")
        return False

    # Тест 2: Обчислити дату через 150 днів і отримати timeslots
    print("\n📅 Тест 2: Бронювання на дату через 150 днів")
    date_150_days = (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d')
    print(f"   Дата: {date_150_days}")
    
    try:
        url = f"{base_url}/timeslots/{date_150_days}?service_id={service_id}&master_id=admin"
        response = requests.get(url)
        
        if response.status_code == 200:
            timeslots = response.json()
            print(f"✅ Отримано відповідь для дати через 150 днів")
            print(f"   Статус: 200 OK")
            print(f"   Кількість слотів: {len(timeslots)}")
            print("   ✅ НЕМАЄ ПОМИЛКИ ПРО 6 МІСЯЦІВ - ТЕСТ ПРОЙШОВ")
        elif response.status_code == 400:
            try:
                error = response.json()
                if "Cannot book more than 6 months in advance" in error.get('detail', ''):
                    print("❌ Помилка: дата через 150 днів блокується 6-місячним обмеженням")
                    print("   Це неправильно - 150 днів < 180 днів")
                    return False
                else:
                    print(f"❌ Інша помилка 400: {error}")
                    return False
            except:
                print(f"❌ Помилка 400: {response.text}")
                return False
        else:
            print(f"❌ Неочікуваний статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Виняток: {str(e)}")
        return False

    # Тест 3: Створення бронювання на дату через 100 днів
    print("\n📝 Тест 3: Створення бронювання на дату через 100 днів")
    date_100_days = (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d')
    print(f"   Дата: {date_100_days}")
    
    # Спочатку отримаємо доступні слоти
    try:
        url = f"{base_url}/timeslots/{date_100_days}?service_id={service_id}&master_id=admin"
        response = requests.get(url)
        
        if response.status_code == 200:
            timeslots = response.json()
            print(f"   Отримано {len(timeslots)} слотів")
            
            # Використаємо перший слот (навіть якщо він зайнятий, для тесту API)
            if timeslots:
                time_slot = timeslots[0]['time'] if timeslots else "10:00"
            else:
                time_slot = "10:00"  # Дефолтний час для тесту
                
            print(f"   Використовуємо слот: {time_slot}")
        elif response.status_code == 400:
            try:
                error = response.json()
                if "Cannot book more than 6 months in advance" in error.get('detail', ''):
                    print("❌ Помилка: дата через 100 днів блокується 6-місячним обмеженням")
                    print("   Це неправильно - 100 днів < 180 днів")
                    return False
                else:
                    print(f"❌ Інша помилка при отриманні слотів: {error}")
                    return False
            except:
                print(f"❌ Помилка при отриманні слотів: {response.text}")
                return False
        else:
            print(f"❌ Неочікуваний статус при отриманні слотів: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Виняток при отриманні слотів: {str(e)}")
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
        response = requests.post(f"{base_url}/bookings", json=booking_data)
        
        if response.status_code == 200:
            booking = response.json()
            booking_id = booking.get('id')
            print(f"✅ Бронювання створено успішно")
            print(f"   ID: {booking_id}")
            print(f"   Статус: 200 OK")
            
            # Скасуємо тестове бронювання
            try:
                cancel_response = requests.put(
                    f"{base_url}/bookings/{booking_id}/cancel",
                    json={"cancellation_reason": "Тестове бронювання - автоматичне скасування"}
                )
                if cancel_response.status_code == 200:
                    print("   Тестове бронювання автоматично скасовано")
                else:
                    print(f"   Попередження: не вдалося скасувати тестове бронювання (статус: {cancel_response.status_code})")
            except Exception as e:
                print(f"   Попередження: помилка при скасуванні: {str(e)}")
            
            return True
        else:
            try:
                error = response.json()
                print(f"❌ Помилка створення бронювання: {error}")
            except:
                print(f"❌ Помилка створення бронювання: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Виняток при створенні бронювання: {str(e)}")
        return False

def test_6_month_limit():
    """Додатковий тест для перевірки обмеження 6 місяців"""
    base_url = "https://service-booking-hub-31.preview.emergentagent.com/api"
    
    print("\n🔒 Додатковий тест: Перевірка обмеження 6 місяців")
    
    # Отримаємо послугу
    try:
        response = requests.get(f"{base_url}/services")
        if response.status_code == 200:
            services = response.json()
            if services:
                service_id = services[0]['id']
            else:
                print("❌ Немає послуг для тесту обмеження")
                return False
        else:
            print("❌ Не вдалося отримати послуги для тесту обмеження")
            return False
    except Exception as e:
        print(f"❌ Виняток при отриманні послуг: {str(e)}")
        return False

    # Тест дати понад 180 днів (має повернути помилку)
    date_beyond_limit = (datetime.now() + timedelta(days=185)).strftime('%Y-%m-%d')
    
    try:
        url = f"{base_url}/timeslots/{date_beyond_limit}?service_id={service_id}&master_id=admin"
        response = requests.get(url)
        
        if response.status_code == 400:
            try:
                error = response.json()
                if "Cannot book more than 6 months in advance" in error.get('detail', ''):
                    print(f"✅ Обмеження 6 місяців працює коректно")
                    print(f"   Дата {date_beyond_limit} (185 днів) правильно заблокована")
                    return True
                else:
                    print(f"❌ Неочікувана помилка 400: {error}")
                    return False
            except:
                print(f"❌ Помилка парсингу відповіді: {response.text}")
                return False
        else:
            print(f"❌ Очікувалася помилка 400, отримано: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Виняток при тестуванні обмеження: {str(e)}")
        return False

def main():
    """Головна функція"""
    print("Тестування функціональності бронювання на 6 місяців")
    print("Backend URL: https://service-booking-hub-31.preview.emergentagent.com/api")
    
    # Основний тест
    main_test_passed = test_6_month_booking()
    
    # Додатковий тест обмеження
    limit_test_passed = test_6_month_limit()
    
    print("\n" + "=" * 60)
    print("📊 ПІДСУМОК ТЕСТУВАННЯ")
    print("=" * 60)
    
    if main_test_passed and limit_test_passed:
        print("✅ ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО!")
        print("✅ Бронювання на дату через 150 днів працює (немає помилки про 6 місяців)")
        print("✅ Створення бронювання на дату через 100 днів працює")
        print("✅ Обмеження 6 місяців (180 днів) працює коректно")
        return 0
    else:
        print("❌ ДЕЯКІ ТЕСТИ НЕ ПРОЙШЛИ")
        if not main_test_passed:
            print("❌ Основний тест бронювання не пройшов")
        if not limit_test_passed:
            print("❌ Тест обмеження 6 місяців не пройшов")
        return 1

if __name__ == "__main__":
    sys.exit(main())