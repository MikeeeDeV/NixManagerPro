"""
core.exporter
~~~~~~~~~~~~~

Declarative environment and multi-manager software stack backup & restore.

Translates installed packages across Nix, Snap, and Flatpak into:
1. Reproducible Nix expressions (`shell.nix` / `default.nix`).
2. Multi-manager backup manifests (`nixmanager-stack.json`) for 1-click system restoration.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Callable, List, Optional

from .package_manager import NixPackageManager, PackageInfo, PackageOperationError


class NixEnvironmentExporter:
    """Generates declarative Nix definitions and manifests from installed packages."""

    @staticmethod
    def generate_shell_nix(packages: List[PackageInfo]) -> str:
        """Generate a valid, reproducible `shell.nix` with pkgs.mkShell."""
        pkg_attrs = []
        for p in packages:
            if p.source.lower() == "nix" or not p.source:
                clean_name = p.name.strip().replace("-", "_").lower()
                if clean_name:
                    pkg_attrs.append(f"    pkgs.{clean_name}")

        package_list_str = "\n".join(sorted(set(pkg_attrs)))

        return f"""# Generated automatically by NixManager Pro
{{ pkgs ? import <nixpkgs> {{}} }}:

pkgs.mkShell {{
  name = "nix-manager-environment";
  buildInputs = [
{package_list_str}
  ];

  shellHook = ''
    echo "❄️  NixManager Pro environment loaded successfully!"
  '';
}}
"""

    @staticmethod
    def export_to_file(packages: List[PackageInfo], destination_path: str | Path) -> str:
        """Write shell.nix or manifest to disk."""
        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.suffix.lower() == ".json":
            data = {
                "format": "NixManagerPro-Stack",
                "schema_version": "1.0",
                "timestamp": datetime.datetime.now().isoformat(),
                "total_count": len(packages),
                "packages": [
                    {
                        "name": p.name,
                        "version": p.version,
                        "source": p.source,
                        "app_id": p.app_id,
                        "raw_line": p.raw_line,
                    }
                    for p in packages
                ],
            }
            dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            content = NixEnvironmentExporter.generate_shell_nix(packages)
            dest.write_text(content, encoding="utf-8")

        return str(dest.resolve())

    @staticmethod
    def import_from_file(source_path: str | Path) -> List[PackageInfo]:
        """Read and validate a NixManagerPro-Stack JSON manifest."""
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Stack manifest not found: {source_path}")

        raw_data = json.loads(src.read_text(encoding="utf-8"))
        packages_list = []

        # Handle both modern formatted stack and legacy raw array
        items = raw_data.get("packages", []) if isinstance(raw_data, dict) else raw_data

        for item in items:
            name = item.get("name", "").strip()
            if not name:
                continue
            packages_list.append(
                PackageInfo(
                    name=name,
                    version=item.get("version", ""),
                    source=item.get("source", "Nix"),
                    app_id=item.get("app_id", ""),
                    raw_line=item.get("raw_line", ""),
                )
            )

        return packages_list

    @staticmethod
    async def restore_stack(
        packages: List[PackageInfo],
        pkg_manager: NixPackageManager,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> List[str]:
        """
        Batch-installs all packages in the stack.
        """
        results: List[str] = []
        total = len(packages)

        for idx, pkg in enumerate(packages, start=1):
            msg = f"[{idx}/{total}] Restoring {pkg.source} package: {pkg.name}..."
            if progress_cb:
                progress_cb(msg)

            try:
                if pkg.source == "Flatpak":
                    target = pkg.app_id or pkg.name
                    await pkg_manager._exec.run(f"flatpak install -y flathub {target}")
                elif pkg.source == "Snap":
                    await pkg_manager._exec.run(f"snap install {pkg.name}")
                else:
                    await pkg_manager._exec.run(f"nix-env -iA nixpkgs.{pkg.name}")
                results.append(f"✓ {pkg.name} installed successfully.")
            except Exception as exc:
                results.append(f"✗ Failed to install {pkg.name}: {exc}")

        return results
