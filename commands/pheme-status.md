---
name: pheme-status
description: Show configured Pheme channels and routing
---

# /pheme-status

Show the current Pheme configuration.

## What to do

1. Call `mcp__pheme__list_channels()` to get configured channels
2. Call `mcp__pheme__get_routes()` to get urgency routing
3. Present both in a clear table format:

### Configured Channels

| Channel | Status |
|---------|--------|
| slack | configured |
| telegram | configured |

### Urgency Routing

| Urgency | Channels |
|---------|----------|
| critical | slack, telegram, system |
| high | slack |
| normal | slack |
| low | session |

Note: channels in routes that aren't configured will show as (not configured).
