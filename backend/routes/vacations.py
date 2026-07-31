"""Маршрути відпусток"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from database import db
from models import Vacation, VacationCreate, VacationUpdate
from auth import verify_master_or_admin
import uuid
from datetime import datetime, timezone

router = APIRouter()


@router.get("/vacations", response_model=List[Vacation])
async def get_vacations(master_id: Optional[str] = None, user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    elif master_id:
        query["master_id"] = master_id
    
    vacations = await db.vacations.find(query, {"_id": 0}).sort("start_date", 1).to_list(100)
    return vacations

@router.post("/vacations", response_model=Vacation)
async def create_vacation(vacation: VacationCreate, user: Dict = Depends(verify_master_or_admin)):
    if user["role"] == "master":
        vacation.master_id = user["user_id"]
    
    new_vacation = Vacation(**vacation.model_dump())
    await db.vacations.insert_one(new_vacation.model_dump())
    
    affected = await db.bookings.count_documents({
        "master_id": vacation.master_id,
        "date": {"$gte": vacation.start_date, "$lte": vacation.end_date},
        "status": {"$in": ["pending", "confirmed"]}
    })
    
    if affected > 0:
        await db.bookings.update_many(
            {"master_id": vacation.master_id,
             "date": {"$gte": vacation.start_date, "$lte": vacation.end_date},
             "status": {"$in": ["pending", "confirmed"]}},
            {"$set": {"status": "cancelled", "cancellation_reason": "Відпустка майстра"}}
        )
    
    return new_vacation

@router.get("/vacations/{vacation_id}", response_model=Vacation)
async def get_vacation(vacation_id: str, user: Dict = Depends(verify_master_or_admin)):
    query = {"id": vacation_id}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    
    vacation = await db.vacations.find_one(query, {"_id": 0})
    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation not found")
    return vacation

@router.put("/vacations/{vacation_id}", response_model=Vacation)
async def update_vacation(vacation_id: str, vacation: VacationUpdate, user: Dict = Depends(verify_master_or_admin)):
    query = {"id": vacation_id}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    
    existing = await db.vacations.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Vacation not found")
    
    update_data = {k: v for k, v in vacation.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.vacations.update_one({"id": vacation_id}, {"$set": update_data})
    updated = await db.vacations.find_one({"id": vacation_id}, {"_id": 0})
    return Vacation(**updated)

@router.delete("/vacations/{vacation_id}")
async def delete_vacation(vacation_id: str, user: Dict = Depends(verify_master_or_admin)):
    query = {"id": vacation_id}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    
    vacation = await db.vacations.find_one(query)
    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation not found")
    
    await db.vacations.delete_one({"id": vacation_id})
    return {"message": "Vacation deleted"}
