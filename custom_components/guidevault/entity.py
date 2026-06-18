"""Base entities for GuideVault."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GuideVaultCoordinator


class GuideVaultEntity(CoordinatorEntity[GuideVaultCoordinator]):
    """Base class for GuideVault entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GuideVaultCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"guidevault_{key}"
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.api.base_url)},
            "name": "GuideVault",
            "manufacturer": "GuideVault",
            "configuration_url": coordinator.api.base_url,
        }
