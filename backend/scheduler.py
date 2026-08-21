"""APScheduler — нагадування клієнтам"""
import logging
from datetime import datetime, timezone, timedelta
from database import db
from telegram_bot import telegram_bot
from notifications import notify_master_reminder_status

logger = logging.getLogger(__name__)


async def check_and_send_reminders():
    """Перевірка та відправка нагадувань кожні 5 хвилин"""
    try:
        logger.info("Запуск перевірки нагадувань...")

        import pytz
        kyiv_tz = pytz.timezone('Europe/Kyiv')
        now_utc = datetime.now(timezone.utc)
        now_ukraine = now_utc.astimezone(kyiv_tz)

        logger.info(f"Поточний час UTC: {now_utc.strftime('%Y-%m-%d %H:%M')}, Україна (Kyiv): {now_ukraine.strftime('%Y-%m-%d %H:%M %Z')}")

        today_str = now_ukraine.strftime("%Y-%m-%d")
        bookings = await db.bookings.find({
            "status": {"$in": ["confirmed", "pending"]},
            "reminder_sent": {"$ne": True},
            "date": {"$gte": today_str}
        }).to_list(1000)

        if bookings:
            logger.info(f"Знайдено {len(bookings)} записів для перевірки нагадувань")

        sent_count = 0
        skipped_no_sub = 0

        for booking in bookings:
            try:
                booking_date_str = booking['date']
                if 'T' in booking_date_str:
                    booking_date = datetime.fromisoformat(booking_date_str.replace('Z', '+00:00')).date()
                else:
                    booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()

                booking_time_obj = datetime.strptime(booking['time'], "%H:%M").time()
                booking_datetime_local = datetime.combine(booking_date, booking_time_obj)

                reminder_hours = booking.get('reminder_hours', 2)
                reminder_datetime_local = booking_datetime_local - timedelta(hours=reminder_hours)

                now_local = now_ukraine.replace(tzinfo=None)

                if reminder_datetime_local <= now_local < booking_datetime_local:
                    logger.info(f"Час відправки нагадування для запису {booking['id']} ({booking['client_name']} на {booking['date']} {booking['time']})")

                    sent_telegram = await telegram_bot.send_booking_reminder(
                        booking['id'],
                        booking['client_name'],
                        booking.get('service_name', 'Послуга'),
                        booking['date'],
                        booking['time'],
                        reminder_hours
                    )

                    if sent_telegram:
                        await db.bookings.update_one(
                            {"id": booking['id']},
                            {"$set": {"reminder_sent": True, "reminder_sent_at": datetime.now(timezone.utc).isoformat()}}
                        )
                        sent_count += 1
                        logger.info(f"✓ Нагадування відправлено для {booking['client_name']}")
                        await notify_master_reminder_status(booking, delivered=True)
                    else:
                        skipped_no_sub += 1
                        if not booking.get("reminder_master_notified"):
                            await db.bookings.update_one(
                                {"id": booking['id']},
                                {"$set": {"reminder_master_notified": True}}
                            )
                            await notify_master_reminder_status(booking, delivered=False)

            except Exception as e:
                logger.error(f"Помилка обробки запису {booking.get('id', 'unknown')}: {e}")
                continue

        if sent_count > 0:
            logger.info(f"Відправлено {sent_count} нагадувань")
        if skipped_no_sub > 0:
            logger.info(f"Пропущено {skipped_no_sub} записів (клієнт не підписаний на Telegram)")

    except Exception as e:
        logger.error(f"Помилка перевірки нагадувань: {e}")
