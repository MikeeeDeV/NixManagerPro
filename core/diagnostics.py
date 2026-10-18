"""
core.diagnostics
~~~~~~~~~~~~~~~~

System health checks for the Nix daemon, store disk usage, and channel info.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .command_executor import AsyncCommandExecutor, CommandError


@dataclass
class DaemonStatus:
    """Structured result of a daemon health check."""

    active: bool
    status_text: str        # raw systemctl output or error message


@dataclass
class StoreStats:
    """Disk‑usage statistics for the Nix store."""

    raw_output: str         # raw ``du`` / ``nix path-info`` output
    size_human: str         # e.g. "4.2 GiB"


class Diagnostics:
    """
    Read‑only diagnostic queries.  None of these methods mutate the store
    — use :class:`~core.package_manager.NixPackageManager.garbage_collect`
    for that.
    """

    def __init__(self, executor: AsyncCommandExecutor) -> None:
        self._exec = executor

    # ---- daemon -----------------------------------------------------------

    async def daemon_status(self) -> DaemonStatus:
        """
        Check whether ``nix-daemon.service`` is running via *systemctl*.

        Returns a :class:`DaemonStatus` regardless of outcome — never raises
        for a stopped daemon.
        """
        try:
            result = await self._exec.run(
                "systemctl is-active nix-daemon.service", timeout=10
            )
            return DaemonStatus(active=True, status_text=result.stdout.strip())
        except CommandError:
            # Daemon is not running — that's fine, just report it.
            return DaemonStatus(active=False, status_text="inactive / not found")

    async def daemon_active(self) -> bool:
        """Convenience helper: ``True`` when the daemon unit is *active*."""
        status = await self.daemon_status()
        return status.active

    # ---- store usage ------------------------------------------------------

    async def store_usage(self) -> StoreStats:
        """
        Return human‑readable store size.

        Tries ``du -sh /nix/store`` first; falls back to a placeholder on
        error (permission denied on some multi‑user setups).
        """
        try:
            result = await self._exec.run("du -sh /nix/store", timeout=60)
            size = result.stdout.split()[0] if result.stdout else "unknown"
            return StoreStats(raw_output=result.stdout, size_human=size)
        except CommandError as exc:
            return StoreStats(raw_output=str(exc), size_human="N/A")

    # ---- channel info -----------------------------------------------------

    async def channel_list(self) -> str:
        """Return the output of ``nix-channel --list``."""
        try:
            result = await self._exec.run("nix-channel --list", timeout=10)
            return result.stdout.strip() or "(no channels configured)"
        except CommandError as exc:
            return f"Error listing channels: {exc}"
