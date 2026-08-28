#!/usr/bin/env python3
"""
Logger Module - Setup logging
"""

import logging
import sys
from pathlib import Path

def setup_logger(log_file: str = "data/logs/hunter.log", log_level: str = "INFO"):
    """Setup logger dengan file dan console output."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logger initialized: {log_file}")
    
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """Dapatkan logger untuk module."""
    return logging.getLogger(name)
