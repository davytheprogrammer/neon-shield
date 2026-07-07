"""
Logging handler for NEON-SHIELD.

Provides structured logging to file and console with rotation.
"""
import logging
import logging.handlers
import os
import sys
from typing import Optional


def setup_logging(
    log_file: str,
    log_level: str = "INFO",
    max_size_mb: int = 100,
    backup_count: int = 5,
    verbose: bool = False,
):
    """
    Configure logging with file rotation and console output.

    Args:
        log_file: Path to log file (creates directories if needed)
        log_level: LOG level (DEBUG, INFO, WARN, ERROR)
        max_size_mb: Max log file size before rotation
        backup_count: Number of rotated logs to keep
        verbose: If True, also log DEBUG to console
    """
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Clear any existing handlers
    root.handlers.clear()

    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    root.addHandler(console_handler)

    return root


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
