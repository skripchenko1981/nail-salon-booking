from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta, time
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

# ============ MODELS ============

class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    duration_minutes: int
    price: int
    image_url: Optional[str] = None
    active: bool = True

class ServiceCreate(BaseModel):
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
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # "09:00"
    end_time: str  # "18:00"
    is_working: bool = True

class WorkScheduleCreate(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    is_working: bool = True

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    service_id: str
    service_name: str
    date: str  # "2025-01-15"
    time: str  # "10:00"
    duration_minutes: int
    price: int
    status: str = "pending"  # pending, confirmed, cancelled, completed
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

class BookingCreate(BaseModel):
    client_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    service_id: str
    date: str
    time: str
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

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

# ============ AUTH HELPERS ============

def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ SERVICE ROUTES ============

@api_router.get("/services", response_model=List[Service])
async def get_services():
    services = await db.services.find({"active": True}, {"_id": 0}).to_list(100)
    return services

@api_router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, _: str = Depends(verify_token)):
    service_obj = Service(**service.model_dump())
    doc = service_obj.model_dump()
    await db.services.insert_one(doc)
    return service_obj

@api_router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service: ServiceUpdate, _: str = Depends(verify_token)):
    update_data = {k: v for k, v in service.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.services.update_one({"id": service_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    updated_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    return Service(**updated_service)

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, _: str = Depends(verify_token)):
    result = await db.services.update_one({"id": service_id}, {"$set": {"active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted"}

# ============ WORK SCHEDULE ROUTES ============

@api_router.get("/schedule", response_model=List[WorkSchedule])
async def get_schedule():
    schedules = await db.work_schedule.find({}, {"_id": 0}).to_list(7)
    # Ensure all 7 days are present
    existing_days = {s["day_of_week"] for s in schedules}
    for day in range(7):
        if day not in existing_days:
            default = WorkSchedule(
                day_of_week=day,
                start_time="09:00",
                end_time="18:00",
                is_working=True if day < 6 else False  # Sunday off by default
            )
            schedules.append(default.model_dump())
    schedules.sort(key=lambda x: x["day_of_week"])
    return schedules

@api_router.post("/schedule", response_model=WorkSchedule)
async def create_or_update_schedule(schedule: WorkScheduleCreate, _: str = Depends(verify_token)):
    # Check if schedule for this day exists
    existing = await db.work_schedule.find_one({"day_of_week": schedule.day_of_week}, {"_id": 0})
    if existing:
        # Update existing
        await db.work_schedule.update_one(
            {"day_of_week": schedule.day_of_week},
            {"$set": schedule.model_dump()}
        )
        updated = await db.work_schedule.find_one({"day_of_week": schedule.day_of_week}, {"_id": 0})
        return WorkSchedule(**updated)
    else:
        # Create new
        schedule_obj = WorkSchedule(**schedule.model_dump())
        doc = schedule_obj.model_dump()
        await db.work_schedule.insert_one(doc)
        return schedule_obj

# ============ BOOKING ROUTES ============

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    # Get service details
    service = await db.services.find_one({"id": booking.service_id, "active": True}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check if time slot is available
    existing_booking = await db.bookings.find_one({
        "date": booking.date,
        "time": booking.time,
        "status": {"$in": ["pending", "confirmed"]}
    })
    if existing_booking:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    
    booking_obj = Booking(
        **booking.model_dump(),
        service_name=service["name"],
        duration_minutes=service["duration_minutes"],
        price=service["price"]
    )
    doc = booking_obj.model_dump()
    await db.bookings.insert_one(doc)
    return booking_obj

@api_router.get("/bookings/client/{phone}", response_model=List[Booking])
async def get_client_bookings(phone: str):
    bookings = await db.bookings.find(
        {"client_phone": phone},
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
async def cancel_booking(booking_id: str):
    result = await db.bookings.update_one(
        {"id": booking_id, "status": {"$in": ["pending", "confirmed"]}},
        {"$set": {"status": "cancelled"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found or already cancelled")
    return {"message": "Booking cancelled successfully"}

# ============ TIMESLOTS ============

@api_router.get("/timeslots/{date}", response_model=List[TimeSlot])
async def get_available_timeslots(date: str, service_id: str):
    # Get service duration
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Parse date and get day of week
    try:
        date_obj = datetime.fromisoformat(date)
        day_of_week = date_obj.weekday()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get work schedule for this day
    schedule = await db.work_schedule.find_one({"day_of_week": day_of_week}, {"_id": 0})
    if not schedule or not schedule.get("is_working", False):
        return []  # Day off
    
    start_time = schedule.get("start_time", "09:00")
    end_time = schedule.get("end_time", "18:00")
    
    # Generate time slots
    time_slots = []
    current_time = datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()
    
    # Get existing bookings for this date
    bookings = await db.bookings.find(
        {"date": date, "status": {"$in": ["pending", "confirmed"]}},
        {"_id": 0}
    ).to_list(100)
    booked_times = {b["time"] for b in bookings}
    
    while current_time < end_time_obj:
        time_str = current_time.strftime("%H:%M")
        time_slots.append(TimeSlot(
            time=time_str,
            available=time_str not in booked_times
        ))
        # Increment by 30 minutes
        current_datetime = datetime.combine(datetime.today(), current_time)
        current_datetime += timedelta(minutes=30)
        current_time = current_datetime.time()
    
    return time_slots

# ============ ADMIN ROUTES ============

@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLogin):
    # Simple hardcoded admin for MVP (in production, use database)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(credentials.username)
    return AdminLoginResponse(token=token, username=credentials.username)

@api_router.get("/admin/bookings", response_model=List[Booking])
async def get_all_bookings(_: str = Depends(verify_token)):
    bookings = await db.bookings.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    return bookings

@api_router.put("/admin/bookings/{booking_id}", response_model=Booking)
async def update_booking_status(booking_id: str, update: BookingUpdate, _: str = Depends(verify_token)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return Booking(**updated_booking)

@api_router.get("/admin/stats", response_model=Stats)
async def get_stats(_: str = Depends(verify_token)):
    all_bookings = await db.bookings.find({}, {"_id": 0}).to_list(10000)
    
    total = len(all_bookings)
    pending = len([b for b in all_bookings if b["status"] == "pending"])
    confirmed = len([b for b in all_bookings if b["status"] == "confirmed"])
    completed = len([b for b in all_bookings if b["status"] == "completed"])
    cancelled = len([b for b in all_bookings if b["status"] == "cancelled"])
    
    # Calculate total revenue (completed bookings only)
    total_revenue = sum(b["price"] for b in all_bookings if b["status"] == "completed")
    
    # Today's bookings
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()