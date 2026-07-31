"""
Telegram Bot Webhook Handler
Обробляє команду /start та контакт для підписки на сповіщення
"""
import logging
import re
from fastapi import APIRouter, Request, HTTPException
from telegram_bot import telegram_bot
import os

logger = logging.getLogger(__name__)

telegram_router = APIRouter(prefix="/telegram", tags=["telegram"])

# MongoDB connection - use shared database
from database import db


def normalize_phone(phone: str) -> str:
    """Нормалізувати номер телефону для порівняння"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('380'):
        return '+' + digits
    if digits.startswith('80') and len(digits) == 12:
        return '+3' + digits
    if digits.startswith('0') and len(digits) == 10:
        return '+38' + digits
    if len(digits) == 9:
        return '+380' + digits
    return '+' + digits if not phone.startswith('+') else phone


async def link_client_by_phone(chat_id: str, phone: str) -> bool:
    """Зв'язати telegram_id з клієнтом по номеру телефону"""
    normalized = normalize_phone(phone)
    
    # Шукаємо клієнта по різних варіантах номера
    phone_variants = [normalized]
    digits = re.sub(r'\D', '', normalized)
    if digits.startswith('380'):
        phone_variants.append('+' + digits)
        phone_variants.append('0' + digits[3:])
        phone_variants.append(digits)
    
    updated = False
    for variant in phone_variants:
        result = await db.clients.update_many(
            {"phone": variant},
            {"$set": {"telegram_id": chat_id}}
        )
        if result.modified_count > 0:
            updated = True
            logger.info(f"Зв'язано telegram_id {chat_id} з клієнтом (телефон: {variant})")
    
    return updated


@telegram_router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Обробка webhook від Telegram
    """
    try:
        data = await request.json()
        logger.info(f"Отримано webhook: {data}")
        
        if "message" not in data:
            return {"status": "ok"}
            
        message = data["message"]
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")
        
        # Обробка контакту (коли клієнт ділиться номером телефону)
        if "contact" in message:
            contact = message["contact"]
            phone = contact.get("phone_number", "")
            first_name = contact.get("first_name", "")
            
            if phone:
                linked = await link_client_by_phone(chat_id, phone)
                
                if linked:
                    # Прибрати клавіатуру після успішного зв'язування
                    await telegram_bot.send_message(
                        chat_id,
                        f"""✅ <b>Готово, {first_name}!</b>

Ваш номер {phone} знайдено в базі. Тепер ви будете автоматично отримувати нагадування за 2 години до кожного вашого запису.

💅 Soul Nail Studio""",
                        reply_markup={"remove_keyboard": True}
                    )
                else:
                    await telegram_bot.send_message(
                        chat_id,
                        f"""Номер {phone} не знайдено в базі клієнтів.

Можливо, ви записувались з іншим номером. Запишіться через сайт — і після запису натисніть посилання на бот.

💅 Soul Nail Studio""",
                        reply_markup={"remove_keyboard": True}
                    )
            return {"status": "ok"}
        
        # Обробка команди /start
        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1:
                booking_id = parts[1]
                
                # Отримати інформацію про бронювання
                booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
                
                if booking:
                    # Зареєструвати підписку
                    success = await telegram_bot.register_client_subscription(
                        telegram_id=chat_id,
                        booking_id=booking_id,
                        client_phone=booking.get("client_phone", ""),
                        client_name=booking.get("client_name", "")
                    )
                    
                    # Зберегти telegram_id в записі клієнта
                    client_phone = booking.get("client_phone", "")
                    if client_phone and str(chat_id).lstrip("-").isdigit():
                        await link_client_by_phone(chat_id, client_phone)
                    
                    if success:
                        await telegram_bot.send_message(
                            chat_id,
                            f"""✅ <b>Вітаємо!</b>

Ви успішно підписалися на сповіщення!

💅 <b>{booking.get('service_name')}</b>
📅 Дата: {booking.get('date')}
🕐 Час: {booking.get('time')}

Тепер ви будете отримувати нагадування за 2 години до кожного запису автоматично.

💅 Soul Nail Studio"""
                        )
                    else:
                        await telegram_bot.send_message(
                            chat_id, 
                            "Помилка підписки. Спробуйте пізніше."
                        )
                else:
                    await telegram_bot.send_message(
                        chat_id,
                        "Запис не знайдено. Перевірте посилання."
                    )
            else:
                # /start без параметрів
                # Перевірити чи вже зв'язаний
                existing_client = await db.clients.find_one({"telegram_id": chat_id})
                if existing_client:
                    await telegram_bot.send_message(
                        chat_id,
                        f"""👋 <b>Вітаємо, {existing_client.get('name', '')}!</b>

Ви вже підключені! Нагадування про записи приходитимуть автоматично.

💅 Soul Nail Studio"""
                    )
                else:
                    # Запросити номер телефону через кнопку
                    await telegram_bot.send_message(
                        chat_id,
                        """👋 <b>Вітаємо в Soul Nail Studio!</b>

Щоб отримувати нагадування про ваші записи, натисніть кнопку нижче та поділіться номером телефону.

Це потрібно зробити <b>лише один раз</b> — далі нагадування приходитимуть автоматично.""",
                        reply_markup={
                            "keyboard": [[{
                                "text": "Поділитися номером телефону",
                                "request_contact": True
                            }]],
                            "resize_keyboard": True,
                            "one_time_keyboard": True
                        }
                    )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Помилка обробки webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@telegram_router.get("/set-webhook")
async def set_webhook(webhook_url: str):
    """Встановити webhook URL для бота"""
    if not telegram_bot.enabled:
        raise HTTPException(status_code=400, detail="Telegram bot не налаштовано")
    
    import aiohttp
    url = f"{telegram_bot.base_url}/setWebhook"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"url": webhook_url}) as response:
            result = await response.json()
            return result


@telegram_router.get("/webhook-info")
async def get_webhook_info():
    """Отримати інформацію про поточний webhook"""
    if not telegram_bot.enabled:
        raise HTTPException(status_code=400, detail="Telegram bot не налаштовано")
    
    import aiohttp
    url = f"{telegram_bot.base_url}/getWebhookInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            return result
