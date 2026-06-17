"""Select entities for GuideVault."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import async_send_command
from .const import ACTION_SET_DISPLAY_MODE, DATA_COORDINATORS, DISPLAY_MODES, DOMAIN
from .coordinator import GuideVaultDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities([GuideVaultDisplayModeSelect(hass, coordinator, entry)])


class GuideVaultDisplayModeSelect(CoordinatorEntity[GuideVaultDataUpdateCoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Display mode"
    _attr_icon = "mdi:book-open-variant"

    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_display_mode_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        value = _find_first(data, ("displayMode", "reader.displayMode", "pageMode", "reader.pageMode"))
        if value is None:
            return None
        return _normalize_display_mode(value)

    @property
    def options(self) -> list[str]:
        return list(DISPLAY_MODES)

    async def async_select_option(self, option: str) -> None:
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_SET_DISPLAY_MODE, "display_mode": option})


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
