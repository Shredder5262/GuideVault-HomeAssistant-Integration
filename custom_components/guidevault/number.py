"""Number entities for GuideVault."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import async_send_command
from .const import ACTION_SET_BACKGROUND_BRIGHTNESS, ACTION_SET_ZOOM, DATA_COORDINATORS, DOMAIN
from .coordinator import GuideVaultDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities([
        GuideVaultZoomNumber(hass, coordinator, entry),
        GuideVaultBackgroundBrightnessNumber(hass, coordinator, entry),
    ])


class GuideVaultBaseNumber(CoordinatorEntity[GuideVaultDataUpdateCoordinator], NumberEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry, key: str, name: str, icon: str, minimum: float, maximum: float, step: float, mode: NumberMode) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_mode = mode
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }


class GuideVaultZoomNumber(GuideVaultBaseNumber):
    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(hass, coordinator, entry, "zoom_control", "Zoom", "mdi:magnify", 10, 500, 5, NumberMode.BOX)

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        value = _find_first(data, ("zoom", "reader.zoom", "zoomPercent", "reader.zoomPercent"))
        return _float_or_none(value)

    async def async_set_native_value(self, value: float) -> None:
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_SET_ZOOM, "zoom": value})


class GuideVaultBackgroundBrightnessNumber(GuideVaultBaseNumber):
    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry) -> None:
        # BOX mode avoids the Home Assistant more-info panel popping open when
        # dragging an inline slider all the way to 0. The value can still be set
        # to 0 and the service still sends set_background_brightness.
        super().__init__(hass, coordinator, entry, "background_brightness_control", "Background brightness", "mdi:brightness-6", 0, 100, 1, NumberMode.BOX)

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        value = _find_first(data, ("backgroundBrightness", "reader.backgroundBrightness", "brightness", "reader.brightness"))
        number = _float_or_none(value)
        return 100 if number is None else number

    async def async_set_native_value(self, value: float) -> None:
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_SET_BACKGROUND_BRIGHTNESS, "background_brightness": value})


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


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
