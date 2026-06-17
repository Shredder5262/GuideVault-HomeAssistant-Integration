"""Number entities for GuideVault."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import async_send_command
from .const import ACTION_SET_ZOOM, DATA_COORDINATORS, DOMAIN
from .coordinator import GuideVaultDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities([GuideVaultZoomNumber(hass, coordinator, entry)])


class GuideVaultZoomNumber(CoordinatorEntity[GuideVaultDataUpdateCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Zoom"
    _attr_icon = "mdi:magnify"
    _attr_native_min_value = 10
    _attr_native_max_value = 500
    _attr_native_step = 5
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_zoom_control"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        value = _find_first(data, ("zoom", "reader.zoom", "zoomPercent", "reader.zoomPercent"))
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_SET_ZOOM, "zoom": value})


def _find_first(data: Any, paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = _get_path(data, path)
        if value not in (None, ""):
            return value
    return None


def _get_path(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current
