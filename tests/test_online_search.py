import pytest
from unittest.mock import patch, MagicMock
from core.online_search import OnlineSearchService


@pytest.mark.asyncio
async def test_search_flathub_mapping():
    mock_payload = b'{"hits":[{"name":"Obsidian","app_id":"md.obsidian.Obsidian","summary":"Markdown note-taking app","categories":["Utility"]}]}'

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = await OnlineSearchService.search_flathub("obsidian")
        assert len(results) == 1
        hit = results[0]
        assert hit.name == "Obsidian"
        assert hit.attr == "md.obsidian.Obsidian"
        assert "Markdown note-taking" in hit.description
        assert "flathub.org/apps/md.obsidian.Obsidian" in hit.homepage


@pytest.mark.asyncio
async def test_search_flathub_empty_query():
    results = await OnlineSearchService.search_flathub("")
    assert results == []
