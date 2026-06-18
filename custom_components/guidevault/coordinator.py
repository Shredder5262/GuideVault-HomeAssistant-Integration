"""Coordinator for GuideVault status."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import GuideVaultApiError, GuideVaultClient, GuideVaultConnectionError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GuideVaultDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates GuideVault status updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: GuideVaultClient) -> None:
        interval = int(entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=max(2, interval)),
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_status()
        except (GuideVaultConnectionError, GuideVaultApiError) as err:
            raise UpdateFailed(str(err)) from err
