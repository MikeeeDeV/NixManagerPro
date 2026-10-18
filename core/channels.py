"""
core.channels
~~~~~~~~~~~~~

Nix channel management service.

Channels are pointers to upstream package repositories (such as nixpkgs).
This service exposes listing, adding, removing, updating, probing health,
and curated quick-subscribe presets.
"""

from __future__ import annotations

import asyncio
import time
import urllib.request
from dataclasses import dataclass
from typing import List, Optional

from .command_executor import AsyncCommandExecutor, CommandError


class ChannelError(RuntimeError):
    """Raised when an operation on Nix channels fails."""


@dataclass
class ChannelInfo:
    """Represents a configured Nix channel."""

    name: str
    url: str
    status: str = "Online"
    latency_ms: int = 0


@dataclass
class ChannelPreset:
    """Curated Nix channel preset for 1-click subscription."""

    name: str
    url: str
    description: str
    tag: str = "Official"        # "Stable", "Rolling", "Community", "Overlay"
    recommended: bool = False


CURATED_CHANNEL_PRESETS: List[ChannelPreset] = [
    ChannelPreset(
        name="nixpkgs-unstable",
        url="https://nixos.org/channels/nixpkgs-unstable",
        description="Bleeding-edge packages updated multiple times daily with latest software.",
        tag="Rolling",
        recommended=True,
    ),
    ChannelPreset(
        name="nixos-24.05",
        url="https://nixos.org/channels/nixos-24.05",
        description="Production stable release with security backports and highest stability.",
        tag="Stable",
        recommended=True,
    ),
    ChannelPreset(
        name="nixos-unstable",
        url="https://nixos.org/channels/nixos-unstable",
        description="Full rolling NixOS system channel with cutting-edge system modules.",
        tag="Rolling",
    ),
    ChannelPreset(
        name="home-manager",
        url="https://github.com/nix-community/home-manager/archive/master.tar.gz",
        description="Declarative user configuration, dotfiles, and home environment manager.",
        tag="Community",
        recommended=True,
    ),
    ChannelPreset(
        name="rust-overlay",
        url="https://github.com/oxalica/rust-overlay/archive/master.tar.gz",
        description="Pure Nix overlay providing all Rust releases, nightly toolchains, and WASM targets.",
        tag="Overlay",
    ),
    ChannelPreset(
        name="nixos-hardware",
        url="https://github.com/NixOS/nixos-hardware/archive/master.tar.gz",
        description="Community hardware profiles and hardware-specific configurations.",
        tag="Hardware",
    ),
]


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

    async def update_single_channel(self, name: str) -> str:
        """
        Update a specific single channel via `nix-channel --update <name>`.
        """
        try:
            result = await self._exec.run(f"nix-channel --update {name}")
            return result.stdout.strip() or f"Channel '{name}' updated successfully"
        except CommandError as exc:
            raise ChannelError(f"Update failed for '{name}': {exc}") from exc

    async def rollback(self) -> str:
        """Rollback channel state via `nix-channel --rollback`."""
        try:
            result = await self._exec.run("nix-channel --rollback")
            return result.stdout.strip() or "Channel rollback successful"
        except CommandError as exc:
            raise ChannelError(f"Channel rollback failed: {exc}") from exc

    @staticmethod
    async def check_channel_health(url: str) -> dict:
        """Check HTTP connectivity and response latency to upstream channel repository."""
        if not url:
            return {"status": "Unknown", "latency_ms": 0}

        def _probe():
            start = time.time()
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "NixManagerPro/1.7.0"},
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    elapsed = int((time.time() - start) * 1000)
                    return {"status": "Online", "latency_ms": elapsed, "code": resp.status}
            except Exception as e:
                return {"status": "Unreachable", "latency_ms": 0, "error": str(e)}

        return await asyncio.to_thread(_probe)
