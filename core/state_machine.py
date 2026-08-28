import logging
import time
from enum import Enum, auto
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class State(Enum):
    IDLE = auto()
    SCANNING = auto()
    APPROACHING = auto()
    IN_COMBAT = auto()
    COLLECTING_DROP = auto()
    SEARCHING = auto()
    PAUSED = auto()
    STOPPED = auto()

class StateMachine:
    """
    Simple state machine buat hunting flow.
    """
    
    def __init__(self):
        self.current_state = State.IDLE
        self.previous_state = None
        self.state_start_time = time.time()
        self.handlers = {}
    
    def set_handler(self, state: State, handler: Callable):
        """Set handler buat state."""
        self.handlers[state] = handler
    
    def transition_to(self, new_state: State, context: Dict[str, Any] = None):
        """Pindah state."""
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        logger.debug(f"State: {self.previous_state} -> {new_state}")
        
        if new_state in self.handlers:
            try:
                self.handlers[new_state](context or {})
            except Exception as e:
                logger.error(f"Handler error di {new_state}: {e}")
    
    def get_state_duration(self) -> float:
        """Durasi di state saat ini."""
        return time.time() - self.state_start_time
    
    def is_in_state(self, state: State) -> bool:
        """Check state."""
        return self.current_state == state
