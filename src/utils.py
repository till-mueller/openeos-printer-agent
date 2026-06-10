import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Configure logging with console and optional file handler."""
    log_format = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if config.file:
        log_path = Path(config.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            config.file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
        )
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("socketio").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
