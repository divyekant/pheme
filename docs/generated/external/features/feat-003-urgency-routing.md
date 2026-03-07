---
id: feat-003
type: feature-doc
audience: external
topic: urgency-routing
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Urgency Routing

## Overview

Not every notification deserves the same treatment. A production outage should blast every channel you have. A background task completing is fine as a quiet FYI. Urgency routing lets you define these rules once and forget about them -- your agents just specify an urgency level, and Pheme delivers to the right channels automatically.

You configure a mapping from urgency levels to channels. When an agent calls `send` with an `urgency` parameter instead of specifying channels directly, Pheme looks up the routes and delivers accordingly.

## How to Use It

### Send with urgency

Instead of choosing channels yourself, pass an urgency level and let Pheme route it:

```
mcp__pheme__send(
  message="Production API is returning 503 errors.",
  urgency="critical",
  title="Outage Alert"
)
```

Pheme resolves `"critical"` against your route configuration, finds the list of channels mapped to that level, and delivers to each one that is configured.

### Check current routes

Use `get_routes` to see the active urgency-to-channel mapping:

```
mcp__pheme__get_routes()
```

Response:

```json
{
  "critical": ["slack", "telegram", "system"],
  "high": ["slack"],
  "normal": ["slack"],
  "low": ["session"]
}
```

This tells you exactly where each urgency level will deliver. If a channel in the route list is not configured (no corresponding `PHEME_*` env var), it is silently skipped at delivery time.

## Configuration

### Route config files (YAML)

Urgency routes are defined in YAML files. Pheme searches for route configuration in this order and uses the first file it finds:

| Priority | Path                                | Scope           |
|----------|-------------------------------------|-----------------|
| 1        | `.claude/pheme-routes.yaml`         | Project-level   |
| 2        | `~/.claude/pheme-routes.yaml`       | Global (user)   |
| 3        | `config/default-routes.yaml`        | Built-in default|

This means you can override routing per-project by placing a `pheme-routes.yaml` in your project's `.claude/` directory.

### Route file format

```yaml
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

Each key under `routes` is an urgency level. The value is a list of channel names. These names must match your `PHEME_*` environment variable suffixes (lowercased).

### Default routes

If no custom route file is found, Pheme uses these built-in defaults:

| Urgency    | Channels                     | Intent                                  |
|------------|------------------------------|-----------------------------------------|
| `critical` | slack, telegram, system      | Blast every available channel.          |
| `high`     | slack                        | Primary communication channel.          |
| `normal`   | slack                        | Standard informational delivery.        |
| `low`      | session                      | Minimal -- just the active session.     |

## Urgency Level Guide

Use this guide when deciding which urgency level to assign:

### critical

The human must act NOW. Use this when something is broken, blocked, or poses an immediate risk.

- Production is down or degraded
- Security incident detected
- An approval is blocking active work and timing out
- Data loss is imminent

```
mcp__pheme__send(
  message="Production database connection pool exhausted. All API requests failing.",
  urgency="critical",
  title="DATABASE DOWN"
)
```

### high

Important, but not an emergency. The human should see this soon, but a few minutes of delay is acceptable.

- Pull request ready for review
- Deployment completed successfully
- A monitored threshold was crossed
- Approval requested (not yet urgent)

```
mcp__pheme__send(
  message="PR #42 is ready for review. All checks passing.",
  urgency="high",
  title="Review Requested"
)
```

### normal

Informational. The human should know about this, but no action is necessarily required.

- Task completed
- Issue triaged and labeled
- Scheduled job ran successfully
- Status update

```
mcp__pheme__send(
  message="Issue #87 has been triaged as P2 and labeled 'enhancement'.",
  urgency="normal",
  title="Issue Triaged"
)
```

### low

FYI only. Useful context that the human might want later, but does not need to see immediately.

- Background task progress
- Periodic summary
- Non-critical metric update
- Informational log entries

```
mcp__pheme__send(
  message="Weekly dependency audit complete. No vulnerabilities found.",
  urgency="low",
  title="Audit Summary"
)
```

## Examples

### Critical alert to all channels

With default routing, a critical notification reaches Slack, Telegram, and system notifications:

```
mcp__pheme__send(
  message="CI pipeline has been failing for 30 minutes. Last 5 commits all red.",
  urgency="critical",
  title="CI Broken"
)
```

Result (assuming all three channels are configured):

```json
{
  "success": true,
  "delivered": ["slack", "telegram", "system"],
  "failed": []
}
```

### High-priority to Slack only

With default routing, high urgency goes to Slack:

```
mcp__pheme__send(
  message="Deploy v2.1.0 to production complete. All health checks green.",
  urgency="high",
  title="Deploy Complete"
)
```

```json
{
  "success": true,
  "delivered": ["slack"],
  "failed": []
}
```

### Custom routing config

Suppose you want critical alerts to also go to email, and you want high-priority messages to reach both Slack and Discord. Create a route file:

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
    - discord
  normal:
    - slack
  low:
    - session
```

After restarting the Pheme server, verify the new routes:

```
mcp__pheme__get_routes()
```

```json
{
  "critical": ["slack", "telegram", "email", "system"],
  "high": ["slack", "discord"],
  "normal": ["slack"],
  "low": ["session"]
}
```

Now `urgency="high"` delivers to both Slack and Discord.

### Unconfigured channels in routes are skipped

If your route config lists `telegram` for critical, but you have not set `PHEME_TELEGRAM`, that channel is silently skipped. Only configured channels receive the notification. This means you can define an ambitious route config and progressively add channels as you set them up.

## Limitations

- **No dynamic routing.** Route configuration is loaded at server startup and remains static. To change routes, update the YAML file and restart the server.
- **No per-message route overrides beyond channel/urgency.** You can specify exact channels or an urgency level, but you cannot say "use the critical routes plus this extra channel." If you need a specific set of channels, use the `channels` parameter directly.
- **No time-based or context-based routing.** Routes are purely urgency-to-channel mappings. You cannot route based on time of day, message content, or other dimensions.
- **Unknown urgency levels fall back to normal.** If you pass an urgency value that is not in your route config (e.g., `urgency="extreme"`), Pheme falls back to the `normal` route.

## Related

- [Notification Sending](feat-001-notification-sending.md) -- the `send` tool that uses urgency routing
- [Configuration Reference](../config-reference.md) -- full reference for route YAML and environment variables
