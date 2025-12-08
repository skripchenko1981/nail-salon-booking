import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import aiohttp
import json

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Сервіс для роботи з Google Calendar API"""
    
    def __init__(self):
        self.api_base = "https://www.googleapis.com/calendar/v3"
        
    async def create_event(
        self, 
        access_token: str,
        calendar_id: str,
        service_name: str,
        client_name: str,
        client_phone: str,
        date: str,
        time: str,
        duration_minutes: int,
        status: str = "pending",
        notes: Optional[str] = None
    ) -> Optional[str]:
        """Створити подію в Google Calendar"""
        
        if not access_token or not calendar_id:
            logger.warning("Google Calendar не налаштовано для цього майстра")
            return None
        
        # Формування часу початку та кінця
        start_datetime = datetime.fromisoformat(f"{date}T{time}:00")
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Колір події залежно від статусу
        color_id = self._get_color_by_status(status)
        
        # Формування події
        event = {
            "summary": f"[{service_name}] - {client_name}",
            "description": self._format_description(client_name, client_phone, service_name, notes),
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Europe/Kiev"
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Europe/Kiev"
            },
            "colorId": color_id,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60}
                ]
            }
        }
        
        try:
            url = f"{self.api_base}/calendars/{calendar_id}/events"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=event, headers=headers) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        event_id = result.get("id")
                        logger.info(f"Google Calendar подія створена: {event_id}")
                        return event_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Помилка створення події Google Calendar: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Помилка при створенні події Google Calendar: {e}")
            return None
    
    async def update_event(
        self,
        access_token: str,
        calendar_id: str,
        event_id: str,
        service_name: str,
        client_name: str,
        client_phone: str,
        date: str,
        time: str,
        duration_minutes: int,
        status: str = "confirmed",
        notes: Optional[str] = None
    ) -> bool:
        """Оновити подію в Google Calendar"""
        
        if not access_token or not calendar_id or not event_id:
            logger.warning("Немає даних для оновлення події")
            return False
        
        # Формування часу
        start_datetime = datetime.fromisoformat(f"{date}T{time}:00")
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Колір події
        color_id = self._get_color_by_status(status)
        
        # Оновлені дані
        event = {
            "summary": f"[{service_name}] - {client_name}",
            "description": self._format_description(client_name, client_phone, service_name, notes),
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Europe/Kiev"
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Europe/Kiev"
            },
            "colorId": color_id
        }
        
        try:
            url = f"{self.api_base}/calendars/{calendar_id}/events/{event_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=event, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Google Calendar подія оновлена: {event_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Помилка оновлення події: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Помилка при оновленні події: {e}")
            return False
    
    async def delete_event(
        self,
        access_token: str,
        calendar_id: str,
        event_id: str
    ) -> bool:
        """Видалити подію з Google Calendar"""
        
        if not access_token or not calendar_id or not event_id:
            logger.warning("Немає даних для видалення події")
            return False
        
        try:
            url = f"{self.api_base}/calendars/{calendar_id}/events/{event_id}"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status == 204:
                        logger.info(f"Google Calendar подія видалена: {event_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Помилка видалення події: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Помилка при видаленні події: {e}")
            return False
    
    def _get_color_by_status(self, status: str) -> str:
        """Отримати колір події по статусу"""
        color_map = {
            "pending": "5",      # Жовтий
            "confirmed": "10",   # Зелений
            "completed": "9",    # Синій
            "cancelled": "11"    # Червоний
        }
        return color_map.get(status, "1")  # За замовчуванням блакитний
    
    def _format_description(
        self,
        client_name: str,
        client_phone: str,
        service_name: str,
        notes: Optional[str]
    ) -> str:
        """Форматувати опис події"""
        description = f"""Клієнт: {client_name}
Телефон: {client_phone}
Послуга: {service_name}"""
        
        if notes:
            description += f"\n\nПримітки: {notes}"
        
        return description

# Глобальний екземпляр
google_calendar_service = GoogleCalendarService()
