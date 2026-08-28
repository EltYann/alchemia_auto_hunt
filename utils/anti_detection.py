#!/usr/bin/env python3
"""
Anti-Detection Module - Human-like behavior
"""

import random
import time
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class AntiDetection:
    """Sistem anti-detection untuk buat input terlihat natural."""
    
    def __init__(
        self,
        random_delay_min: float = 0.2,
        random_delay_max: float = 1.2,
        click_variance: int = 8
    ):
        self.random_delay_min = random_delay_min
        self.random_delay_max = random_delay_max
        self.click_variance = click_variance
    
    def random_delay(self):
        """Jeda random antara actions."""
        delay = random.uniform(self.random_delay_min, self.random_delay_max)
        time.sleep(delay)
    
    def add_jitter(
        self,
        x: int,
        y: int,
        variance: Optional[int] = None
    ) -> Tuple[int, int]:
        """Tambah jitter ke koordinat tap."""
        var = variance or self.click_variance
        jx = random.randint(-var, var)
        jy = random.randint(-var, var)
        return (x + jx, y + jy)
    
    def randomize_duration(
        self,
        base: int,
        variance: int = 100
    ) -> int:
        """Randomize durasi swipe."""
        return max(100, base + random.randint(-variance, variance))
