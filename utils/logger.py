"""
utils.logger
~~~~~~~~~~~~~

Centralised, rotating logger used by every module in NixManager Pro.

Usage::

    from utils.logger import get_logger
    log = get_logger()
    log.info("Something happened")
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_LOGGER: Optional[logging.Logger] = None

# Log files live next to the project root: ``NixManagerPro/logs/``
_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


def get_logger(level: str = "DEBUG") -> logging.Logger:
    """
    Return the singleton application logger.

    On first call the logger is configured with:
    * A **console** handler on ``sys.stderr`` (level INFO).
    * A **rotating file** handler in ``logs/nixmanager.log``
      (5 MiB × 3 backups, level DEBUG).
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("NixManagerPro")
    logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))

    fmt = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(threadName)-14s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---- stderr handler ---------------------------------------------------
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # ---- rotating file handler --------------------------------------------
    file_handler = RotatingFileHandler(
        filename=_LOG_DIR / "nixmanager.log",
        maxBytes=5 * 1024 * 1024,   # 5 MiB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    _LOGGER = logger
    return logger
