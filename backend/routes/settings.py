"""Маршрути налаштувань сайту"""
from fastapi import APIRouter, Depends
from database import db
from auth import verify_token

router = APIRouter()

DEFAULT_SETTINGS = {
    "site_name": "Soul Nail Studio",
    "site_description": "",
    "about_text": "",
    "theme": "classic",
    "primary_color": "#D4A5A5",
    "secondary_color": "#9E829C",
    "accent_color": "#F3EBEB",
    "phone": "",
    "email": "",
    "address": "",
    "instagram": "",
    "facebook": "",
    "working_hours": "",
    "hero_title": "",
    "hero_subtitle": "",
    "hero_button_text": "",
    "services_title": "",
    "services_subtitle": "",
    "why_us_title": "",
    "why_us_reason_1": "",
    "why_us_reason_2": "",
    "why_us_reason_3": "",
}


@router.get("/settings")
async def get_site_settings():
    settings = await db.settings.find_one({"type": "site"}, {"_id": 0}) or {}
    settings.pop("type", None)
    return {**DEFAULT_SETTINGS, **settings}

@router.put("/admin/settings")
async def update_site_settings(settings: dict, _: str = Depends(verify_token)):
    settings.pop("_id", None)
    settings.pop("type", None)
    await db.settings.update_one(
        {"type": "site"},
        {"$set": {**settings, "type": "site"}},
        upsert=True
    )
    return {**DEFAULT_SETTINGS, **settings}
