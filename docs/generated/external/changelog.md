---
type: changelog
audience: external
generated: 2026-03-07
hermes-version: 1.0.0
---

# Changelog

All notable changes to Pheme are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-07

### Added

- **Channel discovery from environment variables.** You configure channels by setting `PHEME_<NAME>` env vars, and Pheme automatically picks them up at startup. No config files required for basic usage.
- **Urgency-based routing.** You can send notifications by urgency level (low, normal, high, critical) instead of naming channels directly. Pheme routes each level to the right channels based on your routing config.
- **MCP server with four tools.** You get `send`, `list_channels`, `test_channel`, and `get_routes` as MCP tools, so any MCP-compatible agent can send notifications with a single tool call.
- **Claude Code slash commands.** You can use `/pheme` and `/pheme-status` directly in Claude Code to send notifications and check channel status without leaving your workflow.
- **YAML route configuration.** You can customize urgency routing by placing a `pheme-routes.yaml` file in your project's `.claude/` directory or in `~/.claude/`. Pheme falls back to sensible defaults if no file is found.
- **Apprise integration for 100+ notification services.** You can deliver to Slack, Telegram, Discord, email, and dozens more by providing the appropriate Apprise URL -- no per-service integration code needed.
- **Agent instruction file (SKILL.md).** Agents that support skill files can read Pheme's SKILL.md to learn how to use the notification tools without additional prompting.
- **Quick-start documentation and configuration guide.** You get a README with setup instructions, tool reference, and routing examples to get started in minutes.
