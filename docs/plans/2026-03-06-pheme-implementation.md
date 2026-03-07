# Pheme Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python MCP server wrapping Apprise for universal agent-to-human notifications, packaged as a CC plugin.

**Architecture:** FastMCP server with 4 tools (send, list_channels, test_channel, get_routes). Config loaded from PHEME_* env vars (channel URLs) and YAML (urgency routes). Apprise library handles channel delivery.

**Tech Stack:** Python 3.10+, FastMCP (mcp[cli]), Apprise, PyYAML, pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pheme/.claude-plugin/plugin.json`
- Create: `pheme/.gitignore`
- Create: `pheme/pyproject.toml`
- Create: `pheme/server/__init__.py`
- Create: `pheme/config/default-routes.yaml`

**Step 1: Create plugin manifest**

```json
// .claude-plugin/plugin.json
{
  "name": "pheme",
  "version": "0.1.0",
  "description": "Universal communication layer -- agents notify humans across any channel",
  "author": "Divyekant",
  "license": "MIT"
}
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "pheme"
version = "0.1.0"
description = "Universal communication layer for agent-to-human notifications"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.2.0",
    "apprise>=1.9.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

**Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.env
```

**Step 4: Create empty server/__init__.py**

```python
# pheme/server/__init__.py
```

**Step 5: Create default routes config**

```yaml
# config/default-routes.yaml
routes:
  critical:
    - slack
    - telegram
    - system
  high:
    - slack
  normal:
    - slack
  low:
    - session
```

**Step 6: Set up virtual environment and install deps**

Run:
```bash
cd /Users/divyekant/Projects/pheme
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Step 7: Commit**

```bash
git add .claude-plugin/ pyproject.toml .gitignore server/__init__.py config/
git commit -m "scaffold: project structure, deps, plugin manifest"
```

---

### Task 2: Config Module

**Files:**
- Create: `server/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing tests**

```python
# tests/test_config.py
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
        assert len([k for k in channels if k != "slack"]) == 0 or "home" not in channels

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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server.config'`

**Step 3: Write the implementation**

```python
# server/config.py
"""Configuration loading for Pheme.

Channels are discovered from PHEME_* environment variables.
Routes are loaded from YAML config files.
"""
import os
import yaml

DEFAULT_ROUTES = {
    "critical": ["slack", "telegram", "system"],
    "high": ["slack"],
    "normal": ["slack"],
    "low": ["session"],
}


def discover_channels() -> dict[str, str]:
    """Discover configured channels from PHEME_* env vars.

    Each env var PHEME_<NAME>=<apprise_url> defines a channel.
    Returns dict mapping lowercase channel name to Apprise URL.
    """
    channels = {}
    for key, value in os.environ.items():
        if key.startswith("PHEME_") and value:
            name = key[len("PHEME_"):].lower()
            channels[name] = value
    return channels


def load_routes(path: str) -> dict[str, list[str]]:
    """Load urgency -> channel routing from YAML file.

    Falls back to DEFAULT_ROUTES if file is missing or invalid.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if data and "routes" in data and isinstance(data["routes"], dict):
            return data["routes"]
    except (FileNotFoundError, yaml.YAMLError, OSError):
        pass
    return DEFAULT_ROUTES.copy()
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_config.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add server/config.py tests/test_config.py
git commit -m "feat: config module — channel discovery and route loading"
```

---

### Task 3: Router Module

**Files:**
- Create: `server/router.py`
- Create: `tests/test_router.py`

**Step 1: Write the failing tests**

```python
# tests/test_router.py
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_router.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server.router'`

**Step 3: Write the implementation**

```python
# server/router.py
"""Urgency-based channel routing for Pheme."""


class Router:
    """Resolves which channels to send to based on explicit selection or urgency."""

    def __init__(self, channels: dict[str, str], routes: dict[str, list[str]]):
        self._channels = channels
        self._routes = routes

    def resolve(
        self,
        channel: str | None = None,
        channels: list[str] | None = None,
        urgency: str | None = None,
    ) -> dict[str, str]:
        """Resolve channel names to Apprise URLs.

        Priority: channel > channels > urgency > default (normal).
        Only returns channels that are actually configured.
        """
        if channel:
            names = [channel]
        elif channels:
            names = channels
        else:
            level = urgency or "normal"
            names = self._routes.get(level, self._routes.get("normal", []))

        return {
            name: self._channels[name]
            for name in names
            if name in self._channels
        }
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_router.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add server/router.py tests/test_router.py
git commit -m "feat: router module — urgency-based channel resolution"
```

---

### Task 4: MCP Server — list_channels and get_routes Tools

**Files:**
- Create: `server/server.py`
- Create: `tests/test_server.py`

**Step 1: Write the failing tests**

```python
# tests/test_server.py
import os
import pytest
import pytest_asyncio
from unittest.mock import patch
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_server.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server.server'`

**Step 3: Write the implementation**

