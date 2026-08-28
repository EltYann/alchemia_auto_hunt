#!/usr/bin/env python3
"""
Capture Monster Template - Ambil gambar monster buat template
"""

import sys
import time
from pathlib import Path
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.adb_controller import ADBController
from modules.screen_capture import ScreenCapture
from utils.logger import setup_logger, get_logger

logger = get_logger(__name__)

def main():
    """Capture template monster."""
    setup_logger()
    
    print("=" * 50)
    print("Capture Monster Template")
    print("=" * 50)
    
    # Connect ADB
    adb = ADBController()
    if not adb.connect():
        print("Gagal connect ADB")
        return
    
    screen_capture = ScreenCapture(adb)
    
    # Buat folder
    Path("config/templates/monsters").mkdir(parents=True, exist_ok=True)
    
    while True:
        print("\n1. Buka game, posisikan monster di layar")
        print("2. Tekan Enter buat capture")
        print("3. Ketik 'done' buat selesai")
        
        choice = input("\nPilihan: ").strip()
        
        if choice.lower() == "done":
            break
        
        # Capture screenshot
        screenshot = screen_capture.capture()
        if screenshot is None:
            print("Gagal capture")
            continue
        
        # Save full screenshot dulu
        screen_capture.save(screenshot, "full_screen.png")
        print("Full screenshot tersimpan: data/screenshots/full_screen.png")
        
        # Minta nama monster
        monster_name = input("Nama monster (contoh: slime): ").strip().lower()
        if not monster_name:
            print("Nama kosong, skip")
            continue
        
        # Minta crop region
        print("\nSekarang tentukan area monster:")
        print("Format: x,y,width,height")
        print("Contoh: 400,800,200,200 (x=400, y=800, lebar=200, tinggi=200)")
        
        region_input = input("Region: ").strip()
        
        try:
            parts = region_input.split(",")
            x = int(parts[0])
            y = int(parts[1])
            w = int(parts[2])
            h = int(parts[3])
            
            # Crop monster
            monster_img = screenshot[y:y+h, x:x+w]
            
            # Save template
            template_path = f"config/templates/monsters/{monster_name}.png"
            cv2.imwrite(template_path, monster_img)
            
            print(f"Template '{monster_name}' tersimpan: {template_path}")
            
        except Exception as e:
            print(f"Error crop: {e}")
            print("Coba format: x,y,width,height")
    
    print("\nCapture selesai!")

if __name__ == "__main__":
    main()
