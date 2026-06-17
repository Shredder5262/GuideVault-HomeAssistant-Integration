"""Sensor entities for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATORS, DOMAIN
from .coordinator import GuideVaultDataUpdateCoordinator


def _first(data: dict[str, Any], *paths: str) -> Any:
    """Return the first populated value from dotted paths."""
    for path in paths:
        current: Any = data
        found = True

        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break

        if found and current not in (None, ""):
            return current

    return None


def _reader_state(data: dict[str, Any]) -> str | None:
    value = _first(data, "readerOpen", "reader.open", "isReaderOpen", "open")
    if isinstance(value, bool):
        return "open" if value else "closed"

    explicit = _first(data, "readerState", "reader.state", "state")
    if explicit is not None:
        return str(explicit)

    return None


def _currently_reading(data: dict[str, Any]) -> str | None:
    return _first(
        data,
        "currentlyReading",
        "currentTitle",
        "itemTitle",
        "title",
        "reader.currentTitle",
        "reader.itemTitle",
        "reader.title",
    )


def _content_type(data: dict[str, Any]) -> str | None:
    return _first(data, "contentType", "itemKind", "kind", "reader.contentType", "reader.itemKind")


def _page(data: dict[str, Any]) -> int | None:
    return _int_or_none(_first(data, "page", "currentPage", "reader.page", "reader.currentPage"))


def _page_count(data: dict[str, Any]) -> int | None:
    return _int_or_none(_first(data, "pageCount", "totalPages", "reader.pageCount", "reader.totalPages"))


def _zoom(data: dict[str, Any]) -> float | int | None:
    return _number_or_none(_first(data, "zoom", "reader.zoom"))


def _display_mode(data: dict[str, Any]) -> str | None:
    return _first(data, "displayMode", "reader.displayMode")


def _background(data: dict[str, Any]) -> str | None:
    return _first(data, "background", "reader.background")


def _background_brightness(data: dict[str, Any]) -> float | int | None:
    return _number_or_none(_first(data, "backgroundBrightness", "reader.backgroundBrightness"))


def _fullscreen(data: dict[str, Any]) -> str | None:
    value = _first(data, "fullscreen", "isFullscreen", "reader.fullscreen", "reader.isFullscreen")
    if isinstance(value, bool):
        return "on" if value else "off"
    if value is not None:
        return str(value)
    return None


def _version(data: dict[str, Any]) -> str | None:
    return _first(data, "version", "serverVersion", "guideVaultVersion")


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _number_or_none(value: Any) -> float | int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number.is_integer():
        return int(number)

    return number


@dataclass(frozen=True, slots=True)
class GuideVaultSensorDescription(SensorEntityDescription):
    """Description for a GuideVault sensor."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None


SENSORS: tuple[GuideVaultSensorDescription, ...] = (
    GuideVaultSensorDescription(
        key="currently_reading",
        name="Currently reading",
        icon="mdi:book-open-page-variant",
        value_fn=_currently_reading,
    ),
    GuideVaultSensorDescription(
        key="reader_state",
        name="Reader state",
        icon="mdi:book-open",
        value_fn=_reader_state,
    ),
    GuideVaultSensorDescription(
        key="content_type",
        name="Content type",
        icon="mdi:shape",
        value_fn=_content_type,
    ),
    GuideVaultSensorDescription(
        key="page",
        name="Page",
        icon="mdi:file-document-outline",
        value_fn=_page,
    ),
    GuideVaultSensorDescription(
        key="page_count",
        name="Page count",
        icon="mdi:file-document-multiple-outline",
        value_fn=_page_count,
    ),
    GuideVaultSensorDescription(
        key="zoom",
        name="Zoom",
        icon="mdi:magnify",
        value_fn=_zoom,
    ),
    GuideVaultSensorDescription(
        key="display_mode",
        name="Display mode",
        icon="mdi:book-open-variant",
        value_fn=_display_mode,
    ),
    GuideVaultSensorDescription(
        key="background",
        name="Background",
        icon="mdi:image",
        value_fn=_background,
    ),
    GuideVaultSensorDescription(
        key="background_brightness",
        name="Background brightness",
        icon="mdi:brightness-6",
        value_fn=_background_brightness,
    ),
    GuideVaultSensorDescription(
        key="fullscreen",
        name="Fullscreen",
        icon="mdi:fullscreen",
        value_fn=_fullscreen,
    ),
    GuideVaultSensorDescription(
        key="version",
        name="Version",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_version,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GuideVault sensors."""
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]

    async_add_entities(
        GuideVaultSensor(coordinator, entry, description)
        for description in SENSORS
    )


class GuideVaultSensor(CoordinatorEntity[GuideVaultDataUpdateCoordinator], SensorEntity):
    """GuideVault status sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GuideVaultDataUpdateCoordinator,
        entry: ConfigEntry,
        description: GuideVaultSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.last_update_success:
            return None

        data = self.coordinator.data or {}
        if not isinstance(data, dict):
            return None

        if self.entity_description.value_fn is None:
            return None

        return self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return useful status attributes for the main reading sensor."""
        if self.entity_description.key != "currently_reading":
            return None

        data = self.coordinator.data or {}
        if not isinstance(data, dict):
            return None

        return {
            "reader_state": _reader_state(data),
            "content_type": _content_type(data),
            "page": _page(data),
            "page_count": _page_count(data),
            "zoom": _zoom(data),
            "display_mode": _display_mode(data),
            "background": _background(data),
            "background_brightness": _background_brightness(data),
            "fullscreen": _fullscreen(data),
            "status_endpoint": self.coordinator.client.status_url,
        }
