"""Маршрути робочого розкладу"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from database import db
from models import WorkSchedule, WorkScheduleCreate
from auth import verify_master_or_admin

router = APIRouter()


@router.get("/schedule", response_model=List[WorkSchedule])
async def get_schedule(master_id: str = "admin"):
    schedules = await db.work_schedule.find({"master_id": master_id}, {"_id": 0}).to_list(7)
    
    if not schedules:
        schedules = await db.work_schedule.find({"master_id": "admin"}, {"_id": 0}).to_list(7)
    
    if not schedules:
        default = []
        for day in range(7):
            s = WorkSchedule(
                master_id=master_id,
                day_of_week=day,
                is_working=day < 5,
                start_time="09:00",
                end_time="18:00"
            )
            default.append(s.model_dump())
        await db.work_schedule.insert_many(default)
        schedules = default
    
    return schedules

@router.post("/schedule", response_model=WorkSchedule)
async def create_or_update_schedule(schedule: WorkScheduleCreate, user: Dict = Depends(verify_master_or_admin)):
    master_id = schedule.master_id
    if user["role"] == "master":
        master_id = user["user_id"]
    
    existing = await db.work_schedule.find_one(
        {"master_id": master_id, "day_of_week": schedule.day_of_week}
    )
    
    data = schedule.model_dump()
    data["master_id"] = master_id
    
    if existing:
        await db.work_schedule.update_one(
            {"master_id": master_id, "day_of_week": schedule.day_of_week},
            {"$set": data}
        )
    else:
        new_schedule = WorkSchedule(**data)
        await db.work_schedule.insert_one(new_schedule.model_dump())
    
    result = await db.work_schedule.find_one(
        {"master_id": master_id, "day_of_week": schedule.day_of_week}, {"_id": 0}
    )
    return result