```python
# server/server.py
"""Pheme MCP Server — universal agent-to-human notification layer.

Wraps Apprise to deliver notifications across 100+ channels.
Agents call MCP tools; Pheme routes to the right channels.
"""
import os
import logging
import sys

import apprise
from mcp.server.fastmcp import FastMCP

from server.config import discover_channels, load_routes
from server.router import Router

logger = logging.getLogger("pheme")
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)

# Route config search order: project > global > default
ROUTE_CONFIG_PATHS = [
    os.path.join(os.getcwd(), ".claude", "pheme-routes.yaml"),
    os.path.expanduser("~/.claude/pheme-routes.yaml"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "default-routes.yaml"),
]


class PhemeServer:
    """Pheme server encapsulating config, router, and MCP tools."""

    def __init__(self):
        self.channels = discover_channels()
        self.routes = self._load_first_route_config()
        self.router = Router(self.channels, self.routes)
        self.mcp = FastMCP("pheme")
        self._register_tools()

    def _load_first_route_config(self) -> dict[str, list[str]]:
        for path in ROUTE_CONFIG_PATHS:
            if os.path.isfile(path):
                return load_routes(path)
        return load_routes("")  # returns defaults

    def _register_tools(self):
        @self.mcp.tool()
        async def list_channels() -> dict:
            """List all configured notification channels.

            Returns which channels are available based on PHEME_* env vars.
            """
            return await self._list_channels()

        @self.mcp.tool()
        async def get_routes() -> dict:
            """Get the current urgency-to-channel routing configuration.

            Shows which channels each urgency level maps to.
            """
            return await self._get_routes()

        @self.mcp.tool()
        async def send(
            message: str,
            channel: str | None = None,
            channels: list[str] | None = None,
            urgency: str | None = None,
            title: str | None = None,
            context: dict | None = None,
            format: str = "text",
        ) -> dict:
            """Send a notification to humans via configured channels.

            Agents use this to notify humans about events, approvals, errors, etc.
            Specify exact channels OR an urgency level to let routing decide.

            Args:
                message: The notification content.
                channel: Single channel name (e.g. "slack").
                channels: Multiple channel names (e.g. ["slack", "telegram"]).
                urgency: Route by urgency: "low", "normal", "high", "critical".
                title: Optional notification title/subject.
                context: Optional structured metadata (repo, issue, action, etc.).
                format: Message format: "text", "markdown", or "html".
            """
            return await self._send(message, channel, channels, urgency, title, context, format)

        @self.mcp.tool()
        async def test_channel(channel: str) -> dict:
            """Send a test notification to verify a channel is working.

            Args:
                channel: The channel name to test (e.g. "slack").
            """
            return await self._test_channel(channel)

    async def _list_channels(self) -> dict:
        return {
            "channels": [
                {"name": name, "configured": True}
                for name in sorted(self.channels.keys())
            ]
        }

    async def _get_routes(self) -> dict:
        return self.routes

    async def _send(
        self,
        message: str,
        channel: str | None = None,
        channels: list[str] | None = None,
        urgency: str | None = None,
        title: str | None = None,
        context: dict | None = None,
        format: str = "text",
    ) -> dict:
        resolved = self.router.resolve(channel=channel, channels=channels, urgency=urgency)

        if not resolved:
            return {"success": False, "delivered": [], "failed": [], "error": "No configured channels matched"}

        body_format = apprise.NotifyFormat.TEXT
        if format == "markdown":
            body_format = apprise.NotifyFormat.MARKDOWN
        elif format == "html":
            body_format = apprise.NotifyFormat.HTML

        delivered = []
        failed = []

        for name, url in resolved.items():
            ap = apprise.Apprise()
            ap.add(url)
            ok = await ap.async_notify(body=message, title=title or "", body_format=body_format)
            if ok:
                delivered.append(name)
            else:
                failed.append(name)

        return {
            "success": len(failed) == 0 and len(delivered) > 0,
            "delivered": delivered,
            "failed": failed,
        }

    async def _test_channel(self, channel: str) -> dict:
        if channel not in self.channels:
            return {"success": False, "error": f"Channel '{channel}' not configured. Set PHEME_{channel.upper()} env var."}
        return await self._send(
            message=f"Pheme test -- '{channel}' channel is working.",
            channel=channel,
            title="Pheme Test",
        )


def create_pheme_server() -> PhemeServer:
    """Factory function for creating a PhemeServer instance."""
    return PhemeServer()


# Entry point
server = create_pheme_server()
mcp = server.mcp
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_server.py::TestListChannels tests/test_server.py::TestGetRoutes -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add server/server.py tests/test_server.py
git commit -m "feat: MCP server with list_channels and get_routes tools"
```

---

### Task 5: MCP Server — send and test_channel Tools

**Files:**
- Modify: `tests/test_server.py`

**Step 1: Write the failing tests**

Add to `tests/test_server.py`:

