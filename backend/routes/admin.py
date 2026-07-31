"""Адмін маршрути: логін, статистика, управління записами"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict
from database import db
from models import (AdminLogin, AdminLoginResponse, Stats, Booking, BookingUpdate,
                    ReminderSettings)
from auth import verify_admin, verify_master_or_admin, verify_token, hash_password, create_token
from helpers import update_client_stats
from telegram_bot import telegram_bot
from scheduler import check_and_send_reminders
from datetime import datetime, timezone, timedelta
import os

router = APIRouter()


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLogin):
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password_hash = hash_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
    
    if credentials.username != admin_username or hash_password(credentials.password) != admin_password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(admin_username, role="admin")
    return {"token": token, "admin": {"username": admin_username, "role": "admin"}}


@router.get("/admin/bookings", response_model=List[Booking])
async def get_admin_bookings(user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    bookings = await db.bookings.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return bookings


@router.put("/admin/bookings/{booking_id}", response_model=Booking)
async def update_booking_status(booking_id: str, update: BookingUpdate,
                                background_tasks: BackgroundTasks,
                                user: Dict = Depends(verify_master_or_admin)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if "status" in update_data:
        new_status = update_data["status"]
        
        if new_status == "confirmed":
            background_tasks.add_task(
                telegram_bot.notify_client_booking_confirmed,
                booking_id, booking["client_name"],
                booking.get("service_name", ""), booking["date"], booking["time"]
            )
        elif new_status == "cancelled" and booking.get("status") != "cancelled":
            admin_telegram_id = os.environ.get('ADMIN_TELEGRAM_ID')
            if admin_telegram_id:
                master = await db.masters.find_one({"id": booking.get("master_id")}, {"_id": 0, "name": 1})
                m_name = master.get("name", "") if master else ""
                background_tasks.add_task(
                    telegram_bot.notify_admin_booking_cancelled,
                    booking["client_name"], booking["client_phone"],
                    booking.get("service_name", ""), booking["date"],
                    booking["time"], booking.get("price", 0),
                    update_data.get("notes"), admin_telegram_id, m_name
                )
        
        if new_status in ["completed", "confirmed"]:
            client = await db.clients.find_one({"phone": booking["client_phone"]}, {"_id": 0})
            if client:
                background_tasks.add_task(
                    update_client_stats,
                    client["id"], booking.get("price", 0), new_status
                )
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    updated = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return Booking(**updated)


@router.get("/admin/stats", response_model=Stats)
async def get_stats(user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    
    total = await db.bookings.count_documents(query)
    
    revenue_pipeline = [{"$match": {**query, "status": {"$in": ["confirmed", "completed"]}}},
                        {"$group": {"_id": None, "total": {"$sum": "$price"}}}]
    revenue = await db.bookings.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue[0]["total"] if revenue else 0
    
    client_query = {"master_id": user["user_id"]} if user["role"] == "master" else {}
    total_clients = await db.clients.count_documents(client_query)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pending = await db.bookings.count_documents({**query, "status": "pending"})
    confirmed = await db.bookings.count_documents({**query, "status": "confirmed"})
    completed = await db.bookings.count_documents({**query, "status": "completed"})
    cancelled = await db.bookings.count_documents({**query, "status": "cancelled"})
    today_count = await db.bookings.count_documents({**query, "date": today})
    
    return Stats(
        total_bookings=total, total_revenue=total_revenue, total_clients=total_clients,
        pending_bookings=pending, confirmed_bookings=confirmed,
        completed_bookings=completed, cancelled_bookings=cancelled, today_bookings=today_count
    )


@router.get("/admin/stats/monthly")
async def get_monthly_stats(year: int, master_id: Optional[str] = None, user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    elif master_id:
        query["master_id"] = master_id
    
    months = []
    for month in range(1, 13):
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1}-01-01"
        else:
            end = f"{year}-{month + 1:02d}-01"
        
        month_query = {**query, "date": {"$gte": start, "$lt": end}}
        
        bookings = await db.bookings.count_documents(month_query)
        revenue_pipeline = [{"$match": {**month_query, "status": {"$in": ["confirmed", "completed"]}}},
                            {"$group": {"_id": None, "total": {"$sum": "$price"}}}]
        revenue = await db.bookings.aggregate(revenue_pipeline).to_list(1)
        
        months.append({
            "month": month, "bookings": bookings,
            "revenue": revenue[0]["total"] if revenue else 0
        })
    
    return months


@router.get("/admin/stats/masters")
async def get_masters_stats(user: Dict = Depends(verify_admin)):
    masters = await db.masters.find({"is_active": True}, {"_id": 0, "password_hash": 0}).to_list(100)
    
    stats = []
    for master in masters:
        total = await db.bookings.count_documents({"master_id": master["id"]})
        revenue_pipeline = [
            {"$match": {"master_id": master["id"], "status": {"$in": ["confirmed", "completed"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$price"}}}
        ]
        revenue = await db.bookings.aggregate(revenue_pipeline).to_list(1)
        
        stats.append({
            "master": master,
            "total_bookings": total,
            "total_revenue": revenue[0]["total"] if revenue else 0
        })
    
    return stats


@router.delete("/admin/bookings/{booking_id}")
async def delete_booking(booking_id: str, user: Dict = Depends(verify_master_or_admin)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if user["role"] == "master" and booking.get("master_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.bookings.delete_one({"id": booking_id})
    return {"message": "Booking deleted"}


# ============ REMINDER SETTINGS ============

@router.get("/admin/reminder-settings", response_model=ReminderSettings)
async def get_reminder_settings(_: str = Depends(verify_token)):
    settings = await db.settings.find_one({"type": "reminders"}, {"_id": 0})
    if settings:
        return ReminderSettings(**settings)
    return ReminderSettings()

@router.put("/admin/reminder-settings", response_model=ReminderSettings)
async def update_reminder_settings(settings: ReminderSettings, _: str = Depends(verify_token)):
    await db.settings.update_one(
        {"type": "reminders"}, {"$set": {**settings.model_dump(), "type": "reminders"}}, upsert=True
    )
    return settings

@router.post("/admin/send-reminders")
async def trigger_reminders_manually(user: Dict = Depends(verify_admin)):
    await check_and_send_reminders()
    return {"success": True, "message": "Перевірку нагадувань виконано"}

@router.get("/admin/reminder-status")
async def get_reminder_status(user: Dict = Depends(verify_admin)):
    import pytz
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    now_utc = datetime.now(timezone.utc)
    now_ukraine = now_utc.astimezone(kyiv_tz)
    
    today_str = now_ukraine.strftime("%Y-%m-%d")
    tomorrow_str = (now_ukraine + timedelta(days=1)).strftime("%Y-%m-%d")
    
    today_bookings = await db.bookings.find(
        {"date": today_str, "status": {"$in": ["confirmed", "pending"]}}, {"_id": 0}
    ).to_list(100)
    
    tomorrow_bookings = await db.bookings.find(
        {"date": tomorrow_str, "status": {"$in": ["confirmed", "pending"]}}, {"_id": 0}
    ).to_list(100)
    
    reminder_settings = await db.settings.find_one({"type": "reminders"}, {"_id": 0})
    
    pending_reminders = []
    for b in today_bookings + tomorrow_bookings:
        if not b.get("reminder_sent"):
            pending_reminders.append({
                "booking_id": b["id"], "client_name": b["client_name"],
                "date": b["date"], "time": b["time"],
                "service_name": b.get("service_name", ""),
                "reminder_hours": b.get("reminder_hours", 2)
            })
    
    return {
        "current_time_utc": now_utc.isoformat(),
        "current_time_ukraine": now_ukraine.strftime("%Y-%m-%d %H:%M %Z"),
        "today_bookings": len(today_bookings),
        "tomorrow_bookings": len(tomorrow_bookings),
        "pending_reminders": pending_reminders,
        "reminder_settings": reminder_settings
    }
