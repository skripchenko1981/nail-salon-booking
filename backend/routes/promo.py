"""Маршрути промо-блоків"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from database import db
from models import PromoBlock, PromoBlockCreate, PromoBlockUpdate
from auth import verify_admin
from s3_utils import generate_presigned_url, delete_file_from_s3

router = APIRouter()


def refresh_promo_block_urls(blocks):
    for block in blocks:
        if block.get("image_key"):
            block["image_url"] = generate_presigned_url(block["image_key"], expiration=3600)
    return blocks


@router.get("/promo-blocks", response_model=List[PromoBlock])
async def get_active_promo_blocks():
    blocks = await db.promo_blocks.find({"is_active": True}, {"_id": 0}).sort("position", 1).to_list(100)
    return refresh_promo_block_urls(blocks)

@router.get("/admin/promo-blocks", response_model=List[PromoBlock])
async def get_all_promo_blocks(user: Dict = Depends(verify_admin)):
    blocks = await db.promo_blocks.find({}, {"_id": 0}).sort("position", 1).to_list(100)
    return refresh_promo_block_urls(blocks)

@router.post("/admin/promo-blocks", response_model=PromoBlock)
async def create_promo_block(block: PromoBlockCreate, user: Dict = Depends(verify_admin)):
    new_block = PromoBlock(**block.model_dump())
    doc = new_block.model_dump()
    await db.promo_blocks.insert_one(doc)
    if doc.get("image_key"):
        doc["image_url"] = generate_presigned_url(doc["image_key"], expiration=3600)
    return doc

@router.put("/admin/promo-blocks/{block_id}", response_model=PromoBlock)
async def update_promo_block(block_id: str, block: PromoBlockUpdate, user: Dict = Depends(verify_admin)):
    existing = await db.promo_blocks.find_one({"id": block_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Promo block not found")
    
    update_data = {k: v for k, v in block.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.promo_blocks.update_one({"id": block_id}, {"$set": update_data})
    updated_block = await db.promo_blocks.find_one({"id": block_id}, {"_id": 0})
    if updated_block.get("image_key"):
        updated_block["image_url"] = generate_presigned_url(updated_block["image_key"], expiration=3600)
    return PromoBlock(**updated_block)

@router.delete("/admin/promo-blocks/{block_id}")
async def delete_promo_block(block_id: str, user: Dict = Depends(verify_admin)):
    block = await db.promo_blocks.find_one({"id": block_id}, {"_id": 0})
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    if block.get("image_key"):
        delete_file_from_s3(block["image_key"])
    
    await db.promo_blocks.delete_one({"id": block_id})
    return {"message": "Promo block deleted"}
