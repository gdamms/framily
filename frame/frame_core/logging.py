from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from frame_core.settings import LOG_FILE_PATH, LOG_LEVEL


_LOGGING_CONFIGURED = False


def _build_file_handler(path: Path) -> logging.Handler:
    path.parent.mkdir(parents=True, exist_ok=True)
    return RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3)


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    try:
        handlers.append(_build_file_handler(LOG_FILE_PATH))
    except OSError:
        fallback = Path("/tmp/framily-frame.log")
        handlers.append(_build_file_handler(fallback))

    log_level_name = str(LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=False,
    )

    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
