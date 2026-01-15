import logging
import sys
from pathlib import Path
from nmie.config import LOGS_DIR

def setup_logging(name: str = "synegious"):
    """
    Configures logging to both console and file.
    """
    LOGS_DIR.mkdir(exist_ok=True, parents=True)
    log_file = LOGS_DIR / f"{name}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Default logger
logger = setup_logging()
