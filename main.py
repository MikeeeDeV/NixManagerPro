#!/usr/bin/env python3
"""
NixManager Pro — Entry Point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch the application::

    python main.py

Or make executable and run directly::

    chmod +x main.py && ./main.py
"""

from __future__ import annotations

import sys
import traceback

from utils.logger import get_logger


def main() -> int:
    """Bootstrap and run the Tk main loop.  Returns an exit code."""
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("NixManager Pro starting")
    logger.info("=" * 60)

    # 1. Initialize environment (guarantee Nix, Snap, Flatpak paths)
    try:
        from core.command_executor import get_effective_env
        import os
        os.environ.update(get_effective_env())
    except Exception as exc:
        logger.warning("Could not set effective environment: %s", exc)

    # 2. Sync shell environment & desktop entries
    try:
        from utils.desktop_integrator import ensure_shell_environment, sync_nix_desktop_entries
        ensure_shell_environment()
        synced = sync_nix_desktop_entries()
        if synced > 0:
            logger.info("Synced %d Nix desktop application shortcut(s) into Ubuntu Dash", synced)
    except Exception as exc:
        logger.warning("Desktop integration error: %s", exc)

    try:
        # Late import so that if customtkinter is missing we get a clean error.
        from ui.app import NixManagerApp

        app = NixManagerApp()
        app.mainloop()
        return 0

    except ImportError as exc:
        logger.critical(
            "Missing dependency: %s\n"
            "Run:  pip install -r requirements.txt",
            exc,
        )
        print(
            f"\n❌  Missing dependency: {exc}\n"
            "   Run:  pip install -r requirements.txt\n",
            file=sys.stderr,
        )
        return 1

    except Exception:
        logger.critical("Fatal error:\n%s", traceback.format_exc())
        print(
            f"\n❌  Fatal error — see logs/nixmanager.log for details.\n",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
