"""
core.command_executor
~~~~~~~~~~~~~~~~~~~~~

Asynchronous subprocess wrapper that streams stdout/stderr line‑by‑line.
Consumers register an ``on_output`` callback to receive real‑time output
(used by the Console Log widget).

All long‑running Nix CLI invocations go through this executor so that the
UI thread is never blocked.
"""

from __future__ import annotations

import asyncio
import os
import shlex
import shutil
from dataclasses import dataclass, field
from typing import Callable, List, Optional


def get_effective_env(custom_env: Optional[dict] = None) -> dict:
    """Build an execution environment with Nix, Snap, and Flatpak paths guaranteed."""
    env = dict(os.environ)
    if custom_env:
        env.update(custom_env)

    nix_bin_dirs = [
        os.path.expanduser("~/.nix-profile/bin"),
        "/nix/var/nix/profiles/default/bin",
        "/run/current-system/sw/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/snap/bin",
    ]
    current_path = env.get("PATH", "")
    dirs_to_add = [d for d in nix_bin_dirs if os.path.isdir(d) and d not in current_path.split(":")]
    if dirs_to_add:
        env["PATH"] = ":".join(dirs_to_add) + ((":" + current_path) if current_path else "")

    nix_share = os.path.expanduser("~/.nix-profile/share")
    default_share = "/nix/var/nix/profiles/default/share"
    current_xdg = env.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    if os.path.isdir(nix_share) and nix_share not in current_xdg:
        current_xdg = f"{nix_share}:{current_xdg}"
    if os.path.isdir(default_share) and default_share not in current_xdg:
        current_xdg = f"{default_share}:{current_xdg}"
    env["XDG_DATA_DIRS"] = current_xdg
    return env


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------

class CommandError(RuntimeError):
    """Raised when a subprocess exits with a non‑zero return code."""


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class CommandResult:
    """Immutable container for the output of a finished command."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0

    def __bool__(self) -> bool:          # truthy when exit‑code == 0
        return self.returncode == 0


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class AsyncCommandExecutor:
    """
    Execute shell commands asynchronously via ``asyncio.create_subprocess_exec``.

    **Thread‑safety note**: the ``on_output`` callback is invoked *inside* the
    asyncio event loop that runs the subprocess.  If the consumer is a Tk
    widget it must use ``widget.after(0, …)`` to marshal the call to the
    main thread — the :pymod:`ui.console_log` module already does this.
    """

    def __init__(self) -> None:
        self._on_output: Optional[Callable[[str, str], None]] = None

    # ---- public API -------------------------------------------------------

    def set_output_callback(self, cb: Callable[[str, str], None]) -> None:
        """
        Register a function ``cb(stream, line)`` that is invoked for every
        line of output produced by a running command.

        *stream* is either ``"stdout"`` or ``"stderr"``.
        """
        self._on_output = cb

    async def run(
        self,
        cmd: str | List[str],
        *,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """
        Run *cmd* and return a :class:`CommandResult`.

        Parameters
        ----------
        cmd:
            Shell command string **or** a pre‑split argument list.
        cwd:
            Working directory for the subprocess.
        env:
            Optional environment override (merged with ``os.environ`` by the OS).
        timeout:
            Maximum wall‑clock seconds before the process is killed.

        Raises
        ------
        CommandError
            If the process exits with a non‑zero return code or times out.
        """
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        effective_env = get_effective_env(env)
        if cmd:
            resolved_bin = shutil.which(cmd[0], path=effective_env.get("PATH"))
            if resolved_bin:
                cmd[0] = resolved_bin

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=effective_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []

        async def _read_stream(
            stream: asyncio.StreamReader, name: str
        ) -> None:
            while True:
                raw = await stream.readline()
                if not raw:
                    break
                decoded = raw.decode(errors="replace")
                if name == "stdout":
                    stdout_chunks.append(decoded)
                else:
                    stderr_chunks.append(decoded)

                if self._on_output:
                    self._on_output(name, decoded.rstrip("\n"))

        if proc.stdout is None or proc.stderr is None:
            raise CommandError(f"Failed to capture process I/O for command: {' '.join(cmd)}")

        stdout_stream: asyncio.StreamReader = proc.stdout
        stderr_stream: asyncio.StreamReader = proc.stderr

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    _read_stream(stdout_stream, "stdout"),
                    _read_stream(stderr_stream, "stderr"),
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise CommandError(
                f"Command timed out after {timeout}s: {' '.join(cmd)}"
            )

        await proc.wait()
        returncode = proc.returncode if proc.returncode is not None else -1

        result = CommandResult(
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            returncode=returncode,
        )

        if returncode != 0:
            raise CommandError(
                f"Command failed (exit {returncode}): {' '.join(cmd)}\n"
                f"stderr: {result.stderr.strip()}"
            )

        return result

