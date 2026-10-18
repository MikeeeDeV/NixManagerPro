"""
core.generations
~~~~~~~~~~~~~~~~

Service for querying and controlling Nix profile generations.

Nix profiles are atomic and versioned. Every package transaction
creates a new generation. This service enables users to list generations,
switch between them, and rollback instantly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .command_executor import AsyncCommandExecutor, CommandError


class GenerationError(RuntimeError):
    """Raised when an operation on a profile generation fails."""


@dataclass
class GenerationInfo:
    """Structured information regarding a single Nix generation."""

    id: int
    timestamp: str
    is_current: bool
    raw: str = ""


class NixGenerationManager:
    """Controls `nix-env` profile generation lifecycles."""

    def __init__(self, executor: AsyncCommandExecutor) -> None:
        self._exec = executor

    async def list_generations(self) -> List[GenerationInfo]:
        """
        Parse and return the history of profile generations.
        Lines typically match: '  42   2026-10-18 20:30:00   (current)'
        """
        result = await self._exec.run("nix-env --list-generations")
        generations: List[GenerationInfo] = []

        for line in result.stdout.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            # Match: <number> <date> <time> (current)?
            match = re.match(r"^(\d+)\s+([\d-]+\s+[\d:]+)(.*)$", line_str)
            if match:
                gen_id = int(match.group(1))
                timestamp = match.group(2).strip()
                extra = match.group(3).strip()
                is_current = "(current)" in extra.lower()

                generations.append(
                    GenerationInfo(
                        id=gen_id,
                        timestamp=timestamp,
                        is_current=is_current,
                        raw=line_str,
                    )
                )

        return sorted(generations, key=lambda g: g.id, reverse=True)

    async def rollback(self) -> str:
        """Rollback to the previous generation via `nix-env --rollback`."""
        try:
            result = await self._exec.run("nix-env --rollback")
            return result.stdout.strip() or "Rollback successful"
        except CommandError as exc:
            raise GenerationError(f"Rollback failed: {exc}") from exc

    async def switch_generation(self, generation_id: int) -> str:
        """Switch profile to a specific generation number."""
        try:
            result = await self._exec.run(f"nix-env --switch-generation {generation_id}")
            return result.stdout.strip() or f"Switched to generation {generation_id}"
        except CommandError as exc:
            raise GenerationError(f"Failed switching to generation {generation_id}: {exc}") from exc

    async def delete_old(self) -> str:
        """Purge non-current generations to free storage via `nix-env --delete-generations old`."""
        try:
            result = await self._exec.run("nix-env --delete-generations old")
            return result.stdout.strip() or "Old generations deleted successfully"
        except CommandError as exc:
            raise GenerationError(f"Failed to delete old generations: {exc}") from exc
