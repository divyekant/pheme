"""Urgency-based channel routing for Pheme."""


class Router:
    """Resolves which channels to send to based on explicit selection or urgency."""

    def __init__(self, channels: dict[str, str], routes: dict[str, list[str]]):
        self._channels = channels
        self._routes = routes

    def resolve(
        self,
        channel: str | None = None,
        channels: list[str] | None = None,
        urgency: str | None = None,
    ) -> dict[str, str]:
        """Resolve channel names to Apprise URLs.

        Priority: channel > channels > urgency > default (normal).
        Only returns channels that are actually configured.
        """
        if channel:
            names = [channel]
        elif channels:
            names = channels
        else:
            level = urgency or "normal"
            names = self._routes.get(level, self._routes.get("normal", []))

        return {
            name: self._channels[name]
            for name in names
            if name in self._channels
        }
