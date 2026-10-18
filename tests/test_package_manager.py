import pytest
from unittest.mock import AsyncMock, patch
from core.package_manager import NixPackageManager, PackageInfo
from core.command_executor import CommandResult


@pytest.fixture
def mock_executor():
    executor = AsyncMock()
    executor.run = AsyncMock(return_value=CommandResult(stdout="success", stderr="", returncode=0))
    return executor


@pytest.mark.asyncio
async def test_uninstall_generic_nix(mock_executor):
    pm = NixPackageManager(executor=mock_executor)
    pkg = PackageInfo(name="htop", version="3.2.0", source="Nix")

    await pm.uninstall_generic(pkg)
    mock_executor.run.assert_awaited_with("nix-env -e htop")


@pytest.mark.asyncio
async def test_uninstall_generic_snap(mock_executor):
    pm = NixPackageManager(executor=mock_executor)
    pkg = PackageInfo(name="vlc", version="3.0.18", source="Snap")

    await pm.uninstall_generic(pkg)
    mock_executor.run.assert_awaited_with("snap remove vlc")


@pytest.mark.asyncio
async def test_uninstall_generic_flatpak(mock_executor):
    pm = NixPackageManager(executor=mock_executor)
    pkg = PackageInfo(name="Spotify", version="1.2.0", app_id="com.spotify.Client", source="Flatpak")

    await pm.uninstall_generic(pkg)
    mock_executor.run.assert_awaited_with("flatpak uninstall -y com.spotify.Client")


@pytest.mark.asyncio
async def test_purge_generic_nix(mock_executor, tmp_path):
    pm = NixPackageManager(executor=mock_executor)
    pkg = PackageInfo(name="testpkg", version="1.0.0", source="Nix")

    with patch("os.path.expanduser", return_value=str(tmp_path)):
        # create fake user config & cache dirs
        cfg_dir = tmp_path / ".config" / "testpkg"
        cfg_dir.mkdir(parents=True)
        cache_dir = tmp_path / ".cache" / "testpkg"
        cache_dir.mkdir(parents=True)

        res = await pm.purge_generic(pkg)

        assert not cfg_dir.exists()
        assert not cache_dir.exists()
        assert "Purged user directory" in res
        assert "Removed testpkg from active Nix profile" in res


@pytest.mark.asyncio
async def test_purge_generic_snap(mock_executor, tmp_path):
    pm = NixPackageManager(executor=mock_executor)
    pkg = PackageInfo(name="testsnap", version="2.0", source="Snap")

    with patch("os.path.expanduser", return_value=str(tmp_path)):
        snap_dir = tmp_path / "snap" / "testsnap"
        snap_dir.mkdir(parents=True)

        res = await pm.purge_generic(pkg)

        assert not snap_dir.exists()
        assert "Removed snap package with --purge flag: testsnap" in res
        mock_executor.run.assert_any_await("snap remove --purge testsnap")


@pytest.mark.asyncio
async def test_purge_generic_flatpak(mock_executor, tmp_path):
    pm = NixPackageManager(executor=mock_executor)
    pkg = PackageInfo(name="testflat", version="3.0", app_id="org.test.Flat", source="Flatpak")

    with patch("os.path.expanduser", return_value=str(tmp_path)):
        var_dir = tmp_path / ".var" / "app" / "org.test.Flat"
        var_dir.mkdir(parents=True)

        res = await pm.purge_generic(pkg)

        assert not var_dir.exists()
        assert "Removed flatpak with --delete-data: org.test.Flat" in res
        mock_executor.run.assert_any_await("flatpak uninstall --delete-data -y org.test.Flat")
