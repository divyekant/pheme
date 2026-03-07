---
id: feat-001
type: feature-doc
audience: external
topic: notification-sending
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Notification Sending

## Overview

The `send` tool is the core of Pheme. You call it once, and your notification reaches humans across any combination of 100+ channels -- Slack, Telegram, email, Discord, SMS, webhooks, and more. No channel-specific adapters, no multiple API calls. One MCP tool call does it all.

Pheme wraps the [Apprise](https://github.com/caronc/apprise) library, so any channel Apprise supports is available to you out of the box.

## How to Use It

### Send to a specific channel

Specify the `channel` parameter to target a single configured channel:

```
mcp__pheme__send(
  message="Deployment to staging complete.",
  channel="slack"
)
```

### Send to multiple channels

Use the `channels` parameter (a list) to deliver to several channels at once:

```
mcp__pheme__send(
  message="Deployment to staging complete.",
  channels=["slack", "telegram"]
)
```

### Send with urgency routing

Skip channel selection entirely and let Pheme decide based on urgency. Pheme resolves the urgency level to the appropriate channels using your route configuration:

```
mcp__pheme__send(
  message="Production database is unreachable.",
  urgency="critical",
  title="Outage Alert"
)
```

### Resolution order

Pheme resolves the target channels in this priority:

1. `channel` is set -- send to that one channel only.
2. `channels` is set -- send to those specific channels.
3. `urgency` is set -- the router resolves channels from your route config.
4. Nothing is set -- defaults to `urgency="normal"`.

## Configuration

### Parameters

| Parameter  | Type       | Required | Default  | Description                                        |
|------------|------------|----------|----------|----------------------------------------------------|
| `message`  | string     | Yes      | --       | The notification content.                          |
| `channel`  | string     | No       | None     | Single channel name (e.g., `"slack"`).             |
| `channels` | list[str]  | No       | None     | Multiple channel names (e.g., `["slack", "telegram"]`). |
| `urgency`  | string     | No       | None     | Urgency level: `"low"`, `"normal"`, `"high"`, `"critical"`. |
| `title`    | string     | No       | None     | Notification title or subject line.                |
| `context`  | dict       | No       | None     | Structured metadata (repo, issue, action, etc.).   |
| `format`   | string     | No       | `"text"` | Message format: `"text"`, `"markdown"`, or `"html"`. |

### Message formats

You control how your message body is interpreted:

- **text** (default) -- Plain text. Works everywhere.
- **markdown** -- Rendered as Markdown where the channel supports it (Slack, Telegram, Discord). Falls back to plain text on channels that don't.
- **html** -- Rendered as HTML where supported (email, some webhook endpoints).

### Response

Every `send` call returns a result object:

```json
{
  "success": true,
  "delivered": ["slack", "telegram"],
  "failed": []
}
```

- `success` is `true` only when at least one channel delivered and none failed.
- `delivered` lists channels that accepted the notification.
- `failed` lists channels where delivery did not succeed.

## Examples

### Simple notification

Send a plain text message to Slack:

```
mcp__pheme__send(
  message="Build passed for commit abc123.",
  channel="slack"
)
```

### Multi-channel alert

Notify both Slack and Telegram about a completed task:

```
mcp__pheme__send(
  message="Issue #87 has been triaged and labeled as P1.",
  channels=["slack", "telegram"],
  title="Issue Triaged"
)
```

### Urgency-routed critical alert

Let Pheme route a critical notification to all channels configured for that urgency level:

```
mcp__pheme__send(
  message="Production API is returning 503 errors. Immediate attention required.",
  urgency="critical",
  title="Production Outage"
)
```

With default routing, this delivers to Slack, Telegram, and system notifications simultaneously.

### Markdown-formatted message

Send a structured message using Markdown:

```
mcp__pheme__send(
  message="## PR Ready for Review\n\n**Repo:** acme/widget\n**PR:** #42 — Add caching layer\n**Author:** @alice\n\nAll checks passing. Awaiting your review.",
  channel="slack",
  title="Code Review",
  format="markdown"
)
```

### With context metadata

Attach structured metadata for downstream processing:

```
mcp__pheme__send(
  message="Approval needed: delete production database backup older than 90 days.",
  urgency="critical",
  title="Action Required",
  context={
    "repo": "acme/infra",
    "action": "approval_needed",
    "issue": 204
  }
)
```

## Limitations

- **One-way only.** Pheme sends notifications to humans. It does not receive replies or support two-way conversation.
- **No delivery receipts in v1.** You know whether Apprise accepted the message, but not whether the human read it.
- **No message templates.** You construct the full message content yourself. Template support is planned for a future version.
- **No rate limiting.** Pheme does not throttle sends. If you call `send` in a tight loop, all messages go out immediately. Be mindful of channel-side rate limits.
- **No message history.** Sent notifications are not stored or retrievable after delivery.

## Related

- [Channel Management](feat-002-channel-management.md) -- discover and verify your notification channels
- [Urgency Routing](feat-003-urgency-routing.md) -- configure which channels receive which urgency levels
- [API Reference](../api-reference.md) -- full reference for all MCP tools
