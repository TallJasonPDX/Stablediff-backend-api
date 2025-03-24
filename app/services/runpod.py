
import os
import json
import httpx
from fastapi import APIRouter, Request
from datetime import datetime
from app.config import settings
from app.repository import runpod as runpod_repo
from app.database import SessionLocal

router = APIRouter()

async def submit_to_runpod(request_id: str, input_image: str, workflow_id: str):
    """Submit job to RunPod endpoint"""
    endpoint_url = f"https://api.runpod.ai/v2/{settings.RUNPOD_ENDPOINT_ID}/run"
    payload = {
        "input": {
            "image": input_image,
            "workflow": workflow_id
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint_url,
            json=payload,
            headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            db = SessionLocal()
            try:
                runpod_repo.update_request_status(
                    db,
                    request_id=request_id,
                    status="submitted",
                    runpod_job_id=data["id"]
                )
            finally:
                db.close()
            return data["id"]
    return None

@router.post("/webhook")
async def runpod_webhook(request: Request):
    """Webhook endpoint for RunPod results"""
    data = await request.json()
    job_id = data.get("id")
    
    db = SessionLocal()
    try:
        # Find request by RunPod job ID
        request = runpod_repo.get_request_by_job_id(db, job_id)
        if request and data.get("status") == "COMPLETED":
            output_url = data.get("output", {}).get("image_url")
            if output_url:
                runpod_repo.update_request_status(
                    db,
                    request_id=request.id,
                    status="completed",
                    output_url=output_url
                )
    finally:
        db.close()
    
    return {"status": "success"}

# Background task to process pending requests
async def process_pending_requests():
    """Process pending RunPod requests"""
    db = SessionLocal()
    try:
        pending_requests = runpod_repo.get_pending_requests(db)
        for request in pending_requests:
            await submit_to_runpod(
                request.id,
                request.input_image_url,
                request.workflow_id
            )
    finally:
        db.close()
