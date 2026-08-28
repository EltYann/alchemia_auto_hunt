#!/usr/bin/env python3
"""
Capture Monster Template - Ambil gambar monster buat template
Versi tanpa OpenCV (PIL only)
"""

import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.adb_controller import ADBController
from modules.screen_capture import ScreenCapture
from utils.logger import setup_logger, get_logger
from PIL import Image
import numpy as np

logger = get_logger(__name__)

def load_config():
    """Load config."""
    with open("config/settings.yaml", 'r') as f:
        return yaml.safe_load(f)

def main():
    """Capture template monster."""
    setup_logger()
    
    print("=" * 50)
    print("Capture Monster Template")
    print("=" * 50)
    
    config = load_config()
    
    # Connect ADB
    adb = ADBController(
        device_ip=config['adb']['device_ip'],
        port=config['adb']['port']
    )
    
    if not adb.connect():
        print("Gagal connect ADB")
        return
    
    screen_capture = ScreenCapture(
        adb_controller=adb,
        width=config['adb']['screen_width'],
        height=config['adb']['screen_height']
    )
    
    # Buat folder
    monster_dir = Path("config/templates/monsters")
    if not monster_dir.exists():
        monster_dir.mkdir(parents=True)
    
    print("\n=== Cara Pakai ===")
    print("1. Buka game Alchemia Story")
    print("2. Posisikan monster di layar")
    print("3. Tekan Enter buat screenshot")
    print("4. Tentukan area monster (x,y,width,height)")
    print("5. Ketik 'done' buat selesai")
    
    while True:
        print("\n" + "-" * 30)
        choice = input("Tekan Enter buat capture, atau ketik 'done': ").strip()
        
        if choice.lower() == "done":
            break
        
        # Capture screenshot
        screenshot = screen_capture.capture()
        if screenshot is None:
            print("Gagal capture")
            continue
        
        # Save full screenshot
        screen_capture.save(screenshot, "full_screen.png")
        print("Full screenshot: data/screenshots/full_screen.png")
        print(f"Screenshot size: {screenshot.shape}")
        
        # Minta nama monster
        monster_name = input("Nama monster (contoh: slime): ").strip().lower()
        if not monster_name:
            print("Nama kosong, skip")
            continue
        
        # Minta crop region
        print("\nTentukan area monster.")
        print("Format: x,y,width,height")
        print("x = jarak dari kiri (pixel)")
        print("y = jarak dari atas (pixel)")
        print("width = lebar area")
        print("height = tinggi area")
        print("Contoh: 500,300,200,200")
        
        region_input = input("Region: ").strip()
        
        try:
            parts = region_input.split(",")
            x = int(parts[0])
            y = int(parts[1])
            w = int(parts[2])
            h = int(parts[3])
            
            # Cek bounds
            if x < 0 or y < 0 or x + w > screenshot.shape[1] or y + h > screenshot.shape[0]:
                print(f"Error: Region di luar screenshot. Max: {screenshot.shape[1]}x{screenshot.shape[0]}")
                continue
            
            # Crop monster
            monster_img = screenshot[y:y+h, x:x+w]
            
            # Save template
            template_path = f"config/templates/monsters/{monster_name}.png"
            img = Image.fromarray(monster_img)
            img.save(template_path)
            
            print(f"Template '{monster_name}' tersimpan: {template_path}")
            print(f"Ukuran template: {monster_img.shape}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nCapture selesai!")

if __name__ == "__main__":
    main()
