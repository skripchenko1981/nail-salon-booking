"""
Telegram Bot Webhook Handler
Обробляє команду /start з deep linking для підписки на сповіщення
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from telegram_bot import telegram_bot
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

telegram_router = APIRouter(prefix="/api/telegram", tags=["telegram"])

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]


@telegram_router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Обробка webhook від Telegram
    """
    try:
        data = await request.json()
        logger.info(f"Отримано webhook: {data}")
        
        # Обробка команди /start
        if "message" in data:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            
            if text.startswith("/start"):
                # Отримати параметр (booking_id)
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
                        
                        # Зберегти telegram_id в записі клієнта для майбутніх нагадувань
                        # chat_id з Telegram API завжди числовий
                        client_phone = booking.get("client_phone", "")
                        if client_phone and str(chat_id).lstrip("-").isdigit():
                            await db.clients.update_many(
                                {"phone": client_phone},
                                {"$set": {"telegram_id": chat_id}}
                            )
                            logger.info(f"Збережено telegram_id {chat_id} для клієнта з телефоном {client_phone}")
                        
                        if success:
                            # Відправити привітальне повідомлення
                            welcome_text = f"""✅ <b>Вітаємо!</b>

Ви успішно підписалися на сповіщення!

💅 <b>{booking.get('service_name')}</b>
📅 Дата: {booking.get('date')}
🕐 Час: {booking.get('time')}

Тепер ви будете отримувати:
• Нагадування за 2 години до запису
• Підтвердження та зміни статусу
• <b>Автоматичні нагадування для всіх майбутніх записів</b>

Дякуємо за довіру! 💅 Soul Nail Studio"""
                            await telegram_bot.send_message(chat_id, welcome_text)
                        else:
                            await telegram_bot.send_message(
                                chat_id, 
                                "❌ Помилка підписки. Спробуйте пізніше."
                            )
                    else:
                        await telegram_bot.send_message(
                            chat_id,
                            "❌ Запис не знайдено. Перевірте посилання."
                        )
                else:
                    # /start без параметрів — зберегти chat_id для можливого зв'язування
                    # Перевірити чи цей telegram_id вже є в клієнтах
                    existing_client = await db.clients.find_one({"telegram_id": chat_id})
                    if existing_client:
                        await telegram_bot.send_message(
                            chat_id,
                            f"""👋 <b>Вітаємо, {existing_client.get('name', '')}!</b>

Ви вже підписані на сповіщення. Ми будемо надсилати нагадування про всі ваші записи автоматично.

💅 Soul Nail Studio"""
                        )
                    else:
                        welcome = """👋 <b>Вітаємо в Soul Nail Studio!</b>

Цей бот надсилає нагадування про ваші записи.

Щоб підписатися, використовуйте посилання, яке ви отримали після бронювання. Після першої підписки всі майбутні записи отримуватимуть нагадування автоматично.

💅 Soul Nail Studio"""
                        await telegram_bot.send_message(chat_id, welcome)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Помилка обробки webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@telegram_router.get("/set-webhook")
async def set_webhook(webhook_url: str):
    """
    Встановити webhook URL для бота
    Викликається один раз при налаштуванні
    """
    if not telegram_bot.enabled:
        raise HTTPException(status_code=400, detail="Telegram bot не налаштовано")
    
    url = f"{telegram_bot.base_url}/setWebhook"
    data = {"url": webhook_url}
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            result = await response.json()
            return result


@telegram_router.get("/webhook-info")
async def get_webhook_info():
    """
    Отримати інформацію про поточний webhook
    """
    if not telegram_bot.enabled:
        raise HTTPException(status_code=400, detail="Telegram bot не налаштовано")
    
    url = f"{telegram_bot.base_url}/getWebhookInfo"
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            return result
