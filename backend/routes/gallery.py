"""Маршрути галереї / портфоліо"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict
from database import db
from models import GalleryImage
from auth import verify_master_or_admin
from s3_utils import generate_presigned_url, delete_file_from_s3, upload_file_with_thumbnail
from datetime import datetime, timezone
import uuid

router = APIRouter()


@router.get("/gallery")
async def get_gallery_images(master_id: Optional[str] = None, skip: int = 0, limit: int = 12):
    query = {"is_active": True}
    if master_id:
        query["master_id"] = master_id
    
    total = await db.gallery.count_documents(query)
    images = await db.gallery.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for img in images:
        if img.get("thumb_key"):
            img["thumb_url"] = generate_presigned_url(img["thumb_key"], expiration=3600)
        if img.get("file_key"):
            img["image_url"] = generate_presigned_url(img["file_key"], expiration=3600)
    
    return {"images": images, "total": total, "skip": skip, "limit": limit, "has_more": skip + limit < total}

@router.get("/masters/{master_id}/gallery")
async def get_master_gallery(master_id: str, skip: int = 0, limit: int = 12):
    query = {"master_id": master_id, "is_active": True}
    
    total = await db.gallery.count_documents(query)
    images = await db.gallery.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for img in images:
        if img.get("thumb_key"):
            img["thumb_url"] = generate_presigned_url(img["thumb_key"], expiration=3600)
        if img.get("file_key"):
            img["image_url"] = generate_presigned_url(img["file_key"], expiration=3600)
    
    return {"images": images, "total": total, "skip": skip, "limit": limit, "has_more": skip + limit < total}

@router.get("/admin/gallery", response_model=List[GalleryImage])
async def get_all_gallery_images(user: Dict = Depends(verify_master_or_admin)):
    query = {}
    if user["role"] == "master":
        query["master_id"] = user["user_id"]
    
    images = await db.gallery.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    for image in images:
        if image.get('thumb_key'):
            image['thumb_url'] = generate_presigned_url(image['thumb_key'], expiration=3600)
        if image.get('file_key'):
            image['image_url'] = generate_presigned_url(image['file_key'], expiration=3600)
    
    return images

@router.post("/admin/gallery")
async def create_gallery_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    user: Dict = Depends(verify_master_or_admin)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        raise HTTPException(status_code=400, detail="Unsupported image format")
    
    file_content = await file.read()
    
    try:
        result = upload_file_with_thumbnail(file_content, file_extension)
        file_key = result["file_key"]
        thumb_key = result["thumb_key"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
    
    master_id = user["user_id"] if user["role"] == "master" else None
    master_name = None
    if master_id:
        master = await db.masters.find_one({"id": master_id}, {"_id": 0, "name": 1})
        if master:
            master_name = master.get("name")
    
    image_id = str(uuid.uuid4())
    image = {
        "id": image_id, "image_url": "",
        "file_key": file_key, "thumb_key": thumb_key,
        "master_id": master_id, "master_name": master_name,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.gallery.insert_one(image)
    saved = await db.gallery.find_one({"id": image_id}, {"_id": 0})
    saved['image_url'] = generate_presigned_url(file_key, expiration=3600)
    saved['thumb_url'] = generate_presigned_url(thumb_key, expiration=3600)
    return saved

@router.post("/admin/gallery/batch")
async def create_gallery_images_batch(
    files: List[UploadFile] = File(...),
    description: Optional[str] = Form(None),
    user: Dict = Depends(verify_master_or_admin)
):
    master_id = user["user_id"] if user["role"] == "master" else None
    master_name = None
    if master_id:
        master = await db.masters.find_one({"id": master_id}, {"_id": 0, "name": 1})
        if master:
            master_name = master.get("name")
    
    uploaded = []
    errors = []
    
    for file in files:
        try:
            if not file.content_type.startswith('image/'):
                errors.append(f"{file.filename}: не зображення")
                continue
            
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                errors.append(f"{file.filename}: непідтримуваний формат")
                continue
            
            file_content = await file.read()
            result = upload_file_with_thumbnail(file_content, file_extension)
            
            image_id = str(uuid.uuid4())
            image = {
                "id": image_id, "image_url": "",
                "file_key": result["file_key"], "thumb_key": result["thumb_key"],
                "master_id": master_id, "master_name": master_name,
                "description": description,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            await db.gallery.insert_one(image)
            uploaded.append(image_id)
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return {"uploaded": len(uploaded), "errors": errors, "image_ids": uploaded}

@router.delete("/admin/gallery/{image_id}")
async def delete_gallery_image(image_id: str, user: Dict = Depends(verify_master_or_admin)):
    image = await db.gallery.find_one({"id": image_id}, {"_id": 0})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if image.get("file_key"):
        delete_file_from_s3(image["file_key"])
    if image.get("thumb_key"):
        delete_file_from_s3(image["thumb_key"])
    
    await db.gallery.delete_one({"id": image_id})
    return {"message": "Image deleted"}

@router.put("/admin/gallery/{image_id}")
async def update_gallery_image(image_id: str, is_active: bool, user: Dict = Depends(verify_master_or_admin)):
    result = await db.gallery.update_one({"id": image_id}, {"$set": {"is_active": is_active}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image updated", "is_active": is_active}
