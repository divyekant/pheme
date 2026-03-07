import os
import pytest
from unittest.mock import AsyncMock, patch
from server.server import create_pheme_server, MAX_MESSAGE_LENGTH


@pytest.fixture
def env_channels(monkeypatch):
    monkeypatch.setenv("PHEME_SLACK", "slack://token/channel")
    monkeypatch.setenv("PHEME_TELEGRAM", "tgram://bot/chat")


class TestListChannels:
    async def test_returns_configured_channels(self, env_channels):
        server = create_pheme_server()
        result = await server._list_channels()
        channels = result["channels"]
        names = [c["name"] for c in channels]
        assert "slack" in names
        assert "telegram" in names
        assert all(c["configured"] is True for c in channels)

    async def test_empty_when_no_channels(self, monkeypatch):
        for key in list(os.environ.keys()):
            if key.startswith("PHEME_"):
                monkeypatch.delenv(key)
        server = create_pheme_server()
        result = await server._list_channels()
        assert result["channels"] == []


class TestGetRoutes:
    async def test_returns_route_config(self, env_channels):
        server = create_pheme_server()
        result = await server._get_routes()
        assert "critical" in result
        assert "normal" in result
        assert isinstance(result["critical"], list)


class TestSend:
    async def test_send_to_explicit_channel(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test", channel="slack")
        assert result["success"] is True
        assert "slack" in result["delivered"]

    async def test_send_to_multiple_channels(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test", channels=["slack", "telegram"])
        assert result["success"] is True
        assert len(result["delivered"]) == 2

    async def test_send_with_urgency(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test", urgency="high")
        assert result["success"] is True

    async def test_send_no_args_defaults_to_normal(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="test")
        assert result["success"] is True

    async def test_send_to_unconfigured_channel_fails(self, env_channels):
        server = create_pheme_server()
        result = await server._send(message="test", channel="discord")
        assert result["success"] is False
        assert "No configured channels matched" in result.get("error", "")

    async def test_send_handles_delivery_failure(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=False):
            result = await server._send(message="test", channel="slack")
        assert result["success"] is False
        assert "slack" in result["failed"]


class TestMessageLengthCap:
    async def test_rejects_message_over_limit(self, env_channels):
        server = create_pheme_server()
        long_msg = "x" * (MAX_MESSAGE_LENGTH + 1)
        result = await server._send(message=long_msg, channel="slack")
        assert result["success"] is False
        assert "too long" in result["error"].lower()

    async def test_allows_message_at_limit(self, env_channels):
        server = create_pheme_server()
        msg = "x" * MAX_MESSAGE_LENGTH
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message=msg, channel="slack")
        assert result["success"] is True


class TestSecretDetection:
    async def test_warns_on_jwt_in_message(self, env_channels, caplog):
        server = create_pheme_server()
        jwt_msg = "Here is a token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            import logging
            with caplog.at_level(logging.WARNING, logger="pheme"):
                result = await server._send(message=jwt_msg, channel="slack")
        assert result["success"] is True  # warns but doesn't block
        assert "sensitive data" in caplog.text.lower()

    async def test_warns_on_api_key_pattern(self, env_channels, caplog):
        server = create_pheme_server()
        msg = 'config: api_key="sk_live_abc123def456ghi789"'
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            import logging
            with caplog.at_level(logging.WARNING, logger="pheme"):
                result = await server._send(message=msg, channel="slack")
        assert "sensitive data" in caplog.text.lower()

    async def test_no_warning_on_normal_message(self, env_channels, caplog):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            import logging
            with caplog.at_level(logging.WARNING, logger="pheme"):
                await server._send(message="Deploy complete", channel="slack")
        assert "sensitive data" not in caplog.text.lower()


class TestTestChannel:
    async def test_configured_channel(self, env_channels):
        server = create_pheme_server()
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._test_channel("slack")
        assert result["success"] is True

    async def test_unconfigured_channel(self, env_channels):
        server = create_pheme_server()
        result = await server._test_channel("discord")
        assert result["success"] is False
        assert "not configured" in result["error"]
