"""GuideVault integration for Home Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import (
    GuideVaultApiError,
    GuideVaultClient,
    GuideVaultClientConfig,
    GuideVaultConnectionError,
)
from .const import (
    ACTION_CLOSE,
    ACTION_OPEN,
    ACTION_PAGE_FIRST,
    ACTION_PAGE_GOTO,
    ACTION_PAGE_LAST,
    ACTION_PAGE_NEXT,
    ACTION_PAGE_PREVIOUS,
    ACTION_SET_BACKGROUND,
    ACTION_TOGGLE_FULLSCREEN,
    CONF_API_KEY,
    CONF_SSL,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    CONTENT_TYPES,
    DATA_CLIENTS,
    DATA_SERVICES_REGISTERED,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PLATFORMS,
    SERVICE_CLOSE_READER,
    SERVICE_COMMAND,
    SERVICE_FIRST_PAGE,
    SERVICE_GO_TO_PAGE,
    SERVICE_LAST_PAGE,
    SERVICE_NEXT_PAGE,
    SERVICE_OPEN_ITEM,
    SERVICE_PREVIOUS_PAGE,
    SERVICE_SET_BACKGROUND,
    SERVICE_TOGGLE_FULLSCREEN,
)

SERVICE_SCHEMA_BASE = {
    vol.Optional("entry_id"): cv.string,
}

COMMAND_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("command_action"): cv.string,
        vol.Optional("item_title"): cv.string,
        vol.Optional("content_type"): vol.In(CONTENT_TYPES),
        vol.Optional("issue"): cv.string,
        vol.Optional("volume"): cv.string,
        vol.Optional("page"): cv.positive_int,
        vol.Optional("background"): cv.string,
        vol.Optional("fullscreen"): cv.boolean,
        vol.Optional("payload"): dict,
    }
)

OPEN_ITEM_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("item_title"): cv.string,
        vol.Optional("content_type", default="auto"): vol.In(CONTENT_TYPES),
        vol.Optional("issue"): cv.string,
        vol.Optional("volume"): cv.string,
    }
)

SIMPLE_SCHEMA = vol.Schema({**SERVICE_SCHEMA_BASE})

GO_TO_PAGE_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("page"): cv.positive_int,
    }
)

SET_BACKGROUND_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("background"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GuideVault from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_CLIENTS, {})

    session = async_get_clientsession(
        hass,
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )

    client = GuideVaultClient(
        session,
        GuideVaultClientConfig(
            host=entry.data[CONF_HOST],
            port=entry.data.get(CONF_PORT),
            ssl=entry.data.get(CONF_SSL, False),
            verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
            api_key=entry.data.get(CONF_API_KEY),
            timeout=entry.options.get(
                CONF_TIMEOUT,
                entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            ),
        ),
    )

    try:
        await client.async_test_connection()
    except GuideVaultConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    hass.data[DOMAIN][DATA_CLIENTS][entry.entry_id] = client

    if not hass.data[DOMAIN].get(DATA_SERVICES_REGISTERED):
        _register_services(hass)
        hass.data[DOMAIN][DATA_SERVICES_REGISTERED] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GuideVault config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        clients = hass.data.get(DOMAIN, {}).get(DATA_CLIENTS, {})
        clients.pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload GuideVault config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _register_services(hass: HomeAssistant) -> None:
    """Register GuideVault services."""

    async def handle_command(call: ServiceCall) -> None:
        payload: dict[str, Any] = dict(call.data)
        entry_id = payload.pop("entry_id", None)

        extra_payload = payload.pop("payload", None)
        if isinstance(extra_payload, dict):
            payload.update(extra_payload)

        await async_send_command(hass, entry_id, payload)

    async def handle_open_item(call: ServiceCall) -> None:
        payload = {
            "command_action": ACTION_OPEN,
            "item_title": call.data["item_title"],
            "content_type": None
            if call.data.get("content_type") == "auto"
            else call.data.get("content_type"),
            "issue": call.data.get("issue"),
            "volume": call.data.get("volume"),
        }
        await async_send_command(hass, call.data.get("entry_id"), payload)

    async def handle_simple(action: str, call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {"command_action": action},
        )

    async def handle_go_to_page(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "command_action": ACTION_PAGE_GOTO,
                "page": call.data["page"],
            },
        )

    async def handle_set_background(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "command_action": ACTION_SET_BACKGROUND,
                "background": call.data["background"],
            },
        )

    hass.services.async_register(DOMAIN, SERVICE_COMMAND, handle_command, schema=COMMAND_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_OPEN_ITEM, handle_open_item, schema=OPEN_ITEM_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_NEXT_PAGE,
        lambda call: handle_simple(ACTION_PAGE_NEXT, call),
        schema=SIMPLE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PREVIOUS_PAGE,
        lambda call: handle_simple(ACTION_PAGE_PREVIOUS, call),
        schema=SIMPLE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_FIRST_PAGE,
        lambda call: handle_simple(ACTION_PAGE_FIRST, call),
        schema=SIMPLE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LAST_PAGE,
        lambda call: handle_simple(ACTION_PAGE_LAST, call),
        schema=SIMPLE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GO_TO_PAGE,
        handle_go_to_page,
        schema=GO_TO_PAGE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_FULLSCREEN,
        lambda call: handle_simple(ACTION_TOGGLE_FULLSCREEN, call),
        schema=SIMPLE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BACKGROUND,
        handle_set_background,
        schema=SET_BACKGROUND_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLOSE_READER,
        lambda call: handle_simple(ACTION_CLOSE, call),
        schema=SIMPLE_SCHEMA,
    )


async def async_send_command(
    hass: HomeAssistant,
    entry_id: str | None,
    payload: dict[str, Any],
) -> None:
    """Send a command through a configured GuideVault client."""
    client = _get_client(hass, entry_id)

    try:
        await client.async_command(payload)
    except GuideVaultConnectionError as err:
        raise HomeAssistantError(f"GuideVault is unavailable: {err}") from err
    except GuideVaultApiError as err:
        raise HomeAssistantError(str(err)) from err


def _get_client(hass: HomeAssistant, entry_id: str | None) -> GuideVaultClient:
    """Get a GuideVault client."""
    clients: dict[str, GuideVaultClient] = hass.data.get(DOMAIN, {}).get(DATA_CLIENTS, {})

    if entry_id:
        client = clients.get(entry_id)
        if client is None:
            raise HomeAssistantError(f"GuideVault config entry was not found: {entry_id}")
        return client

    if not clients:
        raise HomeAssistantError("No GuideVault instance is configured.")

    return next(iter(clients.values()))
