"""
core.package_manager
~~~~~~~~~~~~~~~~~~~~

High‑level façade over the Nix CLI for package CRUD operations.

Every method is an ``async`` coroutine that delegates to the shared
:class:`~core.command_executor.AsyncCommandExecutor`.  The calling code
(usually a background worker thread) wraps the call in ``asyncio.run()``.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
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


@dataclass
class UpdateCandidate:
    """Represents an installed application with an upgrade available."""

    name: str
    current_version: str
    new_version: str
    source: str = "Nix"          # "Nix", "Flatpak", "Snap"
    app_id: str = ""


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

    @staticmethod
    def _parse_line(line: str) -> PackageInfo:
        line = line.strip()
        match = re.match(r"^(.+)-(\d.*)$", line)
        if match:
            return PackageInfo(
                name=match.group(1),
                version=match.group(2),
                source="Nix",
                raw_line=line,
            )
        return PackageInfo(name=line, version="?", source="Nix", raw_line=line)

    async def list_flake_profiles(self) -> List[PackageInfo]:
        """
        Query modern Nix 2.4+ flakes profile via ``nix profile list --json``.
        """
        try:
            res = await self._exec.run(
                'nix --extra-experimental-features "nix-command flakes" profile list --json',
                timeout=6,
            )
            data = json.loads(res.stdout)
            elements = data.get("elements", {})
            pkgs: List[PackageInfo] = []
            for name, meta in elements.items():
                store_paths = meta.get("storePaths", [])
                version = "flake"
                if store_paths:
                    sp = store_paths[0].rstrip("/")
                    parts = sp.rsplit("-", 1)
                    if len(parts) == 2 and parts[1] and parts[1][0].isdigit():
                        version = parts[1]
                pkgs.append(PackageInfo(name=name, version=version, source="Nix (Flake)", raw_line=f"{name}-{version}"))
            return pkgs
        except Exception:
            return []

    async def list_installed(self) -> List[PackageInfo]:
        """
        Parse the output of ``nix-env -q`` and ``nix profile list`` to return structured Nix package data.
        """
        packages: List[PackageInfo] = []
        try:
            result = await self._exec.run("nix-env -q")
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                packages.append(self._parse_line(line))
        except Exception:
            pass

        # Query flakes profile packages if supported
        try:
            flake_pkgs = await self.list_flake_profiles()
            existing_names = {p.name for p in packages}
            for fp in flake_pkgs:
                if fp.name not in existing_names:
                    packages.append(fp)
        except Exception:
            pass

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
        """Standard uninstall using native package manager (retains user configs)."""
        try:
            if pkg.source == "Flatpak":
                target = pkg.app_id or pkg.name
                await self._exec.run(f"flatpak uninstall -y {target}")
            elif pkg.source == "Snap":
                await self._exec.run(f"snap remove {pkg.name}")
            elif pkg.source == "Nix (Flake)":
                await self._exec.run(f'nix --extra-experimental-features "nix-command flakes" profile remove {pkg.name}')
            else:
                await self._exec.run(f"nix-env -e {pkg.name}")
        except CommandError as exc:
            raise PackageOperationError(
                f"Failed to uninstall {pkg.source} package '{pkg.name}': {exc}"
            ) from exc

    async def purge_generic(self, pkg: PackageInfo) -> str:
        """
        Deep Purge: completely eradicates the package, its user configurations,
        application cache, desktop entries, and runs store garbage collection.
        """
        import os
        import shutil

        log_messages: List[str] = []
        name = pkg.name
        home = os.path.expanduser("~")

        try:
            if pkg.source == "Snap":
                await self._exec.run(f"snap remove --purge {name}")
                log_messages.append(f"✓ Removed snap package with --purge flag: {name}")
                snap_dir = os.path.join(home, "snap", name)
                if os.path.exists(snap_dir):
                    shutil.rmtree(snap_dir, ignore_errors=True)
                    log_messages.append(f"✓ Cleaned snap data directory: {snap_dir}")

            elif pkg.source == "Flatpak":
                target = pkg.app_id or name
                await self._exec.run(f"flatpak uninstall --delete-data -y {target}")
                log_messages.append(f"✓ Removed flatpak with --delete-data: {target}")
                var_dir = os.path.join(home, ".var", "app", target)
                if os.path.exists(var_dir):
                    shutil.rmtree(var_dir, ignore_errors=True)
                    log_messages.append(f"✓ Purged flatpak app data: {var_dir}")

            elif pkg.source == "Nix (Flake)":
                await self._exec.run(f'nix --extra-experimental-features "nix-command flakes" profile remove {name}')
                log_messages.append(f"✓ Removed {name} from Nix flakes profile")

            else:
                # Nix Package Deep Purge
                await self._exec.run(f"nix-env -e {name}")
                log_messages.append(f"✓ Removed {name} from active Nix profile")

                # Purge user directories
                user_dirs = [
                    os.path.join(home, ".config", name),
                    os.path.join(home, ".cache", name),
                    os.path.join(home, ".local", "share", name),
                ]
                for udir in user_dirs:
                    if os.path.exists(udir):
                        shutil.rmtree(udir, ignore_errors=True)
                        log_messages.append(f"✓ Purged user directory: {udir}")

                # Remove desktop launcher
                apps_dir = os.path.join(home, ".local", "share", "applications")
                if os.path.isdir(apps_dir):
                    for f in os.listdir(apps_dir):
                        if f.startswith(name) and f.endswith(".desktop"):
                            try:
                                os.remove(os.path.join(apps_dir, f))
                                log_messages.append(f"✓ Removed desktop launcher: {f}")
                            except Exception:
                                pass

                # Deep store garbage collection
                try:
                    await self._exec.run("nix-collect-garbage -d")
                    log_messages.append("✓ Executed deep Nix store garbage collection (nix-collect-garbage -d)")
                except Exception:
                    try:
                        await self._exec.run("nix-store --gc")
                        log_messages.append("✓ Store garbage collection finished")
                    except Exception:
                        pass

            return "\n".join(log_messages)

        except CommandError as exc:
            raise PackageOperationError(
                f"Failed to deep purge {pkg.source} package '{pkg.name}': {exc}"
            ) from exc

    async def check_updates(self) -> List[UpdateCandidate]:
        """
        Scan Nix, Snap, and Flatpak concurrently for available package upgrades
        with strict timeouts to prevent channel evaluation hangs.
        """
        candidates: List[UpdateCandidate] = []

        async def _check_nix() -> List[UpdateCandidate]:
            nix_candidates: List[UpdateCandidate] = []
            try:
                # Target installed packages rather than global nixpkgs to prevent slow evaluations
                installed_res = await self._exec.run("nix-env -q")
                installed_names = [line.strip().split("-")[0] for line in installed_res.stdout.splitlines() if line.strip()]
                target_str = " ".join(installed_names) if installed_names else ""
                cmd = f"nix-env -u --dry-run {target_str}" if target_str else "nix-env -u --dry-run"

                res = await asyncio.wait_for(self._exec.run(cmd), timeout=4.0)
                import re
                for line in res.stdout.splitlines():
                    match = re.search(r"upgrade[d]? ['\"]?(.*?)['\"]? to ['\"]?(.*?)['\"]?", line, re.IGNORECASE)
                    if match:
                        cur_str, new_str = match.group(1), match.group(2)
                        cur_info = self._parse_line(cur_str)
                        new_info = self._parse_line(new_str)
                        nix_candidates.append(
                            UpdateCandidate(
                                name=cur_info.name or cur_str,
                                current_version=cur_info.version or "installed",
                                new_version=new_info.version or "latest",
                                source="Nix",
                            )
                        )
            except Exception:
                pass
            return nix_candidates

        async def _check_snap() -> List[UpdateCandidate]:
            snap_candidates: List[UpdateCandidate] = []
            if shutil.which("snap"):
                try:
                    res = await asyncio.wait_for(self._exec.run("snap refresh --list"), timeout=5.0)
                    lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 2 and parts[0].lower() != "name":
                            snap_candidates.append(
                                UpdateCandidate(
                                    name=parts[0],
                                    current_version="installed",
                                    new_version=parts[1],
                                    source="Snap",
                                )
                            )
                except Exception:
                    pass
            return snap_candidates

        async def _check_flatpak() -> List[UpdateCandidate]:
            flatpak_candidates: List[UpdateCandidate] = []
            if shutil.which("flatpak"):
                try:
                    res = await asyncio.wait_for(self._exec.run("flatpak remote-ls --updates"), timeout=5.0)
                    for line in res.stdout.splitlines():
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if parts[0].lower() == "name":
                                continue
                            app_name = parts[0]
                            app_id = parts[1] if len(parts) > 1 else app_name
                            version = parts[2] if len(parts) > 2 else "latest"
                            flatpak_candidates.append(
                                UpdateCandidate(
                                    name=app_name,
                                    current_version="installed",
                                    new_version=version,
                                    source="Flatpak",
                                    app_id=app_id,
                                )
                            )
                except Exception:
                    pass
            return flatpak_candidates

        results = await asyncio.gather(_check_nix(), _check_snap(), _check_flatpak())
        for res_list in results:
            candidates.extend(res_list)

        return candidates

    async def upgrade_candidate(self, candidate: UpdateCandidate) -> str:
        """Upgrade a single package candidate."""
        try:
            if candidate.source == "Snap":
                res = await self._exec.run(f"snap refresh {candidate.name}")
                return res.stdout or f"Updated snap: {candidate.name}"
            elif candidate.source == "Flatpak":
                target = candidate.app_id or candidate.name
                res = await self._exec.run(f"flatpak update -y {target}")
                return res.stdout or f"Updated flatpak: {target}"
            else:
                res = await self._exec.run(f"nix-env -u {candidate.name}")
                return res.stdout or f"Updated nix package: {candidate.name}"
        except CommandError as exc:
            raise PackageOperationError(f"Upgrade failed for {candidate.name}: {exc}") from exc

    async def upgrade_all_generic(self) -> str:
        """Upgrade all packages across Nix, Snap, and Flatpak."""
        logs = []
        try:
            res_nix = await self._exec.run("nix-env -u")
            logs.append(f"Nix Upgrade: {res_nix.stdout.strip() or 'Success'}")
        except Exception as e:
            logs.append(f"Nix Upgrade: {e}")

        if shutil.which("flatpak"):
            try:
                res_flat = await self._exec.run("flatpak update -y")
                logs.append(f"Flatpak Upgrade: {res_flat.stdout.strip() or 'Success'}")
            except Exception as e:
                logs.append(f"Flatpak Upgrade: {e}")

        if shutil.which("snap"):
            try:
                res_snap = await self._exec.run("snap refresh")
                logs.append(f"Snap Upgrade: {res_snap.stdout.strip() or 'Success'}")
            except Exception as e:
                logs.append(f"Snap Upgrade: {e}")

        return "\n".join(logs)

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

