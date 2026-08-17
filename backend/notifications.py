"""Telegram сповіщення для індивідуальних ботів майстрів"""
import httpx
import logging
from database import db

logger = logging.getLogger(__name__)


async def send_master_telegram_notification(master_id: str, message: str) -> bool:
    """Відправити повідомлення через індивідуальний Telegram бот майстра"""
    master = await db.masters.find_one({"id": master_id}, {"_id": 0})
    if not master:
        return False

    bot_token = master.get("telegram_bot_token")
    chat_id = master.get("telegram_chat_id")
    enabled = master.get("telegram_notifications_enabled", False)

    if not bot_token or not chat_id or not enabled:
        logger.warning(f"Telegram not configured for master {master_id}")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }, timeout=10.0)

            if response.status_code == 200:
                logger.info(f"Telegram notification sent to master {master_id}")
                return True
            else:
                logger.error(f"Telegram error for master {master_id}: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending master notification: {e}")
        return False


async def notify_master_new_booking(booking: dict, service_name: str, master_name: str = ""):
    """Сповістити майстра про новий запис"""
    master_id = booking.get("master_id")

    await db.masters.update_one(
        {"id": master_id},
        {"$inc": {"unread_bookings_count": 1}}
    )

    message = f"""🆕 <b>Новий запис!</b>

💇 Майстер: {master_name}
👤 Клієнт: {booking.get('client_name')} {booking.get('client_surname', '')}
📱 Телефон: {booking.get('client_phone')}
💅 Послуга: {service_name}
📅 Дата: {booking.get('date')}
🕐 Час: {booking.get('time')}

💰 Вартість: {booking.get('price', 0)} ₴"""

    if booking.get('notes'):
        message += f"\n📝 Примітка: {booking.get('notes')}"

    await send_master_telegram_notification(master_id, message)
