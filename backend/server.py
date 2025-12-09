from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta, time
import jwt
import re
import phonenumbers
import hashlib
from telegram_bot import telegram_bot
from sms_service import sms_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

# ============ VALIDATORS ============

def validate_ukrainian_phone(phone: str) -> str:
    """Валідація українського телефону"""
    try:
        # Спроба парсити як міжнародний номер
        parsed = phonenumbers.parse(phone, "UA")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except:
        pass
    
    # Спроба парсити українські формати
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    patterns = [
        r'^\+380\d{9}$',  # +380XXXXXXXXX
        r'^380\d{9}$',     # 380XXXXXXXXX
        r'^0\d{9}$',       # 0XXXXXXXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone_clean):
            if phone_clean.startswith('+380'):
                return phone_clean
            elif phone_clean.startswith('380'):
                return '+' + phone_clean
            elif phone_clean.startswith('0'):
                return '+38' + phone_clean
    
    raise ValueError("Невірний формат телефону. Використовуйте формат: +380XXXXXXXXX")

# ============ MODELS ============

# ============ MASTER MODELS ============

class Master(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: str
    password_hash: str
    role: str = "master"  # "admin" or "master"
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MasterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: EmailStr
    phone: str
    role: str = "master"
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: str

class MasterCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        return validate_ukrainian_phone(v)

class MasterUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            return validate_ukrainian_phone(v)
        return v

class MasterPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class MasterLogin(BaseModel):
    email: EmailStr
    password: str

class MasterLoginResponse(BaseModel):
    token: str
    master: Dict

class MasterPublic(BaseModel):
    """Публічна інформація про майстра (без password_hash)"""
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: EmailStr
    phone: str
    role: str = "master"
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True

# ============ VACATION MODELS ============

class Vacation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VacationCreate(BaseModel):
    master_id: str
    start_date: str
    end_date: str
    reason: Optional[str] = None

class VacationUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None

# ============ SERVICE MODELS ============

class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    name: str
    description: str
    duration_minutes: int
    price: int
    image_url: Optional[str] = None
    active: bool = True

class ServiceCreate(BaseModel):
    master_id: str
    name: str
    description: str
    duration_minutes: int
    price: int
    image_url: Optional[str] = None

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    active: Optional[bool] = None

class WorkSchedule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    day_of_week: int
    start_time: str
    end_time: str
    is_working: bool = True

class WorkScheduleCreate(BaseModel):
    master_id: str
    day_of_week: int
    start_time: str
    end_time: str
    is_working: bool = True

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    name: str
    phone: str
    email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    total_bookings: int = 0
    completed_bookings: int = 0
    cancelled_bookings: int = 0
    total_spent: int = 0
    first_visit: Optional[str] = None
    last_visit: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ClientStats(BaseModel):
    total_clients: int
    new_clients_this_month: int
    returning_clients: int
    top_clients: List[Dict]

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    client_id: str
    client_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    service_id: str
    service_name: str
    date: str
    time: str
    duration_minutes: int
    price: int
    status: str = "pending"
    reminder_hours: int = 24
    reminder_sent: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

class BookingCreate(BaseModel):
    master_id: str
    client_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    service_id: str
    date: str
    time: str
    reminder_hours: int = 24
    notes: Optional[str] = None
    
    @field_validator('client_phone')
    @classmethod
    def validate_phone(cls, v):
        return validate_ukrainian_phone(v)

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    duration_minutes: Optional[int] = None

class BookingCancelRequest(BaseModel):
    cancellation_reason: Optional[str] = None

class ReminderSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "reminder_settings"
    default_hours_before: int = 24
    enabled: bool = True

class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "site_settings"
    site_name: str = "Nail Studio"
    site_description: str = "Професійний догляд за вашими руками та ногами"
    about_text: str = "Професійна студія манікюру та педикюру з командою досвідчених майстрів. Ми створюємо красу та піклуємося про здоров'я ваших нігтів."
    theme: str = "classic"  # classic, winter, spring, summer, autumn
    primary_color: str = "#D4A5A5"
    secondary_color: str = "#9E829C"
    accent_color: str = "#F3EBEB"
    phone: str = "+380 99 123 45 67"
    email: str = "info@beauty-alena.pp.ua"
    address: str = "Київ, вул. Прикладна, 1"
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    working_hours: str = "Пн-Сб: 9:00-18:00"
    # Контент головної сторінки
    hero_title: str = "Ваша краса - наша пристрасть"
    hero_subtitle: str = "Професійний манікюр та педикюр у затишній атмосфері"
    hero_button_text: str = "Записатися онлайн"
    services_title: str = "Наші послуги"
    services_subtitle: str = "Ми пропонуємо широкий спектр послуг для догляду за вашими руками та ногами"
    why_us_title: str = "Чому обирають нас?"
    why_us_reason_1: str = "Досвідчені майстри з сертифікатами"
    why_us_reason_2: str = "Якісні матеріали преміум-класу"
    why_us_reason_3: str = "Стерильність та безпека"

class GalleryImage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_url: str
    master_id: Optional[str] = None  # Якщо None - загальне фото
    master_name: Optional[str] = None
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class GalleryImageCreate(BaseModel):
    image_url: str
    master_id: Optional[str] = None
    master_name: Optional[str] = None
    description: Optional[str] = None

class TimeSlot(BaseModel):
    time: str
    available: bool

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    username: str

class Stats(BaseModel):
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: int
    today_bookings: int

# ============ PASSWORD HELPERS ============

def hash_password(password: str) -> str:
    """Хешувати пароль"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Перевірити пароль"""
    return hash_password(password) == password_hash

# ============ AUTH HELPERS ============

def create_token(username: str, role: str = "admin", user_id: Optional[str] = None) -> str:
    payload = {
        "sub": username,
        "role": role,
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "admin")
        user_id = payload.get("user_id")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role, "user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

def verify_admin(user: Dict = Depends(verify_token)) -> Dict:
    """Перевірити, що користувач є адміном"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def verify_master_or_admin(user: Dict = Depends(verify_token)) -> Dict:
    """Перевірити, що користувач є майстром або адміном"""
    if user["role"] not in ["admin", "master"]:
        raise HTTPException(status_code=403, detail="Master or admin access required")
    return user

# ============ CLIENT HELPERS ============

async def get_or_create_client(master_id: str, name: str, phone: str, 
                                email: Optional[str] = None, 
                                telegram_id: Optional[str] = None) -> str:
    """Отримати або створити клієнта для майстра"""
    phone_normalized = validate_ukrainian_phone(phone)
    
    # Шукати клієнта у цього майстра
    existing_client = await db.clients.find_one({
        "master_id": master_id,
        "phone": phone_normalized
    }, {"_id": 0})
    
    if existing_client:
        # Оновити дані якщо потрібно
        update_data = {}
        if email and not existing_client.get("email"):
            update_data["email"] = email
        if telegram_id and not existing_client.get("telegram_id"):
            update_data["telegram_id"] = telegram_id
        if name != existing_client.get("name"):
            update_data["name"] = name
            
        if update_data:
            await db.clients.update_one({
                "master_id": master_id,
                "phone": phone_normalized
            }, {"$set": update_data})
        
        return existing_client["id"]
    else:
        # Створити нового клієнта
        client = Client(
            master_id=master_id,
            name=name,
            phone=phone_normalized,
            email=email,
            telegram_id=telegram_id,
            first_visit=datetime.now(timezone.utc).date().isoformat()
        )
        await db.clients.insert_one(client.model_dump())
        return client.id

async def update_client_stats(client_id: str, booking_price: int, status: str):
    """Оновити статистику клієнта"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        return
    
    update_data = {}
    
    if status == "completed":
        update_data["completed_bookings"] = client.get("completed_bookings", 0) + 1
        update_data["total_spent"] = client.get("total_spent", 0) + booking_price
        update_data["last_visit"] = datetime.now(timezone.utc).date().isoformat()
    elif status == "cancelled":
        update_data["cancelled_bookings"] = client.get("cancelled_bookings", 0) + 1
    
    if update_data:
        await db.clients.update_one({"id": client_id}, {"$set": update_data})

# ============ SERVICE ROUTES ============

@api_router.get("/services", response_model=List[Service])
async def get_services(master_id: Optional[str] = None):
    """Отримати послуги (опціонально по майстру)"""
    query = {"active": True}
    if master_id:
        query["master_id"] = master_id
    services = await db.services.find(query, {"_id": 0}).to_list(100)
    return services

@api_router.get("/masters/{master_id}/services", response_model=List[Service])
async def get_master_services(master_id: str):
    """Отримати послуги конкретного майстра"""
    services = await db.services.find({"master_id": master_id, "active": True}, {"_id": 0}).to_list(100)
    return services

@api_router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, user: Dict = Depends(verify_master_or_admin)):
    """Створити послугу"""
    # Майстер може створювати тільки для себе
    if user["role"] == "master" and service.master_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only create services for yourself")
    
    service_obj = Service(**service.model_dump())
    doc = service_obj.model_dump()
    await db.services.insert_one(doc)
    return service_obj

@api_router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service: ServiceUpdate, user: Dict = Depends(verify_master_or_admin)):
    """Оновити послугу"""
    # Перевірити доступ
    existing_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if user["role"] == "master" and existing_service["master_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only update your own services")
    
    update_data = {k: v for k, v in service.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.services.update_one({"id": service_id}, {"$set": update_data})
    updated_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    return Service(**updated_service)

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Видалити послугу"""
    existing_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if user["role"] == "master" and existing_service["master_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own services")
    
    result = await db.services.update_one({"id": service_id}, {"$set": {"active": False}})
    return {"message": "Service deleted"}

# ============ SCHEDULE ROUTES ============

@api_router.get("/schedule", response_model=List[WorkSchedule])
async def get_schedule(master_id: str = "admin"):
    """Отримати розклад майстра"""
    
    schedules = await db.work_schedule.find({"master_id": master_id}, {"_id": 0}).to_list(7)
    existing_days = {s["day_of_week"] for s in schedules}
    for day in range(7):
        if day not in existing_days:
            default = WorkSchedule(
                master_id=master_id,
                day_of_week=day,
                start_time="09:00",
                end_time="18:00",
                is_working=True if day < 6 else False
            )
            schedules.append(default.model_dump())
    schedules.sort(key=lambda x: x["day_of_week"])
    return schedules

@api_router.post("/schedule", response_model=WorkSchedule)
async def create_or_update_schedule(schedule: WorkScheduleCreate, user: Dict = Depends(verify_master_or_admin)):
    """Створити або оновити розклад"""
    # Майстер може редагувати тільки свій розклад
    if user["role"] == "master" and schedule.master_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only edit your own schedule")
    
    existing = await db.work_schedule.find_one({
        "master_id": schedule.master_id, 
        "day_of_week": schedule.day_of_week
    }, {"_id": 0})
    
    if existing:
        await db.work_schedule.update_one(
            {"master_id": schedule.master_id, "day_of_week": schedule.day_of_week},
            {"$set": schedule.model_dump()}
        )
        updated = await db.work_schedule.find_one({
            "master_id": schedule.master_id,
            "day_of_week": schedule.day_of_week
        }, {"_id": 0})
        return WorkSchedule(**updated)
    else:
        schedule_obj = WorkSchedule(**schedule.model_dump())
        doc = schedule_obj.model_dump()
        await db.work_schedule.insert_one(doc)
        return schedule_obj

# ============ BOOKING ROUTES ============

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate, background_tasks: BackgroundTasks):
    service = await db.services.find_one({"id": booking.service_id, "active": True}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    existing_booking = await db.bookings.find_one({
        "date": booking.date,
        "time": booking.time,
        "status": {"$in": ["pending", "confirmed"]}
    })
    if existing_booking:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    
    # Створити або отримати клієнта
    client_id = await get_or_create_client(
        booking.master_id,
        booking.client_name,
        booking.client_phone,
        booking.client_email,
        booking.telegram_id
    )
    
    # Оновити загальну кількість записів
    await db.clients.update_one(
        {"id": client_id},
        {"$inc": {"total_bookings": 1}}
    )
    
    booking_obj = Booking(
        client_id=client_id,
        **booking.model_dump(),
        service_name=service["name"],
        duration_minutes=service["duration_minutes"],
        price=service["price"]
    )
    doc = booking_obj.model_dump()
    await db.bookings.insert_one(doc)
    
    # Відправити повідомлення клієнту (SMS або Telegram)
    if booking.telegram_id:
        # Якщо є Telegram ID - відправити в Telegram
        background_tasks.add_task(
            telegram_bot.send_booking_pending,
            booking.client_name,
            service["name"],
            booking.date,
            booking.time,
            booking.telegram_id
        )
    else:
        # Якщо немає Telegram ID - відправити SMS
        background_tasks.add_task(
            sms_service.send_booking_confirmation,
            booking.client_name,
            service["name"],
            booking.date,
            booking.time,
            booking.client_phone
        )
    
    # Відправити повідомлення адміну про новий запис
    admin_telegram_id = os.environ.get('ADMIN_TELEGRAM_ID')
    if admin_telegram_id:
        background_tasks.add_task(
            telegram_bot.notify_admin_new_booking,
            booking.client_name,
            booking.client_phone,
            service["name"],
            booking.date,
            booking.time,
            service["price"],
            admin_telegram_id
        )
    
    return booking_obj

@api_router.get("/bookings/client/{phone}", response_model=List[Booking])
async def get_client_bookings(phone: str):
    phone_normalized = validate_ukrainian_phone(phone)
    bookings = await db.bookings.find(
        {"client_phone": phone_normalized},
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    return bookings

@api_router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Booking(**booking)

@api_router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, cancel_req: BookingCancelRequest, 
                         background_tasks: BackgroundTasks):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
    
    result = await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "cancelled"}}
    )
    
    # Оновити статистику клієнта
    await update_client_stats(booking["client_id"], booking["price"], "cancelled")
    
    # Відправити повідомлення клієнту про скасування (SMS або Telegram)
    if booking.get("telegram_id"):
        background_tasks.add_task(
            telegram_bot.send_booking_cancelled,
            booking["client_name"],
            booking["service_name"],
            booking["date"],
            booking["time"],
            booking["telegram_id"],
            cancel_req.cancellation_reason
        )
    else:
        background_tasks.add_task(
            sms_service.send_booking_cancelled,
            booking["client_name"],
            booking["service_name"],
            booking["date"],
            booking["time"],
            booking["client_phone"],
            cancel_req.cancellation_reason
        )
    
    # Відправити повідомлення адміну про скасування
    admin_telegram_id = os.environ.get('ADMIN_TELEGRAM_ID')
    if admin_telegram_id:
        background_tasks.add_task(
            telegram_bot.notify_admin_booking_cancelled,
            booking["client_name"],
            booking["client_phone"],
            booking["service_name"],
            booking["date"],
            booking["time"],
            booking["price"],
            cancel_req.cancellation_reason,
            admin_telegram_id
        )
    
    return {"message": "Booking cancelled successfully"}

# ============ TIMESLOTS ============

@api_router.get("/timeslots/{date}", response_model=List[TimeSlot])
async def get_available_timeslots(date: str, service_id: str, master_id: str):
    """Отримати доступні слоти для майстра на певну дату"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        date_obj = datetime.fromisoformat(date)
        day_of_week = date_obj.weekday()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Перевірити чи дата не більше ніж 6 місяців вперед
    max_date = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=180)
    if date_obj > max_date:
        raise HTTPException(status_code=400, detail="Cannot book more than 6 months in advance")
    
    # Перевірити чи майстер у відпустці в цей день
    vacations = await db.vacations.find({
        "master_id": master_id,
        "start_date": {"$lte": date},
        "end_date": {"$gte": date}
    }).to_list(10)
    
    if vacations:
        return []  # Майстер у відпустці - немає доступних слотів
    
    # Отримати розклад майстра
    schedule = await db.work_schedule.find_one({
        "master_id": master_id,
        "day_of_week": day_of_week
    }, {"_id": 0})
    
    if not schedule or not schedule.get("is_working", False):
        return []
    
    start_time = schedule.get("start_time", "09:00")
    end_time = schedule.get("end_time", "18:00")
    
    # Отримати всі підтверджені та очікуючі записи майстра на цю дату
    bookings = await db.bookings.find(
        {
            "master_id": master_id,
            "date": date, 
            "status": {"$in": ["pending", "confirmed"]}
        },
        {"_id": 0}
    ).to_list(100)
    
    # Функція для перевірки, чи слот доступний
    def is_slot_available(slot_time_str: str, service_duration: int) -> bool:
        slot_start = datetime.strptime(slot_time_str, "%H:%M")
        slot_end = slot_start + timedelta(minutes=service_duration)
        
        for booking in bookings:
            booking_start = datetime.strptime(booking["time"], "%H:%M")
            booking_end = booking_start + timedelta(minutes=booking["duration_minutes"])
            
            # Перевірка перетину часових інтервалів
            if not (slot_end <= booking_start or slot_start >= booking_end):
                return False
        
        return True
    
    # Генерувати часові слоти
    time_slots = []
    current_time = datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
    
    while current_time < end_time_obj:
        time_str = current_time.strftime("%H:%M")
        
        # Перевірити, чи достатньо часу для цієї послуги до закриття
        slot_datetime = datetime.combine(date_obj, current_time)
        end_datetime = datetime.combine(date_obj, end_time_obj)
        time_until_close = (end_datetime - slot_datetime).total_seconds() / 60
        
        available = (time_until_close >= service["duration_minutes"] and 
                    is_slot_available(time_str, service["duration_minutes"]))
        
        time_slots.append(TimeSlot(
            time=time_str,
            available=available
        ))
        
        current_datetime = datetime.combine(datetime.today(), current_time)
        current_datetime += timedelta(minutes=30)
        current_time = current_datetime.time()
    
    return time_slots

