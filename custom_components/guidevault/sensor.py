"""Sensor entities for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATORS, DOMAIN
from .coordinator import GuideVaultDataUpdateCoordinator


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _flatten(data: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            full = f"{prefix}.{key}" if prefix else str(key)
            flat[_normalize_key(full)] = value
            flat[_normalize_key(str(key))] = value
            flat.update(_flatten(value, full))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            flat.update(_flatten(value, f"{prefix}.{index}" if prefix else str(index)))
    return flat


def _find(data: dict[str, Any], *keys: str) -> Any:
    flat = _flatten(data)
    for key in keys:
        normalized = _normalize_key(key)
        if normalized in flat and flat[normalized] not in (None, ""):
            return flat[normalized]
    return None


def _reader_state(data: dict[str, Any]) -> str | None:
    explicit = _find(data, "readerState", "reader.state", "state", "readingState")
    if explicit is not None:
        return str(explicit)
    value = _find(data, "readerOpen", "reader.open", "isReaderOpen", "open", "readerVisible")
    if isinstance(value, bool):
        return "open" if value else "closed"
    if _currently_reading(data) or _page(data) is not None:
        return "reading"
    return None


def _currently_reading(data: dict[str, Any]) -> str | None:
    value = _find(data, "currentlyReading", "currentTitle", "itemTitle", "title", "reader.currentTitle", "reader.itemTitle", "reader.title", "activeTitle", "activeItem.title", "document.title")
    return None if value is None else str(value)


def _content_type(data: dict[str, Any]) -> str | None:
    value = _find(data, "contentType", "itemKind", "kind", "type", "reader.contentType", "reader.itemKind")
    return None if value is None else str(value)


def _page(data: dict[str, Any]) -> int | None:
    return _int_or_none(_find(data, "page", "currentPage", "pageNumber", "reader.page", "reader.currentPage"))


def _page_count(data: dict[str, Any]) -> int | None:
    return _int_or_none(_find(data, "pageCount", "totalPages", "pages", "reader.pageCount", "reader.totalPages"))


def _zoom(data: dict[str, Any]) -> float | int | None:
    return _number_or_none(_find(data, "zoom", "zoomPercent", "reader.zoom", "reader.zoomPercent"))


def _display_mode(data: dict[str, Any]) -> str | None:
    value = _find(data, "displayMode", "pageMode", "reader.displayMode", "reader.pageMode")
    if value is None:
        return None
    return _normalize_display_mode(value)


def _background(data: dict[str, Any]) -> str | None:
    value = _find(data, "background", "backgroundName", "reader.background", "reader.backgroundName")
    return None if value is None else str(value)


def _background_brightness(data: dict[str, Any]) -> float | int | None:
    return _number_or_none(_find(data, "backgroundBrightness", "brightness", "reader.backgroundBrightness", "reader.brightness"))


def _overlay(data: dict[str, Any]) -> str | None:
    value = _find(data, "fullscreen", "isFullscreen", "reader.fullscreen", "reader.isFullscreen", "fullScreen", "overlay", "overlayVisible")
    if isinstance(value, bool):
        return "on" if value else "off"
    if value is not None:
        return str(value)
    return None


def _version(data: dict[str, Any]) -> str | None:
    value = _find(data, "version", "serverVersion", "guideVaultVersion", "appVersion", "applicationVersion", "buildVersion")
    return None if value is None else str(value)


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
    return int(number) if number.is_integer() else number


@dataclass(frozen=True, slots=True)
class GuideVaultSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None


SENSORS: tuple[GuideVaultSensorDescription, ...] = (
    GuideVaultSensorDescription(key="currently_reading", name="Currently reading", icon="mdi:book-open-page-variant", value_fn=_currently_reading),
    GuideVaultSensorDescription(key="reader_state", name="Reader state", icon="mdi:book-open", value_fn=_reader_state),
    GuideVaultSensorDescription(key="content_type", name="Content type", icon="mdi:shape", value_fn=_content_type),
    GuideVaultSensorDescription(key="page", name="Page", icon="mdi:file-document-outline", value_fn=_page),
    GuideVaultSensorDescription(key="page_count", name="Page count", icon="mdi:file-document-multiple-outline", value_fn=_page_count),
    GuideVaultSensorDescription(key="zoom", name="Zoom", icon="mdi:magnify", value_fn=_zoom),
    GuideVaultSensorDescription(key="display_mode", name="Display mode", icon="mdi:book-open-variant", value_fn=_display_mode),
    GuideVaultSensorDescription(key="background", name="Background", icon="mdi:image", value_fn=_background),
    GuideVaultSensorDescription(key="background_brightness", name="Background brightness", icon="mdi:brightness-6", value_fn=_background_brightness),
    GuideVaultSensorDescription(key="fullscreen", name="Overlay / fullscreen", icon="mdi:fullscreen", value_fn=_overlay),
    GuideVaultSensorDescription(key="version", name="Version", icon="mdi:information-outline", entity_category=EntityCategory.DIAGNOSTIC, value_fn=_version),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(GuideVaultSensor(coordinator, entry, description) for description in SENSORS)


class GuideVaultSensor(CoordinatorEntity[GuideVaultDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry, description: GuideVaultSensorDescription) -> None:
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
        data = self.coordinator.data or {}
        if not isinstance(data, dict) or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data or {}
        if not isinstance(data, dict) or self.entity_description.key != "currently_reading":
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
            "overlay_or_fullscreen": _overlay(data),
            "version": _version(data),
            "status_endpoint": self.coordinator.client.status_url,
        }
