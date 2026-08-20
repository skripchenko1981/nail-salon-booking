"""Маршрути записів та таймслотів"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict
from database import db
from models import Booking, BookingCreate, BookingUpdate, BookingCancelRequest, TimeSlot
from auth import verify_master_or_admin
from helpers import get_or_create_client
from notifications import notify_master_new_booking, notify_cancellation_flow
from telegram_bot import telegram_bot
from datetime import datetime, timedelta
import os
import uuid

router = APIRouter()


async def is_slot_available(master_id: str, date: str, time: str, duration_minutes: int, exclude_booking_id: str = None) -> bool:
    """Перевірити доступність слоту з урахуванням тривалості"""
    new_start = datetime.strptime(time, "%H:%M")
    new_end = new_start + timedelta(minutes=duration_minutes)
    
    query = {"master_id": master_id, "date": date, "status": {"$in": ["pending", "confirmed"]}}
    if exclude_booking_id:
        query["id"] = {"$ne": exclude_booking_id}
    
    existing_bookings = await db.bookings.find(query, {"_id": 0}).to_list(100)
    
    for existing in existing_bookings:
        existing_start = datetime.strptime(existing["time"], "%H:%M")
        existing_duration = existing.get("duration_minutes", 60)
        existing_end = existing_start + timedelta(minutes=existing_duration)
        
        if not (new_end <= existing_start or new_start >= existing_end):
            return False
    
    return True


@router.post("/bookings")
async def create_booking(booking: BookingCreate, background_tasks: BackgroundTasks):
    service = await db.services.find_one({"id": booking.service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    duration = service.get("duration_minutes", 60)
    
    available = await is_slot_available(booking.master_id, booking.date, booking.time, duration)
    if not available:
        raise HTTPException(status_code=400, detail="Цей час вже зайнятий. Оберіть інший слот.")
    
    booking_obj = Booking(
        master_id=booking.master_id,
        service_id=booking.service_id,
        service_name=service["name"],
        client_name=booking.client_name,
        client_surname=booking.client_surname,
        client_phone=booking.client_phone,
        client_email=booking.client_email,
        date=booking.date,
        time=booking.time,
        duration_minutes=duration,
        price=service.get("price", 0),
        status="pending",
        notes=booking.notes,
        reminder_hours=booking.reminder_hours,
        reminder_sent=False
    )
    
    doc = booking_obj.model_dump()
    
    background_tasks.add_task(
        get_or_create_client,
        booking.master_id, booking.client_name, booking.client_phone,
        booking.client_email, booking.client_surname
    )
    
    await db.bookings.insert_one(doc)
    
    telegram_link = None
    if telegram_bot.enabled:
        telegram_link = telegram_bot.generate_subscription_link(booking_obj.id)
    
    # Отримати ім'я майстра
    master = await db.masters.find_one({"id": booking.master_id}, {"_id": 0, "name": 1})
    master_name = master.get("name", "Невідомий") if master else "Невідомий"
    
    admin_telegram_id = os.environ.get('ADMIN_TELEGRAM_ID')
    if admin_telegram_id:
        background_tasks.add_task(
            telegram_bot.notify_admin_new_booking,
            booking.client_name, booking.client_phone,
            service["name"], booking.date, booking.time,
            service["price"], admin_telegram_id, master_name
        )
    
    background_tasks.add_task(notify_master_new_booking, doc, service["name"], master_name)
    
    response = booking_obj.model_dump()
    response["telegram_subscription_link"] = telegram_link
    return response


@router.get("/bookings/client/{phone}", response_model=List[Booking])
async def get_client_bookings(phone: str):
    bookings = await db.bookings.find({"client_phone": phone}, {"_id": 0}).sort("date", -1).to_list(100)
    return bookings

@router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, cancel_req: BookingCancelRequest,
                         background_tasks: BackgroundTasks):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "cancelled", "cancellation_reason": cancel_req.cancellation_reason}}
    )
    
    master = await db.masters.find_one({"id": booking.get("master_id")}, {"_id": 0, "name": 1})
    cancel_master_name = master.get("name", "") if master else ""

    background_tasks.add_task(
        notify_cancellation_flow,
        booking, cancel_req.cancellation_reason, cancel_master_name
    )

    admin_telegram_id = os.environ.get('ADMIN_TELEGRAM_ID')
    if admin_telegram_id:
        background_tasks.add_task(
            telegram_bot.notify_admin_booking_cancelled,
            booking["client_name"], booking["client_phone"],
            booking["service_name"], booking["date"],
            booking["time"], booking["price"],
            cancel_req.cancellation_reason, admin_telegram_id,
            cancel_master_name
        )
    
    return {"message": "Booking cancelled successfully"}


@router.get("/timeslots/{date}", response_model=List[TimeSlot])
async def get_available_timeslots(date: str, service_id: str, master_id: str):
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    duration = service.get("duration_minutes", 60)
    
    from datetime import datetime as dt
    try:
        date_obj = dt.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    day_of_week = date_obj.weekday()
    
    # Перевірка відпустки
    vacations = await db.vacations.find({"master_id": master_id}, {"_id": 0}).to_list(100)
    for vacation in vacations:
        if vacation["start_date"] <= date <= vacation["end_date"]:
            return []
    
    schedule = await db.work_schedule.find_one(
        {"master_id": master_id, "day_of_week": day_of_week}, {"_id": 0}
    )
    if not schedule:
        schedule = await db.work_schedule.find_one(
            {"master_id": "admin", "day_of_week": day_of_week}, {"_id": 0}
        )
    
    if not schedule or not schedule.get("is_working", True):
        return []
    
    start_time = dt.strptime(schedule.get("start_time", "09:00"), "%H:%M")
    end_time = dt.strptime(schedule.get("end_time", "18:00"), "%H:%M")
    break_start = dt.strptime(schedule["break_start"], "%H:%M") if schedule.get("break_start") else None
    break_end = dt.strptime(schedule["break_end"], "%H:%M") if schedule.get("break_end") else None
    
    existing = await db.bookings.find(
        {"master_id": master_id, "date": date, "status": {"$in": ["pending", "confirmed"]}},
        {"_id": 0}
    ).to_list(100)
    
    slots = []
    current = start_time
    while current + timedelta(minutes=duration) <= end_time:
        if break_start and break_end:
            slot_end = current + timedelta(minutes=duration)
            if not (slot_end <= break_start or current >= break_end):
                current += timedelta(minutes=30)
                continue
        
        available = True
        new_end = current + timedelta(minutes=duration)
        for booking in existing:
            b_start = dt.strptime(booking["time"], "%H:%M")
            b_dur = booking.get("duration_minutes", 60)
            b_end = b_start + timedelta(minutes=b_dur)
            if not (new_end <= b_start or current >= b_end):
                available = False
                break
        
        slots.append(TimeSlot(time=current.strftime("%H:%M"), available=available))
        current += timedelta(minutes=30)
    
    return slots
