"""
utils.desktop_integrator
~~~~~~~~~~~~~~~~~~~~~~~~

Ensures that Nix packages installed by the user actually WORK everywhere:
1. Automatically configures ~/.bashrc & ~/.profile with Nix PATH and XDG_DATA_DIRS.
2. Automatically detects and syncs .desktop entries from ~/.nix-profile/share/applications
   into ~/.local/share/applications so GUI apps appear in Ubuntu Dash / App Grid.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


NIX_SHELL_SNIPPET = """
# >>> NixManager Pro: Environment & Desktop Integration >>>
if [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
    . "$HOME/.nix-profile/etc/profile.d/nix.sh"
elif [ -e "/nix/var/nix/profiles/default/etc/profile.d/nix.sh" ]; then
    . "/nix/var/nix/profiles/default/etc/profile.d/nix.sh"
fi
export PATH="$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:$PATH"
export XDG_DATA_DIRS="$HOME/.nix-profile/share:/nix/var/nix/profiles/default/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
# <<< NixManager Pro: Environment & Desktop Integration <<<
"""


def ensure_shell_environment() -> None:
    """Ensure ~/.bashrc and ~/.profile have Nix bin in PATH and XDG_DATA_DIRS."""
    home = Path.home()
    target_files = [home / ".bashrc", home / ".profile"]

    for target in target_files:
        try:
            if not target.exists():
                continue
            content = target.read_text(encoding="utf-8", errors="ignore")
            if "NixManager Pro: Environment & Desktop Integration" not in content:
                with open(target, "a", encoding="utf-8") as f:
                    f.write("\n" + NIX_SHELL_SNIPPET.strip() + "\n")
        except Exception:
            pass


def sync_nix_desktop_entries() -> int:
    """
    Scan Nix profile share directories for .desktop files and copy/link them to
    ~/.local/share/applications so GNOME / Ubuntu App Grid displays them.
    Returns number of synced desktop entries.
    """
    home = Path.home()
    dest_dir = home / ".local" / "share" / "applications"
    dest_dir.mkdir(parents=True, exist_ok=True)

    source_dirs = [
        home / ".nix-profile" / "share" / "applications",
        Path("/nix/var/nix/profiles/default/share/applications"),
    ]

    synced_count = 0
    for sdir in source_dirs:
        if not sdir.is_dir():
            continue
        for desktop_file in sdir.glob("*.desktop"):
            target_link = dest_dir / desktop_file.name
            try:
                if not target_link.exists():
                    shutil.copy2(desktop_file, target_link)
                    synced_count += 1
            except Exception:
                pass

    if synced_count > 0:
        try:
            subprocess.run(
                ["update-desktop-database", str(dest_dir)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass

    return synced_count
