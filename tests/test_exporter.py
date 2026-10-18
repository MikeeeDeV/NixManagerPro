from core.exporter import NixEnvironmentExporter
from core.package_manager import PackageInfo


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
