
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
