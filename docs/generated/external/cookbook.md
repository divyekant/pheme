---
type: cookbook
audience: external
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Pheme Cookbook

Copy-paste recipes for common notification scenarios. Each recipe has a goal, a tool call you can use directly, and any relevant notes.

---

## Basic Notifications

### Send a Simple Message to One Channel

**Goal:** Deliver a plain text message to a single, specific channel.

```
mcp__pheme__send(
  message="Deployment to staging completed successfully.",
  channel="slack"
)
```

**Notes:** The `channel` value must match a configured `PHEME_<NAME>` env var (lowercased). If the channel is not configured, the response will include an `"error"` field.

---

### Send to Multiple Channels at Once

**Goal:** Deliver the same message to several channels in a single call.

```
mcp__pheme__send(
  message="v2.1.0 has been released. All checks passed.",
  channels=["slack", "telegram", "discord"]
)
```

**Notes:** Pheme attempts delivery to each channel independently. The response lists which channels succeeded in `delivered` and which failed in `failed`. Channels that are not configured are silently skipped.

---

### Send with a Title

**Goal:** Include a title (subject line) alongside the message body.

```
mcp__pheme__send(
  message="PR #87 merged into main. 4 files changed, all tests passing.",
  channel="slack",
  title="CI/CD: owner/repo"
)
```

**Notes:** How the title renders depends on the channel. Slack shows it as a bold header, email uses it as the subject line, and some channels may not display it at all.

---

## Urgency-Based Routing

### Send a Critical Alert

**Goal:** Reach all high-priority channels immediately for an urgent situation.

```
mcp__pheme__send(
  message="Production API is returning 503 errors. Error rate at 45%. Immediate investigation needed.",
  urgency="critical",
  title="ALERT: Production Down"
)
```

**Notes:** With the default route config, `critical` sends to `slack`, `telegram`, and `system` (macOS notification). You can customize which channels each urgency level targets in your route config YAML. Only channels that are actually configured (have a `PHEME_*` env var) will receive the message.

---

### Send a Low-Priority FYI

**Goal:** Send a background update that does not need immediate attention.

```
mcp__pheme__send(
  message="Processed 12 issues today. 10 auto-triaged, 2 flagged for review.",
  urgency="low",
  title="Daily Summary"
)
```

**Notes:** By default, `low` urgency routes to `session` only. If you do not have a `PHEME_SESSION` channel configured, this will return `"No configured channels matched"`. Adjust your routes to point `low` at a channel you have configured.

---

### Check Current Routing Config

**Goal:** See which channels each urgency level maps to.

```
mcp__pheme__get_routes()
```

Example response:

```json
{
  "critical": ["slack", "telegram", "system"],
  "high": ["slack"],
  "normal": ["slack"],
  "low": ["session"]
}
```

**Notes:** Route config is loaded from (in priority order): `.claude/pheme-routes.yaml` in your project, `~/.claude/pheme-routes.yaml` globally, or the built-in `config/default-routes.yaml`.

---

## Message Formatting

### Send a Markdown-Formatted Message

**Goal:** Send a message with Markdown formatting (bold, lists, links, etc.).

```
mcp__pheme__send(
  message="## Build Report\n\n- **Status:** Passed\n- **Duration:** 3m 42s\n- **Coverage:** 94.2%\n\n[View full report](https://ci.example.com/builds/456)",
  channel="slack",
  title="Build #456",
  format="markdown"
)
```

**Notes:** Markdown rendering depends on channel support. Slack and Telegram handle Markdown well. Email clients vary. Plain text channels will show the raw Markdown syntax.

---

### Send an HTML-Formatted Message

**Goal:** Send a message with rich HTML formatting.

```
mcp__pheme__send(
  message="<h3>Deploy Complete</h3><p>Version <b>2.1.0</b> is now live.</p><ul><li>3 new features</li><li>2 bug fixes</li></ul>",
  channel="email",
  title="Deploy Notification",
  format="html"
)
```

**Notes:** HTML format works best with email channels. Slack and Telegram will strip or ignore HTML tags. Use `markdown` for those channels instead.

---

### Include Context Metadata

**Goal:** Attach structured metadata to a notification for richer context.

