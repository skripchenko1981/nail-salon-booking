"""Pydantic моделі"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime, timezone
import uuid


# ============ MASTER MODELS ============

class Master(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password_hash: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_notifications_enabled: bool = False
    unread_bookings_count: int = 0

class MasterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_notifications_enabled: bool = False
    unread_bookings_count: int = 0

class MasterCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True

class MasterUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_notifications_enabled: Optional[bool] = None

class MasterPasswordUpdate(BaseModel):
    current_password: Optional[str] = None
    new_password: str

class MasterTelegramConfig(BaseModel):
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_notifications_enabled: bool = False

class MasterLogin(BaseModel):
    email: str
    password: str

class MasterLoginResponse(BaseModel):
    token: str
    master: MasterResponse

class MasterPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True


# ============ VACATION MODELS ============

class Vacation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    start_date: str
    end_date: str
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

class ServiceCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    master_id: Optional[str] = None
    position: int = 0
    is_default: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ServiceCategoryCreate(BaseModel):
    name: str
    master_id: Optional[str] = None

class ServiceCategoryUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None

class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    duration_minutes: int = 60
    price: int = 0
    is_active: bool = True
    category: Optional[str] = None
    category_id: Optional[str] = None
    master_id: Optional[str] = None

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = 60
    price: int = 0
    is_active: bool = True
    category: Optional[str] = None
    category_id: Optional[str] = None
    master_id: Optional[str] = None

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    master_id: Optional[str] = None


# ============ OTHER MODELS ============

class WorkSchedule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str = "admin"
    day_of_week: int
    start_time: str = "09:00"
    end_time: str = "18:00"
    is_working: bool = True
    break_start: Optional[str] = None
    break_end: Optional[str] = None

class WorkScheduleCreate(BaseModel):
    master_id: str = "admin"
    day_of_week: int
    start_time: str = "09:00"
    end_time: str = "18:00"
    is_working: bool = True
    break_start: Optional[str] = None
    break_end: Optional[str] = None

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    surname: Optional[str] = None
    phone: str
    email: Optional[str] = None
    master_id: Optional[str] = None
    notes: Optional[str] = None
    telegram_id: Optional[str] = None
    total_bookings: int = 0
    total_spent: int = 0
    last_visit: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ClientStats(BaseModel):
    total_clients: int = 0
    new_this_month: int = 0
    returning_clients: int = 0
    avg_visits: float = 0
    top_clients: List[dict] = []

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_id: str
    service_id: str
    service_name: Optional[str] = None
    client_name: str
    client_surname: Optional[str] = None
    client_phone: str
    client_email: Optional[str] = None
    date: str
    time: str
    duration_minutes: int = 60
    price: int = 0
    status: str = "pending"
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reminder_hours: int = 2
    reminder_sent: bool = False

class BookingCreate(BaseModel):
    master_id: str
    service_id: str
    client_name: str
    client_surname: Optional[str] = None
    client_phone: str
    client_email: Optional[str] = None
    date: str
    time: str
    notes: Optional[str] = None
    reminder_hours: int = 2

    @field_validator('client_phone')
    @classmethod
    def validate_phone(cls, v):
        from helpers import validate_ukrainian_phone
        return validate_ukrainian_phone(v)

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class BookingCancelRequest(BaseModel):
    cancellation_reason: Optional[str] = None

class ReminderSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reminder_hours: int = 2
    reminder_enabled: bool = True
    reminder_text: Optional[str] = None

class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    studio_name: str = "Soul Nail Studio"
    studio_description: str = ""
    studio_phone: str = ""
    studio_address: str = ""
    studio_instagram: str = ""
    studio_facebook: str = ""
    studio_email: str = ""
    working_hours: str = ""
    hero_title: str = ""
    hero_subtitle: str = ""
    hero_image: str = ""
    logo_url: str = ""
    primary_color: str = "#D4A5A5"
    secondary_color: str = "#F5E6E0"
    accent_color: str = "#9E829C"
    font_family: str = "Playfair Display"
    booking_confirmation_text: str = ""
    meta_title: str = ""
    meta_description: str = ""
    custom_css: str = ""

class GalleryImage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_url: Optional[str] = None
    file_key: Optional[str] = None
    thumb_key: Optional[str] = None
    master_id: Optional[str] = None
    master_name: Optional[str] = None
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class GalleryImageCreate(BaseModel):
    image_url: str
    description: Optional[str] = None


# ============ PROMO BLOCK MODELS ============

class PromoBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    button_text: Optional[str] = None
    button_link: Optional[str] = None
    is_active: bool = True
    position: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PromoBlockCreate(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    button_text: Optional[str] = None
    button_link: Optional[str] = None
    is_active: bool = True
    position: int = 0

class PromoBlockUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    button_text: Optional[str] = None
    button_link: Optional[str] = None
    is_active: Optional[bool] = None
    position: Optional[int] = None

class TimeSlot(BaseModel):
    time: str
    available: bool

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    admin: dict

class Stats(BaseModel):
    total_bookings: int = 0
    total_revenue: int = 0
    total_clients: int = 0
    pending_bookings: int = 0
    confirmed_bookings: int = 0
    completed_bookings: int = 0
    cancelled_bookings: int = 0
    today_bookings: int = 0
