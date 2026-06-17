"""Select entities for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass
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
    DEFAULT_DISPLAY_MODES,
    DOMAIN,
)
from .coordinator import GuideVaultDataUpdateCoordinator


@dataclass(frozen=True, slots=True)
class GuideVaultSelectDescription:
    """Description for a GuideVault select."""

    key: str
    name: str
    icon: str
    action: str
    value_keys: tuple[str, ...]
    options_keys: tuple[str, ...]
    fallback_options: list[str]
    payload_key: str
    fixed_options: bool = False


SELECTS: tuple[GuideVaultSelectDescription, ...] = (
    GuideVaultSelectDescription(
        key="background_select",
        name="Background",
        icon="mdi:image",
        action=ACTION_SET_BACKGROUND,
        value_keys=("background", "reader.background", "backgroundName", "reader.backgroundName", "selectedBackground", "reader.selectedBackground"),
        options_keys=("backgrounds", "availableBackgrounds", "installedBackgrounds", "backgroundOptions", "reader.availableBackgrounds", "reader.installedBackgrounds", "settings.backgrounds", "settings.availableBackgrounds"),
        fallback_options=DEFAULT_BACKGROUNDS,
        payload_key="background",
    ),
    GuideVaultSelectDescription(
        key="display_mode_select",
        name="Display mode",
        icon="mdi:book-open-variant",
        action=ACTION_SET_DISPLAY_MODE,
        value_keys=("displayMode", "reader.displayMode", "pageMode", "reader.pageMode"),
        options_keys=("displayModes", "availableDisplayModes", "reader.availableDisplayModes", "settings.displayModes"),
        fallback_options=DEFAULT_DISPLAY_MODES,
        payload_key="display_mode",
        fixed_options=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GuideVault selects."""
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]

    async_add_entities(
        GuideVaultSelect(hass, coordinator, entry, description)
        for description in SELECTS
    )


class GuideVaultSelect(CoordinatorEntity[GuideVaultDataUpdateCoordinator], SelectEntity):
    """GuideVault select entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: GuideVaultDataUpdateCoordinator,
        entry: ConfigEntry,
        description: GuideVaultSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }

    @property
    def current_option(self) -> str | None:
        """Return current option."""
        value = _find_first(self.coordinator.data or {}, self._description.value_keys)

        if value is None:
            return None

        value_text = str(value)

        if self._description.key == "display_mode_select":
            return _normalize_display_mode(value_text)

        return value_text

    @property
    def options(self) -> list[str]:
        """Return available options."""
        if self._description.fixed_options:
            return list(self._description.fallback_options)

        data = self.coordinator.data or {}
        raw = _find_first(data, self._description.options_keys)

        options = _coerce_options(raw)

        # If GuideVault exposes installed backgrounds under a differently named
        # key, try to discover any list/dict whose path contains "background".
        if not options and self._description.key == "background_select":
            options = _discover_background_options(data)

        if options:
            current = self.current_option
            if current and current not in options:
                options.insert(0, current)
            return options

        return list(self._description.fallback_options)

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        payload_value = option

        await async_send_command(
            self._hass,
            self._entry.entry_id,
            {
                "action": self._description.action,
                self._description.payload_key: payload_value,
            },
        )


def _normalize_display_mode(value: str) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")

    if text in ("single", "one", "one page", "1", "1page", "1 page"):
        return "1 page"

    if text in ("double", "two", "two page", "two pages", "2", "2page", "2 page", "2 pages"):
        return "2 page"

    if text in ("adaptive", "two page adaptive", "two pages adaptive", "2 adaptive", "2pageadaptive", "2 page adaptive", "2 pages adaptive"):
        return "2 page adaptive"

    for option in DEFAULT_DISPLAY_MODES:
        if text == option.lower():
            return option

    return value


def _find_first(data: Any, paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = _get_path_case_insensitive(data, path)
        if value not in (None, ""):
            return value
    return None


def _get_path_case_insensitive(data: Any, path: str) -> Any:
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
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _discover_background_options(data: Any) -> list[str]:
    results: list[str] = []

    def walk(value: Any, path: str = "") -> None:
        nonlocal results

        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if "background" in _normalize_key(child_path):
                    results.extend(_coerce_options(child))
                walk(child, child_path)
        elif isinstance(value, list) and "background" in _normalize_key(path):
            results.extend(_coerce_options(value))

    walk(data)

    return _dedupe(item for item in results if item and len(item) < 80)


def _coerce_options(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("value") or item.get("id") or item.get("name") or item.get("label") or item.get("title")
                if name not in (None, ""):
                    result.append(str(name))
            elif item not in (None, ""):
                result.append(str(item))
        return _dedupe(result)

    if isinstance(value, dict):
        dict_values = []
        for key, item in value.items():
            if isinstance(item, dict):
                name = item.get("value") or item.get("id") or item.get("name") or item.get("label") or item.get("title") or key
                dict_values.append(str(name))
            else:
                dict_values.append(str(key))
        return _dedupe(dict_values)

    if isinstance(value, str):
        return _dedupe(part.strip() for part in value.split(",") if part.strip())

    return []


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
