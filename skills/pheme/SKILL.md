---
name: pheme
description: Use when an agent needs to notify, alert, or communicate with a human across any channel (Slack, Telegram, email, Discord, etc.). Triggers on notifications, alerts, approval requests, status updates, error reports, task completions, or any scenario where an agent needs to reach a human outside the current session. Also use when another plugin or skill mentions "notify the user", "send alert", "request approval", or "inform the human". Even if the user doesn't explicitly mention Pheme, if the task involves agent-to-human communication, use this skill.
---

# Pheme — Universal Agent-to-Human Communication

Pheme is an MCP server that lets you send notifications to humans across 100+ channels (Slack, Telegram, email, Discord, webhooks, etc.) via a single tool call. It wraps Apprise and routes messages based on urgency or explicit channel selection.

## When to use Pheme

You are an agent that needs to reach a human. Examples:
- An approval is needed before proceeding
- A task completed and the human should know
- An error occurred that requires human attention
- A periodic status update is due
- Another plugin (like Argos) asks you to "notify the user"

## When NOT to use Pheme

- Internal agent-to-agent communication (use MCP tools directly)
- Logging or debugging output (write to stderr or log files)
- Anything that doesn't need human attention right now

## The Tools

### send — The core tool

```
mcp__pheme__send(
  message="Your notification text",
  channel="slack",           # OR
  channels=["slack", "telegram"],  # OR
  urgency="critical",        # Let routing decide
  title="Optional Title",
  format="text"              # or "markdown" or "html"
)
```

**How to choose what to pass:**

| Situation | What to pass |
|-----------|-------------|
| You know the exact channel | `channel="slack"` |
| Multiple specific channels | `channels=["slack", "telegram"]` |
| You know the urgency, not the channel | `urgency="critical"` |
| Just informational | No channel or urgency — defaults to `urgency="normal"` |

If both `channel` and `urgency` are passed, `channel` wins.

### Urgency levels

Pick the right urgency based on what happened and whether the human needs to act:

| Level | When to use | Example |
|-------|------------|---------|
| `critical` | Human must act NOW — blocking work, production issue, security | "Prod deploy failed — rollback needed" |
| `high` | Important, not emergency — human should see this soon | "PR #42 ready for review", "Build failed on main" |
| `normal` | Informational — human can see this whenever | "Labeled issue #15 as bug", "Triage complete" |
| `low` | FYI — background activity, summaries | "Processed 3 issues today, all auto-handled" |

### Other tools

- `mcp__pheme__list_channels()` — See what channels are configured
- `mcp__pheme__test_channel(channel="slack")` — Verify a channel works
- `mcp__pheme__get_routes()` — See urgency-to-channel mappings

## Writing good notification messages

Keep messages short and actionable. A human glancing at their phone should immediately understand:
1. **What happened** — the event or action
2. **Where** — repo, issue, PR, system
3. **What they need to do** — if anything

Good: "Argos: PR #42 opened for login-fix on owner/repo. Review needed."
Bad: "A pull request has been created. Please review at your earliest convenience."

Use `title` for the source/context and `message` for the details:
```
mcp__pheme__send(
  title="Argos: owner/repo",
  message="PR #42 opened for login-fix. Fixes null check in auth middleware. Review needed.",
  urgency="high"
)
```

## Channel setup

Channels are configured by the user via environment variables. You don't need to worry about this — just call the tools. If a channel isn't configured, `send` will tell you in the response.

If you're unsure what's available, call `list_channels()` first.
