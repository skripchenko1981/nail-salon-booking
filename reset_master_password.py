#!/usr/bin/env python3
"""
Скрипт для скидання паролю майстра
Використання: python3 reset_master_password.py
"""
import asyncio
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
import sys

async def reset_password():
    # З'єднання з MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Запитати email майстра
    email = input("Введіть email майстра: ").strip()
    
    # Перевірити чи існує майстер
    master = await db.masters.find_one({"email": email}, {"_id": 0})
    
    if not master:
        print(f"❌ Майстра з email '{email}' не знайдено")
        client.close()
        return
    
    print(f"\n✓ Знайдено майстра: {master['name']}")
    print(f"  ID: {master['id']}")
    print(f"  Email: {master['email']}")
    
    # Запитати новий пароль
    new_password = input("\nВведіть новий пароль: ").strip()
    
    if len(new_password) < 6:
        print("❌ Пароль повинен містити мінімум 6 символів")
        client.close()
        return
    
    # Хешувати пароль (SHA256)
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    # Оновити в базі
    result = await db.masters.update_one(
        {"email": email},
        {"$set": {"password_hash": password_hash}}
    )
    
    if result.modified_count > 0:
        print(f"\n✅ Пароль успішно оновлено!")
        print(f"   Email: {email}")
        print(f"   Новий пароль: {new_password}")
    else:
        print("❌ Помилка оновлення паролю")
    
    client.close()

if __name__ == "__main__":
    try:
        asyncio.run(reset_password())
    except KeyboardInterrupt:
        print("\n\nСкасовано користувачем")
        sys.exit(0)
