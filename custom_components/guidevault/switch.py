"""Switch entities for GuideVault."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import async_send_command
from .const import (
    ACTION_FULLSCREEN_OFF,
    ACTION_FULLSCREEN_ON,
    DATA_COORDINATORS,
    DOMAIN,
)
from .coordinator import GuideVaultDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GuideVault switch entities."""
    coordinator: GuideVaultDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities([GuideVaultFullscreenSwitch(hass, coordinator, entry)])


class GuideVaultFullscreenSwitch(CoordinatorEntity[GuideVaultDataUpdateCoordinator], SwitchEntity):
    """GuideVault fullscreen switch."""

    _attr_has_entity_name = True
    _attr_name = "Fullscreen"
    _attr_icon = "mdi:fullscreen"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: GuideVaultDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fullscreen_switch"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GuideVault",
            "model": "GuideVault Server",
        }

    @property
    def is_on(self) -> bool | None:
        """Return whether the reader is fullscreen."""
        value = _find_first(
            self.coordinator.data or {},
            (
                "fullscreen",
                "isFullscreen",
                "reader.fullscreen",
                "reader.isFullscreen",
                "reader.readerFullscreen",
                "fullScreen",
            ),
        )
        return _bool_or_none(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enter fullscreen."""
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_FULLSCREEN_ON})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Exit fullscreen."""
        await async_send_command(self._hass, self._entry.entry_id, {"action": ACTION_FULLSCREEN_OFF})


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
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "on", "fullscreen"):
        return True
    if text in ("false", "0", "no", "off", "windowed"):
        return False
    return None
