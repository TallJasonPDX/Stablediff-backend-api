from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict
import os
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Image, User, ThemeEnum, ProcessRequest
from app.dependencies import get_current_active_user
from app.repository import image as image_repo
from app.repository import user as user_repo
from app.services.stable_diffusion import sd_service
from app.config import settings

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Image)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload an original image"""
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Generate unique filename
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    # Ensure directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create database entry
    image_data = {
        "filename": filename,
        "original_url": f"/static/uploads/{filename}",
        "user_id": current_user.id
    }

    db_image = image_repo.create_image(db=db, image_data=image_data)
    return db_image

@router.get("/{image_id}", response_model=Image)
def get_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve a specific processed image"""
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

class ProcessImageRequest(BaseModel):
    image_base64: str
    workflow_id: str

@router.post("/process")
async def process_image(
    request: ProcessImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process an image with specified theme LoRA"""
    # Check user quota
    remaining_quota = user_repo.get_remaining_quota(db, user_id=current_user.id)
    if remaining_quota <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Image processing quota exceeded"
        )

    # Validate workflow exists
    workflow = next((w for w in WORKFLOWS if w.id == request.workflow_id), None)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID"
        )

    # Create RunPod request
    runpod_request = runpod_repo.create_request(
        db=db,
        user_id=current_user.id,
        workflow_id=request.workflow_id,
        input_image_url=request.image_base64,
        status="pending"
    )

    try:
        # Submit job to RunPod
        job_id = await runpod_service.submit_job(
            workflow_id=request.workflow_id,
            input_data={"image": request.image_base64},
            webhook_url=request.webhook_url
        )

        # Update request with RunPod job ID
        runpod_repo.update_request_status(
            db=db,
            request_id=runpod_request.id,
            status="submitted",
            runpod_job_id=job_id
        )

        # Decrement user quota
        user_repo.decrement_quota(db, user_id=current_user.id)

        return {"request_id": runpod_request.id, "job_id": job_id}

    except Exception as e:
        runpod_repo.update_request_status(
            db=db,
            request_id=runpod_request.id,
            status="failed"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/images/runpod-webhook")
async def runpod_webhook(request: Request):
    """Handles RunPod webhook notifications."""
    try:
        data = await request.json()
        # Process the webhook data (replace with your actual processing logic)
        print(f"Received RunPod webhook: {data}")
        return {"status": "success"}
    except Exception as e:
        print(f"Error processing RunPod webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")