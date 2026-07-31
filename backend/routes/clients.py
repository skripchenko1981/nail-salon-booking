"""Маршрути клієнтів"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from database import db
from models import Client, ClientStats, Booking
from auth import verify_master_or_admin
from datetime import datetime, timezone

router = APIRouter()


@router.get("/admin/clients", response_model=List[Client])
async def get_all_clients(user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    clients = await db.clients.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return clients

@router.get("/admin/clients/stats", response_model=ClientStats)
async def get_client_stats(user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    
    total = await db.clients.count_documents(query)
    
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).isoformat()
    new_this_month = await db.clients.count_documents({**query, "created_at": {"$gte": month_start}})
    returning = await db.clients.count_documents({**query, "total_bookings": {"$gt": 1}})
    
    pipeline = [{"$match": query}, {"$group": {"_id": None, "avg": {"$avg": "$total_bookings"}}}]
    avg_result = await db.clients.aggregate(pipeline).to_list(1)
    avg_visits = round(avg_result[0]["avg"], 1) if avg_result else 0
    
    top = await db.clients.find(query, {"_id": 0}).sort("total_spent", -1).to_list(5)
    
    return ClientStats(
        total_clients=total, new_this_month=new_this_month,
        returning_clients=returning, avg_visits=avg_visits, top_clients=top
    )

@router.get("/admin/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, user: Dict = Depends(verify_master_or_admin)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.get("/admin/clients/{client_id}/bookings", response_model=List[Booking])
async def get_client_bookings_admin(client_id: str, user: Dict = Depends(verify_master_or_admin)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    bookings = await db.bookings.find(
        {"client_phone": client["phone"]}, {"_id": 0}
    ).sort("date", -1).to_list(100)
    return bookings
