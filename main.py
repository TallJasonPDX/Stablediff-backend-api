
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import os
import uuid
import shutil
from PIL import Image
import httpx
import json
from datetime import datetime, timedelta

from app.routers import auth, user, images, themes
from app.dependencies import get_current_user
from app.config import settings

# Create application directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/processed', exist_ok=True)

app = FastAPI(title="NurseFilter API", 
              description="A service that processes images with nurse-themed LoRAs using Stable Diffusion")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/user", tags=["Users"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(themes.router, prefix="/api/themes", tags=["Themes"])

@app.get("/")
def read_root():
    return {"message": "Welcome to NurseFilter API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
