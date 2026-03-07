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
