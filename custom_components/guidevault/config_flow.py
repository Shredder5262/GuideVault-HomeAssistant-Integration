"""Config flow for GuideVault."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import GuideVaultClient, GuideVaultClientConfig, GuideVaultConnectionError
from .const import (
    COMMAND_ENDPOINT,
    CONF_API_KEY,
    CONF_COMMAND_ENDPOINT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_STATUS_ENDPOINT,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    DEFAULT_HOST,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    STATUS_ENDPOINT,
)


class GuideVaultConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GuideVault."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized = _normalize_input(user_input)
            await self.async_set_unique_id(_unique_id(normalized))
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass, verify_ssl=normalized.get(CONF_VERIFY_SSL, True))
            client = GuideVaultClient(
                session,
                GuideVaultClientConfig(
                    host=normalized[CONF_HOST],
                    port=normalized.get(CONF_PORT),
                    ssl=normalized.get(CONF_SSL, False),
                    verify_ssl=normalized.get(CONF_VERIFY_SSL, True),
                    api_key=normalized.get(CONF_API_KEY),
                    timeout=normalized.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    command_endpoint=normalized.get(CONF_COMMAND_ENDPOINT, COMMAND_ENDPOINT),
                    status_endpoint=normalized.get(CONF_STATUS_ENDPOINT, STATUS_ENDPOINT),
                ),
            )

            try:
                await client.async_test_connection()
            except GuideVaultConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=normalized.get(CONF_NAME) or DEFAULT_NAME, data=normalized)

        return self.async_show_form(step_id="user", data_schema=_user_schema(user_input), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GuideVaultOptionsFlow(config_entry)


class GuideVaultOptionsFlow(config_entries.OptionsFlow):
    """Handle GuideVault options."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self._config_entry.data
        options = self._config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_TIMEOUT, default=options.get(CONF_TIMEOUT, data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
                    vol.Optional(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
                    vol.Optional(CONF_COMMAND_ENDPOINT, default=options.get(CONF_COMMAND_ENDPOINT, data.get(CONF_COMMAND_ENDPOINT, COMMAND_ENDPOINT))): str,
                    vol.Optional(CONF_STATUS_ENDPOINT, default=options.get(CONF_STATUS_ENDPOINT, data.get(CONF_STATUS_ENDPOINT, STATUS_ENDPOINT))): str,
                }
            ),
        )


def _user_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, DEFAULT_HOST)): str,
            vol.Optional(CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)): vol.Any(None, vol.Coerce(int)),
            vol.Optional(CONF_SSL, default=user_input.get(CONF_SSL, False)): bool,
            vol.Optional(CONF_VERIFY_SSL, default=user_input.get(CONF_VERIFY_SSL, True)): bool,
            vol.Optional(CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")): str,
            vol.Optional(CONF_TIMEOUT, default=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
            vol.Optional(CONF_SCAN_INTERVAL, default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
            vol.Optional(CONF_COMMAND_ENDPOINT, default=user_input.get(CONF_COMMAND_ENDPOINT, COMMAND_ENDPOINT)): str,
            vol.Optional(CONF_STATUS_ENDPOINT, default=user_input.get(CONF_STATUS_ENDPOINT, STATUS_ENDPOINT)): str,
        }
    )


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(user_input)
    host = str(normalized[CONF_HOST]).strip().rstrip("/")

    if host.startswith("http://") or host.startswith("https://"):
        parsed = urlparse(host)
        normalized[CONF_SSL] = parsed.scheme == "https"
        entered_port = normalized.get(CONF_PORT)
        normalized[CONF_HOST] = parsed.hostname or host
        normalized[CONF_PORT] = parsed.port or entered_port

        if parsed.path and parsed.path != "/":
            normalized[CONF_HOST] = host
    else:
        normalized[CONF_HOST] = host

    api_key = str(normalized.get(CONF_API_KEY, "")).strip()
    if api_key:
        normalized[CONF_API_KEY] = api_key
    else:
        normalized.pop(CONF_API_KEY, None)

    return normalized


def _unique_id(data: dict[str, Any]) -> str:
    scheme = "https" if data.get(CONF_SSL) else "http"
    port = data.get(CONF_PORT)
    return f"{scheme}://{data[CONF_HOST]}:{port}" if port else f"{scheme}://{data[CONF_HOST]}"
