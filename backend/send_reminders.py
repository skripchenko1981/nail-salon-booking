#!/usr/bin/env python3
"""
Скрипт для автоматичної відправки нагадувань про записи

Запускається через cron кожні 15 хвилин
"""

import asyncio
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Додати шлях до backend
sys.path.insert(0, str(Path(__file__).parent))

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from telegram_bot import telegram_bot
from sms_service import sms_service

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/reminders.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_reminders():
    """Головна функція для відправки нагадувань"""
    try:
        # Підключення до MongoDB
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        logger.info("Початок перевірки нагадувань...")
        
        now = datetime.now(timezone.utc)
        today = now.date()
        current_time = now.time()
        
        # Знайти всі підтверджені записи, для яких ще не відправлено нагадування
        bookings = await db.bookings.find({
            "status": {"$in": ["confirmed", "pending"]},
            "reminder_sent": {"$ne": True}
        }).to_list(1000)
        
        logger.info(f"Знайдено {len(bookings)} записів для перевірки")
        
        sent_count = 0
        
        for booking in bookings:
            try:
                # Розрахувати час запису
                booking_date = datetime.fromisoformat(booking['date']).date()
                booking_time = datetime.strptime(booking['time'], "%H:%M").time()
                booking_datetime = datetime.combine(booking_date, booking_time)
                
                # Розрахувати час відправки нагадування
                reminder_hours = booking.get('reminder_hours', 24)
                reminder_datetime = booking_datetime - timedelta(hours=reminder_hours)
                
                # Перевірити чи настав час відправки
                # Відправляємо якщо час нагадування <= поточного часу < час запису
                if reminder_datetime <= now < booking_datetime:
                    logger.info(f"Відправка нагадування для запису {booking['id']}")
                    
                    # Спробувати відправити через Telegram якщо є ID
                    sent_telegram = False
                    if booking.get('telegram_id'):
                        sent_telegram = await telegram_bot.send_booking_reminder(
                            booking['client_name'],
                            booking['service_name'],
                            booking['date'],
                            booking['time'],
                            booking['telegram_id'],
                            reminder_hours
                        )
                    
                    # Якщо Telegram не вдалося або немає ID - відправити SMS
                    sent_sms = False
                    if not sent_telegram:
                        sent_sms = await sms_service.send_booking_reminder(
                            booking['client_name'],
                            booking['service_name'],
                            booking['date'],
                            booking['time'],
                            booking['client_phone'],
                            reminder_hours
                        )
                    
                    # Якщо хоча б одне повідомлення відправлено - позначити
                    if sent_telegram or sent_sms:
                        await db.bookings.update_one(
                            {"id": booking['id']},
                            {"$set": {"reminder_sent": True}}
                        )
                        sent_count += 1
                        logger.info(f"✓ Нагадування відправлено для {booking['client_name']}")
                    else:
                        logger.warning(f"✗ Не вдалося відправити нагадування для {booking['client_name']}")
                        
            except Exception as e:
                logger.error(f"Помилка обробки запису {booking.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Завершено. Відправлено {sent_count} нагадувань")
        
        # Закрити з'єднання
        client.close()
        
    except Exception as e:
        logger.error(f"Критична помилка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(send_reminders())
