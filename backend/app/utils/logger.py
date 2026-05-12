import logging
import sys

from app.core.config import settings


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("blog_publisher")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    ))
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


logger = setup_logger()
