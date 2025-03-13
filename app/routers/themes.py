from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_db
from app.models import ThemeEnum, ThemeDetail
from sqlalchemy.orm import Session
from typing import List, Dict
from app.services.theme_registry import ThemeRegistry

router = APIRouter(
    prefix="/api/themes",
    tags=["themes"]
)

theme_registry = ThemeRegistry()

@router.get("/", response_model=List[ThemeDetail])
async def list_themes():
    """List available themes"""
    return theme_registry.get_all_themes()

@router.get("/available")
async def get_available_themes():
    """Get theme availability status"""
    return theme_registry.get_lora_availability()

@router.get("/{theme_id}", response_model=ThemeDetail)
async def get_theme(theme_id: str):
    """Get details for a specific theme"""
    theme = theme_registry.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")
    return theme