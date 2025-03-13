
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict, Any

from app.database import get_db
from app.models import Token, User
from app.dependencies import create_access_token
from app.repository import user as user_repo
from app.security import verify_password
from app.config import settings
from app.services.instagram import instagram_service

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = user_repo.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/instagram/authorize")
async def instagram_authorize():
    """Get Instagram authorization URL"""
    auth_url = instagram_service.get_authorization_url()
    return {"authorization_url": auth_url}

@router.get("/instagram/callback")
async def instagram_callback(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle Instagram OAuth callback"""
    token_data = await instagram_service.exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
    
    # Store the token with the user
    access_token = token_data.get("access_token")
    if access_token:
        updated_user = user_repo.update_instagram_token(db, current_user.id, access_token)
        if updated_user:
            return {"message": "Successfully connected to Instagram"}
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to store Instagram token"
    )
