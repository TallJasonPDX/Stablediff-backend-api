
import os
import json
from typing import Dict, List, Optional
from app.config import settings
from app.models import ThemeDetail

class ThemeRegistry:
    """Service to manage theme LoRAs and their metadata"""
    
    def __init__(self):
        self.lora_dir = "sd_models/loras"
        self.themes_metadata_path = os.path.join(self.lora_dir, "themes_metadata.json")
        self.themes: Dict[str, ThemeDetail] = {}
        self._load_themes()
    
    def _load_themes(self):
        """Load theme metadata from JSON file or initialize with defaults"""
        os.makedirs(self.lora_dir, exist_ok=True)
        
        # Check if metadata file exists
        if os.path.exists(self.themes_metadata_path):
            try:
                with open(self.themes_metadata_path, 'r') as f:
                    themes_data = json.load(f)
                    
                for theme_id, data in themes_data.items():
                    self.themes[theme_id] = ThemeDetail(
                        id=theme_id,
                        name=data.get('name', theme_id),
                        description=data.get('description', ''),
                        lora_file=data.get('lora_file', f"nurse-{theme_id}-lora"),
                        preview_image=data.get('preview_image', '')
                    )
                    
            except Exception as e:
                print(f"Error loading themes metadata: {str(e)}")
                self._initialize_default_themes()
        else:
            self._initialize_default_themes()
            self._save_themes()
    
    def _initialize_default_themes(self):
        """Initialize with default themes"""
        default_themes = {
            "classic": {
                "name": "Classic Nurse",
                "description": "Traditional nursing attire with a classic, professional look",
                "lora_file": "nurse-classic-lora",
                "preview_image": "/static/theme_previews/classic.jpg"
            },
            "modern": {
                "name": "Modern Healthcare",
                "description": "Contemporary medical professional style with modern scrubs",
                "lora_file": "nurse-modern-lora",
                "preview_image": "/static/theme_previews/modern.jpg"
            },
            "vintage": {
                "name": "Vintage Nurse",
                "description": "Retro nursing style inspired by mid-20th century healthcare",
                "lora_file": "nurse-vintage-lora",
                "preview_image": "/static/theme_previews/vintage.jpg"
            },
            "anime": {
                "name": "Anime Nurse",
                "description": "Stylized anime-inspired nurse character design",
                "lora_file": "nurse-anime-lora",
                "preview_image": "/static/theme_previews/anime.jpg"
            },
            "future": {
                "name": "Future Medical",
                "description": "Futuristic healthcare professional with advanced tech elements",
                "lora_file": "nurse-future-lora",
                "preview_image": "/static/theme_previews/future.jpg"
            }
        }
        
        for theme_id, data in default_themes.items():
            self.themes[theme_id] = ThemeDetail(
                id=theme_id,
                name=data["name"],
                description=data["description"],
                lora_file=data["lora_file"],
                preview_image=data["preview_image"]
            )
    
    def _save_themes(self):
        """Save theme metadata to JSON file"""
        themes_data = {}
        for theme_id, theme in self.themes.items():
            themes_data[theme_id] = {
                "name": theme.name,
                "description": theme.description,
                "lora_file": theme.lora_file,
                "preview_image": theme.preview_image
            }
            
        with open(self.themes_metadata_path, 'w') as f:
            json.dump(themes_data, f, indent=2)
    
    def get_all_themes(self) -> List[ThemeDetail]:
        """Get all available themes"""
        return list(self.themes.values())
    
    def get_theme(self, theme_id: str) -> Optional[ThemeDetail]:
        """Get a specific theme by ID"""
        return self.themes.get(theme_id)
    
    def detect_loras(self) -> List[str]:
        """Scan the lora directory and detect available LoRAs"""
        available_loras = []
        
        for filename in os.listdir(self.lora_dir):
            # Skip metadata file and README
            if filename in ["themes_metadata.json", "README.md"]:
                continue
                
            # Check if the file is present and add to available list
            if os.path.isfile(os.path.join(self.lora_dir, filename)):
                available_loras.append(filename)
        
        return available_loras
    
    def get_lora_availability(self) -> Dict[str, bool]:
        """Check which theme LoRAs are available on disk"""
        available_files = self.detect_loras()
        availability = {}
        
        for theme_id, theme in self.themes.items():
            availability[theme_id] = theme.lora_file in available_files
            
        return availability
    
    def add_theme(self, theme_detail: ThemeDetail) -> bool:
        """Add or update a theme in the registry"""
        self.themes[theme_detail.id] = theme_detail
        self._save_themes()
        return True
