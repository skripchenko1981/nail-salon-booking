import os
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)

class SMSService:
    """Сервіс для відправки SMS через Twilio"""
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.from_number = os.environ.get('TWILIO_PHONE_NUMBER', '')
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        
        if not self.enabled:
            logger.warning("SMS сервіс не налаштовано. Встановіть TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN та TWILIO_PHONE_NUMBER")
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """Відправка SMS через Twilio"""
        if not self.enabled:
            logger.warning(f"SMS сервіс вимкнено. Не можу відправити SMS на {to_number}")
            return False
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        data = {
            'From': self.from_number,
            'To': to_number,
            'Body': message
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                async with session.post(url, data=data, auth=auth) as response:
                    if response.status in [200, 201]:
                        logger.info(f"SMS відправлено на {to_number}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Помилка відправки SMS: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Помилка при відправці SMS: {e}")
            return False
    
    async def send_booking_confirmation(self, client_name: str, service_name: str, 
                                       date: str, time: str, phone: str) -> bool:
        """SMS підтвердження запису"""
        message = f"""Nail Studio

Вітаємо, {client_name}!

Ваш запис підтверджено:
Послуга: {service_name}
Дата: {date}
Час: {time}

Чекаємо на вас!
Для скасування: https://nailstudio.ua/my-bookings"""
        
        return await self.send_sms(phone, message)
    
    async def send_booking_reminder(self, client_name: str, service_name: str,
                                   date: str, time: str, phone: str, hours_before: int) -> bool:
        """SMS нагадування про візит"""
        message = f"""Nail Studio - Нагадування

{client_name}, нагадуємо про ваш візит!

Послуга: {service_name}
Дата: {date}
Час: {time}

До візиту залишилось {hours_before} год.

Чекаємо на вас!"""
        
        return await self.send_sms(phone, message)
    
    async def send_booking_cancelled(self, client_name: str, service_name: str,
                                    date: str, time: str, phone: str, 
                                    reason: Optional[str] = None) -> bool:
        """SMS про скасування запису"""
        message = f"""Nail Studio

{client_name}, ваш запис скасовано:

Послуга: {service_name}
Дата: {date}
Час: {time}"""
        
        if reason:
            message += f"\n\nПричина: {reason}"
        
        message += "\n\nВи можете записатися на інший час: https://nailstudio.ua"
        
        return await self.send_sms(phone, message)

# Глобальний екземпляр
sms_service = SMSService()
