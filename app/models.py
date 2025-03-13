
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class ThemeEnum(str, Enum):
    classic = "classic"
    modern = "modern"
    vintage = "vintage"
    anime = "anime"
    future = "future"

class ThemeDetail(BaseModel):
    id: str
    name: str
    description: str
    lora_file: str
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
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ImageBase(BaseModel):
    filename: str
    theme: ThemeEnum
    
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
        orm_mode = True

class ProcessRequest(BaseModel):
    theme: ThemeEnum = Field(default=ThemeEnum.classic)
    strength: float = Field(default=0.75, ge=0.1, le=1.0)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    steps: int = Field(default=30, ge=10, le=150)