```python
from unittest.mock import AsyncMock, patch


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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest tests/test_server.py::TestSend tests/test_server.py::TestTestChannel -v`
Expected: PASS (implementation already in Task 4's server.py)

Note: Since we wrote send and test_channel in Task 4, these should pass immediately. If any fail, debug and fix.

**Step 3: Run full test suite**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest -v`
Expected: All tests PASS (config: 7, router: 8, server: 11 = 26 total)

**Step 4: Commit**

```bash
git add tests/test_server.py
git commit -m "test: send and test_channel tool tests"
```

---

### Task 6: CC Commands

**Files:**
- Create: `commands/pheme.md`
- Create: `commands/pheme-status.md`

**Step 1: Create /pheme command**

```markdown
<!-- commands/pheme.md -->
---
name: pheme
description: Send a test notification or message via Pheme
---

# /pheme

Use the Pheme MCP server to send a notification.

## Usage

- `/pheme test <channel>` — Send a test ping to verify a channel works
- `/pheme send <channel> <message>` — Send a message to a specific channel
- `/pheme send --urgency <level> <message>` — Send using urgency routing

## Examples

- `/pheme test slack`
- `/pheme send telegram "deploy complete"`
- `/pheme send --urgency critical "prod is down"`

## How it works

Call the appropriate Pheme MCP tool:
- `test` → `mcp__pheme__test_channel(channel="<channel>")`
- `send` with channel → `mcp__pheme__send(channel="<channel>", message="<message>")`
- `send` with urgency → `mcp__pheme__send(urgency="<level>", message="<message>")`

Report the result back to the user.
```

**Step 2: Create /pheme-status command**

```markdown
<!-- commands/pheme-status.md -->
---
name: pheme-status
description: Show configured Pheme channels and routing
---

# /pheme-status

Show the current Pheme configuration.

## What to do

1. Call `mcp__pheme__list_channels()` to get configured channels
2. Call `mcp__pheme__get_routes()` to get urgency routing
3. Present both in a clear table format:

### Configured Channels

| Channel | Status |
|---------|--------|
| slack | configured |
| telegram | configured |

### Urgency Routing

| Urgency | Channels |
|---------|----------|
| critical | slack, telegram, system |
| high | slack |
| normal | slack |
| low | session |

Note: channels in routes that aren't configured will show as (not configured).
```

**Step 3: Commit**

```bash
git add commands/
git commit -m "feat: CC commands — /pheme and /pheme-status"
```

---

### Task 7: SKILL.md

**Files:**
- Create: `skills/pheme/SKILL.md`

**Step 1: Create the skill file**

(Content created via skill-creator — see separate skill-creator output)

**Step 2: Commit**

```bash
git add skills/
git commit -m "feat: SKILL.md — agent instructions for Pheme"
```

---

### Task 8: Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration test — verifies the full MCP server wiring works end-to-end."""
import os
import pytest
from unittest.mock import AsyncMock, patch
from server.server import create_pheme_server


@pytest.fixture
def full_env(monkeypatch):
    monkeypatch.setenv("PHEME_SLACK", "slack://tokenA/tokenB/tokenC/#general")
    monkeypatch.setenv("PHEME_TELEGRAM", "tgram://bot_token/chat_id")


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_flow(self, full_env):
        """Simulate an agent discovering channels, checking routes, then sending."""
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
```

**Step 2: Run full test suite**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration test — full agent flow"
```

---

### Task 9: README

**Files:**
- Modify: `README.md` (replace placeholder)

**Step 1: Write README**

```markdown
# Pheme

Universal communication layer for agent-to-human notifications.

Pheme wraps [Apprise](https://github.com/caronc/apprise) (100+ channels) in an MCP server,
so any agent can send notifications via a single tool call.

## Quick Start

1. Install: `pip install -e .`
2. Configure channels via env vars:
   ```bash
   export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
   export PHEME_TELEGRAM="tgram://bot_token/chat_id"
   ```
3. Run the MCP server: `python -m server.server`

## MCP Tools

| Tool | Description |
|------|-------------|
| `send` | Send a notification (by channel or urgency) |
| `list_channels` | Show configured channels |
| `test_channel` | Verify a channel works |
| `get_routes` | Show urgency routing config |

## CC Plugin

Install as a Claude Code plugin for `/pheme` and `/pheme-status` commands.

## Channel Configuration

Set `PHEME_<NAME>=<apprise_url>` for each channel. See
[Apprise wiki](https://github.com/caronc/apprise/wiki) for URL formats.

## Urgency Routing

Configure in `~/.claude/pheme-routes.yaml` or `.claude/pheme-routes.yaml`:

```yaml
routes:
  critical: [slack, telegram, system]
  high: [slack]
  normal: [slack]
  low: [session]
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with quick start and configuration guide"
```

---

### Task 10: Final Verification

**Step 1: Run full test suite**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/pytest -v --tb=short`
Expected: All tests PASS

**Step 2: Verify MCP server starts**

Run: `cd /Users/divyekant/Projects/pheme && .venv/bin/python -c "from server.server import mcp; print('Pheme MCP server ready')"`
Expected: `Pheme MCP server ready`

**Step 3: Final commit (if any changes)**

```bash
git status
# If clean, no commit needed
```
