#!/usr/bin/env python3
"""
Скрипт для ініціалізації тестової бази даних
Створює майстрів, послуги, графіки роботи для тестування
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from uuid import uuid4
import bcrypt

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


def hash_password(password: str) -> str:
    """Хешувати пароль"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def init_database():
    """Ініціалізувати базу даних з тестовими даними"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔄 Очищення старих даних...")
    
    # Видаляємо всі неактивні майстри та старі дані без master_id
    await db.masters.delete_many({"is_active": False})
    await db.services.delete_many({"master_id": "admin"})
    await db.work_schedule.delete_many({"master_id": {"$exists": False}})
    
    print("✅ Старі дані очищені")
    
    # Створюємо тестових майстрів
    print("\n👤 Створення майстрів...")
    
    masters_data = [
        {
            "id": str(uuid4()),
            "name": "Олена Коваль",
            "email": "olena@example.com",
            "phone": "+380501234567",
            "password_hash": hash_password("master123"),
            "role": "master",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid4()),
            "name": "Марія Петренко",
            "email": "maria@example.com",
            "phone": "+380502345678",
            "password_hash": hash_password("master123"),
            "role": "master",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Перевіряємо, чи майстри вже існують
    for master in masters_data:
        existing = await db.masters.find_one({"email": master["email"]})
        if not existing:
            await db.masters.insert_one(master)
            print(f"  ✅ Створено майстра: {master['name']} (email: {master['email']})")
        else:
            # Оновлюємо існуючого майстра, щоб він став активним
            await db.masters.update_one(
                {"email": master["email"]},
                {"$set": {"is_active": True}}
            )
            master["id"] = existing["id"]  # Використовуємо існуючий ID
            print(f"  ♻️  Активовано майстра: {master['name']}")
    
    # Отримуємо ID майстрів
    master1_id = masters_data[0]["id"]
    master2_id = masters_data[1]["id"]
    
    # Створюємо послуги для кожного майстра
    print("\n💅 Створення послуг...")
    
    services_data = [
        # Послуги для Олени
        {
            "id": str(uuid4()),
            "master_id": master1_id,
            "name": "Класичний манікюр",
            "description": "Класичний манікюр з покриттям",
            "duration_minutes": 60,
            "price": 350.0
        },
        {
            "id": str(uuid4()),
            "master_id": master1_id,
            "name": "Педикюр",
            "description": "Класичний педикюр",
            "duration_minutes": 90,
            "price": 450.0
        },
        {
            "id": str(uuid4()),
            "master_id": master1_id,
            "name": "Манікюр + Педикюр",
            "description": "Комплекс манікюр + педикюр",
            "duration_minutes": 120,
            "price": 700.0
        },
        # Послуги для Марії
        {
            "id": str(uuid4()),
            "master_id": master2_id,
            "name": "Класичний манікюр",
            "description": "Класичний манікюр з покриттям",
            "duration_minutes": 60,
            "price": 400.0
        },
        {
            "id": str(uuid4()),
            "master_id": master2_id,
            "name": "Апаратний педикюр",
            "description": "Апаратний педикюр з покриттям",
            "duration_minutes": 75,
            "price": 500.0
        },
        {
            "id": str(uuid4()),
            "master_id": master2_id,
            "name": "Нарощування нігтів",
            "description": "Нарощування гелем",
            "duration_minutes": 180,
            "price": 800.0
        }
    ]
    
    for service in services_data:
        # Видаляємо старі послуги з таким же іменем та master_id
        await db.services.delete_many({
            "master_id": service["master_id"],
            "name": service["name"]
        })
        await db.services.insert_one(service)
        master_name = next(m["name"] for m in masters_data if m["id"] == service["master_id"])
        print(f"  ✅ Послуга: {service['name']} для {master_name}")
    
    # Створюємо графік роботи для кожного майстра
    print("\n📅 Створення графіків роботи...")
    
    for master in masters_data:
        master_id = master["id"]
        
        # Видаляємо старий графік цього майстра
        await db.work_schedule.delete_many({"master_id": master_id})
        
        # Створюємо графік: працює Пн-Пт (0-4), 09:00-18:00
        for day in range(7):
            schedule = {
                "id": str(uuid4()),
                "master_id": master_id,
                "day_of_week": day,
                "start_time": "09:00",
                "end_time": "18:00",
                "is_working": day < 5  # Працює Пн-Пт
            }
            await db.work_schedule.insert_one(schedule)
        
        print(f"  ✅ Графік для {master['name']}: Пн-Пт 09:00-18:00")
    
    print("\n✨ База даних успішно ініціалізована!")
    print("\n📋 Створені майстри:")
    for master in masters_data:
        print(f"  Email: {master['email']}")
        print(f"  Пароль: master123")
        print()


if __name__ == "__main__":
    asyncio.run(init_database())
