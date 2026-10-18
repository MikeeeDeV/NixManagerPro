import pytest
from unittest.mock import AsyncMock
from core.exporter import NixEnvironmentExporter
from core.package_manager import NixPackageManager, PackageInfo
from core.command_executor import CommandResult


def test_generate_shell_nix():
    packages = [
        PackageInfo(name="ripgrep", version="14.1.0"),
        PackageInfo(name="htop", version="3.3.0"),
        PackageInfo(name="neovim", version="0.10.0"),
    ]

    content = NixEnvironmentExporter.generate_shell_nix(packages)

    assert "pkgs.mkShell" in content
    assert "pkgs.ripgrep" in content
    assert "pkgs.htop" in content
    assert "pkgs.neovim" in content


def test_export_and_import_json_stack(tmp_path):
    dest = tmp_path / "nixmanager-stack.json"
    packages = [
        PackageInfo(name="htop", version="3.3.0", source="Nix"),
        PackageInfo(name="vlc", version="3.0.18", source="Snap"),
        PackageInfo(name="Spotify", version="1.2.0", source="Flatpak", app_id="com.spotify.Client"),
    ]

    saved = NixEnvironmentExporter.export_to_file(packages, dest)
    assert dest.exists()
    assert saved == str(dest.resolve())

    imported = NixEnvironmentExporter.import_from_file(dest)
    assert len(imported) == 3
    assert imported[0].name == "htop"
    assert imported[1].source == "Snap"
    assert imported[2].app_id == "com.spotify.Client"


@pytest.mark.asyncio
async def test_restore_stack():
    executor = AsyncMock()
    executor.run = AsyncMock(return_value=CommandResult(stdout="ok", stderr="", returncode=0))
    pm = NixPackageManager(executor=executor)

    packages = [
        PackageInfo(name="htop", version="3.3.0", source="Nix"),
        PackageInfo(name="vlc", version="3.0.18", source="Snap"),
        PackageInfo(name="Spotify", version="1.2.0", source="Flatpak", app_id="com.spotify.Client"),
    ]

    results = await NixEnvironmentExporter.restore_stack(packages, pm)
    assert len(results) == 3
    assert all("installed successfully" in r for r in results)
    executor.run.assert_any_await("nix-env -iA nixpkgs.htop")
    executor.run.assert_any_await("snap install vlc")
    executor.run.assert_any_await("flatpak install -y flathub com.spotify.Client")
