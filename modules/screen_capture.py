#!/usr/bin/env python3
"""
Screen Capture - Ambil screenshot tanpa OpenCV
Pake PIL buat decode image
"""

import logging
import time
from typing import Optional, Tuple
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
            screenshot_bytes = self.adb.screenshot()
            
            if screenshot_bytes is None:
                logger.error("Gagal ambil screenshot")
                return None
            
            # Decode pake PIL
            img = Image.open(BytesIO(screenshot_bytes))
            img = img.convert('RGB')
            
            # Resize
            if img.width != self.width or img.height != self.height:
                img = img.resize((self.width, self.height), Image.LANCZOS)
            
            # Convert ke numpy array
            screenshot = np.array(img, dtype=np.uint8)
            
            self.last_screenshot = screenshot
            self.last_capture_time = current_time
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Capture error: {e}")
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
