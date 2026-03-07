import os
import pytest
from unittest.mock import AsyncMock, patch
from server.server import create_pheme_server


@pytest.fixture
def env_channels(monkeypatch):
    monkeypatch.setenv("PHEME_SLACK", "slack://token/channel")
    monkeypatch.setenv("PHEME_TELEGRAM", "tgram://bot/chat")


class TestListChannels:
    @pytest.mark.asyncio
    async def test_returns_configured_channels(self, env_channels):
        server = create_pheme_server()
        result = await server._list_channels()
        channels = result["channels"]
        names = [c["name"] for c in channels]
        assert "slack" in names
        assert "telegram" in names
        assert all(c["configured"] is True for c in channels)

    @pytest.mark.asyncio
    async def test_empty_when_no_channels(self, monkeypatch):
        for key in list(os.environ.keys()):
            if key.startswith("PHEME_"):
                monkeypatch.delenv(key)
        server = create_pheme_server()
        result = await server._list_channels()
        assert result["channels"] == []


class TestGetRoutes:
    @pytest.mark.asyncio
    async def test_returns_route_config(self, env_channels):
        server = create_pheme_server()
        result = await server._get_routes()
        assert "critical" in result
        assert "normal" in result
        assert isinstance(result["critical"], list)
