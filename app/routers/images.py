
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, Image, ProcessRequest, ThemeEnum
from app.dependencies import get_current_active_user
from app.repository import image as image_repo
from app.config import settings
from app.services.stable_diffusion import sd_service

router = APIRouter()

@router.post("/upload", response_model=Image)
async def upload_image(
    file: UploadFile = File(...),
    theme: ThemeEnum = Form(ThemeEnum.classic),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type not supported"
        )
    
    # Create a unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save the file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create an image record
    image_url = f"/static/uploads/{unique_filename}"
    db_image = image_repo.create_image(
        db=db,
        image={"filename": unique_filename, "theme": theme},
        user_id=current_user.id,
        original_url=image_url
    )
    
    return db_image

@router.post("/{image_id}/process", response_model=Image)
async def process_image(
    image_id: str,
    process_request: ProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Get the image
    db_image = image_repo.get_image(db, image_id=image_id)
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Check if user owns the image
    if db_image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this image"
        )
    
    # Load the original image
    original_path = os.path.join(settings.UPLOAD_DIR, db_image.filename)
    if not os.path.exists(original_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original image file not found"
        )
    
    with open(original_path, "rb") as f:
        image_data = f.read()
    
    # Process with Stable Diffusion
    processed_image = await sd_service.process_image(
        image_data=image_data,
        theme=process_request.theme,
        strength=process_request.strength,
        guidance_scale=process_request.guidance_scale,
        steps=process_request.steps
    )
    
    if not processed_image:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process image"
        )
    
    # Save the processed image
    processed_filename = f"processed_{db_image.filename}"
    processed_path = os.path.join(settings.PROCESSED_DIR, processed_filename)
    with open(processed_path, "wb") as f:
        f.write(processed_image)
    
    # Update the image record
    processed_url = f"/static/processed/{processed_filename}"
    updated_image = image_repo.update_processed_image(
        db=db,
        image_id=image_id,
        processed_url=processed_url
    )
    
    return updated_image

@router.get("/", response_model=List[Image])
def get_user_images(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    images = image_repo.get_images_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return images

@router.get("/{image_id}", response_model=Image)
def get_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_image = image_repo.get_image(db, image_id=image_id)
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Check if user owns the image
    if db_image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this image"
        )
    
    return db_image

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Implementation of delete functionality would go here
    pass
