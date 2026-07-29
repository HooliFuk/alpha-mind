# monitoring/logger.py
import logging
import os
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Import and call this at the top of every file.

    Usage:
        from monitoring.logger import get_logger
        logger = get_logger(__name__)
        logger.info("This is a message")
        logger.error("This is an error")
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create logs directory if it does not exist
    os.makedirs("logs", exist_ok=True)

    # File handler saves everything
    log_filename = (
        f"logs/alpha_trader_"
        f"{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)

    # Console handler shows INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format for both handlers
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger