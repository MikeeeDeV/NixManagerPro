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
    """Parsed representation of one installed Nix package."""

    name: str
    version: str
    raw_line: str = ""          # original nix‑env output line


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class NixPackageManager:
    """
    Provides install / uninstall / list / search / GC via the ``nix-env``
    and ``nix-store`` command‑line tools.
    """

    def __init__(self, executor: AsyncCommandExecutor) -> None:
        self._exec = executor

    # ---- queries ----------------------------------------------------------

    async def list_installed(self) -> List[PackageInfo]:
        """
        Parse the output of ``nix-env -q`` and return structured data.

        Each line looks like ``pkgname-1.2.3``.  We split on the *last*
        dash to separate name from version.
        """
        result = await self._exec.run("nix-env -q")
        packages: List[PackageInfo] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Split on last '-' that precedes a digit  →  name / version
            match = re.match(r"^(.+)-(\d.*)$", line)
            if match:
                packages.append(
                    PackageInfo(
                        name=match.group(1),
                        version=match.group(2),
                        raw_line=line,
                    )
                )
            else:
                packages.append(PackageInfo(name=line, version="?", raw_line=line))
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
        supplies a bare name.
        """
        # Normalise: if the user typed a bare name, prefix nixpkgs.
        if "." not in attr_path:
            attr_path = f"nixpkgs.{attr_path}"

        try:
            await self._exec.run(f"nix-env -iA {attr_path}")
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
