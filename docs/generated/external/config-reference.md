---
type: config-reference
audience: external
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Configuration Reference

Pheme uses two configuration mechanisms: **environment variables** for channel credentials and **YAML files** for urgency routing. This reference covers every option with its type, default, and usage.

## Channel Configuration (Environment Variables)

You define notification channels by setting environment variables. Pheme auto-discovers all `PHEME_*` variables at server startup.

### Pattern

```
PHEME_<NAME>=<apprise_url>
```

- **Type:** String (Apprise URL)
- **Default:** None -- no channels are configured unless you set them
- **Description:** Each environment variable whose name starts with `PHEME_` registers a notification channel. The `<NAME>` portion (everything after `PHEME_`) becomes the channel identifier, **lowercased**. The value is an [Apprise URL](https://github.com/caronc/apprise/wiki) for that channel.
- **Empty values are ignored.** If you set `PHEME_SLACK=""`, no `slack` channel is registered.
- **Discovery is automatic.** You do not need to list channels anywhere else -- Pheme scans all environment variables at startup and picks up every `PHEME_*` entry with a non-empty value.

### Supported Channels

Any channel supported by [Apprise](https://github.com/caronc/apprise/wiki) works. Here are common examples:

#### PHEME_SLACK

- **Type:** String
- **Default:** Not set
- **Description:** Slack workspace notification channel.
- **Example:**
  ```bash
  export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
  ```

#### PHEME_TELEGRAM

- **Type:** String
- **Default:** Not set
- **Description:** Telegram bot notification channel.
- **Example:**
  ```bash
  export PHEME_TELEGRAM="tgram://bot_token/chat_id"
  ```

#### PHEME_EMAIL

- **Type:** String
- **Default:** Not set
- **Description:** Email notification channel via SMTP.
- **Example:**
  ```bash
  export PHEME_EMAIL="mailto://user:pass@gmail.com?to=me@gmail.com"
  ```

#### PHEME_DISCORD

- **Type:** String
- **Default:** Not set
- **Description:** Discord webhook notification channel.
- **Example:**
  ```bash
  export PHEME_DISCORD="discord://webhook_id/webhook_token"
  ```

#### PHEME_SYSTEM

- **Type:** String
- **Default:** Not set
- **Description:** Native desktop notification (macOS, Linux, Windows).
- **Example:**
  ```bash
  export PHEME_SYSTEM="macosx://"
  ```

#### Custom Channels

You can use any name. The variable name determines the channel identifier:

```bash
export PHEME_PAGERDUTY="pagerduty://integration_key"
export PHEME_TEAMS="msteams://webhook_url"
export PHEME_SMS="twilio://account_sid:auth_token@from_phone/to_phone"
```

These register channels named `pagerduty`, `teams`, and `sms` respectively.

### Security Note

Channel URLs contain secrets (tokens, passwords, API keys). Keep them in environment variables only -- never commit them to version control.

## Route Configuration (YAML)

Routes map urgency levels to channels. When an agent sends a notification with an `urgency` value instead of specifying channels directly, Pheme uses the route configuration to determine which channels receive the message.

### File Search Order

Pheme checks for a route configuration file in this order and **uses the first one found**:

| Priority | Path | Scope |
|----------|------|-------|
| 1 (highest) | `.claude/pheme-routes.yaml` | Project-level (relative to working directory) |
| 2 | `~/.claude/pheme-routes.yaml` | Global (user home) |
| 3 (lowest) | `config/default-routes.yaml` | Bundled default (inside the Pheme package) |

- **Type:** YAML file
- **Default:** If no file is found, or the file is missing or contains invalid YAML, Pheme falls back to hardcoded defaults (see below).
- **Description:** Place a `pheme-routes.yaml` file at the project level to customize routing per-project, or at the global level for a personal default. The bundled default ships with Pheme as a starting point.

### File Format

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

- **Type:** YAML map with a top-level `routes` key
- **Default:** See "Default Routes" below
- **Description:** The `routes` key maps each urgency level to an ordered list of channel names. Each channel name must correspond to a configured `PHEME_<NAME>` environment variable for delivery to succeed.

### Urgency Levels

Four urgency levels are supported:

| Level | Type | Default Channels | Description |
|-------|------|-------------------|-------------|
| `critical` | String | `["slack", "telegram", "system"]` | Needs human attention immediately -- production outage, security issue, approval blocking work. |
| `high` | String | `["slack"]` | Important but not an emergency -- PR ready for review, deploy complete. |
| `normal` | String | `["slack"]` | Informational -- task completed, label applied, issue triaged. This is also the fallback when no urgency is specified. |
| `low` | String | `["session"]` | FYI only -- periodic summary, background task progress. |

### Default Routes

If no route configuration file is found, or the file cannot be parsed, Pheme uses these hardcoded defaults:

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

- **Type:** `dict[str, list[str]]`
- **Default:** `{"critical": ["slack", "telegram", "system"], "high": ["slack"], "normal": ["slack"], "low": ["session"]}`
- **Description:** These defaults are compiled into the server and used as a last resort when no YAML file is available or readable.

### Channel Resolution Behavior

- **Unconfigured channels are silently skipped.** If your routes reference `telegram` but you have not set `PHEME_TELEGRAM`, messages are not sent to Telegram and no error is raised. Only channels with a matching `PHEME_*` environment variable receive notifications.
- **No configured channels matched** results in a response with `"success": false` and `"error": "No configured channels matched"`.
- **Fallback urgency.** If an agent calls `send()` with no `channel`, `channels`, or `urgency` parameter, Pheme defaults to `urgency="normal"` and resolves channels using the `normal` route.

## Configuration Examples

### Minimal Setup

One channel, default routing:

```bash
export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
```

With default routes, `normal`, `high`, and `critical` notifications all go to Slack.

### Multi-Channel with Custom Routes

```bash
export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
export PHEME_TELEGRAM="tgram://bot_token/chat_id"
export PHEME_SYSTEM="macosx://"
```

Project-level route override in `.claude/pheme-routes.yaml`:

```yaml
routes:
  critical:
    - slack
    - telegram
    - system
  high:
    - slack
    - telegram
  normal:
    - slack
  low:
    - system
```

### Per-Project Override

Your global config at `~/.claude/pheme-routes.yaml` sends everything to Slack. For a specific project, you create `.claude/pheme-routes.yaml` to add Telegram for critical alerts. The project-level file takes full precedence -- it is not merged with the global file.

## Validating Your Configuration

Use the MCP tools to verify your setup:

- **`list_channels`** -- confirms which channels Pheme discovered from environment variables.
- **`get_routes`** -- shows the active urgency-to-channel routing configuration.
- **`test_channel`** -- sends a test notification to a specific channel to verify end-to-end delivery.
