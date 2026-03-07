"""Integration test — verifies the full MCP server wiring works end-to-end."""
from unittest.mock import AsyncMock, patch
from server.server import create_pheme_server


def _setup_env(monkeypatch):
    monkeypatch.setenv("PHEME_SLACK", "slack://tokenA/tokenB/tokenC/#general")
    monkeypatch.setenv("PHEME_TELEGRAM", "tgram://bot_token/chat_id")


class TestEndToEnd:
    async def test_full_flow(self, monkeypatch):
        """Simulate an agent discovering channels, checking routes, then sending."""
        _setup_env(monkeypatch)
        server = create_pheme_server()

        # Step 1: Agent discovers channels
        channels = await server._list_channels()
        assert len(channels["channels"]) == 2

        # Step 2: Agent checks routes
        routes = await server._get_routes()
        assert "critical" in routes

        # Step 3: Agent sends with urgency
        with patch("apprise.Apprise.async_notify", new_callable=AsyncMock, return_value=True):
            result = await server._send(message="PR #42 ready for review", urgency="high", title="Argos")
        assert result["success"] is True
        assert len(result["delivered"]) > 0
