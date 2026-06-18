"""Number entities for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import async_send_command
from .const import (
    ACTION_PAGE_GOTO,
    ACTION_SET_BACKGROUND_BRIGHTNESS,
    ACTION_SET_ZOOM,
    DATA_COORDINATORS,
    DOMAIN,
)
from .coordinator import GuideVaultDataUpdateCoordinator


@dataclass(frozen=True, slots=True)
class GuideVaultNumberDescription:
    """Description for a GuideVault number entity."""

    key: str
    name: str
    icon: str
    action: str
    value_keys: tuple[str, ...]
    payload_key: str
    minimum: float
    maximum: float
    step: float
    mode: NumberMode


NUMBERS: tuple[GuideVaultNumberDescription, ...] = (
    GuideVaultNumberDescription(
        key="page_control",
        name="Page",
        icon="mdi:file-document-outline",
        action=ACTION_PAGE_GOTO,
        value_keys=("page", "reader.page", "currentPage", "reader.currentPage"),
        payload_key="page",
        minimum=1,
        maximum=9999,
        step=1,
        mode=NumberMode.BOX,
    ),
    GuideVaultNumberDescription(
        key="background_brightness_control",
        name="Background brightness",
        icon="mdi:brightness-6",
        action=ACTION_SET_BACKGROUND_BRIGHTNESS,
        value_keys=("backgroundBrightness", "reader.backgroundBrightness", "brightness", "reader.brightness"),
        payload_key="background_brightness",
        minimum=0,
        maximum=100,
        step=1,
        mode=NumberMode.SLIDER,
    ),
    GuideVaultNumberDescription(
        key="zoom_control",
        name="Zoom",
        icon="mdi:magnify",
        action=ACTION_SET_ZOOM,
        value_keys=("zoom", "reader.zoom", "zoomPercent", "reader.zoomPercent"),
        payload_key="zoom",
        minimum=10,
        maximum=500,
        step=5,
        mode=NumberMode.BOX,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GuideVault number entities."""
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]

    async_add_entities(
        GuideVaultNumber(hass, coordinator, entry, description)
        for description in NUMBERS
    )


class GuideVaultNumber(CoordinatorEntity[GuideVaultDataUpdateCoordinator], NumberEntity):
    """GuideVault number entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: GuideVaultDataUpdateCoordinator,
        entry: ConfigEntry,
        description: GuideVaultNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step
        self._attr_mode = description.mode
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }

    @property
    def native_value(self) -> float | None:
        """Return current value."""
        value = _find_first(self.coordinator.data or {}, self._description.value_keys)
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set number value."""
        await async_send_command(
            self._hass,
            self._entry.entry_id,
            {
                "action": self._description.action,
                self._description.payload_key: value,
            },
        )


def _find_first(data: Any, paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = _get_path(data, path)
        if value not in (None, ""):
            return value
    return None


def _get_path(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        if part in current:
            current = current[part]
            continue
        normalized = _normalize_key(part)
        matched = None
        for key, value in current.items():
            if _normalize_key(key) == normalized:
                matched = value
                break
        if matched is None:
            return None
        current = matched
    return current


def _normalize_key(value: Any) -> str:
    return ''.join(ch for ch in str(value).lower() if ch.isalnum())
