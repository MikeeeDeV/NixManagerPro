"""
utils.config
~~~~~~~~~~~~~

Typed configuration loader backed by a JSON file next to the project root.

If the file does not exist, sensible defaults are used.  The config is
loaded once at startup and cached.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


@dataclass
class AppConfig:
    """Application‑wide configuration."""

    max_worker_threads: int = 4
    log_level: str = "DEBUG"
    nix_binary: str = "nix-env"
    theme_mode: str = "Dark"            # "Dark" | "Light" | "System"
    colour_theme: str = "blue"          # CustomTkinter built‑in themes
    window_width: int = 1280
    window_height: int = 820


_CACHED: Optional[AppConfig] = None


def load_config() -> AppConfig:
    """Load and cache configuration from ``config.json``."""
    global _CACHED
    if _CACHED is not None:
        return _CACHED

    if _CONFIG_PATH.is_file():
        with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        _CACHED = AppConfig(**{
            k: v for k, v in data.items() if k in AppConfig.__dataclass_fields__
        })
    else:
        _CACHED = AppConfig()

    return _CACHED


def save_config(cfg: AppConfig) -> None:
    """Persist *cfg* back to disk."""
    with _CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(asdict(cfg), fh, indent=2)
