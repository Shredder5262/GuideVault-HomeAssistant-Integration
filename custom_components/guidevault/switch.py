"""Switch entities for GuideVault reader controls."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GuideVaultCoordinator
from .entity import GuideVaultEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up GuideVault switches."""
    coordinator: GuideVaultCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuideVaultFullscreenSwitch(coordinator)])


class GuideVaultFullscreenSwitch(GuideVaultEntity, SwitchEntity):
    """Represent the GuideVault fullscreen state as a controllable switch."""

    def __init__(self, coordinator: GuideVaultCoordinator) -> None:
        super().__init__(coordinator, "fullscreen_switch", "Fullscreen")
        self._attr_icon = "mdi:fullscreen"

    @property
    def is_on(self) -> bool | None:
        fullscreen = self.coordinator.reader.get("fullscreen")
        if fullscreen is None:
            return None
        return bool(fullscreen)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self.is_on is not True:
            await self.coordinator.async_command("toggle_fullscreen")

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.is_on is not False:
            await self.coordinator.async_command("toggle_fullscreen")

    async def async_toggle(self, **kwargs: Any) -> None:
        await self.coordinator.async_command("toggle_fullscreen")
