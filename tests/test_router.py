import pytest
from server.router import Router


@pytest.fixture
def router():
    channels = {
        "slack": "slack://token/channel",
        "telegram": "tgram://bot/chat",
        "system": "macosx://",
    }
    routes = {
        "critical": ["slack", "telegram", "system"],
        "high": ["slack"],
        "normal": ["slack"],
        "low": ["session"],
    }
    return Router(channels, routes)


class TestResolveChannels:
    def test_explicit_single_channel(self, router):
        result = router.resolve(channel="slack")
        assert result == {"slack": "slack://token/channel"}

    def test_explicit_channels_list(self, router):
        result = router.resolve(channels=["slack", "telegram"])
        assert "slack" in result
        assert "telegram" in result
        assert len(result) == 2

    def test_urgency_routing(self, router):
        result = router.resolve(urgency="critical")
        assert "slack" in result
        assert "telegram" in result
        assert "system" in result

    def test_default_urgency_when_nothing_specified(self, router):
        result = router.resolve()
        assert "slack" in result  # normal routes to slack

    def test_unconfigured_channel_excluded(self, router):
        result = router.resolve(channel="discord")
        assert result == {}

    def test_unconfigured_channels_in_route_excluded(self, router):
        # "session" is in low route but not in configured channels
        result = router.resolve(urgency="low")
        assert result == {}

    def test_unknown_urgency_falls_back_to_normal(self, router):
        result = router.resolve(urgency="unknown_level")
        assert "slack" in result

    def test_channel_takes_precedence_over_urgency(self, router):
        result = router.resolve(channel="telegram", urgency="low")
        assert result == {"telegram": "tgram://bot/chat"}
