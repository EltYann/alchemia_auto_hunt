#!/usr/bin/env python3
"""
Screen Capture - Ambil screenshot game
"""

import cv2
import numpy as np
import logging
import time
from typing import Optional, Tuple

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
        self.min_interval = 0.5  # detik
    
    def capture(self) -> Optional[np.ndarray]:
        """Ambil screenshot dan convert ke numpy array."""
        current_time = time.time()
        
        # Rate limiting
        if current_time - self.last_capture_time < self.min_interval:
            return self.last_screenshot
        
        try:
            # Ambil screenshot via ADB
            screenshot_bytes = self.adb.screenshot()
            
            if screenshot_bytes is None:
                logger.error("Gagal ambil screenshot")
                return None
            
            # Decode ke numpy array
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if screenshot is None:
                logger.error("Gagal decode screenshot")
                return None
            
            # Resize kalau perlu
            if screenshot.shape[1] != self.width or screenshot.shape[0] != self.height:
                screenshot = cv2.resize(screenshot, (self.width, self.height))
            
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
            cv2.imwrite(filepath, screenshot)
            return filepath
        except Exception as e:
            logger.error(f"Save error: {e}")
            return None
