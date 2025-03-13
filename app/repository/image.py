
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import List

from app.database import DBImage
from app.models import ImageCreate, Image

def get_image(db: Session, image_id: str):
    return db.query(DBImage).filter(DBImage.id == image_id).first()

def get_images_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(DBImage).filter(DBImage.user_id == user_id).offset(skip).limit(limit).all()

def create_image(db: Session, image: ImageCreate, user_id: str, original_url: str):
    db_image = DBImage(
        id=str(uuid.uuid4()),
        user_id=user_id,
        filename=image.filename,
        theme=image.theme,
        original_url=original_url,
        created_at=datetime.utcnow()
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def update_processed_image(db: Session, image_id: str, processed_url: str):
    db_image = get_image(db, image_id)
    if db_image:
        db_image.processed_url = processed_url
        db_image.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_image)
    return db_image