# ============ MASTER ROUTES ============

@api_router.post("/masters/login", response_model=MasterLoginResponse)
async def master_login(credentials: MasterLogin):
    """Вхід для майстра"""
    master = await db.masters.find_one({"email": credentials.email}, {"_id": 0})
    
    if not master or not verify_password(credentials.password, master["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not master.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    token = create_token(master["email"], "master", master["id"])
    
    # Прибрати password_hash з відповіді
    master_data = {k: v for k, v in master.items() if k != "password_hash"}
    
    return MasterLoginResponse(token=token, master=master_data)

@api_router.get("/masters", response_model=List[MasterPublic])
async def get_masters():
    """Отримати список активних майстрів (публічний endpoint)"""
    masters = await db.masters.find({"is_active": True}, {"_id": 0, "password_hash": 0}).to_list(100)
    return masters

@api_router.post("/masters", response_model=MasterResponse)
async def create_master(master: MasterCreate, _: Dict = Depends(verify_admin)):
    """Створити нового майстра (тільки адмін)"""
    # Перевірити, чи email вже існує
    existing = await db.masters.find_one({"email": master.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    master_obj = Master(
        **master.model_dump(exclude={"password"}),
        password_hash=hash_password(master.password)
    )
    doc = master_obj.model_dump()
    await db.masters.insert_one(doc)
    
    # Створити графік роботи за замовчуванням (Пн-Пт 09:00-18:00)
    master_id = doc["id"]
    default_schedule = []
    for day in range(7):
        schedule_entry = {
            "id": str(uuid.uuid4()),
            "master_id": master_id,
            "day_of_week": day,
            "start_time": "09:00",
            "end_time": "18:00",
            "is_working": day < 5  # Працює Пн-Пт
        }
        default_schedule.append(schedule_entry)
    
    if default_schedule:
        await db.work_schedule.insert_many(default_schedule)
    
    # Прибрати password_hash з відповіді
    return MasterResponse(**{k: v for k, v in doc.items() if k != "password_hash"})

@api_router.get("/masters/{master_id}", response_model=MasterResponse)
async def get_master(master_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Отримати майстра по ID"""
    # Майстер може бачити тільки себе, адмін - всіх
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    master = await db.masters.find_one({"id": master_id}, {"_id": 0, "password_hash": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return MasterResponse(**master)

@api_router.get("/masters/me/profile", response_model=MasterResponse)
async def get_my_profile(user: Dict = Depends(verify_master_or_admin)):
    """Отримати свій профіль"""
    master = await db.masters.find_one({"id": user["user_id"]}, {"_id": 0, "password_hash": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return MasterResponse(**master)

@api_router.put("/masters/{master_id}", response_model=MasterResponse)
async def update_master(master_id: str, master: MasterUpdate, user: Dict = Depends(verify_master_or_admin)):
    """Оновити майстра"""
    # Майстер може редагувати тільки себе, адмін - всіх
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in master.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.masters.update_one({"id": master_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master not found")
    
    updated_master = await db.masters.find_one({"id": master_id}, {"_id": 0, "password_hash": 0})
    return MasterResponse(**updated_master)

@api_router.put("/masters/{master_id}/password")
async def update_master_password(master_id: str, password_update: MasterPasswordUpdate, 
                                 user: Dict = Depends(verify_master_or_admin)):
    """Оновити пароль майстра"""
    # Майстер може змінити тільки свій пароль
    if user["role"] == "master" and user["user_id"] != master_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    master = await db.masters.find_one({"id": master_id}, {"_id": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    
    # Перевірити поточний пароль (тільки для майстра, адмін може змінити без перевірки)
    if user["role"] == "master":
        if not verify_password(password_update.current_password, master["password_hash"]):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    new_password_hash = hash_password(password_update.new_password)
    await db.masters.update_one({"id": master_id}, {"$set": {"password_hash": new_password_hash}})
    
    return {"message": "Password updated successfully"}

@api_router.delete("/masters/{master_id}")
async def delete_master(master_id: str, _: Dict = Depends(verify_admin)):
    """Видалити майстра (деактивувати)"""
    result = await db.masters.update_one({"id": master_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master not found")
    return {"message": "Master deactivated"}

# ============ VACATION ROUTES ============

@api_router.get("/vacations", response_model=List[Vacation])
async def get_vacations(master_id: Optional[str] = None, user: Dict = Depends(verify_master_or_admin)):
    """Отримати відпустки (опціонально фільтр по майстру)"""
    query = {}
    
    # Майстер може бачити тільки свої відпустки
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    elif master_id:
        query["master_id"] = master_id
    
    vacations = await db.vacations.find(query, {"_id": 0}).sort("start_date", 1).to_list(100)
    return vacations

@api_router.post("/vacations", response_model=Vacation)
async def create_vacation(vacation: VacationCreate, user: Dict = Depends(verify_master_or_admin)):
    """Створити відпустку"""
    # Майстер може створювати тільки собі
    if user["role"] == "master" and vacation.master_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only create vacation for yourself")
    
    # Перевірити валідність дат
    try:
        start = datetime.fromisoformat(vacation.start_date)
        end = datetime.fromisoformat(vacation.end_date)
        if end < start:
            raise HTTPException(status_code=400, detail="End date must be after start date")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Перевірити перетин з існуючими відпустками
    existing = await db.vacations.find({
        "master_id": vacation.master_id,
        "$or": [
            {"start_date": {"$lte": vacation.end_date}, "end_date": {"$gte": vacation.start_date}}
        ]
    }).to_list(10)
    
    if existing:
        raise HTTPException(status_code=400, detail="Vacation period overlaps with existing vacation")
    
    vacation_obj = Vacation(**vacation.model_dump())
    doc = vacation_obj.model_dump()
    await db.vacations.insert_one(doc)
    return vacation_obj

@api_router.get("/vacations/{vacation_id}", response_model=Vacation)
async def get_vacation(vacation_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Отримати відпустку по ID"""
    vacation = await db.vacations.find_one({"id": vacation_id}, {"_id": 0})
    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation not found")
    
    # Майстер може бачити тільки свої відпустки
    if user["role"] == "master" and vacation["master_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Vacation(**vacation)

@api_router.put("/vacations/{vacation_id}", response_model=Vacation)
async def update_vacation(vacation_id: str, vacation: VacationUpdate, user: Dict = Depends(verify_master_or_admin)):
    """Оновити відпустку"""
    existing_vacation = await db.vacations.find_one({"id": vacation_id}, {"_id": 0})
    if not existing_vacation:
        raise HTTPException(status_code=404, detail="Vacation not found")
    
    # Майстер може редагувати тільки свої відпустки
    if user["role"] == "master" and existing_vacation["master_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only edit your own vacations")
    
    update_data = {k: v for k, v in vacation.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Перевірити валідність дат якщо вони оновлюються
    if "start_date" in update_data or "end_date" in update_data:
        start_date = update_data.get("start_date", existing_vacation["start_date"])
        end_date = update_data.get("end_date", existing_vacation["end_date"])
        
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            if end < start:
                raise HTTPException(status_code=400, detail="End date must be after start date")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
    result = await db.vacations.update_one({"id": vacation_id}, {"$set": update_data})
    updated_vacation = await db.vacations.find_one({"id": vacation_id}, {"_id": 0})
    return Vacation(**updated_vacation)

@api_router.delete("/vacations/{vacation_id}")
async def delete_vacation(vacation_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Видалити відпустку"""
    vacation = await db.vacations.find_one({"id": vacation_id}, {"_id": 0})
    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation not found")
    
    # Майстер може видаляти тільки свої відпустки
    if user["role"] == "master" and vacation["master_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own vacations")
    
    await db.vacations.delete_one({"id": vacation_id})
    return {"message": "Vacation deleted"}

# ============ ADMIN ROUTES ============

@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLogin):
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(credentials.username, "admin", "admin")
    return AdminLoginResponse(token=token, username=credentials.username)

@api_router.get("/admin/bookings", response_model=List[Booking])
async def get_admin_bookings(user: Dict = Depends(verify_master_or_admin)):
    """Отримати записи майстра (кожен майстер бачить тільки свої)"""
    # Кожен користувач (адмін або майстер) бачить тільки свої записи
    query = {"master_id": user["user_id"]}
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return bookings

@api_router.put("/admin/bookings/{booking_id}", response_model=Booking)
async def update_booking_status(booking_id: str, update: BookingUpdate, 
                                user: Dict = Depends(verify_master_or_admin), 
                                background_tasks: BackgroundTasks = None):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    old_status = booking["status"]
    new_status = update_data.get("status", old_status)
    
    result = await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
    # Оновити статистику клієнта
    if new_status != old_status:
        if new_status == "completed":
            await update_client_stats(booking["client_id"], booking["price"], "completed")
        
        # Відправити повідомлення клієнту (SMS або Telegram)
        if background_tasks:
            if new_status == "confirmed":
                if booking.get("telegram_id"):
                    background_tasks.add_task(
                        telegram_bot.send_booking_confirmed,
                        booking["client_name"],
                        booking["service_name"],
                        booking["date"],
                        booking["time"],
                        booking["telegram_id"]
                    )
                else:
                    background_tasks.add_task(
                        sms_service.send_booking_confirmation,
                        booking["client_name"],
                        booking["service_name"],
                        booking["date"],
                        booking["time"],
                        booking["client_phone"]
                    )
            elif new_status == "cancelled":
                if booking.get("telegram_id"):
                    background_tasks.add_task(
                        telegram_bot.send_booking_cancelled,
                        booking["client_name"],
                        booking["service_name"],
                        booking["date"],
                        booking["time"],
                        booking["telegram_id"],
                        update.cancellation_reason
                    )
                else:
                    background_tasks.add_task(
                        sms_service.send_booking_cancelled,
                        booking["client_name"],
                        booking["service_name"],
                        booking["date"],
                        booking["time"],
                        booking["client_phone"],
                        update.cancellation_reason
                    )
                
                # Сповістити адміна про скасування (тільки якщо скасував клієнт через адмін-панель)
                admin_telegram_id = os.environ.get('ADMIN_TELEGRAM_ID')
                if admin_telegram_id:
                    background_tasks.add_task(
                        telegram_bot.notify_admin_booking_cancelled,
                        booking["client_name"],
                        booking["client_phone"],
                        booking["service_name"],
                        booking["date"],
                        booking["time"],
                        booking["price"],
                        update.cancellation_reason,
                        admin_telegram_id
                    )
    
    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return Booking(**updated_booking)

@api_router.get("/admin/stats", response_model=Stats)
async def get_stats(user: Dict = Depends(verify_master_or_admin)):
    """Отримати статистику (кожен майстер бачить тільки свою)"""
    # Кожен користувач бачить тільки свою статистику
    query = {"master_id": user["user_id"]}
    
    all_bookings = await db.bookings.find(query, {"_id": 0}).to_list(10000)
    
    total = len(all_bookings)
    pending = len([b for b in all_bookings if b["status"] == "pending"])
    confirmed = len([b for b in all_bookings if b["status"] == "confirmed"])
    completed = len([b for b in all_bookings if b["status"] == "completed"])
    cancelled = len([b for b in all_bookings if b["status"] == "cancelled"])
    
    total_revenue = sum(b["price"] for b in all_bookings if b["status"] == "completed")
    
    today = datetime.now(timezone.utc).date().isoformat()
    today_bookings = len([b for b in all_bookings if b["date"] == today])
    
    return Stats(
        total_bookings=total,
        pending_bookings=pending,
        confirmed_bookings=confirmed,
        completed_bookings=completed,
        cancelled_bookings=cancelled,
        total_revenue=total_revenue,
        today_bookings=today_bookings
    )

# ============ CLIENT ROUTES ============

@api_router.get("/admin/clients", response_model=List[Client])
async def get_all_clients(user: Dict = Depends(verify_master_or_admin)):
    """Отримати клієнтів (кожен майстер бачить тільки своїх)"""
    # Кожен користувач бачить тільки своїх клієнтів
    query = {"master_id": user["user_id"]}
    
    clients = await db.clients.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return clients

@api_router.get("/admin/clients/stats", response_model=ClientStats)
async def get_client_stats(user: Dict = Depends(verify_master_or_admin)):
    """Отримати статистику клієнтів (кожен майстер бачить тільки своїх)"""
    # Кожен користувач бачить тільки своїх клієнтів
    query = {"master_id": user["user_id"]}
    all_clients = await db.clients.find(query, {"_id": 0}).to_list(10000)
    
    total_clients = len(all_clients)
    
    # Нові клієнти цього місяця
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    new_this_month = len([c for c in all_clients 
                          if c.get("created_at", "").startswith(current_month)])
    
    # Постійні клієнти (більше 1 візиту)
    returning = len([c for c in all_clients if c.get("total_bookings", 0) > 1])
    
    # Топ клієнти за витратами
    top_clients = sorted(all_clients, key=lambda x: x.get("total_spent", 0), reverse=True)[:10]
    top_clients_data = [
        {
            "name": c["name"],
            "phone": c["phone"],
            "total_spent": c.get("total_spent", 0),
            "total_bookings": c.get("total_bookings", 0),
            "completed_bookings": c.get("completed_bookings", 0)
        }
        for c in top_clients
    ]
    
    return ClientStats(
        total_clients=total_clients,
        new_clients_this_month=new_this_month,
        returning_clients=returning,
        top_clients=top_clients_data
    )

@api_router.get("/admin/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Отримати клієнта (кожен майстер бачить тільки своїх)"""
    client = await db.clients.find_one({
        "id": client_id,
        "master_id": user["user_id"]
    }, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**client)

@api_router.get("/admin/clients/{client_id}/bookings", response_model=List[Booking])
async def get_client_bookings_admin(client_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Отримати записи клієнта (кожен майстер бачить тільки своїх клієнтів)"""
    # Перевірити, що клієнт належить цьому майстру
    client = await db.clients.find_one({
        "id": client_id,
        "master_id": user["user_id"]
    }, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    bookings = await db.bookings.find(
        {
            "client_id": client_id,
            "master_id": user["user_id"]
        },
        {"_id": 0}
    ).sort("date", -1).to_list(100)
    return bookings

# ============ REMINDER SETTINGS ============

@api_router.get("/admin/reminder-settings", response_model=ReminderSettings)
async def get_reminder_settings(_: str = Depends(verify_token)):
    settings = await db.reminder_settings.find_one({"id": "reminder_settings"}, {"_id": 0})
    if not settings:
        default_settings = ReminderSettings()
        await db.reminder_settings.insert_one(default_settings.model_dump())
        return default_settings
    return ReminderSettings(**settings)

@api_router.put("/admin/reminder-settings", response_model=ReminderSettings)
async def update_reminder_settings(settings: ReminderSettings, _: str = Depends(verify_token)):
    await db.reminder_settings.update_one(
        {"id": "reminder_settings"},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return settings

# ============ SITE SETTINGS ============

@api_router.get("/settings", response_model=SiteSettings)
async def get_site_settings():
    """Публічні налаштування сайту"""
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    if not settings:
        default_settings = SiteSettings()
        await db.site_settings.insert_one(default_settings.model_dump())
        return default_settings
    return SiteSettings(**settings)

@api_router.put("/admin/settings", response_model=SiteSettings)
async def update_site_settings(settings: SiteSettings, _: str = Depends(verify_token)):
    """Оновлення налаштувань сайту (тільки адмін)"""
    await db.site_settings.update_one(
        {"id": "site_settings"},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return settings

# ============ GALLERY ============

@api_router.get("/gallery", response_model=List[GalleryImage])
async def get_gallery_images():
    """Отримати всі активні фото з галереї (публічний доступ)"""
    images = await db.gallery.find({"is_active": True}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return images

@api_router.get("/admin/gallery", response_model=List[GalleryImage])
async def get_all_gallery_images(user: Dict = Depends(verify_master_or_admin)):
    """Отримати всі фото з галереї для адміна/майстра"""
    images = await db.gallery.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return images

@api_router.post("/admin/gallery", response_model=GalleryImage)
async def create_gallery_image(image_data: GalleryImageCreate, user: Dict = Depends(verify_master_or_admin)):
    """Додати фото в галерею"""
    image = GalleryImage(**image_data.model_dump())
    await db.gallery.insert_one(image.model_dump())
    return image

@api_router.delete("/admin/gallery/{image_id}")
async def delete_gallery_image(image_id: str, user: Dict = Depends(verify_master_or_admin)):
    """Видалити фото з галереї"""
    result = await db.gallery.delete_one({"id": image_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"success": True, "message": "Image deleted"}

@api_router.put("/admin/gallery/{image_id}")
async def update_gallery_image(image_id: str, is_active: bool, user: Dict = Depends(verify_master_or_admin)):
    """Активувати/деактивувати фото"""
    result = await db.gallery.update_one(
        {"id": image_id},
        {"$set": {"is_active": is_active}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"success": True, "message": "Image updated"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
