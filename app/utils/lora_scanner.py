
import os
import re
import json
from typing import Dict, List, Optional
from app.services.theme_registry import ThemeRegistry

class LoRAScanner:
    """Utility to scan and detect LoRAs in the designated directory"""
    
    def __init__(self, lora_dir="sd_models/loras"):
        self.lora_dir = lora_dir
        self.theme_registry = ThemeRegistry()
    
    def scan_loras(self) -> List[str]:
        """Scan directory for LoRA files"""
        if not os.path.exists(self.lora_dir):
            os.makedirs(self.lora_dir, exist_ok=True)
            return []
            
        # Get all files with potential LoRA extensions
        lora_files = []
        for file in os.listdir(self.lora_dir):
            filepath = os.path.join(self.lora_dir, file)
            if os.path.isfile(filepath) and not file.startswith('.') and file != "themes_metadata.json":
                lora_files.append(file)
                
        return lora_files
    
    def extract_theme_info(self, filename: str) -> Optional[Dict]:
        """Extract potential theme information from filename"""
        # Pattern to match nurse-THEME-lora format
        pattern = r"nurse-([a-zA-Z0-9_-]+)-lora"
        match = re.match(pattern, filename)
        
        if match:
            theme_id = match.group(1).lower()
            
            # Create basic theme info
            return {
                "id": theme_id,
                "name": theme_id.replace("-", " ").replace("_", " ").title() + " Nurse",
                "description": f"Nurse theme in {theme_id.replace('-', ' ').replace('_', ' ').title()} style",
                "lora_file": filename,
                "preview_image": f"/static/theme_previews/{theme_id}.jpg"
            }
        
        return None
    
    def auto_detect_themes(self) -> Dict[str, Dict]:
        """Auto-detect themes from LoRA files"""
        lora_files = self.scan_loras()
        detected_themes = {}
        
        for file in lora_files:
            theme_info = self.extract_theme_info(file)
            if theme_info:
                detected_themes[theme_info["id"]] = theme_info
        
        return detected_themes
    
    def update_theme_registry(self) -> int:
        """Update theme registry with auto-detected themes"""
        new_themes = self.auto_detect_themes()
        count = 0
        
        for theme_id, theme_data in new_themes.items():
            # Skip if theme already exists
            if not self.theme_registry.get_theme(theme_id):
                from app.models import ThemeDetail
                
                theme_detail = ThemeDetail(
                    id=theme_id,
                    name=theme_data["name"],
                    description=theme_data["description"],
                    lora_file=theme_data["lora_file"],
                    preview_image=theme_data["preview_image"]
                )
                
                self.theme_registry.add_theme(theme_detail)
                count += 1
        
        return count

if __name__ == "__main__":
    # Example usage for command line
    scanner = LoRAScanner()
    new_themes = scanner.update_theme_registry()
    print(f"Added {new_themes} new themes to registry")
    
    # Show available themes
    for theme in scanner.theme_registry.get_all_themes():
        print(f"Theme: {theme.name} - LoRA: {theme.lora_file}")
