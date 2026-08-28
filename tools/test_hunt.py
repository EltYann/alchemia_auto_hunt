#!/usr/bin/env python3
"""
Test Hunt - Test koneksi dan deteksi
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.adb_controller import ADBController
from modules.screen_capture import ScreenCapture
from core.vision import Vision
from utils.logger import setup_logger, get_logger

logger = get_logger(__name__)

def test_adb():
    """Test koneksi ADB."""
    print("\n[TEST] ADB Connection...")
    adb = ADBController()
    
    if adb.connect():
        print("  ✓ ADB connected")
        devices = adb.get_devices()
        print(f"  ✓ Devices: {devices}")
        
        width, height = adb.get_screen_size()
        print(f"  ✓ Screen size: {width}x{height}")
        
        return adb
    else:
        print("  ✗ ADB gagal connect")
        return None

def test_screenshot(adb):
    """Test screenshot."""
    print("\n[TEST] Screenshot...")
    screen_capture = ScreenCapture(adb)
    screenshot = screen_capture.capture()
    
    if screenshot is not None:
        print(f"  ✓ Screenshot berhasil: {screenshot.shape}")
        screen_capture.save(screenshot, "test.png")
        print("  ✓ Tersimpan di data/screenshots/test.png")
        return screenshot
    else:
        print("  ✗ Screenshot gagal")
        return None

def test_monster_detection(screenshot):
    """Test deteksi monster."""
    print("\n[TEST] Monster Detection...")
    vision = Vision()
    
    # Load templates
    from pathlib import Path
    monster_dir = Path("config/templates/monsters")
    
    if not monster_dir.exists() or not list(monster_dir.glob("*.png")):
        print("  ! Belum ada template monster")
        print("  ! Jalankan: python tools/capture_monster.py")
        return
    
    for template in monster_dir.glob("*.png"):
        name = template.stem
        vision.load_template(str(template), f"monster_{name}")
        print(f"  ✓ Template loaded: {name}")
    
    # Cari monster
    center = (screenshot.shape[1] // 2, screenshot.shape[0] // 2)
    
    for name in [t.stem for t in monster_dir.glob("*.png")]:
        pos = vision.find_template(screenshot, f"monster_{name}")
        if pos:
            print(f"  ✓ Monster '{name}' ditemukan di {pos}")
        else:
            print(f"  - Monster '{name}' tidak terdeteksi")

def main():
    """Run all tests."""
    setup_logger()
    
    print("=" * 50)
    print("Alchemia Auto Hunt - Test")
    print("=" * 50)
    
    adb = test_adb()
    if not adb:
        print("\nTest gagal di ADB")
        return
    
    screenshot = test_screenshot(adb)
    if screenshot is None:
        print("\nTest gagal di screenshot")
        return
    
    test_monster_detection(screenshot)
    
    print("\n" + "=" * 50)
    print("Test selesai!")
    print("=" * 50)

if __name__ == "__main__":
    main()
