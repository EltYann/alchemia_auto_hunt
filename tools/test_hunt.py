#!/usr/bin/env python3
"""
Test Hunt - Test koneksi dan deteksi
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from modules.adb_controller import ADBController
from modules.screen_capture import ScreenCapture
from core.vision import Vision
from utils.logger import setup_logger, get_logger

logger = get_logger(__name__)

def load_config():
    """Load config dari settings.yaml."""
    with open("config/settings.yaml", 'r') as f:
        return yaml.safe_load(f)

def test_adb(config):
    """Test koneksi ADB."""
    print("\n[TEST] ADB Connection...")
    
    adb = ADBController(
        device_ip=config['adb']['device_ip'],
        port=config['adb']['port']
    )
    
    if adb.connect():
        print("  OK ADB connected")
        devices = adb.get_devices()
        print(f"  OK Devices: {devices}")
        
        width, height = adb.get_screen_size()
        print(f"  OK Screen size: {width}x{height}")
        
        return adb
    else:
        print("  FAIL ADB gagal connect")
        return None

def test_screenshot(adb, config):
    """Test screenshot."""
    print("\n[TEST] Screenshot...")
    
    screen_capture = ScreenCapture(
        adb_controller=adb,
        width=config['adb']['screen_width'],
        height=config['adb']['screen_height']
    )
    
    screenshot = screen_capture.capture()
    
    if screenshot is not None:
        print(f"  OK Screenshot berhasil: {screenshot.shape}")
        screen_capture.save(screenshot, "test.png")
        print("  OK Tersimpan di data/screenshots/test.png")
        return screenshot
    else:
        print("  FAIL Screenshot gagal")
        return None

def test_monster_detection(screenshot, config):
    """Test deteksi monster."""
    print("\n[TEST] Monster Detection...")
    
    vision = Vision(
        template_threshold=config['hunting']['template_threshold']
    )
    
    monster_dir = Path("config/templates/monsters")
    
    if not monster_dir.exists() or not list(monster_dir.glob("*.png")):
        print("  WARN Belum ada template monster")
        print("  INFO Jalankan: python tools/capture_monster.py")
        return
    
    templates_loaded = 0
    for template in monster_dir.glob("*.png"):
        name = template.stem
        if vision.load_template(str(template), f"monster_{name}"):
            templates_loaded += 1
            print(f"  OK Template loaded: {name}")
    
    if templates_loaded == 0:
        print("  FAIL Ga ada template yang ke-load")
        return
    
    for template in monster_dir.glob("*.png"):
        name = template.stem
        pos = vision.find_template(screenshot, f"monster_{name}")
        
        if pos:
            print(f"  OK Monster '{name}' ditemukan di {pos}")
        else:
            print(f"  INFO Monster '{name}' tidak terdeteksi di layar")

def main():
    """Run all tests."""
    setup_logger()
    
    print("=" * 50)
    print("Alchemia Auto Hunt - Test")
    print("=" * 50)
    
    config = load_config()
    
    adb = test_adb(config)
    if not adb:
        print("\nTest gagal di ADB")
        return
    
    screenshot = test_screenshot(adb, config)
    if screenshot is None:
        print("\nTest gagal di screenshot")
        return
    
    test_monster_detection(screenshot, config)
    
    print("\n" + "=" * 50)
    print("Test selesai!")
    print("=" * 50)

if __name__ == "__main__":
    main()
