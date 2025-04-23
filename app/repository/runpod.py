
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import DBRunPodRequest

from typing import Optional
from sqlalchemy import update

def create_request(db: Session, workflow_id: str, input_image_url: str, user_id: Optional[str] = None, anonymous_user_id: Optional[str] = None):
    print(f"[create_request] Creating request with user_id={user_id}, workflow_id={workflow_id}, anonymous_user_id={anonymous_user_id}")
    db_request = DBRunPodRequest(
        user_id=user_id,
        workflow_id=workflow_id,
        input_image_url=input_image_url,
        anonymous_user_id=anonymous_user_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def associate_anonymous_requests(db: Session, anonymous_user_id: str, user_id: str) -> int:
    """Associates RunPod requests from an anonymous ID to a user ID."""
    stmt = (
        update(DBRunPodRequest)
        .where(DBRunPodRequest.anonymous_user_id == anonymous_user_id)
        .where(DBRunPodRequest.user_id == None)
        .values(user_id=user_id, anonymous_user_id=None)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def get_request(db: Session, request_id: str):
    return db.query(DBRunPodRequest).filter(DBRunPodRequest.id == request_id).first()

def update_request_status(db: Session, request_id: str, status: str, output_url: str = None, runpod_job_id: str = None):
    request = get_request(db, request_id)
    if request:
        request.status = status
        if output_url:
            request.output_image_url = output_url
        if runpod_job_id:
            request.runpod_job_id = runpod_job_id
        if status == "submitted":
            request.submitted_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            request.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(request)
    return request

def get_request_by_job_id(db: Session, job_id: str):
    return db.query(DBRunPodRequest).filter(DBRunPodRequest.runpod_job_id == job_id).first()

def get_pending_requests(db: Session):
    return db.query(DBRunPodRequest).filter(DBRunPodRequest.status == "pending").all()

def get_requests_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    """Gets RunPod requests for a specific user, ordered by creation date."""
    return (
        db.query(DBRunPodRequest)
        .filter(DBRunPodRequest.user_id == user_id)
        .order_by(DBRunPodRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
