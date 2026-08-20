"""Маршрути послуг та категорій"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from database import db
from models import Service, ServiceCreate, ServiceUpdate, ServiceCategory, ServiceCategoryCreate, ServiceCategoryUpdate
from auth import verify_master_or_admin
import uuid

router = APIRouter()


@router.get("/service-categories")
async def get_service_categories():
    categories = await db.service_categories.find({}, {"_id": 0}).sort("position", 1).to_list(100)
    return categories

@router.get("/service-categories/{master_id}")
async def get_master_categories(master_id: str):
    default_categories = await db.service_categories.find(
        {"$or": [{"is_default": True}, {"master_id": None}]}, {"_id": 0}
    ).sort("position", 1).to_list(100)
    master_categories = await db.service_categories.find(
        {"master_id": master_id}, {"_id": 0}
    ).sort("position", 1).to_list(100)
    
    all_categories = default_categories + master_categories
    seen_ids = set()
    unique = []
    for cat in all_categories:
        if cat["id"] not in seen_ids:
            seen_ids.add(cat["id"])
            unique.append(cat)
    return unique

@router.post("/service-categories")
async def create_category(category: ServiceCategoryCreate, user: Dict = Depends(verify_master_or_admin)):
    new_category = ServiceCategory(**category.model_dump())
    if user["role"] == "master":
        new_category.master_id = user["user_id"]
    
    existing = await db.service_categories.find_one({"name": new_category.name, "master_id": new_category.master_id})
    if existing:
        raise HTTPException(status_code=400, detail="Категорія з такою назвою вже існує")
    
    max_pos = await db.service_categories.find_one(sort=[("position", -1)])
    new_category.position = (max_pos.get("position", 0) + 1) if max_pos else 0
    
    await db.service_categories.insert_one(new_category.model_dump())
    return new_category

@router.put("/service-categories/{category_id}")
async def update_category(category_id: str, category: ServiceCategoryUpdate, user: Dict = Depends(verify_master_or_admin)):
    update_data = {k: v for k, v in category.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.service_categories.update_one({"id": category_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    
    updated = await db.service_categories.find_one({"id": category_id}, {"_id": 0})
    return updated

@router.delete("/service-categories/{category_id}")
async def delete_category(category_id: str, user: Dict = Depends(verify_master_or_admin)):
    category = await db.service_categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    if category.get("is_default"):
        raise HTTPException(status_code=400, detail="Не можна видалити стандартну категорію")
    
    await db.services.update_many({"category_id": category_id}, {"$unset": {"category_id": "", "category": ""}})
    await db.service_categories.delete_one({"id": category_id})
    return {"message": "Категорію видалено"}

@router.get("/services", response_model=List[Service])
async def get_services(master_id: Optional[str] = None):
    query = {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]}
    if master_id:
        query["master_id"] = master_id
    services = await db.services.find(query, {"_id": 0}).to_list(100)
    return services

@router.get("/services/grouped")
async def get_services_grouped(master_id: Optional[str] = None):
    query = {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]}
    if master_id:
        query["master_id"] = master_id
    
    services = await db.services.find(query, {"_id": 0}).to_list(200)
    
    grouped = {}
    for svc in services:
        cat = svc.get("category") or "other"
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(svc)
    
    default_labels = {"manicure": "Манікюр", "pedicure": "Педикюр", "podology": "Подологія"}
    categories = await db.service_categories.find({}, {"_id": 0}).sort("position", 1).to_list(100)
    
    # Впорядковані підписи лише для категорій, що мають послуги
    cat_labels = {}
    for key, label in default_labels.items():
        if key in grouped:
            cat_labels[key] = label
    for c in categories:
        key = c.get("key") or c.get("id")
        if key in grouped and key not in cat_labels:
            cat_labels[key] = c["name"]
        elif c.get("name") in grouped and c["name"] not in cat_labels:
            cat_labels[c["name"]] = c["name"]
    for key in grouped:
        if key not in cat_labels:
            cat_labels[key] = "Інші" if key == "other" else key
    
    return {"services": grouped, "categories": cat_labels}

@router.get("/masters/{master_id}/services", response_model=List[Service])
async def get_master_services(master_id: str):
    services = await db.services.find(
        {"master_id": master_id, "$or": [{"is_active": True}, {"is_active": {"$exists": False}}]}, {"_id": 0}
    ).to_list(100)
    return services

@router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, user: Dict = Depends(verify_master_or_admin)):
    new_service = Service(**service.model_dump())
    if user["role"] == "master" and not new_service.master_id:
        new_service.master_id = user["user_id"]
    await db.services.insert_one(new_service.model_dump())
    return new_service

@router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service: ServiceUpdate, user: Dict = Depends(verify_master_or_admin)):
    update_data = {k: v for k, v in service.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.services.update_one({"id": service_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    updated = await db.services.find_one({"id": service_id}, {"_id": 0})
    return Service(**updated)

@router.delete("/services/{service_id}")
async def delete_service(service_id: str, user: Dict = Depends(verify_master_or_admin)):
    service = await db.services.find_one({"id": service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await db.services.delete_one({"id": service_id})
    return {"message": "Service deleted successfully"}
