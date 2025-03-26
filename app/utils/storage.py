
from typing import Optional
import base64
from replit.object_storage import Client
import os

async def save_base64_image(base64_data: str, folder: str, filename: str) -> str:
    # Remove data URI prefix if present
    base64_image = base64_data.replace("data:image/png;base64,", "")
    
    # Convert to bytes
    image_data = base64.b64decode(base64_image)
    
    # Create object path
    object_path = f"{folder}/{filename}"
    
    # Save to object storage using the client
    client = Client()
    client.upload_bytes(object_path, image_data)
    
    return object_path
from replit.object_storage import Client
import base64
import io

storage = Client()

async def save_base64_image(base64_str: str, folder: str, filename: str) -> str:
    """Save base64 image to object storage"""
    try:
        # Remove data:image prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
            
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_str)
        
        # Create full path
        full_path = f"{folder}/{filename}"
        
        # Upload bytes to storage
        storage.upload_from_bytes(full_path, image_bytes)
        
        return full_path
    except Exception as e:
        print(f"[Storage] Failed to save image: {e}")
        raise
