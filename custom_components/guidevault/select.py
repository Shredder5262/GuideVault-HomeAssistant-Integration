"""Select entities for GuideVault."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import async_send_command
from .const import (
    ACTION_SET_BACKGROUND,
    ACTION_SET_DISPLAY_MODE,
    DATA_COORDINATORS,
    DEFAULT_BACKGROUNDS,
    DISPLAY_MODES,
    DOMAIN,
)
from .coordinator import GuideVaultDataUpdateCoordinator

UNKNOWN_VALUES = {"unknown", "unavailable", "none", "null", ""}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities([
        GuideVaultDisplayModeSelect(hass, coordinator, entry),
        GuideVaultBackgroundSelect(hass, coordinator, entry),
    ])


class GuideVaultBaseSelect(CoordinatorEntity[GuideVaultDataUpdateCoordinator], SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry, key: str, name: str, icon: str) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }


class GuideVaultDisplayModeSelect(GuideVaultBaseSelect):
    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(hass, coordinator, entry, "display_mode_select", "Display mode", "mdi:book-open-variant")

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        value = _find_first(data, ("displayMode", "reader.displayMode", "pageMode", "reader.pageMode"))
        option = _normalize_display_mode(value) if value is not None else "2 page"
        return option if option in DISPLAY_MODES else "2 page"

    @property
    def options(self) -> list[str]:
        return list(DISPLAY_MODES)

    async def async_select_option(self, option: str) -> None:
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_SET_DISPLAY_MODE, "display_mode": option})


class GuideVaultBackgroundSelect(GuideVaultBaseSelect):
    def __init__(self, hass: HomeAssistant, coordinator: GuideVaultDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(hass, coordinator, entry, "background_select", "Background", "mdi:image")

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        value = _find_first(data, (
            "background", "reader.background", "backgroundName", "reader.backgroundName",
            "selectedBackground", "reader.selectedBackground", "currentBackground", "reader.currentBackground",
        ))
        current = _clean_option(value)
        return current or "default"

    @property
    def options(self) -> list[str]:
        data = self.coordinator.data or {}
        result = _find_background_options(data)
        current = self.current_option

        for fallback in [current, *DEFAULT_BACKGROUNDS]:
            text = _clean_option(fallback)
            if text and text not in result:
                result.insert(0, text)

        # Keep a stable, useful fallback instead of unknown/unavailable.
        return result or list(DEFAULT_BACKGROUNDS)

    async def async_select_option(self, option: str) -> None:
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_SET_BACKGROUND, "background": option})


def _find_background_options(data: Any) -> list[str]:
    names = (
        "backgrounds", "availableBackgrounds", "installedBackgrounds", "backgroundOptions",
        "readerBackgrounds", "reader.backgrounds", "reader.availableBackgrounds",
        "reader.installedBackgrounds", "reader.backgroundOptions", "settings.backgrounds",
        "settings.availableBackgrounds", "readerSettings.backgrounds", "readerSettings.availableBackgrounds",
    )

    for key in names:
        value = _find_first(data, (key,))
        result = _coerce_options(value)
        if result:
            return result

    # Last chance: recursively scan for any list/dict property whose key looks
    # like a background option list. This lets the integration adapt when
    # GuideVault moves the field inside a nested reader/settings object.
    for key, value in _walk_key_values(data):
        normalized = _normalize_key(key)
        if normalized in {
            "backgrounds", "availablebackgrounds", "installedbackgrounds",
            "backgroundoptions", "readerbackgrounds",
        }:
            result = _coerce_options(value)
            if result:
                return result

    return []


def _coerce_options(value: Any) -> list[str]:
    result: list[str] = []

    if isinstance(value, dict):
        # Support either { id: label } maps or objects containing an options/list field.
        for list_key in ("items", "values", "options", "backgrounds", "availableBackgrounds"):
            if list_key in value:
                nested = _coerce_options(value[list_key])
                if nested:
                    return nested
        iterable = value.values()
    elif isinstance(value, list):
        iterable = value
    elif isinstance(value, str) and value.strip():
        iterable = value.split(",")
    else:
        iterable = []

    for item in iterable:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = str(item.get("name") or item.get("label") or item.get("title") or item.get("id") or item.get("value") or "").strip()
        else:
            text = str(item or "").strip()

        text = _clean_option(text)
        if text and text not in result:
            result.append(text)

    return result


def _clean_option(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in UNKNOWN_VALUES else text


def _walk_key_values(data: Any):
    if isinstance(data, dict):
        for key, value in data.items():
            yield str(key), value
            yield from _walk_key_values(value)
    elif isinstance(data, list):
        for value in data:
            yield from _walk_key_values(value)


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


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


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
