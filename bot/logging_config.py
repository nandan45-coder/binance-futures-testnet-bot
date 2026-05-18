"""
Logging configuration for Binance Futures Testnet Trading Bot.
Sets up rotating file handlers and console handlers with structured formatting.
"""

import logging
import logging.handlers
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"


def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """
    Set up and return a logger with rotating file and console handlers.

    Args:
        name: Logger name (default: 'trading_bot')

    Returns:
        Configured logger instance
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers on re-init
    if logger.handlers:
        return logger

    # ── Rotating file handler (all levels) ──────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # ── Rotating error log (WARNING+) ────────────────────────────────────────
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=2 * 1024 * 1024,   # 2 MB
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # ── Console handler (INFO+) ──────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialised — log file: %s", LOG_FILE)
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Return a child logger for a specific module."""
    return logging.getLogger(f"trading_bot.{module_name}")
