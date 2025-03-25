import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "NurseFilter API"
    PROJECT_VERSION: str = "1.0.0"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/nursefilter")

    # Theme preview path (still needed for local previews)
    THEME_PREVIEWS_DIR: str = "static/theme_previews"

    # Instagram OAuth settings
    INSTAGRAM_CLIENT_ID: str = os.getenv("INSTAGRAM_CLIENT_ID", "")
    INSTAGRAM_CLIENT_SECRET: str = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
    INSTAGRAM_REDIRECT_URI: str = os.getenv("INSTAGRAM_REDIRECT_URI", "")
    INSTAGRAM_REQUIRED_FOLLOW: str = os.getenv("INSTAGRAM_REQUIRED_FOLLOW",
                                               "nursefilter_official")

    # Quota settings
    DEFAULT_IMAGE_QUOTA: int = int(os.getenv("DEFAULT_IMAGE_QUOTA", "10"))
    FOLLOWER_IMAGE_QUOTA: int = int(os.getenv("FOLLOWER_IMAGE_QUOTA", "25"))


class Settings:
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY")
    RUNPOD_ENDPOINT_ID: str = os.getenv("RUNPOD_ENDPOINT_ID")
    RUNPOD_TIMEOUT: int = int(os.getenv("RUNPOD_TIMEOUT", "600"))


settings = Settings()
