from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Response, Depends
from sqlalchemy.orm import Session
import asyncio
from app.database import get_db
from app.dependencies import get_current_active_user, get_current_user
from app.models import User
from app.repository import runpod as runpod_repo
from typing import Optional
from pydantic import BaseModel
import httpx
import base64
from datetime import datetime
import os

from app.services.job_tracker import JobTracker, JobStatus
from app.utils.storage import save_base64_image, Client
from app.config import settings

router = APIRouter()


class ImageProcessRequest(BaseModel):
    workflow_name: str
    image: str
    waitForResponse: bool = False


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    output_image: Optional[str] = None
    output: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None


@router.post("/process-image",
             response_model=JobStatusResponse,
             responses={
                 200: {
                     "description": "Successfully started image processing",
                     "content": {
                         "application/json": {
                             "example": {
                                 "job_id":
                                 "abc123",
                                 "status":
                                 "PROCESSING",
                                 "message":
                                 "Image processing started asynchronously"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Invalid request parameters"
                 },
                 500: {
                     "description": "RunPod API error"
                 }
             })
async def process_image(request: ImageProcessRequest,
                        db: Session = Depends(get_db),
                        current_user: Optional[User] = Depends(get_current_user)):
    if not (request.workflow_name and request.image):
        raise HTTPException(400, "Workflow name and image are required")

    # Ensure we have a valid user or None
    if current_user is None:
        user_id = None
    else:
        user_id = current_user.id

    # Create database record with optional user_id
    db_request = runpod_repo.create_request(
        db=db,
        user_id=user_id,
        workflow_id=request.workflow_name,
        input_image_url=request.image[:100]  # Store truncated URL/base64
    )

    # Save input image
    timestamp = datetime.now().timestamp()
    input_filename = f"{int(timestamp)}.png"
    try:
        await save_base64_image(request.image, "uploads", input_filename)
    except Exception as e:
        print(f"[Storage] Failed to save input image: {e}")
        # Continue processing even if storage fails

    # Determine endpoint
    endpoint = "runsync" if request.waitForResponse else "run"
    api_url = f"https://api.runpod.ai/v2/{settings.RUNPOD_ENDPOINT_ID}/{endpoint}"

    # Prepare request body
    request_body = {
        "input": {
            "workflow_name": request.workflow_name,
            "images": [{
                "name": "uploaded_image.jpg",
                "image": request.image
            }]
        }
    }

    # Add webhook for async requests
    if not request.waitForResponse:
        base_url = settings.BASE_URL.rstrip('/')
        request_body["webhook"] = f"{base_url}/api/images/webhook/runpod"

    # Make API request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                api_url,
                json=request_body,
                headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"})
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise HTTPException(500, f"RunPod API error: {str(e)}")

    # Handle async response
    if not request.waitForResponse and data.get("id"):
        JobTracker.set_job(data["id"], JobStatus.PROCESSING)
        # Update database record with RunPod job ID
        runpod_repo.update_request_status(db,
                                          request_id=db_request.id,
                                          status="submitted",
                                          runpod_job_id=data["id"])
        # Start background polling
        asyncio.create_task(JobTracker.poll_job_status(data["id"]))
        return JobStatusResponse(
            job_id=data["id"],
            status=JobStatus.PROCESSING,
            message="Image processing started asynchronously")

    # Handle sync response
    if request.waitForResponse and data.get("status") == "COMPLETED":
        return await handle_completed_job(data)

    return data


@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    if not job_id:
        raise HTTPException(400, "Job ID is required")

    # Check local cache
    cached_job = JobTracker.get_job(job_id)
    if cached_job:
        return cached_job

    # Check RunPod status
    api_url = f"https://api.runpod.ai/v2/{settings.RUNPOD_ENDPOINT_ID}/status/{job_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_url,
                headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"})
            data = response.json()
        except Exception as e:
            raise HTTPException(500, f"Failed to get job status: {str(e)}")

    if data["status"] == "COMPLETED":
        return await handle_completed_job(data)
    elif data["status"] == "FAILED":
        JobTracker.set_job(job_id,
                           JobStatus.FAILED,
                           error=data.get("error", "Unknown error"))

    # Get cached URL if available
    cached_job = JobTracker.get_job(job_id)
    image_url = None
    if cached_job and hasattr(cached_job, 'image_url'):
        image_url = cached_job.image_url

    return JobStatusResponse(job_id=job_id,
                             status=data["status"],
                             output=data.get("output"),
                             error=data.get("error"),
                             image_url=image_url)


@router.get("/webhook/runpod", operation_id="runpod_webhook_get")
@router.post("/webhook/runpod", operation_id="runpod_webhook_post")
async def runpod_webhook(request: Request, db: Session = Depends(get_db)):
    # Log request details
    print("\n=== RunPod Webhook Request ===")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Query Params: {dict(request.query_params)}")

    try:
        # Try to get body for both GET and POST
        body = await request.body()
        print(f"Raw Body: {body.decode()}")
    except Exception as e:
        print(f"Body read error: {str(e)}")

    # Parse data based on request method
    try:
        data = await request.json(
        ) if request.method == "POST" else request.query_params
        print(f"Parsed Data: {data}")
    except Exception as e:
        print(f"Data parse error: {str(e)}")
        raise HTTPException(400, f"Invalid request data: {str(e)}")

    job_id = data.get("id")
    if not job_id:
        raise HTTPException(400, "Job ID is required")

    # Get database record
    db_request = runpod_repo.get_request_by_job_id(db, job_id)
    if not db_request:
        print(f"Warning: No database record found for job {job_id}")
        return {"success": False, "error": "No database record found"}

    # Check for duplicate completion
    cached_job = JobTracker.get_job(job_id)
    if cached_job and cached_job.status == JobStatus.COMPLETED:
        return {"success": True}

    if data["status"] == "COMPLETED":
        job_response = await handle_completed_job(data)
        # Update database with completion
        runpod_repo.update_request_status(db,
                                          request_id=db_request.id,
                                          status="completed",
                                          output_url=job_response.image_url)
        return job_response
    elif data["status"] == "FAILED":
        error = data.get("error", "Unknown error")
        JobTracker.set_job(job_id, JobStatus.FAILED, error=error)
        # Update database with failure
        runpod_repo.update_request_status(db,
                                          request_id=db_request.id,
                                          status="failed")

    return {"success": True}


@router.get("/{filename}")
async def get_stored_image(filename: str):
    """Serve an image from the processed directory in object storage"""
    try:
        storage = Client()
        object_path = f"processed/{filename}"
        image_data = storage.download_as_bytes(object_path)

        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Image not found")


async def handle_completed_job(data: dict) -> JobStatusResponse:
    job_id = data.get("id", str(int(datetime.now().timestamp())))
    output_data = data.get("output", {})

    # Extract output image from various formats
    output_image = (output_data.get("output_image")
                    or (output_data.get("images", [{}])[0].get("image"))
                    or output_data.get("message"))

    if output_image:
        if not output_image.startswith("data:image/"):
            output_image = f"data:image/png;base64,{output_image}"

    try:
        # Use simple timestamp-based filename
        timestamp = int(datetime.now().timestamp())
        output_filename = f"{timestamp}.png"
        await save_base64_image(output_image, "processed", output_filename)

        # Construct simpler URL
        base_url = settings.BASE_URL.rstrip('/')
        image_url = f"{base_url}/api/images/{output_filename}"
    except Exception as e:
        print(f"[Storage] Failed to save output image: {e}")
        image_url = None

    JobTracker.set_job(job_id,
                       JobStatus.COMPLETED,
                       output_image=output_image,
                       image_url=image_url)

    return JobStatusResponse(job_id=job_id,
                             status="COMPLETED",
                             output_image=output_image,
                             image_url=image_url,
                             output=output_data)
