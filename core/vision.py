import cv2
import numpy as np
import logging
import time
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class Vision:
    """
    Computer vision untuk deteksi monster dan UI.
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
        """
        Load template image.
        """
        try:
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE if self.grayscale else cv2.IMREAD_COLOR)
            if img is not None:
                self.templates[name] = img
                logger.info(f"Template '{name}' loaded: {path}")
                return True
            logger.error(f"Gagal load template: {path}")
            return False
        except Exception as e:
            logger.error(f"Error loading template {path}: {e}")
            return False
    
    def find_template(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: Optional[float] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Cari template di screenshot.
        Return center point kalau ketemu.
        """
        if template_name not in self.templates:
            return None
        
        template = self.templates[template_name]
        thresh = threshold or self.template_threshold
        
        # Convert screenshot ke grayscale
        if self.grayscale and len(screenshot.shape) == 3:
            screen_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        else:
            screen_gray = screenshot
        
        # Template matching
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= thresh:
            h, w = template.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            self.last_detections[template_name] = {
                "position": (center_x, center_y),
                "confidence": max_val,
                "timestamp": time.time()
            }
            
            return (center_x, center_y)
        
        return None
    
    def find_all_templates(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: Optional[float] = None
    ) -> List[Tuple[int, int]]:
        """
        Cari semua kemunculan template.
        """
        if template_name not in self.templates:
            return []
        
        template = self.templates[template_name]
        thresh = threshold or self.template_threshold
        
        if self.grayscale and len(screenshot.shape) == 3:
            screen_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        else:
            screen_gray = screenshot
        
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= thresh)
        
        points = []
        h, w = template.shape
        for pt in zip(*locations[::-1]):
            cx = pt[0] + w // 2
            cy = pt[1] + h // 2
            
            # Check jarak dengan point existing
            too_close = False
            for existing in points:
                if abs(existing[0] - cx) < w // 2 and abs(existing[1] - cy) < h // 2:
                    too_close = True
                    break
            
            if not too_close:
                points.append((cx, cy))
        
        return points
    
    def find_monster(
        self,
        screenshot: np.ndarray,
        monster_templates: List[str]
    ) -> Optional[Tuple[str, Tuple[int, int]]]:
        """
        Cari monster di screenshot.
        Return (nama_monster, posisi) kalau ketemu.
        """
        for monster_name in monster_templates:
            template_key = f"monster_{monster_name}"
            pos = self.find_template(screenshot, template_key)
            
            if pos:
                return (monster_name, pos)
        
        return None
    
    def find_closest_monster(
        self,
        screenshot: np.ndarray,
        monster_templates: List[str],
        center: Tuple[int, int]
    ) -> Optional[Tuple[str, Tuple[int, int], float]]:
        """
        Cari monster terdekat dari center.
        Return (nama, posisi, jarak).
        """
        closest = None
        closest_distance = float('inf')
        
        for monster_name in monster_templates:
            template_key = f"monster_{monster_name}"
            positions = self.find_all_templates(screenshot, template_key)
            
            for pos in positions:
                dx = pos[0] - center[0]
                dy = pos[1] - center[1]
                distance = (dx**2 + dy**2) ** 0.5
                
                if distance < closest_distance:
                    closest_distance = distance
                    closest = (monster_name, pos, distance)
        
        return closest
    
    def detect_color(
        self,
        screenshot: np.ndarray,
        target_color: Tuple[int, int, int],
        tolerance: int = 40,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Deteksi warna di screenshot.
        """
        img = screenshot
        if region:
            x, y, w, h = region
            img = screenshot[y:y+h, x:x+w]
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[target_color]]), cv2.COLOR_BGR2HSV)[0][0]
        
        lower = np.array([
            max(0, target_hsv[0] - tolerance),
            max(0, target_hsv[1] - tolerance),
            max(0, target_hsv[2] - tolerance)
        ])
        upper = np.array([
            min(180, target_hsv[0] + tolerance),
            min(255, target_hsv[1] + tolerance),
            min(255, target_hsv[2] + tolerance)
        ])
        
        mask = cv2.inRange(hsv, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 50:
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
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
        """
        Check apakah HP bar visible (berarti lagi combat).
        """
        return self.detect_color(screenshot, hp_color, threshold, region) is not None
