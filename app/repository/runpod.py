
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import DBRunPodRequest

def create_request(db: Session, user_id: str, workflow_id: str, input_image_url: str):
    db_request = DBRunPodRequest(
        user_id=user_id,
        workflow_id=workflow_id,
        input_image_url=input_image_url
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def get_request(db: Session, request_id: str):
    return db.query(DBRunPodRequest).filter(DBRunPodRequest.id == request_id).first()

def update_request_status(db: Session, request_id: str, status: str, output_url: str = None):
    request = get_request(db, request_id)
    if request:
        request.status = status
        if output_url:
            request.output_image_url = output_url
        if status in ["completed", "failed"]:
            request.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(request)
    return request
