# Pheme Design Document

> **Date:** 2026-03-06
> **Status:** Approved
> **Project:** Pheme — Universal Communication Layer
> **Type:** MCP Server + Claude Code Plugin

---

## 1. Problem Statement

Agents (CC plugins, Cursor, Codex, Agent SDK, custom scripts) need to notify humans across multiple channels — Slack, Telegram, email, Discord, etc. Today each tool builds its own notification adapters (e.g., Argos has `lib/notify.sh` with shell script adapters). This duplicates effort, fragments configuration, and limits reach.

Pheme fills the gap: a single MCP server that any agent can call to send notifications to any channel, wrapping the battle-tested Apprise library (100+ channel support).

## 2. Value Proposition

- **Agent-first** — MCP tools designed for agents to reach humans, not the other way around
- **100+ channels** — Apprise handles Slack, Telegram, email, Discord, webhooks, SMS, and dozens more
- **Urgency routing** — agents specify urgency, Pheme resolves which channels to use
- **Zero channel code** — no custom adapters to write or maintain
- **Any MCP host** — works from CC, Cursor, Codex, Agent SDK, or any MCP-compatible system
- **CC plugin** — commands and skill for human setup/testing and cross-plugin invocation

## 3. Architecture

### 3.1 Overview

Pheme is a Python MCP server that imports Apprise as a library. It's packaged as a CC plugin for the Claude Code ecosystem, but any MCP host can connect to the server directly.

```
Agent (any MCP host)
  |
  +-- send(channels=["slack"], message="...", urgency="high")
  |
  v
Pheme MCP Server (server.py)
  |
  +-- If channels specified --> use them directly
  +-- If urgency specified, no channels --> router.py resolves channels
  |
  v
router.py -- reads config/routes + env vars
  |
  v
Apprise library -- delivers to resolved channels
  |
  +-- slack://token@channel
  +-- tgram://bot/chatid
  +-- mailto://...
```

### 3.2 Project Structure

```
pheme/
  .claude-plugin/
    plugin.json                 # CC plugin manifest
  server/
    __init__.py
    server.py                   # MCP server -- tools: send, list_channels, test_channel, get_routes
    router.py                   # Urgency --> channel routing logic
    config.py                   # Load channel URLs from env vars, parse route config
  commands/
    pheme.md                    # /pheme send <channel> <message> -- manual testing
    pheme-status.md             # /pheme-status -- show channels & routes
  skills/
    pheme/
      SKILL.md                  # Agent instructions: when/how to use Pheme
  config/
    default-routes.yaml         # Default urgency --> channel mappings
  requirements.txt              # apprise, mcp SDK
  README.md
```

### 3.3 Key Design Decisions

1. **Apprise as library, not CLI** — importing `apprise` in Python is more reliable than shelling out, and we're already in Python for the MCP server
2. **Channels OR urgency** — callers can specify exact channels or just an urgency level and let routing resolve it. Both paths supported.
3. **Config from env vars** — channel URLs in `PHEME_*` env vars. Route mappings in YAML (project-level or global).
4. **No custom CLI** — Apprise CLI already handles script/cron use cases. Pheme fills the MCP + CC plugin gap.

## 4. MCP Tools

Four tools exposed by the server:

### 4.1 send

The core tool. Agents call this to notify humans.

```python
send(
  message: str,           # Required. The notification content.
  channel: str,           # Optional. Single channel: "slack"
  channels: list[str],    # Optional. Multiple: ["slack", "telegram"]
  urgency: str,           # Optional. "low" | "normal" | "high" | "critical"
                          # If no channels specified, urgency resolves them via routes.
  title: str,             # Optional. Notification title/subject.
  context: dict,          # Optional. Structured metadata (repo, issue, action, etc.)
  format: str,            # Optional. "text" | "markdown" | "html". Default: "text"
)
# Returns: { success: bool, delivered: ["slack", "telegram"], failed: [] }
```

**Resolution order:**
1. `channel` set --> send to that one channel only
2. `channels` set --> send to those specific channels
3. `urgency` set --> router resolves channels from config
4. Nothing set --> defaults to `urgency="normal"`

### 4.2 list_channels

```python
list_channels()
# Returns: { channels: [{ name: "slack", configured: true }, ...] }
```

Shows what's available based on which `PHEME_*` env vars are set.

