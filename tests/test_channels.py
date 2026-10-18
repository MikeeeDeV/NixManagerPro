import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.channels import (
    CURATED_CHANNEL_PRESETS,
    NixChannelManager,
    ChannelInfo,
    ChannelError,
)
from core.command_executor import CommandResult


@pytest.fixture
def mock_executor():
    executor = AsyncMock()
    executor.run = AsyncMock(return_value=CommandResult(stdout="success", stderr="", returncode=0))
    return executor


def test_curated_channel_presets_structure():
    assert len(CURATED_CHANNEL_PRESETS) >= 5
    names = [p.name for p in CURATED_CHANNEL_PRESETS]
    assert "nixpkgs-unstable" in names
    assert "nixos-24.05" in names
    assert "home-manager" in names

    for p in CURATED_CHANNEL_PRESETS:
        assert p.url.startswith("https://")
        assert len(p.description) > 10


@pytest.mark.asyncio
async def test_list_channels(mock_executor):
    mock_executor.run = AsyncMock(
        return_value=CommandResult(
            stdout="nixpkgs https://nixos.org/channels/nixpkgs-unstable\nhome-manager https://github.com/nix-community/home-manager\n",
            stderr="",
            returncode=0,
        )
    )
    cm = NixChannelManager(executor=mock_executor)
    channels = await cm.list_channels()

    assert len(channels) == 2
    assert channels[0].name == "nixpkgs"
    assert channels[0].url == "https://nixos.org/channels/nixpkgs-unstable"
    assert channels[1].name == "home-manager"


@pytest.mark.asyncio
async def test_update_single_channel(mock_executor):
    cm = NixChannelManager(executor=mock_executor)
    res = await cm.update_single_channel("nixpkgs")
    assert bool(res) is True
    mock_executor.run.assert_awaited_with("nix-channel --update nixpkgs")


@pytest.mark.asyncio
async def test_check_channel_health():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = await NixChannelManager.check_channel_health("https://nixos.org/channels/nixpkgs-unstable")
        assert res["status"] == "Online"
        assert res["code"] == 200
        assert "latency_ms" in res
