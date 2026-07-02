"""
Logging configuration and utilities.

Provides structured logging using loguru with both console
and file output, with automatic rotation and retention.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# Remove default handler
logger.remove()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    is_debug: bool = False,
) -> None:
    """
    Configure application-wide logging.
    
    Sets up both console and file logging with appropriate
    formatting and rotation policies.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        is_debug: Enable debug-level console output
    """
    # Console handler
    console_level = level if not is_debug else "DEBUG"
    console_format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        level=console_level,
        format=console_format,
        colorize=True,
    )

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

        logger.add(
            log_file,
            level=level,
            format=file_format,
            rotation="100 MB",
            retention="7 days",
            compression="zip",
        )


def get_logger(name: Optional[str] = None) -> "logger":
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance bound to the specified name
    """
    if name:
        return logger.bind(name=name)
    return logger
