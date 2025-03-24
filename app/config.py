import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NurseFilter API"
    PROJECT_VERSION: str = "1.0.0"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nursefilter")

    # File storage paths
    UPLOAD_DIR: str = "static/uploads"
    PROCESSED_DIR: str = "static/processed"
    THEME_PREVIEWS_DIR: str = "static/theme_previews"
    
    # Theme LoRA mappings
    NURSE_LORAS: dict = {
        "classic": "nurse-classic-lora",
        "modern": "nurse-modern-lora",
        "vintage": "nurse-vintage-lora", 
        "anime": "nurse-anime-lora",
        "future": "nurse-future-lora"
    }
    PROCESSED_DIR: str = "static/processed"

    # Stable Diffusion settings
    SD_MODEL_PATH: str = os.getenv("SD_MODEL_PATH", "sd_models/sdxl-turbo.safetensors")
    SD_LORA_DIR: str = os.getenv("SD_LORA_DIR", "sd_models/loras")

    # Instagram OAuth settings
    INSTAGRAM_CLIENT_ID: str = os.getenv("INSTAGRAM_CLIENT_ID", "")
    INSTAGRAM_CLIENT_SECRET: str = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
    INSTAGRAM_REDIRECT_URI: str = os.getenv("INSTAGRAM_REDIRECT_URI", "")
    INSTAGRAM_REQUIRED_FOLLOW: str = os.getenv("INSTAGRAM_REQUIRED_FOLLOW", "nursefilter_official")

    # Quota settings
    DEFAULT_IMAGE_QUOTA: int = int(os.getenv("DEFAULT_IMAGE_QUOTA", "10"))
    FOLLOWER_IMAGE_QUOTA: int = int(os.getenv("FOLLOWER_IMAGE_QUOTA", "25"))

class Settings:
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY")
    RUNPOD_TIMEOUT: int = int(os.getenv("RUNPOD_TIMEOUT", "600"))
    
settings = Settings()