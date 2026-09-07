"""Dynamic platform registry for extensible social media parser plugins.

This module provides a plugin architecture for registering new social media
platforms without modifying core code. Platforms can be added via:
1. Configuration file (config/platforms.json)
2. Environment variables
3. Programmatic registration

All platform parsers are discovered at runtime and can be hot-reloaded.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..models import SocialPost
from . import generic_web

logger = logging.getLogger("traceface.osint.parsers")


class PlatformRegistry:
    """Registry for social media platform parsers."""

    def __init__(self):
        self._platform_hosts: dict[str, tuple[str, ...]] = {}
        self._fetchers: dict[str, Callable[..., SocialPost | None]] = {}
        self._loaded = False
        self._parser_modules: dict[str, Any] = {}

    def register_platform(
        self,
        platform_key: str,
        hosts: tuple[str, ...],
        fetcher: Callable[..., SocialPost | None] | None = None,
    ) -> None:
        """Register a new platform parser.

        Args:
            platform_key: Internal identifier (e.g., "twitter", "reddit")
            hosts: Tuple of domain substrings to match (e.g., ("twitter.com", "x.com"))
            fetcher: Parser function (url, timeout) -> SocialPost | None
        """
        self._platform_hosts[platform_key] = hosts
        if fetcher:
            self._fetchers[platform_key] = fetcher
        logger.info("Registered platform: %s (hosts: %s)", platform_key, ", ".join(hosts))

    def register_fetcher(
        self,
        platform_key: str,
        fetcher: Callable[..., SocialPost | None],
    ) -> None:
        """Register a fetcher function for an existing platform.

        Args:
            platform_key: Platform identifier
            fetcher: Parser function
        """
        self._fetchers[platform_key] = fetcher
        logger.debug("Registered fetcher for: %s", platform_key)

    def detect_platform(self, url: str) -> str:
        """Classify a URL into a platform key.

        Args:
            url: Post URL to classify

        Returns:
            Platform key or "generic" if unknown
        """
        low = (url or "").lower()
        # Sort platforms by priority (shortest host first to avoid substring false positives)
        # For example: "reddit.com" should not be matched by "t.co" substring
        scored_platforms = []
        for platform_key, hosts in self._platform_hosts.items():
            best_match_len = 0
            for host in hosts:
                if host in low:
                    # Prefer longer host matches (more specific)
                    best_match_len = max(best_match_len, len(host))
            if best_match_len > 0:
                scored_platforms.append((best_match_len, platform_key))
        
        # Return platform with longest matching host (most specific)
        if scored_platforms:
            _, best_platform = max(scored_platforms, key=lambda x: x[0])
            return best_platform
        
        return "generic"

    def get_fetcher(self, platform: str) -> Callable[..., SocialPost | None]:
        """Get the fetcher function for a platform.

        Args:
            platform: Platform key

        Returns:
            Fetcher function, defaults to generic_web.fetch
        """
        return self._fetchers.get(platform, generic_web.fetch)

    def parse_post(self, url: str, timeout: float = 15.0) -> SocialPost | None:
        """Parse a post from any platform.

        Args:
            url: Post URL
            timeout: Request timeout

        Returns:
            SocialPost or None on failure
        """
        return self.get_fetcher(self.detect_platform(url))(url, timeout=timeout)

    def load_from_config(self, config_path: Path | None = None) -> None:
        """Load platform registry from JSON configuration file.

        Args:
            config_path: Path to platforms.json. Defaults to config/platforms.json
        """
        if config_path is None:
            config_path = Path("config/platforms.json")

        if not config_path.exists():
            logger.debug("No platform config found at %s", config_path)
            return

        try:
            with open(config_path) as f:
                config = json.load(f)

            for platform_config in config.get("platforms", []):
                self.register_platform(
                    platform_key=platform_config["key"],
                    hosts=tuple(platform_config["hosts"]),
                    fetcher=None,  # Will be loaded dynamically
                )

            logger.info("Loaded %d platforms from %s", len(config.get("platforms", [])), config_path)
        except Exception as exc:
            logger.warning("Failed to load platform config: %s", exc)

    def load_builtin_parsers(self) -> None:
        """Load built-in parser modules for registered platforms."""
        from . import twitter, reddit, instagram, youtube, tiktok, facebook, generic_web
        
        builtin_parsers = {
            "twitter": twitter,
            "reddit": reddit,
            "instagram": instagram,
            "linkedin": generic_web,
            "youtube": youtube,
            "tiktok": tiktok,
            "facebook": facebook,
        }

        for platform_key, module in builtin_parsers.items():
            if platform_key in self._platform_hosts:
                if hasattr(module, "fetch"):
                    self._fetchers[platform_key] = module.fetch
                    self._parser_modules[platform_key] = module
                    logger.debug("Loaded builtin parser: %s", platform_key)

    def load_from_environment(self) -> None:
        """Load platform overrides from environment variables.

        Environment format:
        PLATFORM_TRUSTED_HOSTS=twitter.com,x.com,youtube.com
        PLATFORM_CUSTOM_PARSER_path/to/parser.py=custom_platform_key
        """
        import os

        trusted_hosts = os.getenv("PLATFORM_TRUSTED_HOSTS")
        if trusted_hosts:
            hosts = tuple(h.strip() for h in trusted_hosts.split(",") if h.strip())
            if hosts:
                self.register_platform("custom", hosts)
                logger.info("Loaded custom platform hosts from environment")

    def initialize(self) -> None:
        """Initialize the platform registry with all sources."""
        if self._loaded:
            return

        # Load builtin defaults first (fastest path)
        default_platforms = {
            "twitter": ("twitter.com", "x.com", "t.co"),
            "reddit": ("reddit.com", "redd.it", "old.reddit.com"),
            "instagram": ("instagram.com", "instagr.am"),
            "linkedin": ("linkedin.com", "lnkd.in"),
            "youtube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
            "tiktok": ("tiktok.com", "vm.tiktok.com"),
            "facebook": ("facebook.com", "fb.com", "fb.watch"),
        }
        for key, hosts in default_platforms.items():
            self.register_platform(key, hosts)

        # Load builtin parsers
        self.load_builtin_parsers()

        # Then load config file (optional)
        try:
            self.load_from_config()
        except Exception as exc:
            logger.debug("Skipping config file load: %s", exc)

        # Load from environment (optional)
        try:
            self.load_from_environment()
        except Exception as exc:
            logger.debug("Skipping environment load: %s", exc)

        self._loaded = True
        logger.info(
            "Platform registry initialized: %s",
            ", ".join(sorted(self._platform_hosts.keys())),
        )

    def list_platforms(self) -> list[str]:
        """List all registered platform keys."""
        return sorted(self._platform_hosts.keys())

    def get_platform_hosts(self, platform_key: str) -> tuple[str, ...] | None:
        """Get hosts for a specific platform."""
        return self._platform_hosts.get(platform_key)


# Global singleton registry
_registry: PlatformRegistry | None = None


def get_platform_registry() -> PlatformRegistry:
    """Get the global platform registry singleton."""
    global _registry
    if _registry is None:
        _registry = PlatformRegistry()
        _registry.initialize()
    return _registry


def reload_platform_registry() -> PlatformRegistry:
    """Reload the platform registry (hot reload)."""
    global _registry
    if _registry is not None:
        _registry = PlatformRegistry()
        _registry.initialize()
    return get_platform_registry()


__all__ = [
    "PlatformRegistry",
    "get_platform_registry",
    "reload_platform_registry",
]
