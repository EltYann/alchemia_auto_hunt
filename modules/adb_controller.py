import subprocess
import logging
import time
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class ADBController:
    """
    Controller ADB buat komunikasi dengan HP.
    """
    
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
        """Connect ke device."""
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
                
                # Get device ID
                devices = self.get_devices()
                if devices:
                    self.device_id = devices[0]
                
                return True
            
            logger.error(f"Gagal connect: {result.stdout}")
            return False
            
        except Exception as e:
            logger.error(f"Error connect: {e}")
            return False
    
    def disconnect
