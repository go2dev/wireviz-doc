"""
Logging utilities for WireViz Doc.

Provides file logging for debugging and audit trails. Console output
is handled by typer's built-in rich integration.

Usage:
    from wireviz_doc.output import setup_file_logging, logger

    # Enable file logging for a build
    setup_file_logging(log_file="build/HAR-001/build.log", level="DEBUG")

    # Log messages
    logger.info("Starting build")
    logger.debug("Processing connector X1")
    logger.warning("Image not found for part ABC")
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# Module-level logger
logger = logging.getLogger("wireviz_doc")


def setup_file_logging(
    log_file: Union[str, Path],
    level: str = "DEBUG",
    format_string: Optional[str] = None,
) -> Path:
    """
    Configure file logging for WireViz Doc.

    Args:
        log_file: Path to log file.
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        format_string: Custom format string for log entries.

    Returns:
        Path to the log file.

    Example:
        # Enable debug logging to build output
        setup_file_logging("build/HAR-001/build.log")

        logger.info("Starting build")
        logger.debug("Detailed info...")
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logger
    logger.setLevel(logging.DEBUG)

    # Remove existing file handlers
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Add new file handler
    file_format = format_string or "%(asctime)s | %(levelname)-8s | %(message)s"
    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="w")
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    # Log session header
    logger.info("=" * 60)
    logger.info(f"WireViz Doc build log - {datetime.now().isoformat()}")
    logger.info(f"Log level: {level}")
    logger.info("=" * 60)

    return log_path


def close_file_logging() -> None:
    """Close and remove file logging handlers."""
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger.removeHandler(handler)
