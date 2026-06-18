"""Local API client for GuideVault."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession


class GuideVaultApiError(Exception):
    """Raised when GuideVault cannot be reached or returns an error."""


class GuideVaultApiClient:
    """Small async client for GuideVault's Home Assistant endpoints."""

    def __init__(self, session: ClientSession, base_url: str, command_token: str | None = None) -> None:
        self._session = session
        self.base_url = self._normalize_base_url(base_url)
        self.command_token = (command_token or "").strip()

    @staticmethod
    def _normalize_base_url(value: str) -> str:
        text = (value or "").strip().rstrip("/")
        if not text:
            raise GuideVaultApiError("GuideVault URL is required.")
        if not text.startswith(("http://", "https://")):
            text = f"http://{text}"
        return text

    async def async_get_status(self) -> dict[str, Any]:
        """Read GuideVault's Home Assistant status snapshot."""
        url = f"{self.base_url}/api/home-assistant/status"
        try:
            async with self._session.get(url, timeout=10) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, ClientResponseError, TimeoutError) as err:
            raise GuideVaultApiError(f"Unable to read GuideVault status: {err}") from err
        if not isinstance(payload, dict):
            raise GuideVaultApiError("GuideVault returned an invalid status payload.")
        return payload

    async def async_send_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Queue a command for the active GuideVault reader."""
        if not self.command_token:
            raise GuideVaultApiError("GuideVault command token is required for controls.")
        url = f"{self.base_url}/api/home-assistant/command"
        headers = {
            "Authorization": f"Bearer {self.command_token}",
            "Content-Type": "application/json",
        }
        try:
            async with self._session.post(url, json=payload, headers=headers, timeout=10) as response:
                response.raise_for_status()
                result = await response.json(content_type=None)
        except (ClientError, ClientResponseError, TimeoutError) as err:
            raise GuideVaultApiError(f"GuideVault command failed: {err}") from err
        return result if isinstance(result, dict) else {"queued": True}
