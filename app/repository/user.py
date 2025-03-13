
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.models import UserCreate
from app.database import DBUser
from app.security import get_password_hash
from app.config import settings

def get_user(db: Session, user_id: str):
    return db.query(DBUser).filter(DBUser.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(DBUser).filter(DBUser.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()

def get_user_by_instagram_id(db: Session, instagram_id: str):
    return db.query(DBUser).filter(DBUser.instagram_id == instagram_id).first()

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
        quota_remaining=settings.DEFAULT_IMAGE_QUOTA,
        quota_reset_date=(datetime.utcnow() + timedelta(days=30))
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_instagram_user(db: Session, instagram_id: str, username: str, instagram_token: str):
    db_user = DBUser(
        id=str(uuid.uuid4()),
        instagram_id=instagram_id,
        username=username,
        email=f"{username}@instagram.user",  # Placeholder email
        hashed_password="",  # No password for OAuth users
        instagram_connected=True,
        instagram_token=instagram_token,
        follows_required=False,  # To be updated after checking
        quota_remaining=settings.DEFAULT_IMAGE_QUOTA,
        quota_reset_date=(datetime.utcnow() + timedelta(days=30))
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_instagram_token(db: Session, user_id: str, token: str):
    db_user = get_user(db, user_id=user_id)
    if db_user:
        db_user.instagram_token = token
        db_user.instagram_connected = True
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_follow_status(db: Session, user_id: str, follows: bool):
    db_user = get_user(db, user_id=user_id)
    if db_user:
        db_user.follows_required = follows
        # If user follows, increase quota
        if follows and db_user.quota_remaining < settings.FOLLOWER_IMAGE_QUOTA:
            db_user.quota_remaining = settings.FOLLOWER_IMAGE_QUOTA
        db.commit()
        db.refresh(db_user)
    return db_user

def get_remaining_quota(db: Session, user_id: str) -> int:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return 0
    
    # Admin users have unlimited quota
    if db_user.is_admin:
        return float('inf')  # Return infinity for unlimited quota
    
    # Check if quota needs to be reset
    if db_user.quota_reset_date and db_user.quota_reset_date < datetime.utcnow():
        # Reset quota based on follower status
        if db_user.follows_required:
            db_user.quota_remaining = settings.FOLLOWER_IMAGE_QUOTA
        else:
            db_user.quota_remaining = settings.DEFAULT_IMAGE_QUOTA
            
        db_user.quota_reset_date = datetime.utcnow() + timedelta(days=30)
        db.commit()
    
    return db_user.quota_remaining

def decrease_quota(db: Session, user_id: str):
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None
        
    # Skip quota decrease for admin users
    if db_user.is_admin:
        return db_user
        
    if db_user.quota_remaining > 0:
        db_user.quota_remaining -= 1
        db.commit()
    return db_user

def get_quota_reset_date(db: Session, user_id: str):
    db_user = get_user(db, user_id=user_id)
    if not db_user or not db_user.quota_reset_date:
        return None
    return db_user.quota_reset_date

def get_user_with_quota(db: Session, user_id: str):
    return db.query(DBUser).filter(DBUser.id == user_id).first()
