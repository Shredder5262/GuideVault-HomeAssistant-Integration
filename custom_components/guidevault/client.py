"""Async API client for GuideVault."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import COMMAND_ENDPOINT, DEFAULT_TIMEOUT


class GuideVaultApiError(Exception):
    """Raised when GuideVault returns an API error."""


class GuideVaultConnectionError(Exception):
    """Raised when GuideVault cannot be reached."""


@dataclass(slots=True)
class GuideVaultClientConfig:
    """GuideVault client configuration."""

    host: str
    port: int | None
    ssl: bool
    verify_ssl: bool
    api_key: str | None = None
    timeout: int = DEFAULT_TIMEOUT

    @property
    def base_url(self) -> str:
        """Return normalized GuideVault base URL."""
        host = self.host.strip().rstrip("/")

        if host.startswith("http://") or host.startswith("https://"):
            parsed = urlparse(host)
            scheme = parsed.scheme
            netloc = parsed.netloc
            path = parsed.path.rstrip("/")
            return f"{scheme}://{netloc}{path}"

        scheme = "https" if self.ssl else "http"
        if self.port:
            return f"{scheme}://{host}:{self.port}"
        return f"{scheme}://{host}"


class GuideVaultClient:
    """Async client for the GuideVault Home Assistant command API."""

    def __init__(self, session: ClientSession, config: GuideVaultClientConfig) -> None:
        self._session = session
        self._config = config

    @property
    def base_url(self) -> str:
        """Return the configured GuideVault base URL."""
        return self._config.base_url

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-GuideVault",
        }

        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        return headers

    async def async_test_connection(self) -> None:
        """Test whether GuideVault can be reached.

        Older GuideVault builds may not expose a dedicated health endpoint,
        so this probes several safe read endpoints and accepts any non-5xx
        response as proof that the server is reachable.
        """
        probes = (
            "/api/home-assistant/status",
            "/api/health",
            "/health",
            "/",
        )

        last_error: Exception | str | None = None

        for path in probes:
            url = f"{self.base_url}{path}"
            try:
                async with asyncio.timeout(self._config.timeout):
                    async with self._session.get(
                        url,
                        headers=self._headers(),
                        ssl=self._config.verify_ssl,
                    ) as response:
                        if response.status < 500:
                            return
                        last_error = f"HTTP {response.status} for {path}"
            except (TimeoutError, ClientError, OSError) as err:
                last_error = err

        raise GuideVaultConnectionError(
            f"Could not reach GuideVault at {self.base_url}: {last_error}"
        )

    async def async_command(self, payload: dict[str, Any]) -> Any:
        """Send a command to GuideVault."""
        cleaned = {
            key: value
            for key, value in payload.items()
            if value is not None and value != ""
        }

        url = f"{self.base_url}{COMMAND_ENDPOINT}"

        try:
            async with asyncio.timeout(self._config.timeout):
                async with self._session.post(
                    url,
                    headers=self._headers(),
                    json=cleaned,
                    ssl=self._config.verify_ssl,
                ) as response:
                    text = await response.text()

                    if response.status < 200 or response.status >= 300:
                        raise GuideVaultApiError(
                            f"GuideVault command failed with HTTP {response.status}: {text}"
                        )

                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        return await response.json()

                    return {"ok": True, "response": text}
        except GuideVaultApiError:
            raise
        except (TimeoutError, ClientResponseError, ClientError, OSError) as err:
            raise GuideVaultConnectionError(
                f"Could not send command to GuideVault: {err}"
            ) from err
