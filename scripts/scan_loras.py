
#!/usr/bin/env python3
"""
Script to scan for nurse LoRAs and update the theme registry.
Run this script after adding new LoRA files to detect them automatically.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.lora_scanner import LoRAScanner

def main():
    scanner = LoRAScanner()
    
    print("Scanning for LoRA files in sd_models/loras...")
    lora_files = scanner.scan_loras()
    
    if not lora_files:
        print("No LoRA files found. Please add LoRA files to sd_models/loras/")
        return
    
    print(f"Found {len(lora_files)} potential LoRA files:")
    for file in lora_files:
        print(f"  - {file}")
    
    print("\nDetecting themes from filenames...")
    detected = scanner.auto_detect_themes()
    print(f"Detected {len(detected)} themes:")
    for theme_id, theme_data in detected.items():
        print(f"  - {theme_data['name']} ({theme_id})")
    
    print("\nUpdating theme registry...")
    new_themes = scanner.update_theme_registry()
    print(f"Added {new_themes} new themes to registry")
    
    print("\nCurrent theme registry:")
    for theme in scanner.theme_registry.get_all_themes():
        print(f"  - {theme.name} ({theme.id}): {theme.lora_file}")

if __name__ == "__main__":
    main()
