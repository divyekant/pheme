---
id: tut-001
type: tutorial
audience: external
topic: first-notification
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Send Your First Notification with Pheme

In this tutorial, you will set up Pheme from scratch and send a notification to Slack (or any channel you prefer). By the end, you will have a working Pheme installation that delivers messages from your agent to your chosen channel.

## Prerequisites

- **Python 3.10+** installed on your machine
- **A Slack workspace** you can send messages to (or any other supported channel -- Telegram, Discord, email, etc.)
- **Estimated time:** 10 minutes

## Step 1: Install Pheme

Clone the repository and set up a virtual environment:

```bash
git clone <repo-url> pheme
cd pheme
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs Pheme along with its dependencies: the MCP SDK, Apprise (which handles delivery to 100+ channels), and PyYAML.

## Step 2: Get Your Channel URL

Pheme uses [Apprise URLs](https://github.com/caronc/apprise/wiki) to connect to notification channels. Each channel type has its own URL format. Here is how to get one for Slack:

1. Go to your Slack workspace and create an **Incoming Webhook** (Settings > Manage Apps > Incoming Webhooks).
2. Copy the webhook URL. It will look something like: `https://hooks.slack.com/services/T.../B.../xxx`
3. Convert it to the Apprise format: `slack://tokenA/tokenB/tokenC/#channel`

For the full Apprise URL format for Slack, see the [Apprise Slack wiki page](https://github.com/caronc/apprise/wiki/Notify_slack).

> **Using a different channel?** Apprise supports Telegram, Discord, email, macOS notifications, and many more. Find your channel's URL format on the [Apprise wiki](https://github.com/caronc/apprise/wiki).

## Step 3: Configure the Channel

Set an environment variable with your channel's Apprise URL. The naming convention is `PHEME_<NAME>`:

```bash
export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
```

The part after `PHEME_` becomes the channel name you use in tool calls. For example, `PHEME_SLACK` creates a channel called `slack`, and `PHEME_TELEGRAM` would create one called `telegram`.

> **Tip:** Add this export to your shell profile (`.zshrc`, `.bashrc`, etc.) so it persists across sessions.

## Step 4: Start the Server

Run the Pheme MCP server:

```bash
python -m server.server
```

The server is now running and ready to accept tool calls from any MCP-compatible host (Claude Code, Cursor, Codex, etc.).

## Step 5: List Channels to Confirm

Verify that Pheme sees your configured channel by calling the `list_channels` tool:

```
mcp__pheme__list_channels()
```

You should see a response like:

```json
{
  "channels": [
    {"name": "slack", "configured": true}
  ]
}
```

If your channel does not appear, double-check the environment variable name (it must start with `PHEME_`) and make sure you exported it in the same shell session where the server is running.

## Step 6: Test the Channel

Before sending a real message, verify that Pheme can reach your channel:

```
mcp__pheme__test_channel(channel="slack")
```

Expected response:

```json
{"success": true, "delivered": ["slack"], "failed": []}
```

This sends a built-in test message -- "Pheme test -- 'slack' channel is working." -- to your Slack channel. Check Slack to confirm it arrived.

## Step 7: Send a Real Notification

Now send your own notification with a title and message:

```
mcp__pheme__send(
  message="Pheme is set up and ready to go. This is my first notification!",
  channel="slack",
  title="Hello from Pheme"
)
```

Expected response:

```json
{"success": true, "delivered": ["slack"], "failed": []}
```

## Verify It Works

Open your Slack channel (or whichever channel you configured). You should see two messages:

1. The test message from Step 6
2. Your custom "Hello from Pheme" notification from Step 7

If both arrived, your Pheme setup is complete and working.

## What's Next

Now that you have a working Pheme installation, you can explore more capabilities:

- **Urgency-based routing** -- Instead of specifying a channel, let Pheme route messages based on urgency (`low`, `normal`, `high`, `critical`). See the urgency routing section in the [Cookbook](../cookbook.md).
- **Add more channels** -- Configure Telegram, Discord, email, or any of the 100+ channels Apprise supports. Each one is just another `PHEME_<NAME>` environment variable.
- **Copy-paste recipes** -- The [Cookbook](../cookbook.md) has ready-to-use patterns for common scenarios like error alerts, approval requests, and status updates.

## Troubleshooting

### "Channel not configured" error

```
{"success": false, "error": "Channel 'slack' not configured. Set PHEME_SLACK env var."}
```

This means Pheme does not see a `PHEME_SLACK` environment variable. Check:

- Did you spell the env var correctly? It must be uppercase and start with `PHEME_`.
- Did you `export` the variable (not just assign it)?
- Is the variable set in the same shell session where the server is running?

### "No configured channels matched"

```
{"success": false, "delivered": [], "failed": [], "error": "No configured channels matched"}
```

This means the channel name you passed does not match any configured channel. The channel name in your tool call must match the part after `PHEME_` in your env var, lowercased. For example, `PHEME_SLACK` maps to `channel="slack"`.

### Server won't start

- Verify you are using Python 3.10 or higher: `python3 --version`
- Make sure you activated the virtual environment: `source .venv/bin/activate`
- Confirm dependencies are installed: `pip install -e ".[dev]"`
- Check for import errors in the output -- they usually indicate a missing dependency.

### Test passes but no message in Slack

- Verify the Apprise URL is correct. A malformed URL may be silently accepted but fail to deliver.
- Check the Slack webhook URL hasn't expired or been revoked.
- Try the [Apprise CLI](https://github.com/caronc/apprise/wiki/CLI_Usage) directly to rule out Pheme-specific issues: `apprise -b "test" "slack://tokenA/tokenB/tokenC/#general"`
