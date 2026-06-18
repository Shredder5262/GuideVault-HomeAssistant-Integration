"""Button entities for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import async_send_command
from .const import (
    ACTION_CLOSE,
    ACTION_PAGE_FIRST,
    ACTION_PAGE_LAST,
    ACTION_PAGE_NEXT,
    ACTION_PAGE_PREVIOUS,
    ACTION_FULLSCREEN,
    ACTION_TOGGLE_OVERLAY,
    ACTION_ZOOM_IN,
    ACTION_ZOOM_OUT,
    DOMAIN,
)


@dataclass(frozen=True, slots=True)
class GuideVaultButtonDescription:
    """Description of a GuideVault command button."""

    key: str
    name: str
    action: str
    icon: str


BUTTONS: tuple[GuideVaultButtonDescription, ...] = (
    GuideVaultButtonDescription("first_page", "First page", ACTION_PAGE_FIRST, "mdi:page-first"),
    GuideVaultButtonDescription("previous_page", "Previous page", ACTION_PAGE_PREVIOUS, "mdi:chevron-left"),
    GuideVaultButtonDescription("next_page", "Next page", ACTION_PAGE_NEXT, "mdi:chevron-right"),
    GuideVaultButtonDescription("last_page", "Last page", ACTION_PAGE_LAST, "mdi:page-last"),
    GuideVaultButtonDescription("fullscreen", "Fullscreen", ACTION_FULLSCREEN, "mdi:fullscreen"),
    GuideVaultButtonDescription("toggle_overlay", "Toggle overlay", ACTION_TOGGLE_OVERLAY, "mdi:layers-outline"),
    GuideVaultButtonDescription("zoom_in", "Zoom in", ACTION_ZOOM_IN, "mdi:magnify-plus-outline"),
    GuideVaultButtonDescription("zoom_out", "Zoom out", ACTION_ZOOM_OUT, "mdi:magnify-minus-outline"),
    GuideVaultButtonDescription("close_reader", "Close reader", ACTION_CLOSE, "mdi:close-box-outline"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GuideVault button entities."""
    async_add_entities(
        GuideVaultButton(hass, entry, description)
        for description in BUTTONS
    )


class GuideVaultButton(ButtonEntity):
    """GuideVault command button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: GuideVaultButtonDescription,
    ) -> None:
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

    async def async_press(self) -> None:
        """Send the button command to GuideVault."""
        await async_send_command(
            self._hass,
            self._entry.entry_id,
            {"action": self._description.action},
        )
