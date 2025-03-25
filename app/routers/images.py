
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from pydantic import BaseModel
import httpx
import base64
from datetime import datetime
import os

from app.services.job_tracker import JobTracker, JobStatus
from app.utils.storage import save_base64_image
from app.config import settings

router = APIRouter()

class ImageProcessRequest(BaseModel):
    workflow_name: str
    image: str
    endpointId: str
    waitForResponse: bool = False

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    output_image: Optional[str] = None
    output: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None

@router.post(
    "/process-image",
    response_model=JobStatusResponse,
    responses={
        200: {
            "description": "Successfully started image processing",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "abc123",
                        "status": "PROCESSING",
                        "message": "Image processing started asynchronously"
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        500: {"description": "RunPod API error"}
    }
)
async def process_image(
    request: ImageProcessRequest,
    description="Process an image using RunPod endpoint. Set waitForResponse=true for synchronous processing"
):
    if not (request.workflow_name and request.image and request.endpointId):
        raise HTTPException(400, "Workflow name, image, and endpoint ID are required")

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
    api_url = f"https://api.runpod.ai/v2/{request.endpointId}/{endpoint}"

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
        request_body["webhook"] = f"{settings.BASE_URL}/api/images/webhook/runpod"

    # Make API request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                api_url,
                json=request_body,
                headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"}
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise HTTPException(500, f"RunPod API error: {str(e)}")

    # Handle async response
    if not request.waitForResponse and data.get("id"):
        JobTracker.set_job(data["id"], JobStatus.PROCESSING)
        return JobStatusResponse(
            job_id=data["id"],
            status=JobStatus.PROCESSING,
            message="Image processing started asynchronously"
        )

    # Handle sync response
    if request.waitForResponse and data.get("status") == "COMPLETED":
        return handle_completed_job(data)

    return data

@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str, endpointId: str):
    if not job_id:
        raise HTTPException(400, "Job ID is required")

    # Check local cache
    cached_job = JobTracker.get_job(job_id)
    if cached_job:
        return cached_job

    # Check RunPod status
    api_url = f"https://api.runpod.ai/v2/{endpointId}/status/{job_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_url,
                headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"}
            )
            data = response.json()
        except Exception as e:
            raise HTTPException(500, f"Failed to get job status: {str(e)}")

    if data["status"] == "COMPLETED":
        return handle_completed_job(data)
    elif data["status"] == "FAILED":
        JobTracker.set_job(job_id, JobStatus.FAILED, error=data.get("error", "Unknown error"))

    return JobStatusResponse(
        job_id=job_id,
        status=data["status"],
        output=data.get("output"),
        error=data.get("error")
    )

@router.post("/webhook/runpod")
async def runpod_webhook(data: dict):
    job_id = data.get("id")
    if not job_id:
        raise HTTPException(400, "Job ID is required")

    # Check for duplicate completion
    cached_job = JobTracker.get_job(job_id)
    if cached_job and cached_job.status == JobStatus.COMPLETED:
        return {"success": True}

    if data["status"] == "COMPLETED":
        return handle_completed_job(data)
    elif data["status"] == "FAILED":
        JobTracker.set_job(job_id, JobStatus.FAILED, error=data.get("error", "Unknown error"))

    return {"success": True}

def handle_completed_job(data: dict) -> JobStatusResponse:
    job_id = data.get("id", str(int(datetime.now().timestamp())))
    output_data = data.get("output", {})
    
    # Extract output image from various formats
    output_image = (
        output_data.get("output_image") or
        (output_data.get("images", [{}])[0].get("image")) or
        output_data.get("message")
    )

    if output_image:
        if not output_image.startswith("data:image/"):
            output_image = f"data:image/png;base64,{output_image}"

        # Save output image
        try:
            timestamp = int(datetime.now().timestamp())
            output_filename = f"{timestamp}.png"
            save_base64_image(output_image, "processed", output_filename)
        except Exception as e:
            print(f"[Storage] Failed to save output image: {e}")

    JobTracker.set_job(job_id, JobStatus.COMPLETED, output_image=output_image)

    return JobStatusResponse(
        job_id=job_id,
        status="COMPLETED",
        output_image=output_image,
        output=output_data
    )
