import sys
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.hunter import Hunter
from utils.logger import setup_logger, get_logger

logger = get_logger(__name__)
hunter = None

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    logger.info("Interrupt diterima, stopping...")
    if hunter:
        hunter.stop()
    sys.exit(0)

def main():
    global hunter
    
    setup_logger("data/logs/hunter.log")
    
    logger.info("=" * 50)
    logger.info("Alchemia Story Auto Hunt")
    logger.info("=" * 50)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    hunter = Hunter("config/settings.yaml")
    
    try:
        hunter.start()
    except KeyboardInterrupt:
        hunter.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        hunter.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
