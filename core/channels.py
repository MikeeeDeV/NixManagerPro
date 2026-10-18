"""
core.channels
~~~~~~~~~~~~~

Nix channel management service.

Channels are pointers to upstream package repositories (such as nixpkgs).
This service exposes listing, adding, removing, updating, and rolling back channels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .command_executor import AsyncCommandExecutor, CommandError


class ChannelError(RuntimeError):
    """Raised when an operation on Nix channels fails."""


@dataclass
class ChannelInfo:
    """Represents a configured Nix channel."""

    name: str
    url: str


class NixChannelManager:
    """High-level interface over `nix-channel` CLI operations."""

    def __init__(self, executor: AsyncCommandExecutor) -> None:
        self._exec = executor

    async def list_channels(self) -> List[ChannelInfo]:
        """
        List currently registered Nix channels.
        Format: '<channel-name> <url>'
        """
        result = await self._exec.run("nix-channel --list")
        channels: List[ChannelInfo] = []
        for line in result.stdout.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split(None, 1)
            if len(parts) == 2:
                channels.append(ChannelInfo(name=parts[0], url=parts[1]))
            elif len(parts) == 1:
                channels.append(ChannelInfo(name=parts[0], url=""))
        return channels

    async def add_channel(self, name: str, url: str) -> None:
        """Add or update a channel using `nix-channel --add <url> <name>`."""
        if not name or not url:
            raise ChannelError("Channel name and URL cannot be empty")
        try:
            await self._exec.run(f"nix-channel --add {url} {name}")
        except CommandError as exc:
            raise ChannelError(f"Failed to add channel '{name}': {exc}") from exc

    async def remove_channel(self, name: str) -> None:
        """Remove a channel by name via `nix-channel --remove <name>`."""
        try:
            await self._exec.run(f"nix-channel --remove {name}")
        except CommandError as exc:
            raise ChannelError(f"Failed to remove channel '{name}': {exc}") from exc

    async def update_channels(self) -> str:
        """
        Update registered channels via `nix-channel --update`.
        Streams downloading and unpacking output.
        """
        try:
            result = await self._exec.run("nix-channel --update")
            return result.stdout.strip() or "Channels updated successfully"
        except CommandError as exc:
            raise ChannelError(f"Channel update failed: {exc}") from exc

    async def rollback(self) -> str:
        """Rollback channel state via `nix-channel --rollback`."""
        try:
            result = await self._exec.run("nix-channel --rollback")
            return result.stdout.strip() or "Channel rollback successful"
        except CommandError as exc:
            raise ChannelError(f"Channel rollback failed: {exc}") from exc
