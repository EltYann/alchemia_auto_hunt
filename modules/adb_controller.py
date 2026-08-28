#!/usr/bin/env python3
"""
ADB Controller - Koneksi dan command ADB
"""

import subprocess
import logging
import time
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class ADBController:
    """Controller ADB buat komunikasi dengan HP."""
    
    def __init__(
        self,
        device_ip: str = "127.0.0.1",
        port: int = 5555,
        device_id: Optional[str] = None
    ):
        self.device_ip = device_ip
        self.port = port
        self.device_id = device_id
        self.connected = False
    
    def connect(self) -> bool:
        """Connect ke device via ADB."""
        try:
            if self.device_id:
                self.connected = True
                return True
            
            result = subprocess.run(
                ["adb", "connect", f"{self.device_ip}:{self.port}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "connected" in result.stdout or "already connected" in result.stdout:
                self.connected = True
                logger.info(f"Connected ke {self.device_ip}:{self.port}")
                
                devices = self.get_devices()
                if devices:
                    self.device_id = devices[0]
                    logger.info(f"Device ID: {self.device_id}")
                
                return True
            
            logger.error(f"Gagal connect: {result.stdout}")
            return False
            
        except Exception as e:
            logger.error(f"Error connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect dari device."""
        try:
            subprocess.run(
                ["adb", "disconnect", f"{self.device_ip}:{self.port}"],
                capture_output=True,
                timeout=5
            )
            self.connected = False
            self.device_id = None
        except Exception as e:
            logger.error(f"Error disconnect: {e}")
    
    def get_devices(self) -> List[str]:
        """Dapatkan list device connected."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                if '\t' in line:
                    device_id, status = line.split('\t')
                    if status == 'device':
                        devices.append(device_id)
            
            return devices
        except Exception as e:
            logger.error(f"Error get devices: {e}")
            return []
    
    def execute(
        self,
        command: List[str],
        timeout: int = 30
    ) -> Tuple[bool, str]:
        """Execute ADB command."""
        if not self.connected and not self.device_id:
            if not self.connect():
                return False, "Not connected"
        
        try:
            full_cmd = ["adb"]
            if self.device_id:
                full_cmd.extend(["-s", self.device_id])
            full_cmd.extend(command)
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout
            return False, result.stderr
            
        except Exception as e:
            return False, str(e)
    
    def tap(self, x: int, y: int) -> bool:
        """Tap di koordinat."""
        success, _ = self.execute(["shell", "input", "tap", str(x), str(y)])
        return success
    
    def swipe(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration: int = 300
    ) -> bool:
        """Swipe dari titik A ke B."""
        success, _ = self.execute([
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration)
        ])
        return success
    
    def press_back(self) -> bool:
        """Tekan tombol back."""
        success, _ = self.execute(["shell", "input", "keyevent", "4"])
        return success
    
    def press_home(self) -> bool:
        """Tekan tombol home."""
        success, _ = self.execute(["shell", "input", "keyevent", "3"])
        return success
    
    def screenshot(self) -> Optional[bytes]:
        """Ambil screenshot dari device."""
        try:
            success, _ = self.execute(
                ["shell", "screencap", "-p", "/sdcard/screen.png"],
                timeout=10
            )
            
            if not success:
                return None
            
            success, output = self.execute(
                ["exec-out", "cat", "/sdcard/screen.png"],
                timeout=10
            )
            
            if success:
                return output.encode() if isinstance(output, str) else output
            
            return None
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Dapatkan ukuran layar."""
        success, output = self.execute(["shell", "wm", "size"])
        
        if success:
            try:
                size_str = output.split(":")[1].strip()
                width, height = size_str.split("x")
                return int(width), int(height)
            except Exception:
                pass
        
        return 1080, 2400
    
    def start_app(self, package: str) -> bool:
        """Start aplikasi."""
        success, _ = self.execute([
            "shell", "monkey", "-p", package,
            "-c", "android.intent.category.LAUNCHER", "1"
        ])
        return success
    
    def get_current_app(self) -> Optional[str]:
        """Dapatkan package name aplikasi aktif."""
        success, output = self.execute(["shell", "dumpsys", "window"])
        
        if success:
            for line in output.split('\n'):
                if 'mCurrentFocus' in line:
                    if '/' in line:
                        parts = line.split('/')
                        for part in parts:
                            part = part.strip()
                            if part.startswith('com.'):
                                return part
        
        return None
