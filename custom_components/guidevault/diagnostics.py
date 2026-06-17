"""Diagnostics support for GuideVault."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DATA_COORDINATORS, DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    data = dict(entry.data)
    if CONF_API_KEY in data:
        data[CONF_API_KEY] = "**REDACTED**"

    coordinator = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).get(entry.entry_id)

    return {
        "entry": {
            "title": entry.title,
            "data": data,
            "options": dict(entry.options),
        },
        "domain_loaded": DOMAIN in hass.data,
        "last_update_success": None if coordinator is None else coordinator.last_update_success,
        "status_url": None if coordinator is None else coordinator.client.status_url,
        "command_url": None if coordinator is None else coordinator.client.command_url,
    }
