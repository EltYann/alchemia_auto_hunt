#!/usr/bin/env python3
"""
Auto Hunter - Main hunting logic
Versi tanpa OpenCV (numpy + PIL only)
"""

import time
import logging
import random
import gc
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

import numpy as np
import yaml

from core.vision import Vision
from core.state_machine import StateMachine, State
from modules.adb_controller import ADBController
from modules.screen_capture import ScreenCapture
from modules.input_controller import InputController
from utils.anti_detection import AntiDetection
from utils.logger import get_logger

logger = get_logger(__name__)

class Hunter:
    """
    Auto hunter untuk Alchemia Story.
    
    Flow:
    1. Screenshot layar
    2. Check drop dialog → tap OK
    3. Check combat mode → tunggu
    4. Cari monster → approach
    5. Ulangi
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.running = False
        self.in_combat = False
        self.combat_start_time = 0
        self.kill_count = 0
        self.error_count = 0
        self.search_count = 0
        
        # ADB Controller
        self.adb = ADBController(
            device_ip=self.config['adb']['device_ip'],
            port=self.config['adb']['port']
        )
        
        # Screen capture
        self.screen_capture = ScreenCapture(
            adb_controller=self.adb,
            width=self.config['adb']['screen_width'],
            height=self.config['adb']['screen_height']
        )
        
        # Anti detection
        self.anti_detection = AntiDetection(
            random_delay_min=self.config['anti_detection']['random_delay_min'],
            random_delay_max=self.config['anti_detection']['random_delay_max'],
            click_variance=self.config['anti_detection']['click_variance']
        )
        
        # Input controller
        self.input = InputController(
            adb_controller=self.adb,
            screen_width=self.config['adb']['screen_width'],
            screen_height=self.config['adb']['screen_height'],
            anti_detection=self.anti_detection
        )
        
        # Vision
        self.vision = Vision(
            template_threshold=self.config['hunting']['template_threshold']
        )
        
        # State machine
        self.state_machine = StateMachine()
        
        # Load templates
        self._load_templates()
        
        # Stats
        self.stats = {
            "start_time": None,
            "monsters_killed": 0,
            "screenshots": 0,
            "actions": 0,
            "errors": 0,
            "combat_duration": []
        }
        
        logger.info("Hunter initialized")
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load YAML config."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_templates(self):
        """Load semua template monster dan button."""
        template_dir = Path("config/templates")
        
        # Load monster templates
        monster_dir = template_dir / "monsters"
        monster_dir.mkdir(parents=True, exist_ok=True)
        
        for monster_name in self.config['hunting']['monster_templates']:
            path = monster_dir / f"{monster_name}.png"
            if path.exists():
                self.vision.load_template(str(path), f"monster_{monster_name}")
                logger.info(f"Template monster '{monster_name}' loaded")
            else:
                logger.warning(f"Template monster '{monster_name}' belum ada di {path}")
                logger.warning(f"Jalankan: python tools/capture_monster.py")
        
        # Load OK button template
        button_dir = template_dir / "buttons"
        button_dir.mkdir(parents=True, exist_ok=True)
        
        ok_template = self.config['drop']['ok_button_template']
        ok_path = button_dir / f"{ok_template}.png"
        if ok_path.exists():
            self.vision.load_template(str(ok_path), f"button_{ok_template}")
            logger.info(f"Template OK button loaded")
        else:
            logger.warning(f"Template OK button belum ada di {ok_path}")
            logger.warning(f"Jalankan: python tools/capture_ok_button.py")
    
    def start(self):
        """Start hunter."""
        self.running = True
        self.stats["start_time"] = time.time()
        
        logger.info("=" * 50)
        logger.info("Auto Hunter Started")
        logger.info("=" * 50)
        
        # Connect ADB
        if not self.adb.connect():
            logger.error("Gagal connect ADB")
            self.stop()
            return
        
        logger.info(f"Connected ke {self.config['adb']['device_ip']}:{self.config['adb']['port']}")
        
        # Main loop
        self._main_loop()
    
    def stop(self):
        """Stop hunter."""
        self.running = False
        
        elapsed = 0
        if self.stats["start_time"]:
            elapsed = time.time() - self.stats["start_time"]
        
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        logger.info("=" * 50)
        logger.info("Auto Hunter Stopped")
        logger.info(f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        logger.info(f"Monster dibunuh: {self.kill_count}")
        logger.info(f"Screenshots: {self.stats['screenshots']}")
        logger.info(f"Actions: {self.stats['actions']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 50)
    
    def _main_loop(self):
        """Main hunting loop."""
        logger.info("Main loop dimulai")
        
        while self.running:
            try:
                # STEP 1: Screenshot
                screenshot = self.screen_capture.capture()
                self.stats["screenshots"] += 1
                
                if screenshot is None:
                    self.error_count += 1
                    if self.error_count >= 10:
                        logger.error("Terlalu banyak error screenshot")
                        self.stop()
                        break
                    time.sleep(2)
                    continue
                
                self.error_count = 0
                
                # STEP 2: Check drop dialog
                if self._check_drop_dialog(screenshot):
                    logger.info("Drop terdeteksi, tap OK")
                    self._tap_ok(screenshot)
                    self.kill_count += 1
                    self.stats["monsters_killed"] += 1
                    time.sleep(self.config['drop']['ok_delay'])
                    continue
                
                # STEP 3: Check combat mode
                if self._check_combat(screenshot):
                    if not self.in_combat:
                        logger.info("Masuk combat mode")
                        self.in_combat = True
                        self.combat_start_time = time.time()
                    
                    # Check kalau combat kelamaan
                    combat_duration = time.time() - self.combat_start_time
                    max_combat = self.config['combat']['max_combat_time']
                    
                    if combat_duration > max_combat:
                        logger.warning(f"Combat terlalu lama ({combat_duration:.0f}s), coba exit")
                        self._force_exit_combat()
                        self.in_combat = False
                    
                    time.sleep(0.5)
                    continue
                
                # STEP 4: Kalau baru keluar combat
                if self.in_combat:
                    combat_duration = time.time() - self.combat_start_time
                    logger.info(f"Combat selesai ({combat_duration:.1f}s)")
                    self.stats["combat_duration"].append(combat_duration)
                    self.in_combat = False
                    time.sleep(0.5)
                    continue
                
                # STEP 5: Cari monster
                monster = self._find_monster(screenshot)
                
                if monster:
                    monster_name, monster_pos = monster
                    self.search_count = 0
                    logger.debug(f"Monster '{monster_name}' di {monster_pos}")
                    
                    # Deketin monster
                    self._approach_monster(monster_pos)
                    self.stats["actions"] += 1
                    time.sleep(0.3)
                else:
                    # Monster ga keliatan
                    self.search_count += 1
                    
                    if self.search_count >= self.config['hunting']['max_scan_attempts']:
                        logger.debug("Monster ga ketemu, cari dengan gerak")
                        self._search_move()
                        self.search_count = 0
                    
                    time.sleep(0.5)
                
                # GC berkala
                if self.stats["screenshots"] % 200 == 0:
                    gc.collect()
                    logger.debug(f"GC done. Stats: {self.stats}")
                
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                logger.error(f"Error di main loop: {e}")
                self.error_count += 1
                if self.error_count >= 10:
                    logger.error("Terlalu banyak error, stop")
                    self.stop()
                    break
                time.sleep(1)
    
    def _check_drop_dialog(self, screenshot: np.ndarray) -> bool:
        """
        Check apakah ada dialog drop.
        Cek template OK button atau brightness di region.
        """
        # Cek template OK button
        ok_template = self.config['drop']['ok_button_template']
        ok_pos = self.vision.find_template(screenshot, f"button_{ok_template}")
        
        if ok_pos:
            return True
        
        # Fallback: cek brightness di region OK button
        region = tuple(self.config['drop']['ok_button_region'])
        brightness_threshold = 80
        
        return self.vision.detect_brightness(screenshot, region, brightness_threshold)
    
    def _tap_ok(self, screenshot: np.ndarray):
        """Tap tombol OK buat close dialog drop."""
        max_attempts = self.config['drop']['max_ok_attempts']
        
        # Coba template dulu
        ok_template = self.config['drop']['ok_button_template']
        ok_pos = self.vision.find_template(screenshot, f"button_{ok_template}")
        
        if ok_pos:
            self.input.tap(ok_pos[0], ok_pos[1])
            self.stats["actions"] += 1
            logger.debug(f"Tap OK di {ok_pos}")
            return
        
        # Fallback: tap region OK button
        region = self.config['drop']['ok_button_region']
        x1, y1, x2, y2 = region
        ok_x = (x1 + x2) // 2
        ok_y = (y1 + y2) // 2
        
        for attempt in range(max_attempts):
            self.input.tap(ok_x, ok_y)
            self.stats["actions"] += 1
            time.sleep(0.5)
            
            # Check kalau dialog udah ilang
            new_screenshot = self.screen_capture.capture()
            if new_screenshot is not None:
                if not self._check_drop_dialog(new_screenshot):
                    logger.debug(f"Drop dialog closed setelah {attempt + 1} tap")
                    return
    
    def _check_combat(self, screenshot: np.ndarray) -> bool:
        """
        Check apakah lagi di combat mode.
        Detect HP bar di region tertentu.
        """
        hp_region = tuple(self.config['combat']['hp_bar_region'])
        hp_color = tuple(self.config['combat']['hp_bar_color'])
        hp_threshold = self.config['combat']['hp_bar_threshold']
        
        return self.vision.check_hp_bar(screenshot, hp_region, hp_color, hp_threshold)
    
    def _force_exit_combat(self):
        """Force exit combat kalau stuck."""
        logger.info("Force exit combat")
        self.input.press_back()
        time.sleep(1)
    
    def _find_monster(self, screenshot: np.ndarray) -> Optional[Tuple[str, Tuple[int, int]]]:
        """
        Cari monster di screenshot.
        Return (nama, posisi) kalau ketemu.
        """
        monster_templates = self.config['hunting']['monster_templates']
        
        # Center layar (posisi karakter biasanya di tengah)
        center = (
            self.input.screen_width // 2,
            self.input.screen_height // 2
        )
        
        # Cari monster terdekat
        closest = self.vision.find_closest_monster(screenshot, monster_templates, center)
        
        if closest:
            monster_name, monster_pos, confidence = closest
            return (monster_name, monster_pos)
        
        return None
    
    def _approach_monster(self, monster_pos: Tuple[int, int]):
        """
        Deketin monster.
        Tap ke arah monster buat gerak karakter.
        """
        monster_x, monster_y = monster_pos
        center_x = self.input.screen_width // 2
        center_y = self.input.screen_height // 2
        
        dx = monster_x - center_x
        dy = monster_y - center_y
        
        tap_threshold = self.config['navigation']['tap_threshold']
        
        if abs(dx) < tap_threshold and abs(dy) < tap_threshold:
            # Monster deket, tap dikit ke arah monster
            tap_x = center_x + dx // 2
            tap_y = center_y + dy // 2
            self.input.tap(tap_x, tap_y)
            logger.debug(f"Monster deket, tap ({tap_x}, {tap_y})")
        else:
            # Monster jauh, tap lebih ke arah monster
            tap_x = center_x + dx // 3
            tap_y = center_y + dy // 3
            self.input.tap(tap_x, tap_y)
            logger.debug(f"Monster jauh, tap ({tap_x}, {tap_y})")
            
            # Kalau monster jauh banget, swipe
            if abs(dx) > 500 or abs(dy) > 500:
                swipe_distance = self.config['navigation']['swipe_distance']
                swipe_duration = self.config['navigation']['swipe_duration']
                
                # Hitung arah swipe
                if abs(dx) > abs(dy):
                    swipe_x = swipe_distance if dx > 0 else -swipe_distance
                    swipe_y = 0
                else:
                    swipe_x = 0
                    swipe_y = swipe_distance if dy > 0 else -swipe_distance
                
                self.input.swipe(
                    (center_x, center_y),
                    (center_x + swipe_x, center_y + swipe_y),
                    duration=swipe_duration
                )
                logger.debug(f"Swipe ke arah monster ({swipe_x}, {swipe_y})")
    
    def _search_move(self):
        """
        Gerak cari monster kalau ga keliatan.
        """
        swipe_distance = self.config['navigation']['swipe_distance']
        swipe_duration = self.config['navigation']['swipe_duration']
        
        center_x = self.input.screen_width // 2
        center_y = self.input.screen_height // 2
        
        # Pattern: kiri, kanan, atas, bawah
        patterns = [
            (-swipe_distance, 0),
            (swipe_distance, 0),
            (0, -swipe_distance),
            (0, swipe_distance),
        ]
        
        pattern_index = self.search_count % len(patterns)
        dx, dy = patterns[pattern_index]
        
        self.input.swipe(
            (center_x, center_y),
            (center_x + dx, center_y + dy),
            duration=swipe_duration
        )
        
        logger.debug(f"Search move: ({dx}, {dy})")
        self.stats["actions"] += 1
        time.sleep(1)
