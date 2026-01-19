#!/usr/bin/env python3
"""
Скрипт для автоматичної відправки нагадувань про записи

Запускається автоматично через APScheduler кожні 5 хвилин
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

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_reminders():
    """Головна функція для відправки нагадувань"""
    try:
        # Підключення до MongoDB
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        logger.info("Початок перевірки нагадувань...")
        
        now = datetime.now(timezone.utc)
        
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
                booking_date_str = booking['date']
                # Підтримка різних форматів дати
                if 'T' in booking_date_str:
                    booking_date = datetime.fromisoformat(booking_date_str.replace('Z', '+00:00')).date()
                else:
                    booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
                    
                booking_time = datetime.strptime(booking['time'], "%H:%M").time()
                booking_datetime = datetime.combine(booking_date, booking_time)
                # Додати timezone info для коректного порівняння
                booking_datetime = booking_datetime.replace(tzinfo=timezone.utc)
                
                # Розрахувати час відправки нагадування (за замовчуванням 2 години до)
                reminder_hours = booking.get('reminder_hours', 2)
                reminder_datetime = booking_datetime - timedelta(hours=reminder_hours)
                
                # Перевірити чи настав час відправки
                # Відправляємо якщо час нагадування <= поточного часу < час запису
                if reminder_datetime <= now < booking_datetime:
                    logger.info(f"Час відправки нагадування для запису {booking['id']} (за {reminder_hours} год до {booking['date']} {booking['time']})")
                    
                    # Спробувати відправити через Telegram
                    sent_telegram = await telegram_bot.send_booking_reminder(
                        booking['id'],
                        booking['client_name'],
                        booking['service_name'],
                        booking['date'],
                        booking['time'],
                        reminder_hours
                    )
                    
                    if sent_telegram:
                        # Позначити що нагадування відправлено
                        await db.bookings.update_one(
                            {"id": booking['id']},
                            {"$set": {"reminder_sent": True, "reminder_sent_at": datetime.now(timezone.utc).isoformat()}}
                        )
                        sent_count += 1
                        logger.info(f"✓ Нагадування відправлено для {booking['client_name']} (запис {booking['id']})")
                    else:
                        logger.warning(f"✗ Клієнт {booking['client_name']} не підписаний на Telegram сповіщення")
                        
            except Exception as e:
                logger.error(f"Помилка обробки запису {booking.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Завершено перевірку нагадувань. Відправлено {sent_count} нагадувань")
        
        # Закрити з'єднання
        client.close()
        
        return sent_count
        
    except Exception as e:
        logger.error(f"Критична помилка: {e}")
        return 0

if __name__ == "__main__":
    asyncio.run(send_reminders())
