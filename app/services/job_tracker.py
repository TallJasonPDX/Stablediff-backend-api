
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel

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
