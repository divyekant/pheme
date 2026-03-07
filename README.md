# Pheme

Universal agent-to-human notification layer. Pheme wraps [Apprise](https://github.com/caronc/apprise) in an [MCP](https://modelcontextprotocol.io/) server so any AI agent can notify humans across 100+ channels — Slack, Telegram, email, Discord, webhooks, and more — via a single tool call.

## Why Pheme?

AI agents run autonomously but still need to reach humans: approvals, error alerts, status updates, task completions. Without a standard notification layer, every agent reinvents channel integration. Pheme solves this by providing:

- **One interface** — 4 MCP tools cover all notification needs
- **100+ channels** — anything Apprise supports, Pheme supports
- **Urgency-based routing** — critical alerts fan out to multiple channels; low-priority updates stay quiet
- **Zero channel lock-in** — channels are configured via env vars, not code
- **Security built in** — message length caps, secret detection warnings, audit logging

## Quick Start

### Prerequisites

- Python 3.10+
- An Apprise-compatible channel (Slack, Telegram, email, etc.)

### Install

```bash
git clone https://github.com/divyekant/pheme.git
cd pheme
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs Pheme along with all dependencies including [Apprise](https://github.com/caronc/apprise), [FastMCP](https://github.com/jlowin/fastmcp), and [PyYAML](https://pyyaml.org/).

### Configure Channels

Set one or more `PHEME_<NAME>` environment variables with [Apprise URLs](https://github.com/caronc/apprise/wiki):

```bash
# Slack
export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"

# Telegram
export PHEME_TELEGRAM="tgram://bot_token/chat_id"

# Email
export PHEME_EMAIL="mailto://user:pass@gmail.com?to=recipient@example.com"

# Discord
export PHEME_DISCORD="discord://webhook_id/webhook_token"

# macOS native notifications
export PHEME_SYSTEM="macosx://"

# Webhooks
export PHEME_WEBHOOK="json://endpoint.example.com/path"
```

See the [Apprise wiki](https://github.com/caronc/apprise/wiki) for the full list of supported services and their URL formats.

### Run the MCP Server

```bash
python -m server
```

The server communicates over stdio using the MCP protocol, ready for any MCP-compatible client to connect.

## MCP Tools

Pheme exposes 4 tools via the MCP protocol:

### `send` — Send a notification

The core tool. Send a message to one or more channels, either by name or by urgency level.

```
send(
  message: str,              # Required. The notification content (max 4000 chars).
  channel: str | None,       # Single channel name, e.g. "slack"
  channels: list[str] | None,  # Multiple channels, e.g. ["slack", "telegram"]
  urgency: str | None,       # "low", "normal", "high", "critical"
  title: str | None,         # Optional title/subject line
  format: str = "text"       # "text", "markdown", or "html"
)
```

**Routing priority:** `channel` > `channels` > `urgency` > default (`normal`)

**Response:**
```json
{
  "success": true,
  "delivered": ["slack", "telegram"],
  "failed": []
}
```

### `list_channels` — Show configured channels

Returns all channels discovered from `PHEME_*` environment variables.

```json
{
  "channels": [
    {"name": "slack", "configured": true},
    {"name": "telegram", "configured": true}
  ]
}
```

### `get_routes` — Show urgency routing

Returns the current urgency-to-channel mapping.

```json
{
  "critical": ["slack", "telegram", "system"],
  "high": ["slack"],
  "normal": ["slack"],
  "low": ["session"]
}
```

### `test_channel` — Verify a channel works

Sends a test notification to confirm a channel is properly configured.

```
test_channel(channel: str)  # e.g. "slack"
```

## Urgency Routing

Pheme routes messages to channels based on urgency level. Instead of hardcoding channel names, agents can say "this is critical" and let routing decide where it goes.

### Default Routes

| Urgency | Channels | Use Case |
|---------|----------|----------|
| `critical` | slack, telegram, system | Production down, security incidents, blocking issues |
| `high` | slack | PR reviews, build failures, important updates |
| `normal` | slack | Task completions, status updates, informational |
| `low` | session | Background activity, summaries, FYI |

### Custom Routes

Override routing by creating a YAML file. Pheme searches in this order (first match wins):

1. **Project-level:** `.claude/pheme-routes.yaml` (in the current working directory)
2. **User-level:** `~/.claude/pheme-routes.yaml`
3. **Default:** `config/default-routes.yaml` (bundled with Pheme)

```yaml
# .claude/pheme-routes.yaml
routes:
  critical:
    - slack
    - telegram
    - email
    - system
  high:
    - slack
    - email
  normal:
    - slack
  low:
    - session
```

## Security

Pheme includes several hardening measures for safe use in production agent workflows:

### Message Length Cap

Messages are capped at 4,000 characters. Longer messages are rejected with an error — this prevents runaway agents from dumping large payloads into notification channels.

### Secret Detection

Before sending, Pheme scans messages for patterns that look like secrets:

- API keys and tokens (`api_key=`, `token=`, etc.)
- JWTs (`eyJ...`)
- Stripe-style keys (`sk_live_...`, `pk_test_...`)
- Slack tokens (`xoxb-...`)
- GitHub PATs (`ghp_...`)
- PEM private keys

If a match is found, Pheme logs a warning to stderr but **does not block** the message — the agent or user may have a legitimate reason to include the content.

### Audit Logging

Every `send` call is logged to stderr with:
- Urgency level
- Target channels
- Delivery results (delivered/failed)
- Message length

## Claude Code Plugin

Pheme ships as a Claude Code plugin with slash commands and an agent skill.

### Slash Commands

| Command | Description |
|---------|-------------|
| `/pheme test <channel>` | Send a test ping to verify a channel |
| `/pheme send <channel> <message>` | Send a message to a specific channel |
| `/pheme send --urgency <level> <message>` | Send using urgency routing |
| `/pheme-status` | Show configured channels and routing table |

### Agent Skill

The bundled skill at `skills/pheme/SKILL.md` teaches agents when and how to use Pheme. It covers:

- When to notify (approvals, errors, completions) vs. when not to (logging, internal comms)
- How to pick the right urgency level
- How to write good notification messages (what happened, where, what to do)
- Tool usage examples

## Architecture

```
┌─────────────┐     MCP (stdio)     ┌──────────────────┐
│  AI Agent   │ ──────────────────> │   Pheme Server   │
│ (Claude,    │                     │                  │
│  Argos,     │                     │  ┌────────────┐  │
│  etc.)      │                     │  │   Router    │  │
└─────────────┘                     │  │ (urgency → │  │
                                    │  │  channels) │  │
                                    │  └─────┬──────┘  │
                                    │        │         │
                                    │  ┌─────▼──────┐  │
                                    │  │  Apprise   │  │
                                    │  │ (delivery) │  │
                                    │  └─────┬──────┘  │
                                    └────────┼─────────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          │                  │                  │
                     ┌────▼────┐       ┌─────▼─────┐     ┌─────▼─────┐
                     │  Slack  │       │ Telegram  │     │  Email    │
                     └─────────┘       └───────────┘     └───────────┘
```

### Project Structure

```
pheme/
├── server/
│   ├── __init__.py
│   ├── __main__.py        # Entry point: python -m server
│   ├── config.py          # Channel discovery (env vars) + route loading (YAML)
│   ├── router.py          # Urgency-based channel resolution
│   └── server.py          # MCP server, tools, security checks
├── config/
│   └── default-routes.yaml
├── skills/
│   └── pheme/
│       └── SKILL.md       # Agent skill — when/how to use Pheme
├── commands/
│   ├── pheme.md           # /pheme slash command
│   └── pheme-status.md    # /pheme-status slash command
├── tests/
│   ├── test_config.py     # 7 tests — channel discovery, route loading
│   ├── test_router.py     # 8 tests — urgency resolution, fallbacks
│   ├── test_server.py     # 16 tests — tools, security, edge cases
│   └── test_integration.py # 1 test — full end-to-end flow
├── .claude-plugin/
│   └── plugin.json        # Claude Code plugin manifest
├── pyproject.toml
└── README.md
```

## Development

### Running Tests

```bash
source .venv/bin/activate
pytest -v
```

All 32 tests should pass:

```
tests/test_config.py       — 7 passed
tests/test_router.py       — 8 passed
tests/test_server.py       — 16 passed
tests/test_integration.py  — 1 passed
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]` >= 1.2.0 | MCP server framework (FastMCP) |
| `apprise` >= 1.9.0 | Notification delivery (100+ channels) |
| `pyyaml` >= 6.0 | Route configuration parsing |
| `pytest` >= 8.0 | Testing (dev) |
| `pytest-asyncio` >= 0.24 | Async test support (dev) |

## Documentation

Full external documentation is available in [`docs/generated/external/`](docs/generated/external/index.md):

- [Getting Started](docs/generated/external/getting-started.md) — Install and send your first notification
- [API Reference](docs/generated/external/api-reference.md) — All 4 MCP tools in detail
- [Configuration Reference](docs/generated/external/config-reference.md) — Env vars and YAML routes
- [Error Reference](docs/generated/external/error-reference.md) — Error codes and resolutions
- [Cookbook](docs/generated/external/cookbook.md) — Copy-paste recipes for common scenarios
- [Tutorial](docs/generated/external/tutorials/tut-001-first-notification.md) — Step-by-step walkthrough
- [Notification Sending](docs/generated/external/features/feat-001-notification-sending.md) — Deep dive into the send tool
- [Channel Management](docs/generated/external/features/feat-002-channel-management.md) — Channel setup and testing
- [Urgency Routing](docs/generated/external/features/feat-003-urgency-routing.md) — Routing configuration guide

## License

MIT
