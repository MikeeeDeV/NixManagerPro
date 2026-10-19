"""
utils.notifications
~~~~~~~~~~~~~~~~~~~

Desktop notifications provider for Linux environments.
Leverages `notify-send` (libnotify) to display system toast alerts
when long background tasks (installs, GC, channel updates) complete.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class DesktopNotifier:
    """Dispatches FreeDesktop desktop notification popups."""

    _ICON_PATH = Path(__file__).resolve().parents[1] / "assets" / "nixmanager.svg"

    @classmethod
    def info(cls, title: str, message: str) -> bool:
        """Send normal urgency desktop notification."""
        return cls.send(title, message, urgency="normal")

    @classmethod
    def warn(cls, title: str, message: str) -> bool:
        """Send critical urgency desktop notification."""
        return cls.send(title, message, urgency="critical")

    @classmethod
    def send(
        cls,
        title: str,
        message: str,
        urgency: str = "normal",
        icon: Optional[str] = None,
    ) -> bool:
        """
        Send a notification toast to the desktop environment.
        Returns True if successful, False otherwise.
        """
        notify_bin = shutil.which("notify-send")
        if not notify_bin:
            return False

        effective_icon = icon or (str(cls._ICON_PATH) if cls._ICON_PATH.is_file() else "software-update-available")

        cmd = [
            notify_bin,
            f"--urgency={urgency}",
            f"--icon={effective_icon}",
            f"--app-name=NixManager Pro",
            title,
            message,
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return True
        except Exception:
            return False
