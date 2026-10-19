"""
utils.icons
~~~~~~~~~~~

Clean vector icon loader for NixManager Pro.
Provides high-DPI modern monochrome icons for buttons, sidebar navigation,
and status badges, replacing all text emojis.

Safely caches raw PIL images while generating fresh CTkImage instances
to prevent '_tkinter.TclError: image pyimageX does not exist' across window
lifecycles and toplevel dialogs.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Optional, Tuple

import customtkinter as ctk

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    Image = None  # type: ignore
    _HAS_PIL = False


_ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


@functools.lru_cache(maxsize=64)
def _load_pil_image(name: str) -> Optional[Any]:
    """Load and cache decoded PIL Image object in memory."""
    if not _HAS_PIL or Image is None:
        return None
    icon_path = _ICONS_DIR / f"{name}.png"
    if not icon_path.exists():
        return None
    try:
        # Load image into memory and return a copy so it can be reused safely
        with Image.open(icon_path) as img:
            return img.copy()
    except Exception:
        return None


def get_icon(name: str, size: Tuple[int, int] = (18, 18)) -> Optional[ctk.CTkImage]:
    """
    Return a fresh CustomTkinter CTkImage referencing the cached PIL Image.
    Creating a new CTkImage wrapper avoids stale Tk PhotoImage (pyimage) references
    when toplevel dialogs or secondary windows are opened.
    """
    if not _HAS_PIL:
        return None

    pil_img = _load_pil_image(name)
    if pil_img is None:
        return None

    try:
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    except Exception:
        return None
