import os
import pytest
from server.config import discover_channels, load_routes


class TestDiscoverChannels:
    def test_finds_pheme_env_vars(self, monkeypatch):
        monkeypatch.setenv("PHEME_SLACK", "slack://token/channel")
        monkeypatch.setenv("PHEME_TELEGRAM", "tgram://bot/chat")
        monkeypatch.delenv("PHEME_SYSTEM", raising=False)
        channels = discover_channels()
        assert "slack" in channels
        assert channels["slack"] == "slack://token/channel"
        assert "telegram" in channels
        assert channels["telegram"] == "tgram://bot/chat"

    def test_ignores_non_pheme_vars(self, monkeypatch):
        monkeypatch.setenv("PHEME_SLACK", "slack://token/channel")
        monkeypatch.setenv("HOME", "/Users/test")
        channels = discover_channels()
        assert "slack" in channels
        assert "home" not in channels

    def test_lowercases_channel_names(self, monkeypatch):
        monkeypatch.setenv("PHEME_SLACK", "slack://token/channel")
        channels = discover_channels()
        assert "slack" in channels

    def test_empty_when_no_pheme_vars(self, monkeypatch):
        for key in list(os.environ.keys()):
            if key.startswith("PHEME_"):
                monkeypatch.delenv(key)
        channels = discover_channels()
        assert channels == {}


class TestLoadRoutes:
    def test_loads_default_routes(self, tmp_path):
        route_file = tmp_path / "routes.yaml"
        route_file.write_text("""
routes:
  critical:
    - slack
    - telegram
  high:
    - slack
  normal:
    - slack
  low:
    - session
""")
        routes = load_routes(str(route_file))
        assert routes["critical"] == ["slack", "telegram"]
        assert routes["high"] == ["slack"]
        assert routes["normal"] == ["slack"]
        assert routes["low"] == ["session"]

    def test_returns_defaults_when_file_missing(self):
        routes = load_routes("/nonexistent/path.yaml")
        assert "normal" in routes

    def test_returns_defaults_when_file_invalid(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("not: valid: yaml: [[[")
        routes = load_routes(str(bad_file))
        assert "normal" in routes
