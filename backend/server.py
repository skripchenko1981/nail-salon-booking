"""Soul Nail Studio — Backend Server"""
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

from database import client as db_client
from telegram_webhook import telegram_router
from scheduler import check_and_send_reminders

# Routes
from routes.services import router as services_router
from routes.bookings import router as bookings_router
from routes.masters import router as masters_router
from routes.admin import router as admin_router
from routes.clients import router as clients_router
from routes.gallery import router as gallery_router
from routes.promo import router as promo_router
from routes.settings import router as settings_router
from routes.vacations import router as vacations_router
from routes.schedule import router as schedule_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

# App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(services_router)
api_router.include_router(bookings_router)
api_router.include_router(masters_router)
api_router.include_router(admin_router)
api_router.include_router(clients_router)
api_router.include_router(gallery_router)
api_router.include_router(promo_router)
api_router.include_router(settings_router)
api_router.include_router(vacations_router)
api_router.include_router(schedule_router)

# Telegram webhook
api_router.include_router(telegram_router)

# Mount
app.include_router(api_router)

# Scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(
        check_and_send_reminders,
        IntervalTrigger(minutes=5),
        id='reminder_job',
        name='Check and send booking reminders',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Планувальник нагадувань запущено (кожні 5 хвилин)")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    db_client.close()
