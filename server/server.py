"""Pheme MCP Server — universal agent-to-human notification layer.

Wraps Apprise to deliver notifications across 100+ channels.
Agents call MCP tools; Pheme routes to the right channels.
"""
import os
import logging
import re
import sys

import apprise
from mcp.server.fastmcp import FastMCP

from server.config import discover_channels, load_routes
from server.router import Router

logger = logging.getLogger("pheme")
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.INFO)

MAX_MESSAGE_LENGTH = 4000

# Patterns that suggest sensitive data is being sent through notifications.
# We warn but don't block — the user may have legitimate reasons.
_SECRET_PATTERNS = [
    re.compile(r'(?:api[_-]?key|api[_-]?secret|token|password|passwd|secret)["\s:=]+\S{8,}', re.IGNORECASE),
    re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),  # JWT
    re.compile(r'(?:sk|pk)[-_](?:live|test)[-_][A-Za-z0-9]{10,}'),  # Stripe-style keys
    re.compile(r'xox[bpras]-[A-Za-z0-9-]{10,}'),  # Slack tokens
    re.compile(r'ghp_[A-Za-z0-9]{30,}'),  # GitHub PATs
    re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'),  # PEM keys
]

# Route config search order: project > global > default
ROUTE_CONFIG_PATHS = [
    os.path.join(os.getcwd(), ".claude", "pheme-routes.yaml"),
    os.path.expanduser("~/.claude/pheme-routes.yaml"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "default-routes.yaml"),
]


class PhemeServer:
    """Pheme server encapsulating config, router, and MCP tools."""

    def __init__(self):
        self.channels = discover_channels()
        self.routes = self._load_first_route_config()
        self.router = Router(self.channels, self.routes)
        self.mcp = FastMCP("pheme")
        self._register_tools()

    def _load_first_route_config(self) -> dict[str, list[str]]:
        for path in ROUTE_CONFIG_PATHS:
            if os.path.isfile(path):
                return load_routes(path)
        return load_routes("")  # returns defaults

    def _register_tools(self):
        @self.mcp.tool()
        async def list_channels() -> dict:
            """List all configured notification channels.

            Returns which channels are available based on PHEME_* env vars.
            """
            return await self._list_channels()

        @self.mcp.tool()
        async def get_routes() -> dict:
            """Get the current urgency-to-channel routing configuration.

            Shows which channels each urgency level maps to.
            """
            return await self._get_routes()

        @self.mcp.tool()
        async def send(
            message: str,
            channel: str | None = None,
            channels: list[str] | None = None,
            urgency: str | None = None,
            title: str | None = None,
            format: str = "text",
        ) -> dict:
            """Send a notification to humans via configured channels.

            Agents use this to notify humans about events, approvals, errors, etc.
            Specify exact channels OR an urgency level to let routing decide.

            Args:
                message: The notification content (max 4000 chars).
                channel: Single channel name (e.g. "slack").
                channels: Multiple channel names (e.g. ["slack", "telegram"]).
                urgency: Route by urgency: "low", "normal", "high", "critical".
                title: Optional notification title/subject.
                format: Message format: "text", "markdown", or "html".
            """
            return await self._send(message, channel, channels, urgency, title, format)

        @self.mcp.tool()
        async def test_channel(channel: str) -> dict:
            """Send a test notification to verify a channel is working.

            Args:
                channel: The channel name to test (e.g. "slack").
            """
            return await self._test_channel(channel)

    async def _list_channels(self) -> dict:
        return {
            "channels": [
                {"name": name, "configured": True}
                for name in sorted(self.channels.keys())
            ]
        }

    async def _get_routes(self) -> dict:
        return self.routes

    async def _send(
        self,
        message: str,
        channel: str | None = None,
        channels: list[str] | None = None,
        urgency: str | None = None,
        title: str | None = None,
        format: str = "text",
    ) -> dict:
        if len(message) > MAX_MESSAGE_LENGTH:
            return {
                "success": False, "delivered": [], "failed": [],
                "error": f"Message too long ({len(message)} chars). Max is {MAX_MESSAGE_LENGTH}.",
            }

        for pattern in _SECRET_PATTERNS:
            if pattern.search(message) or (title and pattern.search(title)):
                logger.warning("SECURITY: message may contain sensitive data (matched secret pattern)")
                break

        resolved = self.router.resolve(channel=channel, channels=channels, urgency=urgency)

        if not resolved:
            return {"success": False, "delivered": [], "failed": [], "error": "No configured channels matched"}

        body_format = apprise.NotifyFormat.TEXT
        if format == "markdown":
            body_format = apprise.NotifyFormat.MARKDOWN
        elif format == "html":
            body_format = apprise.NotifyFormat.HTML

        delivered = []
        failed = []

        for name, url in resolved.items():
            ap = apprise.Apprise()
            ap.add(url)
            ok = await ap.async_notify(body=message, title=title or "", body_format=body_format)
            if ok:
                delivered.append(name)
            else:
                failed.append(name)

        success = len(failed) == 0 and len(delivered) > 0
        logger.info(
            "SEND: urgency=%s channels=%s delivered=%s failed=%s len=%d",
            urgency or "default", list(resolved.keys()), delivered, failed, len(message),
        )

        return {
            "success": success,
            "delivered": delivered,
            "failed": failed,
        }

    async def _test_channel(self, channel: str) -> dict:
        if channel not in self.channels:
            return {"success": False, "error": f"Channel '{channel}' not configured. Set PHEME_{channel.upper()} env var."}
        return await self._send(
            message=f"Pheme test -- '{channel}' channel is working.",
            channel=channel,
            title="Pheme Test",
        )


def create_pheme_server() -> PhemeServer:
    """Factory function for creating a PhemeServer instance."""
    return PhemeServer()


# Entry point
server = create_pheme_server()
mcp = server.mcp
