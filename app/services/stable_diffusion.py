
import os
import uuid
import httpx
from PIL import Image
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, Any

from app.config import settings

class StableDiffusionService:
    def __init__(self):
        self.api_key = settings.SD_API_KEY
        self.api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        self.lora_mappings = settings.NURSE_LORAS
    
    async def process_image(self, 
                           image_data: bytes, 
                           theme: str, 
                           strength: float = 0.75,
                           guidance_scale: float = 7.5,
                           steps: int = 30) -> Optional[bytes]:
        """Process an image using Stable Diffusion with a nurse theme LoRA"""
        if theme not in self.lora_mappings:
            raise ValueError(f"Theme {theme} not found in available LoRAs")
            
        lora_id = self.lora_mappings[theme]
        
        # Prepare the image
        img = Image.open(BytesIO(image_data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize to 1024x1024 if necessary (SDXL requirement)
        if img.width > 1024 or img.height > 1024:
            img.thumbnail((1024, 1024))
        
        # Convert back to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # Prepare the payload
        files = {
            "init_image": ("image.png", img_bytes.getvalue(), "image/png")
        }
        
        data = {
            "init_image_mode": "IMAGE_STRENGTH",
            "image_strength": strength,
            "steps": steps,
            "cfg_scale": guidance_scale,
            "sampler": "K_DPMPP_2M",
            "lora_weights": {lora_id: 0.75},
            "text_prompts[0][text]": f"nurse theme, professional medical staff, {theme} style",
            "text_prompts[0][weight]": 1,
            "text_prompts[1][text]": "bad anatomy, bad proportions, blurry, low quality",
            "text_prompts[1][weight]": -1
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url, 
                    files=files,
                    data=data,
                    headers=self.headers,
                    timeout=60.0  # Longer timeout for image processing
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "artifacts" in result and len(result["artifacts"]) > 0:
                        # Get the first image result
                        image_b64 = result["artifacts"][0]["base64"]
                        return BytesIO(bytes(image_b64, 'utf-8'))
                else:
                    print(f"Error from Stable Diffusion API: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error processing image with Stable Diffusion: {str(e)}")
            return None

# Create a singleton service
sd_service = StableDiffusionService()
