"""Buttons for GuideVault reader controls."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GuideVaultCoordinator
from .entity import GuideVaultEntity


@dataclass(frozen=True)
class GuideVaultButtonDescription:
    key: str
    name: str
    action: str
    icon: str


BUTTONS = [
    GuideVaultButtonDescription("first_page", "First Page", "first_page", "mdi:page-first"),
    GuideVaultButtonDescription("previous_page", "Previous Page", "previous_page", "mdi:chevron-left"),
    GuideVaultButtonDescription("next_page", "Next Page", "next_page", "mdi:chevron-right"),
    GuideVaultButtonDescription("last_page", "Last Page", "last_page", "mdi:page-last"),
    GuideVaultButtonDescription("zoom_out", "Zoom Out", "zoom_out", "mdi:magnify-minus-outline"),
    GuideVaultButtonDescription("zoom_in", "Zoom In", "zoom_in", "mdi:magnify-plus-outline"),
    GuideVaultButtonDescription("toggle_overlay", "Toggle Overlay", "toggle_overlay", "mdi:application-cog-outline"),
    GuideVaultButtonDescription("toggle_fullscreen", "Toggle Fullscreen", "toggle_fullscreen", "mdi:fullscreen"),
    GuideVaultButtonDescription("next_background", "Next Background", "next_background", "mdi:image-multiple-outline"),
    GuideVaultButtonDescription("previous_background", "Previous Background", "previous_background", "mdi:image-multiple"),
    GuideVaultButtonDescription("close_reader", "Close Reader", "close_reader", "mdi:close-box-outline"),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuideVaultButton(coordinator, description) for description in BUTTONS])


class GuideVaultButton(GuideVaultEntity, ButtonEntity):
    """GuideVault button entity."""

    def __init__(self, coordinator: GuideVaultCoordinator, description: GuideVaultButtonDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon

    async def async_press(self) -> None:
        await self.coordinator.async_command(self.entity_description.action)
