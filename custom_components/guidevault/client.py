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


ACTION_ALIASES = {
    # Earlier guessed names -> confirmed GuideVault REST names.
    "next": "next_page",
    "page_next": "next_page",
    "previous": "previous_page",
    "page_previous": "previous_page",
    "first": "first_page",
    "page_first": "first_page",
    "last": "last_page",
    "page_last": "last_page",
    "page": "set_page",
    "go_to_page": "set_page",
    "displayMode": "set_display_mode",
    "display_mode": "set_display_mode",
    "close": "close_reader",
    "manual": "open_manual",
    "strategyGuide": "open_strategy_guide",
    "strategy_guide": "open_strategy_guide",
    "strategy-guide": "open_strategy_guide",
    "magazine": "open_magazine",
}


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
            netloc = f"{hostname}:{port}" if port else hostname
            return f"{scheme}://{netloc}{path}"

        scheme = "https" if self.ssl else "http"
        return f"{scheme}://{host}:{self.port}" if self.port else f"{scheme}://{host}"


class GuideVaultClient:
    """Async client for the GuideVault Home Assistant API."""

    def __init__(self, session: ClientSession, config: GuideVaultClientConfig) -> None:
        self._session = session
        self._config = config

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def command_url(self) -> str:
        return f"{self.base_url}{_normalize_endpoint(self._config.command_endpoint)}"

    @property
    def status_url(self) -> str:
        return f"{self.base_url}{_normalize_endpoint(self._config.status_endpoint)}"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-GuideVault",
        }
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
            headers["X-Api-Key"] = self._config.api_key
        return headers

    async def async_test_connection(self) -> None:
        """Test whether GuideVault can be reached."""
        probes = (_normalize_endpoint(self._config.status_endpoint), "/api/health", "/health", "/")
        last_error: Exception | str | None = None

        for path in probes:
            try:
                async with asyncio.timeout(self._config.timeout):
                    async with self._session.get(
                        f"{self.base_url}{path}",
                        headers=self._headers(),
                        ssl=self._config.verify_ssl,
                    ) as response:
                        if response.status < 500:
                            return
                        last_error = f"HTTP {response.status} for {path}"
            except (TimeoutError, ClientError, OSError) as err:
                last_error = err

        raise GuideVaultConnectionError(f"Could not reach GuideVault at {self.base_url}: {last_error}")

    async def async_status(self) -> dict[str, Any]:
        """Read GuideVault status.

        Preferred:
          GET /api/home-assistant/status

        Fallback:
          POST /api/home-assistant/command
          { "action": "status", ... }
        """
        try:
            data = await self._async_get_json_or_text(self.status_url, fail_on_http_error=True)
            result = data if isinstance(data, dict) else {"ok": True, "raw": data}
        except (GuideVaultApiError, GuideVaultConnectionError):
            fallback = await self._async_post_command_payload(build_guidevault_payload({"action": "status"}))
            result = fallback if isinstance(fallback, dict) else {"ok": True, "raw": fallback}

        if not _has_any_key(result, ("version", "serverVersion", "guideVaultVersion", "appVersion")):
            version = await self._async_read_version_fallback()
            if version:
                result["version"] = version

        return result

    async def _async_read_version_fallback(self) -> str | None:
        for path in (
            "/api/home-assistant/info",
            "/api/home-assistant/version",
            "/api/info",
            "/api/system/info",
            "/api/server/info",
            "/api/version",
            "/version",
        ):
            try:
                value = await self._async_get_json_or_text(f"{self.base_url}{path}", fail_on_http_error=False)
            except (GuideVaultConnectionError, GuideVaultApiError):
                continue
            version = _extract_version(value)
            if version:
                return version
        return None

    async def _async_get_json_or_text(self, url: str, *, fail_on_http_error: bool) -> Any:
        try:
            async with asyncio.timeout(self._config.timeout):
                async with self._session.get(url, headers=self._headers(), ssl=self._config.verify_ssl) as response:
                    text = await response.text()
                    if response.status < 200 or response.status >= 300:
                        if fail_on_http_error:
                            raise GuideVaultApiError(f"GuideVault status failed with HTTP {response.status}: {text}")
                        return None
                    if "application/json" in response.headers.get("Content-Type", ""):
                        return await response.json()
                    return text
        except GuideVaultApiError:
            raise
        except (TimeoutError, ClientResponseError, ClientError, OSError) as err:
            raise GuideVaultConnectionError(f"Could not read GuideVault status: {err}") from err

    async def async_command(self, payload: dict[str, Any]) -> Any:
        return await self._async_post_command_payload(build_guidevault_payload(payload))

    async def _async_post_command_payload(self, command_payload: dict[str, Any]) -> Any:
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
                        raise GuideVaultApiError(f"GuideVault command failed with HTTP {response.status}: {text}")
                    if "application/json" in response.headers.get("Content-Type", ""):
                        return await response.json()
                    return {"ok": True, "response": text}
        except GuideVaultApiError:
            raise
        except (TimeoutError, ClientResponseError, ClientError, OSError) as err:
            raise GuideVaultConnectionError(f"Could not send command to GuideVault: {err}") from err


