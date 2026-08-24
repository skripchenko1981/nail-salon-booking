"""Telegram сповіщення для індивідуальних ботів майстрів"""
import httpx
import html
import logging
import os
from database import db
from telegram_bot import telegram_bot

logger = logging.getLogger(__name__)


def _client_status_block(subscribed: bool, delivered: bool = None) -> str:
    block = "\n\n📲 Клієнт у Telegram: " + ("✅ підписаний" if subscribed else "❌ не підписаний")
    if delivered is not None:
        if delivered:
            block += "\n✉️ Сповіщення клієнту: ✅ надіслано"
        else:
            reason = "клієнт не підписаний" if not subscribed else "помилка відправки"
            block += f"\n✉️ Сповіщення клієнту: ❌ не надіслано ({reason})"
    return block


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
    esc = lambda v: html.escape(str(v)) if v else ""
    client_full_name = f"{esc(booking.get('client_name'))} {esc(booking.get('client_surname'))}".strip()
    message = f"""{header}

💇 Майстер: {esc(master_name)}
👤 Клієнт: {client_full_name}
📱 Телефон: {esc(booking.get('client_phone'))}"""

    if booking.get('client_email'):
        message += f"\n📧 Email: {esc(booking.get('client_email'))}"

    message += f"""
💅 Послуга: {esc(service_name)}
📅 Дата: {booking.get('date')}
🕐 Час: {booking.get('time')}

💰 Вартість: {booking.get('price', 0)} ₴"""
    return message


async def _dispatch_to_masters(booking: dict, message: str, admin_telegram_id: str = None):
    """Надіслати повідомлення майстру запису, головному майстру та адмін-боту"""
    master_id = booking.get("master_id")
    await send_master_telegram_notification(master_id, message)

    head = await get_head_master()
    if head and head["id"] != master_id:
        await send_master_telegram_notification(head["id"], message)

    if admin_telegram_id:
        await telegram_bot.send_message(admin_telegram_id, message)


async def notify_master_new_booking(booking: dict, service_name: str, master_name: str = "",
                                    admin_telegram_id: str = None):
    """Сповістити майстра, головного майстра та адміна про новий запис"""
    master_id = booking.get("master_id")

    await db.masters.update_one(
        {"id": master_id},
        {"$inc": {"unread_bookings_count": 1}}
    )

    message = _build_booking_message("🆕 <b>Новий запис!</b>", booking, service_name, master_name)

    if booking.get('notes'):
        message += f"\n📝 Примітка: {html.escape(str(booking.get('notes')))}"

    subscribed = await telegram_bot.get_client_telegram_id(booking.get("id")) is not None
    message += _client_status_block(subscribed)
    message += "\n\n⚠️ Потребує підтвердження!"

    await _dispatch_to_masters(booking, message, admin_telegram_id)


async def notify_master_booking_cancelled(booking: dict, reason: str = None, master_name: str = "",
                                          subscribed: bool = None, delivered: bool = None,
                                          admin_telegram_id: str = None):
    """Сповістити майстра, головного майстра та адміна про скасування запису"""
    service_name = booking.get("service_name", "")
    message = _build_booking_message("❌ <b>Запис скасовано</b>", booking, service_name, master_name)

    if reason:
        message += f"\n📝 Причина: {html.escape(str(reason))}"

    if subscribed is None:
        subscribed = await telegram_bot.get_client_telegram_id(booking.get("id")) is not None
    message += _client_status_block(subscribed, delivered)

    await _dispatch_to_masters(booking, message, admin_telegram_id)


async def notify_cancellation_flow(booking: dict, reason: str = None, master_name: str = "",
                                   admin_telegram_id: str = None):
    """Скасування: спершу сповістити клієнта, потім майстрів/адміна зі статусом доставки"""
    subscribed = await telegram_bot.get_client_telegram_id(booking.get("id")) is not None
    delivered = False
    if subscribed:
        delivered = await telegram_bot.send_booking_cancelled(
            booking["id"], booking.get("client_name", ""), booking.get("service_name", ""),
            booking.get("date", ""), booking.get("time", ""), reason
        )
    await notify_master_booking_cancelled(booking, reason, master_name, subscribed, delivered, admin_telegram_id)


async def notify_master_reminder_status(booking: dict, delivered: bool):
    """Сповістити майстра (та головного майстра) про статус нагадування клієнту"""
    master = await db.masters.find_one({"id": booking.get("master_id")}, {"_id": 0, "name": 1})
    master_name = master.get("name", "") if master else ""

    message = _build_booking_message(
        "⏰ <b>Нагадування клієнту про візит</b>",
        booking, booking.get("service_name", ""), master_name
    )
    if delivered:
        message += "\n\n✉️ Нагадування: ✅ клієнт отримав нагадування в Telegram"
    else:
        message += "\n\n✉️ Нагадування: ❌ не доставлено (клієнт не підписаний на Telegram)"

    await _dispatch_to_masters(booking, message, os.environ.get('ADMIN_TELEGRAM_ID'))
