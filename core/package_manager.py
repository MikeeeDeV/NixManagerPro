"""
core.package_manager
~~~~~~~~~~~~~~~~~~~~

High‑level façade over the Nix CLI for package CRUD operations.

Every method is an ``async`` coroutine that delegates to the shared
:class:`~core.command_executor.AsyncCommandExecutor`.  The calling code
(usually a background worker thread) wraps the call in ``asyncio.run()``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from .command_executor import AsyncCommandExecutor, CommandError


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------

class PackageOperationError(RuntimeError):
    """Raised when a package install / uninstall / GC operation fails."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PackageInfo:
    """Parsed representation of one installed package across supported managers."""

    name: str
    version: str
    source: str = "Nix"          # "Nix", "Flatpak", "Snap", "System"
    app_id: str = ""
    raw_line: str = ""           # original output line


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class NixPackageManager:
    """
    Provides install / uninstall / list / search / GC via the ``nix-env``,
    ``flatpak``, ``snap``, and ``nix-store`` command‑line tools.
    """

    def __init__(self, executor: AsyncCommandExecutor) -> None:
        self._exec = executor

    # ---- queries ----------------------------------------------------------

    async def list_installed(self) -> List[PackageInfo]:
        """
        Parse the output of ``nix-env -q`` and return structured Nix package data.
        """
        try:
            result = await self._exec.run("nix-env -q")
        except Exception:
            return []

        packages: List[PackageInfo] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^(.+)-(\d.*)$", line)
            if match:
                packages.append(
                    PackageInfo(
                        name=match.group(1),
                        version=match.group(2),
                        source="Nix",
                        raw_line=line,
                    )
                )
            else:
                packages.append(PackageInfo(name=line, version="?", source="Nix", raw_line=line))
        return packages

    async def list_all_installed(self) -> List[PackageInfo]:
        """
        Discover installed packages across all available Linux package managers:
        Nix profiles, Flatpak applications, and Snap packages.
        """
        packages: List[PackageInfo] = []

        # 1. Nix Packages
        try:
            nix_pkgs = await self.list_installed()
            packages.extend(nix_pkgs)
        except Exception:
            pass

        # 2. Flatpak Packages
        try:
            fp_res = await self._exec.run("flatpak list --app --columns=name,application,version", timeout=10)
            for line in fp_res.stdout.splitlines():
                parts = [p.strip() for p in line.split("\t") if p.strip()]
                if len(parts) >= 3:
                    packages.append(PackageInfo(name=parts[0], version=parts[2], source="Flatpak", app_id=parts[1]))
                elif len(parts) == 2:
                    packages.append(PackageInfo(name=parts[0], version="installed", source="Flatpak", app_id=parts[1]))
        except Exception:
            pass

        # 3. Snap Packages
        try:
            snap_res = await self._exec.run("snap list", timeout=10)
            lines = snap_res.stdout.splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        name, ver = parts[0], parts[1]
                        # Filter out internal base system snaps
                        if name in ("bare", "core", "core18", "core20", "core22", "core24", "snapd"):
                            continue
                        packages.append(PackageInfo(name=name, version=ver, source="Snap", app_id=name))
        except Exception:
            pass

        return packages

    async def search(self, query: str) -> List[Dict[str, str]]:
        """
        Search for available packages via ``nix-env -qaP <query>``.

        Returns a list of ``{"attr": …, "name": …}`` dicts.
        """
        result = await self._exec.run(f"nix-env -qaP {query}")
        hits: List[Dict[str, str]] = []
        for line in result.stdout.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                hits.append({"attr": parts[0], "name": parts[1]})
            elif parts:
                hits.append({"attr": parts[0], "name": parts[0]})
        return hits

    # ---- mutations --------------------------------------------------------

    async def install(self, attr_path: str) -> None:
        """
        Install a package by its attribute path (e.g. ``nixpkgs.htop``).

        Falls back to ``nix-env -iA nixpkgs.<attr_path>`` if the caller
        supplies a bare name. Also automatically syncs .desktop entries.
        """
        if "." not in attr_path:
            attr_path = f"nixpkgs.{attr_path}"

        try:
            await self._exec.run(f"nix-env -iA {attr_path}")
            # Automatically integrate new desktop shortcuts into Ubuntu Dash
            try:
                from utils.desktop_integrator import sync_nix_desktop_entries
                sync_nix_desktop_entries()
            except Exception:
                pass
        except CommandError as exc:
            raise PackageOperationError(
                f"Failed to install '{attr_path}': {exc}"
            ) from exc

    async def uninstall(self, pkg_name: str) -> None:
        """Remove *pkg_name* from the active user profile."""
        try:
            await self._exec.run(f"nix-env -e {pkg_name}")
        except CommandError as exc:
            raise PackageOperationError(
                f"Failed to uninstall '{pkg_name}': {exc}"
            ) from exc

    async def uninstall_generic(self, pkg: PackageInfo) -> None:
        """Uninstall package using its native package manager (Nix, Flatpak, or Snap)."""
        try:
            if pkg.source == "Flatpak":
                target = pkg.app_id or pkg.name
                await self._exec.run(f"flatpak uninstall -y {target}")
            elif pkg.source == "Snap":
                await self._exec.run(f"snap remove {pkg.name}")
            else:
                await self._exec.run(f"nix-env -e {pkg.name}")
        except CommandError as exc:
            raise PackageOperationError(
                f"Failed to uninstall {pkg.source} package '{pkg.name}': {exc}"
            ) from exc

    async def upgrade_all(self) -> str:
        """Upgrade all packages in the active profile to latest channel versions."""
        try:
            result = await self._exec.run("nix-env -u")
            return result.stdout.strip() or "All packages up to date."
        except CommandError as exc:
            raise PackageOperationError(f"Upgrade failed: {exc}") from exc

    # ---- maintenance ------------------------------------------------------

    async def garbage_collect(self) -> str:
        """
        Run ``nix-store --gc`` and return its stdout summary.
        """
        try:
            result = await self._exec.run("nix-store --gc")
            return result.stdout
        except CommandError as exc:
            raise PackageOperationError(f"Garbage collection failed: {exc}") from exc

