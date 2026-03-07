---
id: feat-002
type: feature-doc
audience: external
topic: channel-management
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Channel Management

## Overview

Before you send notifications, you need to know what channels are available and whether they actually work. Pheme gives you two tools for this: `list_channels` to discover your configured channels, and `test_channel` to verify that a specific channel can deliver messages.

Together, these tools let you inspect your setup, troubleshoot configuration issues, and confirm everything is wired up before relying on notifications in production workflows.

## How to Use It

### Discover configured channels

Call `list_channels` to see every channel Pheme has detected from your environment:

```
mcp__pheme__list_channels()
```

Response:

```json
{
  "channels": [
    {"name": "slack", "configured": true},
    {"name": "telegram", "configured": true},
    {"name": "system", "configured": true}
  ]
}
```

Each entry represents a `PHEME_*` environment variable that was set when the server started. The `name` is the lowercased suffix of the variable (e.g., `PHEME_SLACK` becomes `"slack"`).

### Verify a channel works

Call `test_channel` with a channel name to send a test notification and confirm delivery:

```
mcp__pheme__test_channel(channel="slack")
```

Response on success:

```json
{
  "success": true,
  "delivered": ["slack"],
  "failed": []
}
```

Response when the channel is not configured:

```json
{
  "success": false,
  "error": "Channel 'discord' not configured. Set PHEME_DISCORD env var."
}
```

This sends a real notification with the message "Pheme test -- 'slack' channel is working." to the specified channel. Use it during setup to confirm your tokens, URLs, and permissions are correct.

## Configuration

### Adding channels via environment variables

Each channel is configured through a single environment variable following the `PHEME_<NAME>` convention. The value is an [Apprise URL](https://github.com/caronc/apprise/wiki) for that channel:

```bash
# Slack
export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"

# Telegram
export PHEME_TELEGRAM="tgram://bot_token/chat_id"

# Email
export PHEME_EMAIL="mailto://user:pass@gmail.com?to=me@gmail.com"

# Discord
export PHEME_DISCORD="discord://webhook_id/webhook_token"

# macOS system notifications
export PHEME_SYSTEM="macosx://"
```

The `<NAME>` portion becomes the channel identifier you use in `send`, `test_channel`, and route configurations. It is automatically lowercased.

### Supported channel types

Pheme supports every channel that Apprise supports -- over 100 services. Some common ones:

| Channel Type       | Apprise URL Prefix | Example                                      |
|--------------------|--------------------|----------------------------------------------|
| Slack              | `slack://`         | `slack://tokenA/tokenB/tokenC/#channel`      |
| Telegram           | `tgram://`         | `tgram://bot_token/chat_id`                  |
| Discord            | `discord://`       | `discord://webhook_id/webhook_token`         |
| Email (SMTP)       | `mailto://`        | `mailto://user:pass@gmail.com?to=recipient`  |
| Microsoft Teams    | `msteams://`       | `msteams://token_a/token_b/token_c`          |
| Pushover           | `pover://`         | `pover://user_key@api_token`                 |
| macOS Notification  | `macosx://`        | `macosx://`                                  |
| Webhook (JSON)     | `json://`          | `json://hostname/path`                       |

For the full list of supported services and their URL formats, see the [Apprise wiki](https://github.com/caronc/apprise/wiki).

## Examples

### List all channels

Check what is currently configured:

```
mcp__pheme__list_channels()
```

```json
{
  "channels": [
    {"name": "discord", "configured": true},
    {"name": "email", "configured": true},
    {"name": "slack", "configured": true},
    {"name": "telegram", "configured": true}
  ]
}
```

Channels are returned in alphabetical order.

### Test a channel

Verify that your Slack configuration is correct:

```
mcp__pheme__test_channel(channel="slack")
```

If the token is valid and the channel exists, you get:

```json
{"success": true, "delivered": ["slack"], "failed": []}
```

If the token is invalid or the channel does not exist, Apprise reports a failure:

```json
{"success": false, "delivered": [], "failed": ["slack"]}
```

### Handle an unconfigured channel

If you try to test or send to a channel that has no corresponding environment variable:

```
mcp__pheme__test_channel(channel="sms")
```

```json
{
  "success": false,
  "error": "Channel 'sms' not configured. Set PHEME_SMS env var."
}
```

The error message tells you exactly which environment variable to set.

### Typical setup workflow

A good setup workflow looks like this:

1. Set your `PHEME_*` environment variables.
2. Start (or restart) the Pheme MCP server.
3. Call `list_channels()` to confirm Pheme sees your channels.
4. Call `test_channel(channel="...")` for each one to verify delivery.
5. You are ready to use `send`.

## Limitations

- **Channels are discovered at server startup only.** If you add, remove, or change a `PHEME_*` environment variable, you must restart the Pheme MCP server for the change to take effect.
- **No channel health monitoring in v1.** Pheme does not periodically check whether channels are reachable. Use `test_channel` for manual verification.
- **No channel aliases or grouping.** Each `PHEME_*` variable maps to exactly one Apprise URL. If you need to send to multiple Slack channels, configure separate variables (e.g., `PHEME_SLACK_GENERAL`, `PHEME_SLACK_ALERTS`).
- **Channel URLs contain secrets.** Tokens and credentials live in the environment variable values. Never commit them to source control.

## Related

- [Notification Sending](feat-001-notification-sending.md) -- send messages through your configured channels
- [Configuration Reference](../config-reference.md) -- full list of environment variables and YAML options
