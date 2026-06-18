"""GuideVault Home Assistant custom integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .api import GuideVaultApiClient
from .const import COMMAND_ACTIONS, CONF_BASE_URL, CONF_COMMAND_TOKEN, DOMAIN, PLATFORMS
from .coordinator import GuideVaultCoordinator

SERVICE_COMMAND = "command"
SERVICE_OPEN_ITEM = "open_item"

# Explicit one-shot services. These mirror the button entities so the controls
# remain available even when Home Assistant hides, disables, or delays entity
# registry creation for a platform after an update.
SERVICE_ACTIONS = {
    **COMMAND_ACTIONS,
    "set_page": "set_page",
    "set_zoom": "set_zoom",
    "set_display_mode": "set_display_mode",
    "set_background": "set_background",
    "set_background_brightness": "set_background_brightness",
}

COMMAND_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("action"): cv.string,
        vol.Optional("item_title"): cv.string,
        vol.Optional("item_kind"): cv.string,
        vol.Optional("issue_number"): cv.string,
        vol.Optional("volume"): cv.string,
        vol.Optional("page"): vol.Coerce(int),
        vol.Optional("zoom"): vol.Coerce(int),
        vol.Optional("display_mode"): cv.string,
        vol.Optional("background"): cv.string,
        vol.Optional("background_brightness"): vol.Coerce(int),
    }
)

OPEN_ITEM_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("item_title"): cv.string,
        vol.Optional("item_kind"): cv.string,
        vol.Optional("issue_number"): cv.string,
        vol.Optional("volume"): cv.string,
    }
)

PAGE_SERVICE_SCHEMA = vol.Schema({vol.Required("page"): vol.Coerce(int)})
ZOOM_SERVICE_SCHEMA = vol.Schema({vol.Required("zoom"): vol.Coerce(int)})
DISPLAY_MODE_SERVICE_SCHEMA = vol.Schema({vol.Required("display_mode"): cv.string})
BACKGROUND_SERVICE_SCHEMA = vol.Schema({vol.Required("background"): cv.string})
BRIGHTNESS_SERVICE_SCHEMA = vol.Schema({vol.Required("background_brightness"): vol.Coerce(int)})
EMPTY_SERVICE_SCHEMA = vol.Schema({})


def _coordinator_for_call(hass: HomeAssistant) -> GuideVaultCoordinator:
    entries = list(hass.data.get(DOMAIN, {}).values())
    if not entries:
        raise RuntimeError("GuideVault is not configured.")
    return entries[0]


def _service_payload(data: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if "item_title" in data:
        payload["itemTitle"] = data.get("item_title", "")
    if "item_kind" in data:
        payload["itemKind"] = data.get("item_kind", "")
    if "issue_number" in data:
        payload["issueNumber"] = data.get("issue_number", "")
    if "volume" in data:
        payload["volume"] = data.get("volume", "")
    if "page" in data:
        payload["page"] = data.get("page")
    if "zoom" in data:
        payload["zoom"] = data.get("zoom")
    if "display_mode" in data:
        payload["displayMode"] = data.get("display_mode", "")
    if "background" in data:
        payload["background"] = data.get("background", "")
    if "background_brightness" in data:
        payload["backgroundBrightness"] = data.get("background_brightness")
    return payload


def _schema_for_service(service_name: str) -> vol.Schema:
    if service_name == "set_page":
        return PAGE_SERVICE_SCHEMA
    if service_name == "set_zoom":
        return ZOOM_SERVICE_SCHEMA
    if service_name == "set_display_mode":
        return DISPLAY_MODE_SERVICE_SCHEMA
    if service_name == "set_background":
        return BACKGROUND_SERVICE_SCHEMA
    if service_name == "set_background_brightness":
        return BRIGHTNESS_SERVICE_SCHEMA
    return EMPTY_SERVICE_SCHEMA


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GuideVault from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    api = GuideVaultApiClient(
        session,
        entry.data[CONF_BASE_URL],
        entry.data.get(CONF_COMMAND_TOKEN, ""),
    )
    coordinator = GuideVaultCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_handle_command(call: ServiceCall) -> None:
        coordinator_for_service = _coordinator_for_call(hass)
        action = str(call.data["action"])
        await coordinator_for_service.async_command(action, **_service_payload(dict(call.data)))

    async def async_handle_open_item(call: ServiceCall) -> None:
        coordinator_for_service = _coordinator_for_call(hass)
        await coordinator_for_service.async_command("open", **_service_payload(dict(call.data)))

    async def async_handle_action(call: ServiceCall) -> None:
        coordinator_for_service = _coordinator_for_call(hass)
        action = SERVICE_ACTIONS[call.service]
        await coordinator_for_service.async_command(action, **_service_payload(dict(call.data)))

    if not hass.services.has_service(DOMAIN, SERVICE_COMMAND):
        hass.services.async_register(DOMAIN, SERVICE_COMMAND, async_handle_command, schema=COMMAND_SERVICE_SCHEMA)
    if not hass.services.has_service(DOMAIN, SERVICE_OPEN_ITEM):
        hass.services.async_register(DOMAIN, SERVICE_OPEN_ITEM, async_handle_open_item, schema=OPEN_ITEM_SERVICE_SCHEMA)
    for service_name in SERVICE_ACTIONS:
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(DOMAIN, service_name, async_handle_action, schema=_schema_for_service(service_name))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GuideVault."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_COMMAND)
            hass.services.async_remove(DOMAIN, SERVICE_OPEN_ITEM)
            for service_name in SERVICE_ACTIONS:
                if hass.services.has_service(DOMAIN, service_name):
                    hass.services.async_remove(DOMAIN, service_name)
            hass.data.pop(DOMAIN, None)
    return unload_ok
