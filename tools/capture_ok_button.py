#!/usr/bin/env python3
"""
Capture OK Button Template
"""

import sys
from pathlib import Path
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.adb_controller import ADBController
from modules.screen_capture import ScreenCapture
from utils.logger import setup_logger, get_logger

logger = get_logger(__name__)

def main():
    """Capture tombol OK."""
    setup_logger()
    
    print("=" * 50)
    print("Capture OK Button")
    print("=" * 50)
    
    adb = ADBController()
    if not adb.connect():
        print("Gagal connect ADB")
        return
    
    screen_capture = ScreenCapture(adb)
    
    Path("config/templates/buttons").mkdir(parents=True, exist_ok=True)
    
    print("\n1. Di game, buat dialog drop muncul (setelah monster mati)")
    print("2. Tekan Enter buat capture")
    
    input()
    
    screenshot = screen_capture.capture()
    if screenshot is None:
        print("Gagal capture")
        return
    
    # Save full screenshot
    screen_capture.save(screenshot, "drop_dialog.png")
    print("Screenshot tersimpan: data/screenshots/drop_dialog.png")
    
    # Minta region tombol OK
    print("\nTentukan posisi tombol OK:")
    print("Format: x,y,width,height")
    
    region_input = input("Region: ").strip()
    
    try:
        parts = region_input.split(",")
        x = int(parts[0])
        y = int(parts[1])
        w = int(parts[2])
        h = int(parts[3])
        
        ok_button = screenshot[y:y+h, x:x+w]
        cv2.imwrite("config/templates/buttons/ok_button.png", ok_button)
        
        print("Template OK button tersimpan!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
