from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, UserCreate, RunPodRequestHistoryItem
from app.dependencies import get_current_active_user
from app.repository import user as user_repo
from app.repository import runpod as runpod_repo

router = APIRouter()


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = user_repo.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered")

    db_user = user_repo.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already taken")

    return user_repo.create_user(db=db, user=user)


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/", response_model=List[User])
def read_users(skip: int = 0,
               limit: int = 100,
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_active_user)):
    users = user_repo.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/profile")
def get_user_profile(current_user: User = Depends(get_current_active_user),
                     db: Session = Depends(get_db)):
    """Return user profile and remaining image quota"""
    # Get user data including quota information
    user_data = user_repo.get_user_with_quota(db, user_id=current_user.id)

    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    return {
        "username":
        user_data.username,
        "email":
        user_data.email,
        "full_name":
        user_data.full_name,
        "instagram_connected":
        user_data.instagram_connected,
        "follows_required":
        user_data.follows_required
        if hasattr(user_data, "follows_required") else False,
        "image_quota": {
            "remaining":
            user_repo.get_remaining_quota(db, user_id=current_user.id),
            "total": settings.DEFAULT_IMAGE_QUOTA,
            "reset_on": user_repo.get_quota_reset_date(db,
                                                       user_id=current_user.id)
        }
    }


@router.get("/history", response_model=List[RunPodRequestHistoryItem])
def get_user_history(skip: int = 0,
                     limit: int = 20,
                     current_user: User = Depends(get_current_active_user),
                     db: Session = Depends(get_db)):
    """Return user's RunPod request history"""
    requests = runpod_repo.get_requests_by_user(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return requests
