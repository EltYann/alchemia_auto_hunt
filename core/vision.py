#!/usr/bin/env python3
"""
Vision Module - Deteksi monster tanpa OpenCV
Pake numpy + PIL buat template matching
"""

import logging
import time
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class Vision:
    """
    Computer vision tanpa OpenCV.
    Pake numpy correlation buat template matching.
    """
    
    def __init__(
        self,
        template_threshold: float = 0.65,
        grayscale: bool = True
    ):
        self.template_threshold = template_threshold
        self.grayscale = grayscale
        self.templates = {}
        self.last_detections = {}
    
    def load_template(self, path: str, name: str) -> bool:
        """Load template image dari file."""
        try:
            img = Image.open(path)
            if self.grayscale:
                img = img.convert('L')
            
            template = np.array(img, dtype=np.float32)
            template = (template - template.mean()) / (template.std() + 1e-8)
            
            self.templates[name] = template
            logger.info(f"Template '{name}' loaded: {path} ({template.shape})")
            return True
            
        except Exception as e:
            logger.error(f"Error loading template {path}: {e}")
            return False
    
    def _prepare_image(self, screenshot: np.ndarray) -> np.ndarray:
        """Convert screenshot ke grayscale float32."""
        if len(screenshot.shape) == 3:
            # Convert ke grayscale pake weighted average
            gray = (0.299 * screenshot[:,:,0] + 
                    0.587 * screenshot[:,:,1] + 
                    0.114 * screenshot[:,:,2])
        else:
            gray = screenshot
        
        gray = gray.astype(np.float32)
        gray = (gray - gray.mean()) / (gray.std() + 1e-8)
        
        return gray
    
    def _template_match(
        self,
        image: np.ndarray,
        template: np.ndarray
    ) -> Tuple[float, Tuple[int, int]]:
        """
        Template matching pake numpy.
        Return (confidence, position).
        """
        img_h, img_w = image.shape
        tpl_h, tpl_w = template.shape
        
        if img_h < tpl_h or img_w < tpl_w:
            return 0.0, (0, 0)
        
        best_score = -float('inf')
        best_pos = (0, 0)
        
        # Sliding window
        for y in range(0, img_h - tpl_h + 1, 5):  # Step 5 buat speed
            for x in range(0, img_w - tpl_w + 1, 5):
                roi = image[y:y+tpl_h, x:x+tpl_w]
                
                # Normalized cross-correlation
                score = np.mean(roi * template)
                
                if score > best_score:
                    best_score = score
                    best_pos = (x, y)
        
        return best_score, best_pos
    
    def find_template(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: Optional[float] = None
    ) -> Optional[Tuple[int, int]]:
        """Cari template di screenshot."""
        if template_name not in self.templates:
            return None
        
        template = self.templates[template_name]
        thresh = threshold or self.template_threshold
        
        # Prepare image
        image = self._prepare_image(screenshot)
        
        # Template matching
        score, pos = self._template_match(image, template)
        
        if score >= thresh:
            tpl_h, tpl_w = template.shape
            center_x = pos[0] + tpl_w // 2
            center_y = pos[1] + tpl_h // 2
            
            self.last_detections[template_name] = {
                "position": (center_x, center_y),
                "confidence": score,
                "timestamp": time.time()
            }
            
            return (center_x, center_y)
        
        return None
    
    def find_monster(
        self,
        screenshot: np.ndarray,
        monster_templates: List[str]
    ) -> Optional[Tuple[str, Tuple[int, int]]]:
        """Cari monster di screenshot."""
        best_score = -float('inf')
        best_result = None
        
        for monster_name in monster_templates:
            template_key = f"monster_{monster_name}"
            
            if template_key not in self.templates:
                continue
            
            pos = self.find_template(screenshot, template_key)
            
            if pos:
                confidence = self.last_detections[template_key]["confidence"]
                
                if confidence > best_score:
                    best_score = confidence
                    best_result = (monster_name, pos)
        
        return best_result
    
    def find_closest_monster(
        self,
        screenshot: np.ndarray,
        monster_templates: List[str],
        center: Tuple[int, int]
    ) -> Optional[Tuple[str, Tuple[int, int], float]]:
        """Cari monster terdekat dari center."""
        best_result = None
        best_distance = float('inf')
        
        for monster_name in monster_templates:
            template_key = f"monster_{monster_name}"
            
            if template_key not in self.templates:
                continue
            
            pos = self.find_template(screenshot, template_key)
            
            if pos:
                dx = pos[0] - center[0]
                dy = pos[1] - center[1]
                distance = (dx**2 + dy**2) ** 0.5
                
                if distance < best_distance:
                    best_distance = distance
                    confidence = self.last_detections[template_key]["confidence"]
                    best_result = (monster_name, pos, confidence)
        
        return best_result
    
    def detect_color(
        self,
        screenshot: np.ndarray,
        target_color: Tuple[int, int, int],
        tolerance: int = 40,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[int, int]]:
        """Deteksi warna di screenshot."""
        img = screenshot
        
        if region:
            x, y, w, h = region
            if x + w > img.shape[1] or y + h > img.shape[0]:
                return None
            img = img[y:y+h, x:x+w]
        
        if len(img.shape) == 3:
            r, g, b = target_color
            
            mask = (
                (abs(img[:,:,0].astype(int) - b) < tolerance) &
                (abs(img[:,:,1].astype(int) - g) < tolerance) &
                (abs(img[:,:,2].astype(int) - r) < tolerance)
            )
        else:
            return None
        
        if mask.any():
            # Cari center dari region yang match
            indices = np.where(mask)
            cy = int(np.mean(indices[0]))
            cx = int(np.mean(indices[1]))
            
            if region:
                cx += region[0]
                cy += region[1]
            
            return (cx, cy)
        
        return None
    
    def check_hp_bar(
        self,
        screenshot: np.ndarray,
        region: Tuple[int, int, int, int],
        hp_color: Tuple[int, int, int],
        threshold: int = 50
    ) -> bool:
        """Check HP bar visible (berarti combat)."""
        return self.detect_color(screenshot, hp_color, threshold, region) is not None
    
    def detect_brightness(
        self,
        screenshot: np.ndarray,
        region: Tuple[int, int, int, int],
        threshold: float = 100
    ) -> bool:
        """Deteksi brightness di region tertentu."""
        x, y, w, h = region
        
        if x + w > screenshot.shape[1] or y + h > screenshot.shape[0]:
            return False
        
        roi = screenshot[y:y+h, x:x+w]
        
        if len(roi.shape) == 3:
            brightness = np.mean(roi)
        else:
            brightness = np.mean(roi)
        
        return brightness > threshold
