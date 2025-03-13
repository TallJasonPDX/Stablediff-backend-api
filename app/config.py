
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "NurseFilter API"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings - in production, use environment variables
    DATABASE_URL: str = "sqlite:///./nursefiler.db"
    
    # Instagram API settings
    INSTAGRAM_CLIENT_ID: str = os.getenv("INSTAGRAM_CLIENT_ID", "")
    INSTAGRAM_CLIENT_SECRET: str = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
    INSTAGRAM_REDIRECT_URI: str = os.getenv("INSTAGRAM_REDIRECT_URI", "")
    
    # Stable Diffusion settings
    SD_API_KEY: str = os.getenv("SD_API_KEY", "")
    
    # Theme LoRAs - map friendly names to actual LoRA IDs/filenames
    NURSE_LORAS: dict = {
        "classic": "nurse-classic-lora",
        "modern": "nurse-modern-lora",
        "vintage": "nurse-vintage-lora",
        "anime": "nurse-anime-lora",
        "future": "nurse-future-lora"
    }
    
    # File storage
    UPLOAD_DIR: str = "static/uploads"
    PROCESSED_DIR: str = "static/processed"
    MAX_FILE_SIZE: int = 10_000_000  # 10MB

settings = Settings()
