"""GuideVault integration for Home Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later

from .client import (
    GuideVaultApiError,
    GuideVaultClient,
    GuideVaultClientConfig,
    GuideVaultConnectionError,
)
from .const import (
    ACTION_CLOSE,
    ACTION_FULLSCREEN,
    ACTION_OPEN,
    ACTION_PAGE_FIRST,
    ACTION_PAGE_GOTO,
    ACTION_PAGE_LAST,
    ACTION_PAGE_NEXT,
    ACTION_PAGE_PREVIOUS,
    ACTION_SET_BACKGROUND,
    ACTION_SET_BACKGROUND_BRIGHTNESS,
    ACTION_SET_DISPLAY_MODE,
    ACTION_SET_ZOOM,
    ACTION_TOGGLE_OVERLAY,
    ACTION_ZOOM_IN,
    ACTION_ZOOM_OUT,
    CONF_API_KEY,
    CONF_COMMAND_ENDPOINT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_STATUS_ENDPOINT,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    DATA_CLIENTS,
    DATA_COORDINATORS,
    DATA_SERVICES_REGISTERED,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ITEM_KINDS,
    PLATFORMS,
    SERVICE_CLOSE_READER,
    SERVICE_COMMAND,
    SERVICE_FIRST_PAGE,
    SERVICE_FULLSCREEN,
    SERVICE_GO_TO_PAGE,
    SERVICE_LAST_PAGE,
    SERVICE_NEXT_PAGE,
    SERVICE_OPEN_ITEM,
    SERVICE_PREVIOUS_PAGE,
    SERVICE_SET_BACKGROUND,
    SERVICE_SET_BACKGROUND_BRIGHTNESS,
    SERVICE_SET_DISPLAY_MODE,
    SERVICE_SET_ZOOM,
    SERVICE_TOGGLE_OVERLAY,
    SERVICE_ZOOM_IN,
    SERVICE_ZOOM_OUT,
)
from .coordinator import GuideVaultDataUpdateCoordinator

SERVICE_SCHEMA_BASE = {
    vol.Optional("entry_id"): cv.string,
}

COMMAND_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Optional("action"): cv.string,
        vol.Optional("command_action"): cv.string,
        vol.Optional("itemTitle"): cv.string,
        vol.Optional("item_title"): cv.string,
        vol.Optional("itemKind"): cv.string,
        vol.Optional("item_kind"): cv.string,
        vol.Optional("content_type"): vol.In(ITEM_KINDS),
        vol.Optional("issueNumber"): cv.string,
        vol.Optional("issue_number"): cv.string,
        vol.Optional("issue"): cv.string,
        vol.Optional("volume"): cv.string,
        vol.Optional("page"): vol.Coerce(int),
        vol.Optional("zoom"): vol.Coerce(float),
        vol.Optional("displayMode"): cv.string,
        vol.Optional("display_mode"): cv.string,
        vol.Optional("background"): cv.string,
        vol.Optional("backgroundBrightness"): vol.Coerce(float),
        vol.Optional("background_brightness"): vol.Coerce(float),
        vol.Optional("fullscreen"): cv.boolean,
        vol.Optional("payload"): dict,
    }
)

OPEN_ITEM_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("item_title"): cv.string,
        vol.Optional("item_kind", default="auto"): vol.In(ITEM_KINDS),
        vol.Optional("issue_number"): cv.string,
        vol.Optional("volume"): cv.string,
        vol.Optional("page"): vol.Coerce(int),
    }
)

SIMPLE_SCHEMA = vol.Schema({**SERVICE_SCHEMA_BASE})

GO_TO_PAGE_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("page"): vol.Coerce(int),
    }
)

SET_BACKGROUND_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("background"): cv.string,
    }
)

SET_BACKGROUND_BRIGHTNESS_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("background_brightness"): vol.Coerce(float),
    }
)

SET_ZOOM_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("zoom"): vol.Coerce(float),
    }
)

SET_DISPLAY_MODE_SCHEMA = vol.Schema(
    {
        **SERVICE_SCHEMA_BASE,
        vol.Required("display_mode"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GuideVault from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_CLIENTS, {})
    hass.data[DOMAIN].setdefault(DATA_COORDINATORS, {})

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
            command_endpoint=entry.options.get(
                CONF_COMMAND_ENDPOINT,
                entry.data.get(CONF_COMMAND_ENDPOINT),
            ),
            status_endpoint=entry.options.get(
                CONF_STATUS_ENDPOINT,
                entry.data.get(CONF_STATUS_ENDPOINT),
            ),
        ),
    )

    try:
        await client.async_test_connection()
    except GuideVaultConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = GuideVaultDataUpdateCoordinator(hass, entry, client)

    # Do not block setup if older GuideVault builds do not have status yet.
    await coordinator.async_refresh()

    hass.data[DOMAIN][DATA_CLIENTS][entry.entry_id] = client
    hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id] = coordinator

    if not hass.data[DOMAIN].get(DATA_SERVICES_REGISTERED):
        _register_services(hass)
        hass.data[DOMAIN][DATA_SERVICES_REGISTERED] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GuideVault config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.get(DOMAIN, {}).get(DATA_CLIENTS, {}).pop(entry.entry_id, None)
        hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).pop(entry.entry_id, None)

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
        await async_send_command(hass, entry_id, payload)

    async def handle_open_item(call: ServiceCall) -> None:
        payload = {
            "action": ACTION_OPEN,
            "item_title": call.data["item_title"],
            "item_kind": call.data.get("item_kind"),
            "issue_number": call.data.get("issue_number"),
            "volume": call.data.get("volume"),
            "page": call.data.get("page"),
        }
        await async_send_command(hass, call.data.get("entry_id"), payload)

    async def handle_simple(action: str, call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {"action": action},
        )

    async def handle_go_to_page(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "action": ACTION_PAGE_GOTO,
                "page": call.data["page"],
            },
        )

    async def handle_set_background(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "action": ACTION_SET_BACKGROUND,
                "background": call.data["background"],
            },
        )

    async def handle_set_background_brightness(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "action": ACTION_SET_BACKGROUND_BRIGHTNESS,
                "background_brightness": call.data["background_brightness"],
            },
        )

    async def handle_set_zoom(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "action": ACTION_SET_ZOOM,
                "zoom": call.data["zoom"],
            },
        )

    async def handle_set_display_mode(call: ServiceCall) -> None:
        await async_send_command(
            hass,
            call.data.get("entry_id"),
            {
                "action": ACTION_SET_DISPLAY_MODE,
                "display_mode": call.data["display_mode"],
            },
        )

    hass.services.async_register(DOMAIN, SERVICE_COMMAND, handle_command, schema=COMMAND_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_OPEN_ITEM, handle_open_item, schema=OPEN_ITEM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_NEXT_PAGE, lambda call: handle_simple(ACTION_PAGE_NEXT, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_PREVIOUS_PAGE, lambda call: handle_simple(ACTION_PAGE_PREVIOUS, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_FIRST_PAGE, lambda call: handle_simple(ACTION_PAGE_FIRST, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_LAST_PAGE, lambda call: handle_simple(ACTION_PAGE_LAST, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_GO_TO_PAGE, handle_go_to_page, schema=GO_TO_PAGE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_FULLSCREEN, lambda call: handle_simple(ACTION_FULLSCREEN, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TOGGLE_OVERLAY, lambda call: handle_simple(ACTION_TOGGLE_OVERLAY, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ZOOM_IN, lambda call: handle_simple(ACTION_ZOOM_IN, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ZOOM_OUT, lambda call: handle_simple(ACTION_ZOOM_OUT, call), schema=SIMPLE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_BACKGROUND, handle_set_background, schema=SET_BACKGROUND_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_BACKGROUND_BRIGHTNESS, handle_set_background_brightness, schema=SET_BACKGROUND_BRIGHTNESS_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_ZOOM, handle_set_zoom, schema=SET_ZOOM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DISPLAY_MODE, handle_set_display_mode, schema=SET_DISPLAY_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLOSE_READER, lambda call: handle_simple(ACTION_CLOSE, call), schema=SIMPLE_SCHEMA)


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

    coordinator = _get_coordinator(hass, entry_id)
    if coordinator is not None:
        await coordinator.async_request_refresh()

        @callback
        def _delayed_refresh(_now) -> None:
            hass.async_create_task(coordinator.async_request_refresh())

        # GuideVault may update reader status just after the command response.
        # Multiple delayed refreshes make button presses and number/select
        # controls feel more responsive in the Home Assistant UI.
        async_call_later(hass, 0.25, _delayed_refresh)
        async_call_later(hass, 1.00, _delayed_refresh)


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


def _get_coordinator(hass: HomeAssistant, entry_id: str | None) -> GuideVaultDataUpdateCoordinator | None:
    """Get a GuideVault coordinator."""
    coordinators: dict[str, GuideVaultDataUpdateCoordinator] = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})

    if entry_id:
        return coordinators.get(entry_id)

    if not coordinators:
        return None

    return next(iter(coordinators.values()))
