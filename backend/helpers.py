"""Допоміжні функції: валідатори, клієнт-хелпери"""
import re
import phonenumbers
from fastapi import HTTPException
from database import db
from datetime import datetime, timezone
import uuid


def validate_ukrainian_phone(phone: str) -> str:
    """Валідація українського номера телефону"""
    if not phone:
        raise ValueError("Номер телефону обов'язковий")
    
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    if cleaned.startswith('+'):
        pass
    elif cleaned.startswith('380'):
        cleaned = '+' + cleaned
    elif cleaned.startswith('80'):
        cleaned = '+3' + cleaned
    elif cleaned.startswith('0'):
        cleaned = '+38' + cleaned
    elif len(cleaned) == 9:
        cleaned = '+380' + cleaned
    
    try:
        parsed = phonenumbers.parse(cleaned, "UA")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        pass
    
    if re.match(r'^\+380\d{9}$', cleaned):
        return cleaned
    
    raise ValueError(f"Невірний формат номера телефону: {phone}")


async def get_or_create_client(master_id: str, name: str, phone: str, 
                               email: str = None, surname: str = None):
    """Отримати або створити клієнта"""
    existing_client = await db.clients.find_one({"phone": phone}, {"_id": 0})
    
    if existing_client:
        update_data = {}
        if surname and not existing_client.get("surname"):
            update_data["surname"] = surname
        if email and not existing_client.get("email"):
            update_data["email"] = email
        if update_data:
            await db.clients.update_one({"phone": phone}, {"$set": update_data})
        return existing_client
    
    new_client = {
        "id": str(uuid.uuid4()),
        "name": name,
        "surname": surname,
        "phone": phone,
        "email": email,
        "master_id": master_id,
        "total_bookings": 0,
        "total_spent": 0,
        "last_visit": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.clients.insert_one(new_client)
    return new_client


async def update_client_stats(client_id: str, booking_price: int, status: str):
    """Оновити статистику клієнта"""
    if status == "completed":
        await db.clients.update_one(
            {"id": client_id},
            {
                "$inc": {"total_bookings": 1, "total_spent": booking_price},
                "$set": {"last_visit": datetime.now(timezone.utc).isoformat()}
            }
        )
    elif status == "confirmed":
        await db.clients.update_one(
            {"id": client_id},
            {"$inc": {"total_bookings": 1}}
        )