```
mcp__pheme__send(
  message="Issue #42 has been triaged and labeled as 'bug'. Assigned to backend team.",
  channel="slack",
  title="Argos: owner/repo",
  context={
    "repo": "owner/repo",
    "issue": 42,
    "action": "triage",
    "labels": ["bug"],
    "assigned_team": "backend"
  }
)
```

**Notes:** The `context` field carries structured data alongside the message. In v1, context is passed through but not used for per-channel formatting. Future versions may use it to generate richer channel-specific layouts.

---

## Channel Management

### List All Configured Channels

**Goal:** See which channels Pheme can currently reach.

```
mcp__pheme__list_channels()
```

Example response:

```json
{
  "channels": [
    {"name": "discord", "configured": true},
    {"name": "slack", "configured": true},
    {"name": "telegram", "configured": true}
  ]
}
```

**Notes:** This reflects which `PHEME_*` environment variables are set. If you expected a channel to appear and it does not, check that the env var is exported in the server's shell session.

---

### Test a Channel Before Sending

**Goal:** Verify that a channel is reachable before relying on it for real notifications.

```
mcp__pheme__test_channel(channel="telegram")
```

Expected response on success:

```json
{"success": true, "delivered": ["telegram"], "failed": []}
```

**Notes:** This sends a built-in test message: "Pheme test -- 'telegram' channel is working." Check the target channel to confirm it arrived. If the channel is not configured, you will get an error with the specific env var you need to set.

---

### Add a New Channel

**Goal:** Configure a new notification channel for Pheme to use.

Set a `PHEME_<NAME>` environment variable with the Apprise URL for your channel:

```bash
# Discord
export PHEME_DISCORD="discord://webhook_id/webhook_token"

# Telegram
export PHEME_TELEGRAM="tgram://bot_token/chat_id"

# Email
export PHEME_EMAIL="mailto://user:pass@gmail.com?to=recipient@example.com"

# macOS system notification
export PHEME_SYSTEM="macosx://"
```

Then restart the Pheme server (or start a new session) for it to pick up the new variable.

**Notes:** Find the Apprise URL format for your channel on the [Apprise wiki](https://github.com/caronc/apprise/wiki). Channel URLs contain secrets (tokens, passwords), so keep them in env vars and never commit them to source control.

---

## Integration Patterns

### Notify on Task Completion

**Goal:** Let a human know that an automated task finished.

```
mcp__pheme__send(
  message="Migration of user_sessions table complete. 1.2M rows migrated, 0 errors. Took 4m 12s.",
  urgency="normal",
  title="DB Migration: production"
)
```

**Notes:** Use `urgency="normal"` for routine completions. The human can check this whenever convenient. If the task is particularly important (e.g., a production deploy), consider `urgency="high"`.

---

### Send an Approval Request

**Goal:** Ask a human to approve an action before the agent proceeds.

```
mcp__pheme__send(
  message="Argos wants to mass-close 23 stale issues in owner/repo. Labels: wontfix. Review and respond in the current session to approve or deny.",
  urgency="critical",
  title="Approval Needed: owner/repo"
)
```

**Notes:** Use `urgency="critical"` for approvals that block further work. Include enough detail for the human to make a decision without switching context: what action, how many items, which repo, and how to respond.

---

### Alert on Error or Failure

**Goal:** Immediately notify a human when something goes wrong.

```
mcp__pheme__send(
  message="CI pipeline failed on main branch. Commit abc1234 by @dev broke test_auth_flow. 3 tests failing.\n\nSee: https://ci.example.com/builds/789",
  urgency="high",
  title="CI Failure: owner/repo"
)
```

**Notes:** Use `urgency="high"` for failures that need attention soon but are not production-down emergencies. Reserve `urgency="critical"` for production outages or security issues. Include a link to the build or error details so the human can jump straight to investigating.

---

### Periodic Status Update

**Goal:** Send a recurring summary of agent activity.

```
mcp__pheme__send(
  message="Weekly triage summary for owner/repo:\n- 18 new issues processed\n- 12 auto-labeled\n- 4 assigned to teams\n- 2 flagged for manual review\n\nNo blockers. Next run scheduled for Monday.",
  urgency="low",
  title="Weekly Report: owner/repo"
)
```

**Notes:** Use `urgency="low"` for periodic summaries and FYI messages. These are informational and do not require action. Make sure your `low` urgency route points to a channel you have configured, or the message will not be delivered.
