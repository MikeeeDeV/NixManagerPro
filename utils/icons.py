"""
utils.icons
~~~~~~~~~~~

Clean vector icon loader for NixManager Pro.
Provides high-DPI modern monochrome icons for buttons, sidebar navigation,
and status badges, replacing all text emojis.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Optional, Tuple

import customtkinter as ctk

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


_ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


@functools.lru_cache(maxsize=64)
def get_icon(name: str, size: Tuple[int, int] = (18, 18)) -> Optional[ctk.CTkImage]:
    """
    Load and cache a CustomTkinter CTkImage from the assets/icons directory.
    Returns None safely if PIL is unavailable or the icon file doesn't exist.
    """
    if not _HAS_PIL:
        return None

    icon_path = _ICONS_DIR / f"{name}.png"
    if not icon_path.exists():
        return None

    try:
        pil_img = Image.open(icon_path)
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    except Exception:
        return None