### 4.3 test_channel

```python
test_channel(channel: str)
# Sends "Pheme test -- this channel is working" to the specified channel.
# Returns: { success: bool, error?: str }
```

For setup verification.

### 4.4 get_routes

```python
get_routes()
# Returns the current urgency --> channel routing config
# { "critical": ["slack", "telegram", "system"], "high": ["slack"], ... }
```

## 5. Configuration

### 5.1 Channel URLs (env vars)

Each channel is a single env var holding an Apprise URL:

```bash
PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
PHEME_TELEGRAM="tgram://bot_token/chat_id"
PHEME_EMAIL="mailto://user:pass@gmail.com?to=me@gmail.com"
PHEME_DISCORD="discord://webhook_id/webhook_token"
PHEME_SYSTEM="macosx://"
```

Convention: `PHEME_<NAME>` -- the name becomes the channel identifier in `send(channel="slack")`.

### 5.2 Urgency Routes (YAML)

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

Override per-project (`.claude/pheme-routes.yaml`) or globally (`~/.claude/pheme-routes.yaml`). Project takes precedence.

### 5.3 How Argos Would Use It

Argos drops `lib/notify.sh` and `lib/adapters/` entirely. Policy YAML changes:

```yaml
# Before (Argos-specific adapters)
notifications:
  auto_actions:
    - github_comment
  approval_needed:
    - system
    - github_comment

# After (Pheme urgency)
notifications:
  auto_actions: normal
  approval_needed: critical
```

Argos's skill calls `mcp__pheme__send(message="...", urgency="critical")`.

## 6. Plugin Integration

### 6.1 plugin.json

```json
{
  "name": "pheme",
  "version": "0.1.0",
  "description": "Universal communication layer -- agents notify humans across any channel",
  "author": "Divyekant",
  "license": "MIT"
}
```

### 6.2 SKILL.md

Agent instructions covering:

- **When to use Pheme:** Notify a human -- approval request, task complete, error alert, status update
- **When NOT to use Pheme:** Internal agent-to-agent communication, logging, anything not needing human attention
- **Urgency guide:**
  - `critical` -- needs human attention NOW (prod down, security issue, approval blocking work)
  - `high` -- important but not emergency (PR ready, deploy complete)
  - `normal` -- informational (task done, label applied, issue triaged)
  - `low` -- FYI only (periodic summary, background task progress)
- **Message formatting:** Short and actionable. Include: what happened, what repo/issue, what action needed.
- **Context field:** Pass structured metadata for rich per-channel formatting.

### 6.3 Cross-Plugin Reference

Other plugins reference Pheme in their own SKILL.md:

```markdown
## Notifications
Use the Pheme MCP server to notify the user.
- Auto actions taken --> send with urgency "normal"
- Approval needed --> send with urgency "critical"
- Approval expired --> send with urgency "high"
```

## 7. Scope

### v1 (this design)
- Python MCP server wrapping Apprise
- 4 tools: send, list_channels, test_channel, get_routes
- Channel config via PHEME_* env vars
- Urgency routing via YAML config (global + project override)
- CC plugin with /pheme and /pheme-status commands
- SKILL.md for agent instructions

### Not in v1
- Message templates / formatting per channel
- Delivery receipts / read tracking
- 2-way communication (human --> agent)
- Message history / persistence
- Rate limiting
- Channel health monitoring

## 8. Dependencies

- Python 3.10+
- `apprise` (pip)
- `mcp` SDK (pip)
- No Docker, no external services, no sudo

## 9. Security Considerations

- **Channel URLs contain secrets** -- env vars only, never in committed files
- **Route config YAML contains no secrets** -- safe to commit
- **Message content** -- passed through to Apprise as-is, no eval, no template injection

## 10. Prior Art & Landscape

Pheme wraps Apprise rather than rebuilding channel adapters. The landscape survey found:

- **Commercial multi-channel MCP servers** exist (Courier, Knock, Infobip) but require paid accounts
- **Single-channel MCP servers** exist (Slack, Telegram, Discord, Gmail) but require N servers running
- **Apprise** provides 100+ channels with a simple URL-based config, BSD licensed
- **The gap**: no open-source unified MCP server providing `send(channel, message)` across all channels

Pheme fills this gap by wrapping Apprise in an MCP server with urgency routing and CC plugin packaging.
