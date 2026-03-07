---
type: api-reference
audience: external
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Pheme API Reference

Pheme is a Python MCP server that exposes 4 tools for sending notifications from agents to humans across 100+ channels. You call these tools through any MCP-compatible host -- Claude Code, Cursor, Codex, or anything that speaks MCP.

There is no REST API, no authentication token, and no base URL. You interact with Pheme entirely through MCP tool calls.

---

## Tools

### `send`

Send a notification to one or more channels. This is the primary tool you will use.

You can target channels explicitly by name, or specify an urgency level and let Pheme's routing configuration decide which channels to use.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | `str` | Yes | -- | The notification content. |
| `channel` | `str \| None` | No | `None` | Single channel name (e.g. `"slack"`). |
| `channels` | `list[str] \| None` | No | `None` | Multiple channel names (e.g. `["slack", "telegram"]`). |
| `urgency` | `str \| None` | No | `None` | Route by urgency: `"low"`, `"normal"`, `"high"`, or `"critical"`. |
| `title` | `str \| None` | No | `None` | Optional notification title or subject line. |
| `context` | `dict \| None` | No | `None` | Optional structured metadata (e.g. repo, issue number, action taken). |
| `format` | `str` | No | `"text"` | Message format: `"text"`, `"markdown"`, or `"html"`. |

#### Channel Resolution Order

Pheme resolves which channels to send to using this priority:

1. **`channel`** is set -- send to that single channel only.
2. **`channels`** is set -- send to those specific channels.
3. **`urgency`** is set -- the router resolves channels from your route configuration.
4. **Nothing is set** -- defaults to `urgency="normal"`.

#### Response Format

On success:

```json
{
  "success": true,
  "delivered": ["slack", "telegram"],
  "failed": []
}
```

On partial failure (some channels delivered, some did not):

```json
{
  "success": false,
  "delivered": ["slack"],
  "failed": ["telegram"]
}
```

When no configured channels match the request:

```json
{
  "success": false,
  "delivered": [],
  "failed": [],
  "error": "No configured channels matched"
}
```

#### Examples

**Send to a single channel:**

```json
{
  "tool": "send",
  "arguments": {
    "message": "Deployment to production completed successfully.",
    "channel": "slack"
  }
}
```

**Send to multiple channels:**

```json
{
  "tool": "send",
  "arguments": {
    "message": "PR #42 is ready for review.",
    "channels": ["slack", "email"],
    "title": "PR Review Needed"
  }
}
```

**Route by urgency:**

```json
{
  "tool": "send",
  "arguments": {
    "message": "Production database is unreachable. Immediate attention required.",
    "urgency": "critical",
    "title": "Production Outage"
  }
}
```

**Send with markdown formatting and metadata:**

```json
{
  "tool": "send",
  "arguments": {
    "message": "**Build failed** on `main` branch.\n\nSee [CI logs](https://ci.example.com/run/789) for details.",
    "urgency": "high",
    "title": "Build Failure",
    "format": "markdown",
    "context": {
      "repo": "acme/web-app",
      "branch": "main",
      "ci_run": 789
    }
  }
}
```

**Let routing default to normal urgency (no channel or urgency specified):**

```json
{
  "tool": "send",
  "arguments": {
    "message": "Issue #15 has been triaged and labeled."
  }
}
```

#### Error Cases

| Scenario | Result |
|----------|--------|
| Channel name is not configured (no matching `PHEME_*` env var) | The channel is silently skipped. If all requested channels are unconfigured, you get `"error": "No configured channels matched"`. |
| Delivery fails for a channel (network error, invalid token, etc.) | The channel appears in the `"failed"` array and `"success"` is `false`. |
| No parameters besides `message` | Defaults to `urgency="normal"` and routes accordingly. If no channels are configured for `"normal"`, you get the "no channels matched" error. |

---

### `list_channels`

List all notification channels that are currently configured. A channel is considered configured when its corresponding `PHEME_*` environment variable is set.

#### Parameters

None.

#### Response Format

```json
{
  "channels": [
    {"name": "discord", "configured": true},
    {"name": "slack", "configured": true},
    {"name": "telegram", "configured": true}
  ]
}
```

The list is sorted alphabetically by channel name. Only configured channels appear -- if a `PHEME_*` env var is not set, that channel is absent from the list entirely.

#### Examples

**Check which channels are available:**

```json
{
  "tool": "list_channels",
  "arguments": {}
}
```

Response when `PHEME_SLACK` and `PHEME_TELEGRAM` are set:

```json
{
  "channels": [
    {"name": "slack", "configured": true},
    {"name": "telegram", "configured": true}
  ]
}
```

Response when no `PHEME_*` env vars are set:

```json
{
  "channels": []
}
```

---

### `test_channel`

Send a test notification to a specific channel to verify it is configured and working. Pheme sends a predefined test message to the channel and reports whether delivery succeeded.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | `str` | Yes | The channel name to test (e.g. `"slack"`). |

#### Response Format

On success:

```json
{
  "success": true,
  "delivered": ["slack"],
  "failed": []
}
```

When the channel is not configured:

```json
{
  "success": false,
  "error": "Channel 'slack' not configured. Set PHEME_SLACK env var."
}
```

When the channel is configured but delivery fails:

```json
{
  "success": false,
  "delivered": [],
  "failed": ["slack"]
}
```

#### Examples

**Test a configured channel:**

```json
{
  "tool": "test_channel",
  "arguments": {
    "channel": "slack"
  }
}
```

**Test a channel that is not configured:**

```json
{
  "tool": "test_channel",
  "arguments": {
    "channel": "discord"
  }
}
```

Response:

```json
{
  "success": false,
  "error": "Channel 'discord' not configured. Set PHEME_DISCORD env var."
}
```

#### Error Cases

| Scenario | Result |
|----------|--------|
| Channel not configured | Returns `"success": false` with an `"error"` string telling you which env var to set. |
| Channel configured but delivery fails | Returns `"success": false` with the channel in the `"failed"` array. Check that your Apprise URL in the env var is valid. |

---

### `get_routes`

Return the current urgency-to-channel routing configuration. This shows you which channels each urgency level maps to, so you can understand how `send` will behave when you specify an `urgency` instead of explicit channels.

#### Parameters

None.

#### Response Format

```json
{
  "critical": ["slack", "telegram", "system"],
  "high": ["slack"],
  "normal": ["slack"],
  "low": ["session"]
}
```

The response is a dictionary mapping each urgency level to its list of channel names. These are the default routes. You can override them with a `pheme-routes.yaml` file at the project level (`.claude/pheme-routes.yaml`) or globally (`~/.claude/pheme-routes.yaml`).

#### Examples

**View current routing:**

```json
{
  "tool": "get_routes",
  "arguments": {}
}
```

Response with default configuration:

```json
{
  "critical": ["slack", "telegram", "system"],
  "high": ["slack"],
  "normal": ["slack"],
  "low": ["session"]
}
```

Response with custom project-level routing:

```json
{
  "critical": ["slack", "telegram", "email", "system"],
  "high": ["slack", "email"],
  "normal": ["slack"],
  "low": ["slack"]
}
```
