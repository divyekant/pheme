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


class TestSend:
    @pytest.mark.asyncio
    async def test_send_to_explicit_channel(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test", channel="slack")
        assert result["success"] is True
        assert "slack" in result["delivered"]

    @pytest.mark.asyncio
    async def test_send_to_multiple_channels(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test", channels=["slack", "telegram"])
        assert result["success"] is True
        assert len(result["delivered"]) == 2

    @pytest.mark.asyncio
    async def test_send_with_urgency(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test", urgency="high")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_no_args_defaults_to_normal(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_to_unconfigured_channel_fails(self, env_channels):
        server = create_pheme_server()
        result = await server._send(message="test", channel="discord")
        assert result["success"] is False
        assert "No configured channels matched" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_send_handles_delivery_failure(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=False):
            result = await server._send(message="test", channel="slack")
        assert result["success"] is False
        assert "slack" in result["failed"]


class TestTestChannel:
    @pytest.mark.asyncio
    async def test_configured_channel(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._test_channel("slack")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unconfigured_channel(self, env_channels):
        server = create_pheme_server()
        result = await server._test_channel("discord")
        assert result["success"] is False
        assert "not configured" in result["error"]
