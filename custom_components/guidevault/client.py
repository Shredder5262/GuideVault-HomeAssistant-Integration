"""Async API client for GuideVault."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import COMMAND_ENDPOINT, DEFAULT_TIMEOUT, STATUS_ENDPOINT


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
    command_endpoint: str = COMMAND_ENDPOINT
    status_endpoint: str = STATUS_ENDPOINT

    @property
    def base_url(self) -> str:
        """Return normalized GuideVault base URL."""
        host = self.host.strip().rstrip("/")

        if host.startswith("http://") or host.startswith("https://"):
            parsed = urlparse(host)
            scheme = parsed.scheme
            hostname = parsed.hostname or parsed.netloc
            path = parsed.path.rstrip("/")
            port = parsed.port or self.port

            if port:
                netloc = f"{hostname}:{port}"
            else:
                netloc = hostname

            return f"{scheme}://{netloc}{path}"

        scheme = "https" if self.ssl else "http"
        if self.port:
            return f"{scheme}://{host}:{self.port}"
        return f"{scheme}://{host}"


class GuideVaultClient:
    """Async client for the GuideVault Home Assistant API."""

    def __init__(self, session: ClientSession, config: GuideVaultClientConfig) -> None:
        self._session = session
        self._config = config

    @property
    def base_url(self) -> str:
        """Return the configured GuideVault base URL."""
        return self._config.base_url

    @property
    def command_url(self) -> str:
        """Return the configured command URL."""
        return f"{self.base_url}{_normalize_endpoint(self._config.command_endpoint)}"

    @property
    def status_url(self) -> str:
        """Return the configured status URL."""
        return f"{self.base_url}{_normalize_endpoint(self._config.status_endpoint)}"

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

        The status endpoint is preferred, but older GuideVault builds may not
        have it. In that case, any non-5xx response from the base URL is enough
        to allow setup.
        """
        probes = (
            _normalize_endpoint(self._config.status_endpoint),
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

    async def async_status(self) -> dict[str, Any]:
        """Read GuideVault status."""
        try:
            async with asyncio.timeout(self._config.timeout):
                async with self._session.get(
                    self.status_url,
                    headers=self._headers(),
                    ssl=self._config.verify_ssl,
                ) as response:
                    text = await response.text()

                    if response.status < 200 or response.status >= 300:
                        raise GuideVaultApiError(
                            f"GuideVault status failed with HTTP {response.status}: {text}"
                        )

                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" not in content_type:
                        return {
                            "ok": True,
                            "raw": text,
                            "statusEndpoint": self.status_url,
                        }

                    data = await response.json()
                    if isinstance(data, dict):
                        return data

                    return {"ok": True, "value": data}
        except GuideVaultApiError:
            raise
        except (TimeoutError, ClientResponseError, ClientError, OSError) as err:
            raise GuideVaultConnectionError(
                f"Could not read GuideVault status: {err}"
            ) from err

    async def async_command(self, payload: dict[str, Any]) -> Any:
        """Send a command to GuideVault."""
        command_payload = build_guidevault_payload(payload)

        try:
            async with asyncio.timeout(self._config.timeout):
                async with self._session.post(
                    self.command_url,
                    headers=self._headers(),
                    json=command_payload,
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


def build_guidevault_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert Home Assistant service data into GuideVault's REST payload.

    GuideVault's existing Home Assistant REST command payload uses camelCase
    names, for example action, itemTitle, itemKind, issueNumber, displayMode,
    and backgroundBrightness. This function preserves that contract while still
    accepting Home Assistant-friendly snake_case service fields.
    """
    incoming = dict(payload)

    extra_payload = incoming.pop("payload", None)
    if isinstance(extra_payload, dict):
        incoming.update(extra_payload)

    action = _first(
        incoming,
        "action",
        "command_action",
        "commandAction",
    )

    if not action:
        raise GuideVaultApiError("A GuideVault action is required.")

    item_kind = _first(incoming, "itemKind", "item_kind", "content_type") or ""
    item_kind = _normalize_item_kind(item_kind)

    return _clean_payload(
        {
            "action": action,
            "itemTitle": _first(incoming, "itemTitle", "item_title", "title") or "",
            "itemKind": item_kind,
            "issueNumber": _first(incoming, "issueNumber", "issue_number", "issue") or "",
            "volume": _first(incoming, "volume") or "",
            "page": _number(_first(incoming, "page"), 0),
            "zoom": _number(_first(incoming, "zoom"), 0),
            "displayMode": _first(incoming, "displayMode", "display_mode") or "",
            "background": _first(incoming, "background") or "",
            "backgroundBrightness": _number(
                _first(incoming, "backgroundBrightness", "background_brightness"),
                0,
            ),
            "fullscreen": _optional_bool(_first(incoming, "fullscreen")),
        }
    )


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = str(endpoint or "").strip()
    if not endpoint:
        return "/"
    return endpoint if endpoint.startswith("/") else f"/{endpoint}"


def _normalize_item_kind(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "auto":
        return ""
    if text in ("strategy_guide", "strategy-guide", "strategy guide", "guide"):
        return "strategyGuide"
    return text


def _first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _number(value: Any, default: int | float) -> int | float:
    if value is None or value == "":
        return default

    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if number.is_integer():
        return int(number)

    return number


def _optional_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off"):
        return False

    return None


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
