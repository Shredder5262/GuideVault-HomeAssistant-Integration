"""Sensors for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERSION
from .coordinator import GuideVaultCoordinator
from .entity import GuideVaultEntity


def _server_version(coordinator: GuideVaultCoordinator) -> str:
    data = coordinator.data or {}
    return str(data.get("version") or data.get("serverVersion") or data.get("appVersion") or "Unknown")


def _display_mode(coordinator: GuideVaultCoordinator) -> str:
    return str(coordinator.reader.get("displayMode") or "")


def _progress(coordinator: GuideVaultCoordinator) -> float:
    try:
        return float(coordinator.reader.get("progressPercent") or 0)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class GuideVaultSensorDescription:
    key: str
    name: str
    value_fn: Callable[[GuideVaultCoordinator], Any]
    icon: str


SENSORS = [
    GuideVaultSensorDescription(
        "integration_version",
        "Integration Version",
        lambda c: VERSION,
        "mdi:puzzle-outline",
    ),
    GuideVaultSensorDescription(
        "server_version",
        "Server Version",
        _server_version,
        "mdi:server",
    ),
    GuideVaultSensorDescription(
        "reader",
        "Reader",
        lambda c: "reading" if c.reader.get("readerActive") else "idle",
        "mdi:book-open-page-variant",
    ),
    GuideVaultSensorDescription(
        "current_item",
        "Current Item",
        lambda c: c.reader.get("itemTitle") or "None",
        "mdi:book-open",
    ),
    GuideVaultSensorDescription(
        "current_item_kind",
        "Current Item Kind",
        lambda c: c.reader.get("itemKind") or "None",
        "mdi:shape-outline",
    ),
    GuideVaultSensorDescription(
        "page",
        "Page",
        lambda c: c.reader.get("page") or 0,
        "mdi:file-document-outline",
    ),
    GuideVaultSensorDescription(
        "page_count",
        "Page Count",
        lambda c: c.reader.get("pageCount") or 0,
        "mdi:file-multiple-outline",
    ),
    GuideVaultSensorDescription(
        "progress_percent",
        "Progress Percent",
        _progress,
        "mdi:progress-check",
    ),
    GuideVaultSensorDescription(
        "zoom",
        "Zoom",
        lambda c: c.reader.get("zoom") or 100,
        "mdi:magnify",
    ),
    GuideVaultSensorDescription(
        "display_mode",
        "Display Mode",
        _display_mode,
        "mdi:book-open-variant",
    ),
    GuideVaultSensorDescription(
        "background",
        "Background",
        lambda c: c.current_background_display_name,
        "mdi:image-filter-hdr",
    ),
    GuideVaultSensorDescription(
        "background_brightness_state",
        "Background Brightness State",
        lambda c: c.reader.get("backgroundBrightness") or 72,
        "mdi:brightness-6",
    ),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up GuideVault sensors."""
    coordinator: GuideVaultCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuideVaultSensor(coordinator, description) for description in SENSORS])


class GuideVaultSensor(GuideVaultEntity, SensorEntity):
    """GuideVault sensor entity."""

    def __init__(self, coordinator: GuideVaultCoordinator, description: GuideVaultSensorDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        reader = self.coordinator.reader
        data = self.coordinator.data or {}
        return {
            "integration_version": VERSION,
            "server_version": data.get("version") or data.get("serverVersion") or data.get("appVersion") or "",
            "enabled": data.get("enabled", False),
            "push_state_enabled": data.get("pushStateEnabled", False),
            "push_events_enabled": data.get("pushEventsEnabled", False),
            "command_enabled": data.get("commandEnabled", False),
            "entity_prefix": data.get("entityPrefix", "guidevault"),
            "reader_active": reader.get("readerActive", False),
            "view": reader.get("view", "library"),
            "item_id": reader.get("itemId", ""),
            "item_title": reader.get("itemTitle", ""),
            "item_kind": reader.get("itemKind", ""),
            "page": reader.get("page", 0),
            "page_count": reader.get("pageCount", 0),
            "progress_percent": reader.get("progressPercent", 0),
            "zoom": reader.get("zoom", 100),
            "display_mode": reader.get("displayMode", ""),
            "fullscreen": reader.get("fullscreen", False),
            "background": self.coordinator.current_background_name,
            "background_display_name": self.coordinator.current_background_display_name,
            "background_brightness": reader.get("backgroundBrightness", 72),
            "available_backgrounds": [bg["name"] for bg in self.coordinator.available_backgrounds],
            "available_background_options": self.coordinator.available_backgrounds,
        }
