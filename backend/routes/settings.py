"""Маршрути налаштувань сайту"""
from fastapi import APIRouter, Depends
from database import db
from models import SiteSettings
from auth import verify_token

router = APIRouter()


@router.get("/settings", response_model=SiteSettings)
async def get_site_settings():
    settings = await db.settings.find_one({"type": "site"}, {"_id": 0})
    if settings:
        return SiteSettings(**settings)
    return SiteSettings()

@router.put("/admin/settings", response_model=SiteSettings)
async def update_site_settings(settings: SiteSettings, _: str = Depends(verify_token)):
    await db.settings.update_one(
        {"type": "site"},
        {"$set": {**settings.model_dump(), "type": "site"}},
        upsert=True
    )
    return settings
