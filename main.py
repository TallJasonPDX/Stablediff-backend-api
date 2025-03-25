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

@app.on_event("startup")
async def startup_event():
    # Run validation checks
    from app.utils.startup_validation import StartupValidator
    validation_results = await StartupValidator.run_all_checks(app)
    
    # Log validation results
    print("\n=== Startup Validation Results ===")
    
    print("\nEnvironment Variables:")
    for var, exists in validation_results["environment_variables"]:
        status = "✓" if exists else "✗"
        print(f"{status} {var}")
    
    print("\nDatabase Connection:", "✓" if validation_results["database_connection"] else "✗")
    
    print("\nAPI Routes:")
    for route, exists in validation_results["api_routes"]:
        print(f"✓ {route}")
    
    # Ensure storage directories exist
    from replit.object_storage import Client
    storage = Client()
    
    print("\nStorage Directories:")
    directories = ['input_images', 'output_images', 'THEME_PREVIEWS']
    for dir in directories:
        try:
            storage.upload_from_text(f"{dir}/.keep", "")
            print(f"✓ {dir}")
        except Exception as e:
            print(f"✗ {dir}: {str(e)}")

    # Scan for LoRAs on startup
    from app.utils.lora_scanner import LoRAScanner
    scanner = LoRAScanner()
    new_themes = scanner.update_theme_registry()
    print(f"\nLoRA Scanning: Found {new_themes} new theme(s)")
    print("\n===============================")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)