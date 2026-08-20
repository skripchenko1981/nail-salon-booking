"""Маршрути майстрів"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from database import db
from models import (Master, MasterResponse, MasterCreate, MasterUpdate,
                    MasterPasswordUpdate, MasterTelegramConfig, MasterLogin,
                    MasterLoginResponse, MasterPublic)
from auth import verify_admin, verify_master_or_admin, hash_password, verify_password, create_token
import httpx
import uuid

router = APIRouter()


@router.post("/masters/login", response_model=MasterLoginResponse)
async def master_login(credentials: MasterLogin):
    master = await db.masters.find_one({"email": credentials.email}, {"_id": 0})
    if not master or not verify_password(credentials.password, master.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(master["email"], role="master", user_id=master["id"])
    return {"token": token, "master": MasterResponse(**master)}

@router.get("/masters", response_model=List[MasterPublic])
async def get_masters():
    masters = await db.masters.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    return masters

@router.post("/masters", response_model=MasterResponse)
async def create_master(master: MasterCreate, _: Dict = Depends(verify_admin)):
    existing = await db.masters.find_one({"email": master.email})
    if existing:
        raise HTTPException(status_code=400, detail="Master with this email already exists")
    
    new_master = Master(
        name=master.name, email=master.email, phone=master.phone,
        password_hash=hash_password(master.password),
        bio=master.bio, photo_url=master.photo_url, is_active=master.is_active
    )
    doc = new_master.model_dump()
    await db.masters.insert_one(doc)
    return MasterResponse(**doc)

@router.get("/masters/{master_id}", response_model=MasterResponse)
async def get_master(master_id: str, user: Dict = Depends(verify_master_or_admin)):
    master = await db.masters.find_one({"id": master_id}, {"_id": 0, "password_hash": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return MasterResponse(**master)

@router.get("/masters/me/profile", response_model=MasterResponse)
async def get_my_profile(user: Dict = Depends(verify_master_or_admin)):
    master = await db.masters.find_one({"id": user["user_id"]}, {"_id": 0, "password_hash": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return MasterResponse(**master)

@router.put("/masters/{master_id}", response_model=MasterResponse)
async def update_master(master_id: str, master: MasterUpdate, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in master.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    await db.masters.update_one({"id": master_id}, {"$set": update_data})
    updated = await db.masters.find_one({"id": master_id}, {"_id": 0, "password_hash": 0})
    return MasterResponse(**updated)

@router.put("/masters/{master_id}/password")
async def update_master_password(master_id: str, password_update: MasterPasswordUpdate,
                                 user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if user["role"] == "master" and password_update.current_password:
        master = await db.masters.find_one({"id": master_id}, {"_id": 0})
        if not verify_password(password_update.current_password, master.get("password_hash", "")):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_hash = hash_password(password_update.new_password)
    await db.masters.update_one({"id": master_id}, {"$set": {"password_hash": new_hash}})
    return {"message": "Password updated"}

@router.patch("/masters/{master_id}/telegram")
async def update_master_telegram(master_id: str, config: MasterTelegramConfig, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {
        "telegram_bot_token": config.telegram_bot_token,
        "telegram_chat_id": config.telegram_chat_id,
        "telegram_notifications_enabled": config.telegram_notifications_enabled,
    }
    result = await db.masters.update_one({"id": master_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master not found")
    return {"message": "Telegram settings updated", "notifications_enabled": config.telegram_notifications_enabled}

@router.post("/masters/{master_id}/test-telegram")
async def test_master_telegram(master_id: str, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    master = await db.masters.find_one({"id": master_id}, {"_id": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    
    bot_token = master.get("telegram_bot_token")
    chat_id = master.get("telegram_chat_id")
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="Telegram bot token або chat ID не налаштовано")
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(url, json={
                "chat_id": chat_id,
                "text": "✅ Тестове повідомлення! Ваш Telegram бот працює коректно.",
                "parse_mode": "HTML"
            }, timeout=10.0)
            
            if response.status_code == 200:
                return {"success": True, "message": "Тестове повідомлення відправлено!"}
            else:
                error_data = response.json()
                error_desc = error_data.get("description", "Unknown error")
                if "chat not found" in error_desc.lower():
                    raise HTTPException(status_code=400, detail="Чат не знайдено. Спершу відкрийте вашого бота в Telegram і надішліть йому /start, потім спробуйте знову.")
                if "bot token" in error_desc.lower() or "unauthorized" in error_desc.lower():
                    raise HTTPException(status_code=400, detail="Невірний Bot Token.")
                raise HTTPException(status_code=400, detail=f"Помилка Telegram API: {error_desc}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Timeout при з'єднанні з Telegram API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка: {str(e)}")

@router.put("/masters/{master_id}/set-head")
async def set_head_master(master_id: str, _: Dict = Depends(verify_admin)):
    """Призначити головного майстра (отримує сповіщення про записи всіх майстрів)"""
    master = await db.masters.find_one({"id": master_id}, {"_id": 0, "name": 1})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    await db.masters.update_many({}, {"$set": {"is_head": False}})
    await db.masters.update_one({"id": master_id}, {"$set": {"is_head": True}})
    return {"message": f"Головним майстром призначено {master['name']}"}


@router.post("/masters/{master_id}/reset-notifications")
async def reset_master_notifications(master_id: str, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.masters.update_one({"id": master_id}, {"$set": {"unread_bookings_count": 0}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master not found")
    return {"message": "Notifications reset", "unread_bookings_count": 0}

# ============ НОТАТКИ МАЙСТРА ============

@router.get("/masters/{master_id}/notes/{date}")
async def get_master_note(master_id: str, date: str, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    note = await db.master_notes.find_one({"master_id": master_id, "date": date}, {"_id": 0})
    return {"text": note.get("text", "") if note else "", "date": date}

@router.put("/masters/{master_id}/notes/{date}")
async def save_master_note(master_id: str, date: str, body: dict, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    text = body.get("text", "")
    await db.master_notes.update_one(
        {"master_id": master_id, "date": date},
        {"$set": {"text": text, "master_id": master_id, "date": date}},
        upsert=True
    )
    return {"message": "Note saved", "date": date, "text": text}

@router.delete("/masters/{master_id}")
async def delete_master(master_id: str, _: Dict = Depends(verify_admin)):
    master = await db.masters.find_one({"id": master_id}, {"_id": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    
    await db.masters.delete_one({"id": master_id})
    
    await db.bookings.update_many(
        {"master_id": master_id, "status": {"$in": ["pending", "confirmed"]}},
        {"$set": {"status": "cancelled", "cancellation_reason": "Майстра видалено"}}
    )
    
    bookings_count = await db.bookings.count_documents({"master_id": master_id})
    services_count = await db.services.count_documents({"master_id": master_id})
    
    return {
        "message": f"Майстра {master['name']} видалено",
        "cancelled_bookings": bookings_count,
        "orphaned_services": services_count
    }
