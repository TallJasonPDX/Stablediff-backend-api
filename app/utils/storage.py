
from typing import Optional
import base64
from replit import Object
import os

async def save_base64_image(base64_data: str, folder: str, filename: str) -> str:
    # Remove data URI prefix if present
    base64_image = base64_data.replace("data:image/png;base64,", "")
    
    # Convert to bytes
    image_data = base64.b64decode(base64_image)
    
    # Create object path
    object_path = f"{folder}/{filename}"
    
    # Save to object storage
    obj = Object(object_path)
    obj.write_bytes(image_data)
    
    return object_path
