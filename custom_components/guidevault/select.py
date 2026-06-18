"""Select entities for GuideVault."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DISPLAY_MODE_LABELS, DISPLAY_MODE_OPTIONS, DOMAIN
from .coordinator import GuideVaultCoordinator
from .entity import GuideVaultEntity

DEFAULT_BACKGROUND_LABEL = "Default Gradient"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            GuideVaultDisplayModeSelect(coordinator),
            GuideVaultBackgroundSelect(coordinator),
        ]
    )


class GuideVaultDisplayModeSelect(GuideVaultEntity, SelectEntity):
    """Reader display mode selector."""

    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator: GuideVaultCoordinator) -> None:
        super().__init__(coordinator, "display_mode", "Display Mode")

    @property
    def options(self) -> list[str]:
        return list(DISPLAY_MODE_OPTIONS)

    @property
    def current_option(self) -> str | None:
        mode = str(self.coordinator.reader.get("displayMode") or "").strip()
        return DISPLAY_MODE_LABELS.get(mode, "2 page")

    async def async_select_option(self, option: str) -> None:
        mode = DISPLAY_MODE_OPTIONS.get(option, "two_page")
        await self.coordinator.async_command("set_display_mode", displayMode=mode)


class GuideVaultBackgroundSelect(GuideVaultEntity, SelectEntity):
    """Reader background selector built from installed GuideVault backgrounds."""

    _attr_icon = "mdi:image-filter-hdr"

    def __init__(self, coordinator: GuideVaultCoordinator) -> None:
        super().__init__(coordinator, "reader_background", "Reader Background")

    @property
    def options(self) -> list[str]:
        labels = [DEFAULT_BACKGROUND_LABEL]
        for background in self.coordinator.available_backgrounds:
            label = background["displayName"] or background["name"]
            if label not in labels:
                labels.append(label)
        return labels

    @property
    def current_option(self) -> str | None:
        current_name = self.coordinator.current_background_name
        if not current_name:
            return DEFAULT_BACKGROUND_LABEL
        for background in self.coordinator.available_backgrounds:
            if background["name"].lower() == current_name.lower():
                return background["displayName"] or background["name"]
        return self.coordinator.current_background_display_name

    async def async_select_option(self, option: str) -> None:
        background_name = ""
        if option != DEFAULT_BACKGROUND_LABEL:
            for background in self.coordinator.available_backgrounds:
                label = background["displayName"] or background["name"]
                if label == option:
                    background_name = background["name"]
                    break
        await self.coordinator.async_command("set_background", background=background_name)
