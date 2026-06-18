"""Binary sensors for GuideVault."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GuideVaultCoordinator
from .entity import GuideVaultEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuideVaultFullscreenBinarySensor(coordinator)])


class GuideVaultFullscreenBinarySensor(GuideVaultEntity, BinarySensorEntity):
    """Whether the GuideVault reader is in fullscreen mode."""

    _attr_icon = "mdi:fullscreen"

    def __init__(self, coordinator: GuideVaultCoordinator) -> None:
        super().__init__(coordinator, "fullscreen", "Fullscreen")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.reader.get("fullscreen"))
