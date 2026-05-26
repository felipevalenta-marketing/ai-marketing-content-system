"""Shared logging utilities for the markdown knowledge ingestion layer."""

from __future__ import annotations

import logging


_CONFIGURED_LOGGERS: set[str] = set()


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a developer-friendly logger with a consistent format."""

    logger = logging.getLogger(name)
    if name not in _CONFIGURED_LOGGERS:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.propagate = False
        _CONFIGURED_LOGGERS.add(name)

    logger.setLevel(level)
    return logger


def log_scan(logger: logging.Logger, message: str) -> None:
    """Log filesystem scanning steps."""

    logger.info("[scan] %s", message)


def log_load(logger: logging.Logger, message: str) -> None:
    """Log file loading steps."""

    logger.info("[load] %s", message)


def log_context(logger: logging.Logger, message: str) -> None:
    """Log context assembly steps."""

    logger.info("[context] %s", message)


def log_warning(logger: logging.Logger, message: str) -> None:
    """Log recoverable warnings."""

    logger.warning("[warning] %s", message)


def log_error(logger: logging.Logger, message: str) -> None:
    """Log recoverable errors."""

    logger.error("[error] %s", message)