def build_guidevault_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the GuideVault REST command payload."""
    incoming = dict(payload)
    extra_payload = incoming.pop("payload", None)
    if isinstance(extra_payload, dict):
        incoming.update(extra_payload)

    action = _first(incoming, "action", "command_action", "commandAction")
    if not action:
        raise GuideVaultApiError("A GuideVault action is required.")

    return {
        "action": _normalize_action(action),
        "itemTitle": _first(incoming, "itemTitle", "item_title", "title") or "",
        "itemKind": _normalize_item_kind(_first(incoming, "itemKind", "item_kind", "content_type") or ""),
        "issueNumber": _first(incoming, "issueNumber", "issue_number", "issue") or "",
        "volume": _first(incoming, "volume") or "",
        "page": _number(_first(incoming, "page"), 0),
        "zoom": _number(_first(incoming, "zoom"), 0),
        "displayMode": _normalize_display_mode(_first(incoming, "displayMode", "display_mode") or ""),
        "background": _first(incoming, "background") or "",
        "backgroundBrightness": _number(_first(incoming, "backgroundBrightness", "background_brightness"), 0),
    }


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = str(endpoint or "").strip()
    if not endpoint:
        return "/"
    return endpoint if endpoint.startswith("/") else f"/{endpoint}"


def _normalize_action(value: Any) -> str:
    text = str(value or "").strip()
    return ACTION_ALIASES.get(text, text)


def _normalize_item_kind(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "auto":
        return ""
    if text in ("strategy_guide", "strategy-guide", "strategy guide", "guide"):
        return "strategyGuide"
    return text


def _normalize_display_mode(value: Any) -> str:
    text = str(value or "").strip()
    low = text.lower().replace("_", " ").replace("-", " ")
    if low in ("single", "one", "one page", "1", "1page", "1 page"):
        return "1 page"
    if low in ("double", "two", "two page", "two pages", "2", "2page", "2 page", "2 pages"):
        return "2 page"
    if low in ("adaptive", "two page adaptive", "two pages adaptive", "2 adaptive", "2pageadaptive", "2 page adaptive", "2 pages adaptive"):
        return "2 page adaptive"
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
    return int(number) if number.is_integer() else number


def _has_any_key(data: dict[str, Any], keys: tuple[str, ...]) -> bool:
    lowered = {str(key).lower() for key in data}
    return any(key.lower() in lowered for key in keys)


def _extract_version(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text if text and len(text) < 80 and "<html" not in text.lower() else None
    if isinstance(value, dict):
        for key in ("version", "serverVersion", "guideVaultVersion", "appVersion"):
            item = value.get(key)
            if item not in (None, ""):
                return str(item)
        for item in value.values():
            version = _extract_version(item)
            if version:
                return version
    return None
