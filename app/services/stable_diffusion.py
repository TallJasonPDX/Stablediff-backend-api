import os
import json
from io import BytesIO
from typing import Optional
import httpx
from PIL import Image
import torch
from diffusers import StableDiffusionXLTurboPipeline, AutoencoderKL
from huggingface_hub import hf_hub_download
from app.config import settings

class StableDiffusionService:
    def __init__(self):
        self.lora_mappings = settings.NURSE_LORAS
        self.model_path = "sd_models"
        self.lora_path = "sd_models/loras"
        self.pipeline = None
        # Add theme registry (assuming it's defined elsewhere)
        self.theme_registry = ThemeRegistry() # Replace with your actual theme registry instantiation

        # Ensure model directories exist
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(self.lora_path, exist_ok=True)

        # Initialize the model
        self._init_model()

    def _init_model(self):
        """Initialize SDXL Turbo model"""
        try:
            print("Loading SDXL Turbo model...")

            # Download model if not already downloaded
            if not os.path.exists(f"{self.model_path}/sdxl-turbo"):
                print("Downloading SDXL Turbo from Hugging Face...")
                # Use Hugging Face pipeline with GPU acceleration if available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.pipeline = StableDiffusionXLTurboPipeline.from_pretrained(
                    "stabilityai/sdxl-turbo", 
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    variant="fp16" if device == "cuda" else None,
                )
                self.pipeline.save_pretrained(f"{self.model_path}/sdxl-turbo")
                print("SDXL Turbo downloaded successfully")
            else:
                # Load from local path
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.pipeline = StableDiffusionXLTurboPipeline.from_pretrained(
                    f"{self.model_path}/sdxl-turbo",
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                )

            # Move to device
            self.pipeline = self.pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
            print(f"SDXL Turbo loaded on {self.pipeline.device}")

            # Enable memory optimization for CPU
            if not torch.cuda.is_available():
                self.pipeline.enable_model_cpu_offload()

        except Exception as e:
            print(f"Error initializing SDXL Turbo: {str(e)}")
            self.pipeline = None

    def _ensure_lora_downloaded(self, theme: str) -> bool:
        """Ensure the LoRA for the theme is downloaded"""
        theme_detail = self.theme_registry.get_theme(theme)
        if not theme_detail:
            return False
        lora_file = theme_detail.lora_file
        lora_path = f"{self.lora_path}/{lora_file}"

        # Check if LoRA already exists
        if os.path.exists(lora_path):
            return True

        # For demonstration purposes, we'll assume LoRAs will be manually downloaded
        # In a real implementation, you'd download from Hugging Face or another source
        print(f"LoRA {lora_file} not found. Please download it to {lora_path}")
        return os.path.exists(lora_path)

    async def process_image(self, 
                           image_data: bytes, 
                           theme: str,
                           strength: float = 0.75,
                           guidance_scale: float = 1.0,  # SDXL Turbo works well with lower guidance
                           steps: int = 4) -> Optional[bytes]:  # SDXL Turbo needs fewer steps
        """Process an image using SDXL Turbo with a nurse theme LoRA"""
        theme_detail = self.theme_registry.get_theme(theme)
        if not theme_detail:
            raise ValueError(f"Theme {theme} not found in registry")

        if not self.pipeline:
            self._init_model()
            if not self.pipeline:
                raise ValueError("Failed to initialize Stable Diffusion model")

        # Ensure the LoRA is available
        if not self._ensure_lora_downloaded(theme):
            raise ValueError(f"LoRA for theme {theme} not available")

        lora_file = theme_detail.lora_file

        try:
            # Prepare the image
            img = Image.open(BytesIO(image_data))
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if necessary
            if img.width > 1024 or img.height > 1024:
                img.thumbnail((1024, 1024))

            # Load LoRA
            self.pipeline.load_lora_weights(f"{self.lora_path}/{lora_file}")

            # Use theme name in prompt for better results
            theme_name = theme_detail.name
            prompt = f"nurse theme, professional medical staff, {theme_name} style, high quality"
            negative_prompt = "bad anatomy, bad proportions, blurry, low quality"

            output = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=img,
                strength=strength,
                guidance_scale=guidance_scale,
                num_inference_steps=steps,
            ).images[0]

            # Convert to bytes
            output_bytes = BytesIO()
            output.save(output_bytes, format="PNG")
            output_bytes.seek(0)

            # Unload LoRA
            self.pipeline.unload_lora_weights()

            return output_bytes

        except Exception as e:
            print(f"Error processing image with SDXL Turbo: {str(e)}")
            return None

# Placeholder for ThemeRegistry -  replace with your actual implementation
class ThemeRegistry:
    def __init__(self):
        #In a real application, this would load from a database or config file.
        self.themes = {
            "theme1": ThemeDetail("theme1", "lora1.safetensors"),
            "theme2": ThemeDetail("Theme 2", "lora2.safetensors"),
        }

    def get_theme(self, theme_name):
        return self.themes.get(theme_name)

class ThemeDetail:
    def __init__(self, name, lora_file):
        self.name = name
        self.lora_file = lora_file

# Create a singleton service
sd_service = StableDiffusionService()