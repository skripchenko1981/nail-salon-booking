"""Telegram сповіщення для індивідуальних ботів майстрів"""
import httpx
import logging
from database import db

logger = logging.getLogger(__name__)


async def get_head_master() -> dict | None:
    """Отримати головного майстра. Якщо не позначено — призначити першого створеного."""
    head = await db.masters.find_one({"is_head": True}, {"_id": 0})
    if head:
        return head
    masters = await db.masters.find({}, {"_id": 0}).sort("created_at", 1).to_list(1)
    if masters:
        head = masters[0]
        await db.masters.update_one({"id": head["id"]}, {"$set": {"is_head": True}})
        head["is_head"] = True
        logger.info(f"Головним майстром автоматично призначено: {head.get('name')}")
        return head
    return None


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


def _build_booking_message(header: str, booking: dict, service_name: str, master_name: str) -> str:
    client_full_name = f"{booking.get('client_name', '')} {booking.get('client_surname', '') or ''}".strip()
    message = f"""{header}

💇 Майстер: {master_name}
👤 Клієнт: {client_full_name}
📱 Телефон: {booking.get('client_phone')}"""

    if booking.get('client_email'):
        message += f"\n📧 Email: {booking.get('client_email')}"

    message += f"""
💅 Послуга: {service_name}
📅 Дата: {booking.get('date')}
🕐 Час: {booking.get('time')}

💰 Вартість: {booking.get('price', 0)} ₴"""
    return message


async def _dispatch_to_masters(booking: dict, message: str):
    """Надіслати повідомлення майстру запису та головному майстру (якщо це інший майстер)"""
    master_id = booking.get("master_id")
    await send_master_telegram_notification(master_id, message)

    head = await get_head_master()
    if head and head["id"] != master_id:
        await send_master_telegram_notification(head["id"], message)


async def notify_master_new_booking(booking: dict, service_name: str, master_name: str = ""):
    """Сповістити майстра (та головного майстра) про новий запис"""
    master_id = booking.get("master_id")

    await db.masters.update_one(
        {"id": master_id},
        {"$inc": {"unread_bookings_count": 1}}
    )

    message = _build_booking_message("🆕 <b>Новий запис!</b>", booking, service_name, master_name)

    if booking.get('notes'):
        message += f"\n📝 Примітка: {booking.get('notes')}"

    await _dispatch_to_masters(booking, message)


async def notify_master_booking_cancelled(booking: dict, reason: str = None, master_name: str = ""):
    """Сповістити майстра (та головного майстра) про скасування запису"""
    service_name = booking.get("service_name", "")
    message = _build_booking_message("❌ <b>Запис скасовано</b>", booking, service_name, master_name)

    if reason:
        message += f"\n📝 Причина: {reason}"

    await _dispatch_to_masters(booking, message)
