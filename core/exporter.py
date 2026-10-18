"""
core.exporter
~~~~~~~~~~~~~

Declarative environment exporter.

Translates imperatively installed Nix packages into reproducible
Nix expressions (`shell.nix` / `default.nix`) and structured JSON manifests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .package_manager import PackageInfo


class NixEnvironmentExporter:
    """Generates declarative Nix definitions and manifests from installed packages."""

    @staticmethod
    def generate_shell_nix(packages: List[PackageInfo]) -> str:
        """Generate a valid, reproducible `shell.nix` with pkgs.mkShell."""
        pkg_attrs = []
        for p in packages:
            # Sanitize package names into standard Nix attribute identifiers
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
            data = [
                {"name": p.name, "version": p.version, "raw": p.raw_line}
                for p in packages
            ]
            dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            content = NixEnvironmentExporter.generate_shell_nix(packages)
            dest.write_text(content, encoding="utf-8")

        return str(dest.resolve())
