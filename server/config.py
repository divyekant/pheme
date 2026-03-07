"""Configuration loading for Pheme.

Channels are discovered from PHEME_* environment variables.
Routes are loaded from YAML config files.
"""
import os
import yaml

DEFAULT_ROUTES = {
    "critical": ["slack", "telegram", "system"],
    "high": ["slack"],
    "normal": ["slack"],
    "low": ["session"],
}


def discover_channels() -> dict[str, str]:
    """Discover configured channels from PHEME_* env vars.

    Each env var PHEME_<NAME>=<apprise_url> defines a channel.
    Returns dict mapping lowercase channel name to Apprise URL.
    """
    channels = {}
    for key, value in os.environ.items():
        if key.startswith("PHEME_") and value:
            name = key[len("PHEME_"):].lower()
            channels[name] = value
    return channels


def load_routes(path: str) -> dict[str, list[str]]:
    """Load urgency -> channel routing from YAML file.

    Falls back to DEFAULT_ROUTES if file is missing or invalid.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if data and "routes" in data and isinstance(data["routes"], dict):
            return data["routes"]
    except (FileNotFoundError, yaml.YAMLError, OSError):
        pass
    return DEFAULT_ROUTES.copy()
