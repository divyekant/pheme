---
name: pheme
description: Send a test notification or message via Pheme
---

# /pheme

Use the Pheme MCP server to send a notification.

## Usage

- `/pheme test <channel>` — Send a test ping to verify a channel works
- `/pheme send <channel> <message>` — Send a message to a specific channel
- `/pheme send --urgency <level> <message>` — Send using urgency routing

## Examples

- `/pheme test slack`
- `/pheme send telegram "deploy complete"`
- `/pheme send --urgency critical "prod is down"`

## How it works

Call the appropriate Pheme MCP tool:
- `test` → `mcp__pheme__test_channel(channel="<channel>")`
- `send` with channel → `mcp__pheme__send(channel="<channel>", message="<message>")`
- `send` with urgency → `mcp__pheme__send(urgency="<level>", message="<message>")`

Report the result back to the user.
