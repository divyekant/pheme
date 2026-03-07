---
type: error-reference
audience: external
status: draft
generated: 2026-03-07
source-tier: direct
hermes-version: 1.0.0
---

# Error Reference

Pheme returns errors as fields in the response dictionary from its MCP tools. This page documents the error scenarios you may encounter and how to resolve them.

## No configured channels matched

**Tool:** `send`

**Response:**
```json
{"success": false, "delivered": [], "failed": [], "error": "No configured channels matched"}
```

**Cause:** You specified a channel name that does not have a corresponding `PHEME_*` environment variable, or the urgency level you chose routes to channels that are not configured. For example, if your routes map `critical` to `["slack", "telegram"]` but you only have `PHEME_SLACK` set, Pheme will deliver to Slack and silently skip Telegram. If none of the routed channels are configured, you get this error.

**Resolution:**
1. Call `list_channels` to see which channels Pheme currently recognizes.
2. Verify the channel name matches exactly -- names are derived from the env var suffix, lowercased (e.g., `PHEME_SLACK` becomes `slack`).
3. If you are routing by urgency, call `get_routes` to see which channels each level maps to, and ensure those channels have env vars set.

---

## Channel 'X' not configured

**Tool:** `test_channel`

**Response:**
```json
{"success": false, "error": "Channel 'X' not configured. Set PHEME_X env var."}
```

**Cause:** You called `test_channel` with a channel name that does not have a `PHEME_<NAME>` environment variable set. Pheme only knows about channels discovered from env vars at startup.

**Resolution:**
1. Set the environment variable for the channel you want to test:
   ```bash
   export PHEME_SLACK="slack://tokenA/tokenB/tokenC/#general"
   ```
2. Restart the Pheme MCP server so it picks up the new variable.
3. Run `test_channel` again.

---

## Delivery failure

**Tool:** `send`

**Response:**
```json
{"success": false, "delivered": ["telegram"], "failed": ["slack"]}
```

**Cause:** Pheme resolved your channels and attempted delivery, but Apprise could not deliver to one or more of them. Common reasons include an invalid or expired Apprise URL, a network connectivity issue, or an authentication failure with the upstream service.

**Resolution:**
1. Check the Apprise URL format for the failed channel against the [Apprise wiki](https://github.com/caronc/apprise/wiki).
2. Use `test_channel` to isolate the problem to a specific channel.
3. Verify your network connectivity, especially if you are behind a proxy or firewall.
4. For token-based services (Slack, Telegram, Discord), confirm that your tokens and credentials are still valid.

---

## Invalid YAML routes

**Scenario:** Your `pheme-routes.yaml` file has a syntax error or missing structure.

**Behavior:** Pheme does not return an explicit error. Instead, it silently falls back to the default routing configuration:
```yaml
routes:
  critical: [slack, telegram, system]
  high: [slack]
  normal: [slack]
  low: [session]
```

**Cause:** The YAML file could not be parsed, or it does not contain a top-level `routes` key with a dictionary value.

**Resolution:**
1. Validate your YAML syntax with a linter or online validator.
2. Ensure the file has the correct structure:
   ```yaml
   routes:
     critical: [slack, telegram]
     high: [slack]
     normal: [slack]
     low: [session]
   ```
3. Confirm the `routes` key is at the top level and each urgency level maps to a list of channel names.
4. Call `get_routes` after restarting the server to verify your custom routes loaded correctly. If you see the defaults above and you expected custom routes, your file was not picked up.
