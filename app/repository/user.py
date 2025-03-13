
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import DBUser
from app.models import UserCreate, User
from app.security import get_password_hash

def get_user(db: Session, user_id: str):
    return db.query(DBUser).filter(DBUser.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(DBUser).filter(DBUser.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(DBUser).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = DBUser(
        id=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_instagram_token(db: Session, user_id: str, token: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.instagram_connected = True
        db_user.instagram_token = token
        db.commit()
        db.refresh(db_user)
    return db_user
