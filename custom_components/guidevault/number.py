"""Number entities for GuideVault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GuideVaultCoordinator
from .entity import GuideVaultEntity


@dataclass(frozen=True)
class GuideVaultNumberDescription:
    key: str
    name: str
    action: str
    payload_key: str
    value_fn: Callable[[GuideVaultCoordinator], float]
    min_value_fn: Callable[[GuideVaultCoordinator], float]
    max_value_fn: Callable[[GuideVaultCoordinator], float]
    step: float
    icon: str


NUMBERS = [
    GuideVaultNumberDescription(
        "page_number",
        "Page",
        "set_page",
        "page",
        lambda c: float(c.reader.get("page") or 0),
        lambda c: 1,
        lambda c: float(c.reader.get("pageCount") or 1),
        1,
        "mdi:file-document-outline",
    ),
    GuideVaultNumberDescription(
        "zoom",
        "Zoom",
        "set_zoom",
        "zoom",
        lambda c: float(c.reader.get("zoom") or 100),
        lambda c: 70,
        lambda c: 145,
        5,
        "mdi:magnify",
    ),
    GuideVaultNumberDescription(
        "background_brightness",
        "Background Brightness",
        "set_background_brightness",
        "backgroundBrightness",
        lambda c: float(c.reader.get("backgroundBrightness") or 72),
        lambda c: 15,
        lambda c: 100,
        1,
        "mdi:brightness-6",
    ),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GuideVaultCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuideVaultNumber(coordinator, description) for description in NUMBERS])


class GuideVaultNumber(GuideVaultEntity, NumberEntity):
    """GuideVault number entity."""

    def __init__(self, coordinator: GuideVaultCoordinator, description: GuideVaultNumberDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon
        self._attr_native_step = description.step

    @property
    def native_value(self) -> float:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def native_min_value(self) -> float:
        return self.entity_description.min_value_fn(self.coordinator)

    @property
    def native_max_value(self) -> float:
        return max(self.native_min_value, self.entity_description.max_value_fn(self.coordinator))

    async def async_set_native_value(self, value: float) -> None:
        payload: dict[str, Any] = {self.entity_description.payload_key: int(round(value))}
        await self.coordinator.async_command(self.entity_description.action, **payload)
