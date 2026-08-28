#!/usr/bin/env python3
"""
Input Controller - Tap dan swipe ke game
"""

import logging
import time
import random
from typing import Tuple, Optional

from modules.adb_controller import ADBController
from utils.anti_detection import AntiDetection

logger = logging.getLogger(__name__)

class InputController:
    """Controller input buat tap dan swipe."""
    
    def __init__(
        self,
        adb_controller: ADBController,
        screen_width: int = 1080,
        screen_height: int = 2400,
        anti_detection: Optional[AntiDetection] = None
    ):
        self.adb = adb_controller
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.anti_detection = anti_detection
    
    def tap(self, x: int, y: int) -> bool:
        """Tap di koordinat dengan jitter."""
        if self.anti_detection:
            x, y = self.anti_detection.add_jitter(x, y)
            self.anti_detection.random_delay()
        
        logger.debug(f"Tap ({x}, {y})")
        return self.adb.tap(x, y)
    
    def swipe(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        duration: int = 300
    ) -> bool:
        """Swipe dari start ke end."""
        x1, y1 = start
        x2, y2 = end
        
        if self.anti_detection:
            x1, y1 = self.anti_detection.add_jitter(x1, y1)
            x2, y2 = self.anti_detection.add_jitter(x2, y2)
            duration = self.anti_detection.randomize_duration(duration)
        
        logger.debug(f"Swipe ({x1},{y1}) -> ({x2},{y2})")
        return self.adb.swipe(x1, y1, x2, y2, duration)
    
    def press_back(self) -> bool:
        """Tekan back."""
        if self.anti_detection:
            self.anti_detection.random_delay()
        return self.adb.press_back()
