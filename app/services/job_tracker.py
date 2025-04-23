
from typing import Dict, Optional
from datetime import datetime
import asyncio
import httpx
from pydantic import BaseModel
from app.config import settings

class JobStatus:
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobData(BaseModel):
    status: str
    output_image: Optional[str] = None
    image_url: Optional[str] = None
    error: Optional[str] = None
    timestamp: float

class JobTracker:
    _jobs: Dict[str, JobData] = {}

    @classmethod
    def get_job(cls, job_id: str) -> Optional[JobData]:
        return cls._jobs.get(job_id)

    @classmethod
    def set_job(cls, job_id: str, status: str, output_image: Optional[str] = None, image_url: Optional[str] = None, error: Optional[str] = None):
        cls._jobs[job_id] = JobData(
            status=status,
            output_image=output_image,
            image_url=image_url,
            error=error,
            timestamp=datetime.now().timestamp()
        )
        return cls._jobs[job_id]

    @classmethod
    async def poll_job_status(cls, job_id: str):
        """Poll RunPod API for job status updates"""
        while True:
            if job_id not in cls._jobs or cls._jobs[job_id].status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
                
            api_url = f"https://api.runpod.ai/v2/{settings.RUNPOD_ENDPOINT_ID}/status/{job_id}"
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        api_url,
                        headers={"Authorization": f"Bearer {settings.RUNPOD_API_KEY}"}
                    )
                    data = response.json()
                    
                    if data["status"] == "COMPLETED":
                        from app.routers.images import handle_completed_job
                        from app.database import SessionLocal
                        from app.repository import runpod as runpod_repo
                        
                        # Get full job response with image URL
                        job_response = await handle_completed_job(data)
                        
                        # Update database with proper image URL
                        db = SessionLocal()
                        try:
                            db_request = runpod_repo.get_request_by_job_id(db, job_id)
                            if db_request:
                                runpod_repo.update_request_status(
                                    db,
                                    request_id=db_request.id,
                                    status="completed",
                                    output_url=job_response.image_url
                                )
                                print(f"[poll_job_status] Updated request {db_request.id} with URL: {job_response.image_url}")
                        finally:
                            db.close()
                        break
                    elif data["status"] == "FAILED":
                        cls.set_job(job_id, JobStatus.FAILED, error=data.get("error", "Unknown error"))
                        break
                except Exception as e:
                    print(f"Error polling job {job_id}: {str(e)}")
                    
            await asyncio.sleep(5)  # Poll every 5 seconds
