
from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel

from app.models import User, ThemeEnum
from app.dependencies import get_current_active_user

router = APIRouter()

class Theme(BaseModel):
    id: str
    name: str
    description: str
    preview_url: str

@router.get("/", response_model=List[Theme])
def list_themes(current_user: User = Depends(get_current_active_user)):
    """List available themes and their descriptions"""
    themes = [
        {
            "id": ThemeEnum.classic,
            "name": "Classic Nurse",
            "description": "Traditional nursing attire with a classic, professional look.",
            "preview_url": "/static/theme_previews/classic.jpg"
        },
        {
            "id": ThemeEnum.modern,
            "name": "Modern Healthcare",
            "description": "Contemporary medical professional style with modern scrubs.",
            "preview_url": "/static/theme_previews/modern.jpg"
        },
        {
            "id": ThemeEnum.vintage,
            "name": "Vintage Nurse",
            "description": "Retro nursing style inspired by mid-20th century healthcare.",
            "preview_url": "/static/theme_previews/vintage.jpg"
        },
        {
            "id": ThemeEnum.anime,
            "name": "Anime Nurse",
            "description": "Stylized anime-inspired nurse character design.",
            "preview_url": "/static/theme_previews/anime.jpg"
        },
        {
            "id": ThemeEnum.future,
            "name": "Future Medical",
            "description": "Futuristic healthcare professional with advanced tech elements.",
            "preview_url": "/static/theme_previews/future.jpg"
        }
    ]
    
    return themes
