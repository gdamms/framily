import logging
import os
from logging.handlers import RotatingFileHandler

LOG_PATH = os.environ.get("FRAMILY_LOG_PATH", "/opt/framily/framily.log")
MAX_BYTES = 2 * 1024 * 1024
BACKUP_COUNT = 3

_configured_loggers = {}


def get_logger(name: str) -> logging.Logger:
    if name in _configured_loggers:
        return _configured_loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_PATH, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        logger.warning(f"Could not open log file '{LOG_PATH}': {e}")

    _configured_loggers[name] = logger
    return logger
