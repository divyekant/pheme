---
type: getting-started
audience: external
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Getting Started

## Prerequisites

- Python 3.10 or higher
- At least one notification channel URL (Slack, Telegram, email, Discord, etc.) — see [Apprise wiki](https://github.com/caronc/apprise/wiki) for URL formats

## Installation

Clone the repository and install:

```bash
git clone <repo-url> pheme
cd pheme
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure a channel

Set an environment variable with your channel's Apprise URL. The naming convention is `PHEME_<NAME>`:

```bash
export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
```

You can configure as many channels as you need:

```bash
export PHEME_TELEGRAM="tgram://bot_token/chat_id"
export PHEME_DISCORD="discord://webhook_id/webhook_token"
export PHEME_EMAIL="mailto://user:pass@gmail.com?to=me@gmail.com"
```

### 2. Start the MCP server

```bash
python -m server
```

The Pheme MCP server is now running and ready to accept tool calls from any MCP-compatible host (Claude Code, Cursor, Codex, etc.).

### 2a. Claude Code setup

Add Pheme to `~/.claude/.mcp.json` (**not** `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "pheme": {
      "command": "/path/to/pheme/.venv/bin/python",
      "args": ["-m", "server"],
      "cwd": "/path/to/pheme",
      "env": {
        "PHEME_TELEGRAM": "tgram://bot_token/chat_id"
      }
    }
  }
}
```

Symlink the agent skill for global availability:

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/pheme/skills/pheme ~/.claude/skills/pheme
```

> **Note:** MCP servers connect at session start. Restart Claude Code after config changes. Servers in `settings.json` are **not** loaded — use `.mcp.json`.

### 3. Verify your setup

Use the `test_channel` tool to confirm a channel is working:

```
mcp__pheme__test_channel(channel="slack")
```

Expected response:

```json
{"success": true, "delivered": ["slack"], "failed": []}
```

### 4. Send your first notification

```
mcp__pheme__send(
  message="Hello from Pheme!",
  channel="slack",
  title="First Notification"
)
```

### 5. Try urgency-based routing

Instead of specifying a channel, let Pheme route based on urgency:

```
mcp__pheme__send(
  message="Deploy complete for v1.2.0",
  urgency="high",
  title="CI/CD"
)
```

Pheme resolves the urgency to configured channels using your route config.

## Next Steps

- [Notification Sending](features/feat-001-notification-sending.md) — learn about message formats, context metadata, and delivery
- [Urgency Routing](features/feat-003-urgency-routing.md) — customize which channels receive which urgency levels
- [API Reference](api-reference.md) — full reference for all 4 MCP tools
- [Configuration Reference](config-reference.md) — all env vars and YAML options
- [Cookbook](cookbook.md) — copy-paste recipes for common notification scenarios
