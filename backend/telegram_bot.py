import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = bool(self.token)
        self.bot_username = None
        
        # MongoDB connection для збереження підписок
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[os.environ.get('DB_NAME', 'test_database')]
        
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Відправка повідомлення в Telegram"""
        if not self.enabled:
            logger.warning("Telegram bot не налаштовано. Пропускаємо відправку повідомлення.")
            return False
            
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"Повідомлення відправлено до {chat_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Помилка відправки: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Помилка при відправці повідомлення: {e}")
            return False
    
    async def send_booking_pending(self, client_name: str, service_name: str, 
                                   date: str, time: str, telegram_id: str) -> bool:
        """Повідомлення про очікування підтвердження"""
        text = f"""🔔 <b>Новий запис очікує підтвердження</b>

👤 Клієнт: {client_name}
💅 Послуга: {service_name}
📅 Дата: {date}
🕐 Час: {time}

⏳ Очікуйте підтвердження від майстра."""
        
        return await self.send_message(telegram_id, text)
    
    async def send_booking_confirmed(self, client_name: str, service_name: str, 
                                     date: str, time: str, telegram_id: str) -> bool:
        """Повідомлення про підтвердження запису"""
        text = f"""✅ <b>Ваш запис підтверджено!</b>

👤 Клієнт: {client_name}
💅 Послуга: {service_name}
📅 Дата: {date}
🕐 Час: {time}

📍 Чекаємо на вас!
Якщо у вас виникли питання, зв'яжіться з нами."""
        
        return await self.send_message(telegram_id, text)
    
    async def send_booking_cancelled(self, client_name: str, service_name: str, 
                                     date: str, time: str, telegram_id: str, 
                                     reason: Optional[str] = None) -> bool:
        """Повідомлення про скасування запису"""
        text = f"""❌ <b>Запис скасовано</b>

👤 Клієнт: {client_name}
💅 Послуга: {service_name}
📅 Дата: {date}
🕐 Час: {time}"""
        
        if reason:
            text += f"\n\n📝 Причина: {reason}"
        
        text += "\n\nВи можете записатися на інший час через наш сайт."
        
        return await self.send_message(telegram_id, text)
    
    async def send_booking_reminder(self, client_name: str, service_name: str, 
                                    date: str, time: str, telegram_id: str, 
                                    hours_before: int) -> bool:
        """Нагадування про запис"""
        text = f"""⏰ <b>Нагадування про запис</b>

👤 {client_name}, нагадуємо про ваш візит!

💅 Послуга: {service_name}
📅 Дата: {date}
🕐 Час: {time}

⏱ До візиту залишилось {hours_before} год.

📍 Чекаємо на вас!"""
        
        return await self.send_message(telegram_id, text)
    
    # ============ ADMIN NOTIFICATIONS ============
    
    async def notify_admin_new_booking(self, client_name: str, client_phone: str,
                                      service_name: str, date: str, time: str,
                                      price: int, admin_telegram_id: str) -> bool:
        """Повідомлення адміну про новий запис"""
        text = f"""🔔 <b>НОВИЙ ЗАПИС!</b>

👤 Клієнт: {client_name}
📱 Телефон: {client_phone}

💅 Послуга: {service_name}
📅 Дата: {date}
🕐 Час: {time}
💰 Вартість: {price} ₴

⚠️ Потребує підтвердження!"""
        
        return await self.send_message(admin_telegram_id, text)
    
    async def notify_admin_booking_cancelled(self, client_name: str, client_phone: str,
                                            service_name: str, date: str, time: str,
                                            price: int, reason: Optional[str],
                                            admin_telegram_id: str) -> bool:
        """Повідомлення адміну про скасування запису"""
        text = f"""❌ <b>СКАСОВАНО ЗАПИС</b>

👤 Клієнт: {client_name}
📱 Телефон: {client_phone}

💅 Послуга: {service_name}
📅 Дата: {date}
🕐 Час: {time}
💰 Втрачено: {price} ₴"""
        
        if reason:
            text += f"\n\n📝 Причина: {reason}"
        
        return await self.send_message(admin_telegram_id, text)
    
    async def notify_admin_daily_summary(self, today_bookings: int, pending_count: int,
                                        confirmed_count: int, total_revenue: int,
                                        admin_telegram_id: str) -> bool:
        """Щоденна статистика для адміна"""
        text = f"""📊 <b>СТАТИСТИКА ЗА ДЕНЬ</b>

📅 Дата: {datetime.now().strftime('%d.%m.%Y')}

📋 Всього записів: {today_bookings}
⏳ Очікують: {pending_count}
✅ Підтверджено: {confirmed_count}

💰 Очікувана виручка: {total_revenue} ₴

Гарного дня! 💅"""
        
        return await self.send_message(admin_telegram_id, text)
    
    async def notify_admin_upcoming_bookings(self, bookings: list, admin_telegram_id: str) -> bool:
        """Нагадування адміну про майбутні записи"""
        if not bookings:
            return False
        
        text = "⏰ <b>ЗАПИСИ НА СЬОГОДНІ</b>\n\n"
        
        for booking in bookings:
            text += f"""🕐 {booking['time']} - {booking['client_name']}
💅 {booking['service_name']}
📱 {booking['client_phone']}

"""
        
        text += "Гарної роботи! 💅"
        
        return await self.send_message(admin_telegram_id, text)

# Глобальний екземпляр бота
telegram_bot = TelegramBot()