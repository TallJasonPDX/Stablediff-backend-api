
import runpod
import asyncio
from typing import Optional
from app.config import settings

class RunPodService:
    def __init__(self):
        runpod.api_key = settings.RUNPOD_API_KEY
        
    async def submit_job(self, workflow_id: str, input_data: dict) -> str:
        """Submit a job to RunPod and return the job ID"""
        endpoint = runpod.Endpoint(settings.RUNPOD_ENDPOINT_ID)
        formatted_input = {
            "input": {
                "workflow_name": workflow_id,
                "image": input_data.get("image")
            }
        }
        run_request = endpoint.run(formatted_input)
        return run_request.id
        
    async def check_job_status(self, job_id: str) -> dict:
        """Check the status of a RunPod job"""
        status = runpod.get_job_status(job_id)
        return status
        
    async def get_job_result(self, job_id: str, timeout: int = 600) -> Optional[dict]:
        """Get job result with timeout"""
        endpoint = runpod.Endpoint("")  # Empty string since we're using job_id
        result = endpoint.wait_for_job(job_id, timeout)
        return result

runpod_service = RunPodService()
