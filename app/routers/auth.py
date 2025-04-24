from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Token, User, UserCreate
from app.dependencies import create_access_token, get_current_user
from app.repository import user as user_repo
from app.security import verify_password, get_password_hash
from app.config import settings
from app.services.facebook import facebook_service
from app.repository import runpod as runpod_repo

router = APIRouter()


@router.post("/register",
             response_model=User,
             status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with username and password"""
    # Check if email already exists
    db_user = user_repo.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered")

    # Check if username already exists
    db_user = user_repo.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already taken")

    # Create the new user
    return user_repo.create_user(db=db, user=user)


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)):
    user = user_repo.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password,
                                       user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username},
                                       expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/facebook/authorize")
async def facebook_authorize():
    """Get Facebook authorization URL"""
    auth_url = facebook_service.get_authorization_url()
    return {"authorization_url": auth_url}


@router.get("/facebook/callback")
async def facebook_callback(code: str,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    """Handle Facebook OAuth callback"""
    token_data = await facebook_service.exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Failed to exchange code for token")

    # Store the token with the user
    access_token = token_data.get("access_token")
    if access_token:
        updated_user = user_repo.update_facebook_token(
            db, current_user.id, access_token)
        if updated_user:
            return {"message": "Successfully connected to Facebook"}

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to store Facebook token")


class FacebookLoginRequest(BaseModel):
    code: str
    anonymous_user_id: Optional[str] = None

@router.post("/facebook-login")
async def facebook_login(request_body: FacebookLoginRequest, db: Session = Depends(get_db)):
    """Handle Facebook OAuth flow for login/registration"""
    token_data = await facebook_service.exchange_code_for_token(request_body.code)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Failed to exchange code for token")

    # Get user profile from Facebook
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No access token received from Facebook")

    # Get Facebook profile and email
    profile = await facebook_service.get_user_profile(access_token)
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Failed to retrieve Facebook profile")

    # Handle anonymous user association
    if request_body.anonymous_user_id:
        print(f"[Facebook Login] Associating anonymous ID: {request_body.anonymous_user_id}")
        updated_count = runpod_repo.associate_anonymous_requests(
            db, 
            request_body.anonymous_user_id, 
            str(facebook_id)
        )
        print(f"[Facebook Login] Associated {updated_count} requests")

    # Check if user exists by Facebook ID
    facebook_id = profile.get("id")
    if not facebook_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No Facebook ID in profile response")

    db_user = user_repo.get_user_by_facebook_id(db, facebook_id=str(facebook_id))

    if not db_user:
        # Create new user with Facebook data
        username = profile.get("name", "").replace(" ", "_").lower()
        # Generate a unique username if it already exists
        if user_repo.get_user_by_username(db, username=username):
            username = f"{username}_{facebook_id}"

        db_user = user_repo.create_facebook_user(db=db,
                                           facebook_id=str(facebook_id),
                                           username=username,
                                           facebook_token=access_token)
    else:
        # Update the token
        db_user = user_repo.update_facebook_token(db, db_user.id,
                                            access_token)


    # Generate JWT token
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(data={"sub": db_user.username},
                                    expires_delta=access_token_expires)

    return {
        "access_token": jwt_token,
        "token_type": "bearer"
    }