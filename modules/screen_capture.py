
#!/usr/bin/env python3
"""
Screen Capture - Ambil screenshot dari device
Versi tanpa OpenCV, pake PIL
"""

import logging
import time
import subprocess
from typing import Optional
from io import BytesIO

import numpy as np
from PIL import Image

from modules.adb_controller import ADBController

logger = logging.getLogger(__name__)

class ScreenCapture:
    """Capture screenshot dari HP via ADB."""
    
    def __init__(
        self,
        adb_controller: ADBController,
        width: int = 1080,
        height: int = 2400
    ):
        self.adb = adb_controller
        self.width = width
        self.height = height
        self.last_screenshot = None
        self.last_capture_time = 0
        self.min_interval = 0.5
    
    def capture(self) -> Optional[np.ndarray]:
        """Ambil screenshot dan convert ke numpy array."""
        current_time = time.time()
        
        if current_time - self.last_capture_time < self.min_interval:
            return self.last_screenshot
        
        try:
            # Cara 1: exec-out screencap langsung
            screenshot_bytes = self._capture_direct()
            
            if screenshot_bytes is None:
                # Cara 2: screencap ke file terus pull
                screenshot_bytes = self._capture_via_file()
            
            if screenshot_bytes is None:
                logger.error("Semua metode screenshot gagal")
                return None
            
            # Decode pake PIL
            img = Image.open(BytesIO(screenshot_bytes))
            img = img.convert('RGB')
            
            # Resize
            if img.width != self.width or img.height != self.height:
                img = img.resize((self.width, self.height), Image.LANCZOS)
            
            # Convert ke numpy
            screenshot = np.array(img, dtype=np.uint8)
            
            self.last_screenshot = screenshot
            self.last_capture_time = current_time
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return None
    
    def _capture_direct(self) -> Optional[bytes]:
        """Capture langsung via exec-out."""
        try:
            device_id = self.adb.device_id
            
            cmd = ["adb"]
            if device_id:
                cmd.extend(["-s", device_id])
            cmd.extend(["exec-out", "screencap", "-p"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=15
            )
            
            if result.returncode == 0 and len(result.stdout) > 0:
                logger.debug(f"Screenshot direct: {len(result.stdout)} bytes")
                return result.stdout
            
            logger.warning(f"Screenshot direct gagal: {result.stderr}")
            return None
            
        except Exception as e:
            logger.warning(f"Screenshot direct error: {e}")
            return None
    
    def _capture_via_file(self) -> Optional[bytes]:
        """Capture via file di device terus pull."""
        try:
            device_id = self.adb.device_id
            
            # Screenshot ke file di device
            cmd1 = ["adb"]
            if device_id:
                cmd1.extend(["-s", device_id])
            cmd1.extend(["shell", "screencap", "-p", "/sdcard/screen.png"])
            
            result1 = subprocess.run(cmd1, capture_output=True, timeout=15)
            
            if result1.returncode != 0:
                logger.warning(f"Screencap ke file gagal: {result1.stderr}")
                return None
            
            # Pull file
            cmd2 = ["adb"]
            if device_id:
                cmd2.extend(["-s", device_id])
            cmd2.extend(["exec-out", "cat", "/sdcard/screen.png"])
            
            result2 = subprocess.run(cmd2, capture_output=True, timeout=15)
            
            if result2.returncode == 0 and len(result2.stdout) > 0:
                logger.debug(f"Screenshot via file: {len(result2.stdout)} bytes")
                return result2.stdout
            
            logger.warning("Cat file gagal")
            return None
            
        except Exception as e:
            logger.warning(f"Screenshot via file error: {e}")
            return None
    
    def save(self, screenshot: np.ndarray, filename: str) -> Optional[str]:
        """Simpan screenshot ke file."""
        try:
            import os
            os.makedirs("data/screenshots", exist_ok=True)
            
            filepath = f"data/screenshots/{filename}"
            img = Image.fromarray(screenshot)
            img.save(filepath)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            return None
EOF
