
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class Workflow(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    preview_image: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool = True
    is_admin: bool = False
    instagram_connected: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ImageBase(BaseModel):
    filename: str
    workflow_id: str

class ImageCreate(ImageBase):
    pass

class Image(ImageBase):
    id: str
    user_id: str
    original_url: HttpUrl
    processed_url: Optional[HttpUrl] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProcessImageRequest(BaseModel):
    workflow_id: str
    image_base64: str
    webhook_url: Optional[str] = None
