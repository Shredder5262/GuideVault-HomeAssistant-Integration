"""Data coordinator for GuideVault."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GuideVaultApiClient, GuideVaultApiError
from .const import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GuideVaultCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll GuideVault status and expose convenience helpers."""

    def __init__(self, hass: HomeAssistant, api: GuideVaultApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_status()
        except GuideVaultApiError as err:
            raise UpdateFailed(str(err)) from err

    @property
    def reader(self) -> dict[str, Any]:
        data = self.data or {}
        reader = data.get("reader") or {}
        return reader if isinstance(reader, dict) else {}

    @property
    def available_backgrounds(self) -> list[dict[str, str]]:
        """Return installed backgrounds from top-level status, falling back to reader status."""
        data = self.data or {}
        raw = data.get("availableBackgrounds") or self.reader.get("availableBackgrounds") or []
        backgrounds: list[dict[str, str]] = []
        if not isinstance(raw, list):
            return backgrounds
        for item in raw:
            if isinstance(item, str):
                name = item.strip()
                if name:
                    backgrounds.append({"name": name, "displayName": name, "url": ""})
            elif isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name:
                    backgrounds.append(
                        {
                            "name": name,
                            "displayName": str(item.get("displayName") or item.get("display_name") or name).strip(),
                            "url": str(item.get("url") or "").strip(),
                        }
                    )
        return backgrounds

    @property
    def current_background_name(self) -> str:
        return str(self.reader.get("background") or self.reader.get("backgroundName") or "").strip()

    @property
    def current_background_display_name(self) -> str:
        display = str(self.reader.get("backgroundDisplayName") or "").strip()
        if display:
            return display
        current = self.current_background_name
        for background in self.available_backgrounds:
            if background["name"].lower() == current.lower():
                return background["displayName"]
        return "Default Gradient" if not current else current

    async def async_command(self, action: str, **payload: Any) -> None:
        command = {"action": action, **payload}
        await self.api.async_send_command(command)
        await self.async_request_refresh()
