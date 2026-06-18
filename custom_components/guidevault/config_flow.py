"""Config flow for GuideVault."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .api import GuideVaultApiClient, GuideVaultApiError
from .const import (
    CONF_BASE_URL,
    CONF_COMMAND_TOKEN,
    CONF_ENABLE_BACKGROUND_CONTROLS,
    CONF_ENABLE_CONTROLS,
    CONF_ENTITY_PREFIX,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_ENABLE_BACKGROUND_CONTROLS,
    DEFAULT_ENABLE_CONTROLS,
    DEFAULT_ENTITY_PREFIX,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    NAME,
)


def _normalize_base_url(value: str) -> str:
    text = (value or "").strip().rstrip("/")
    if text and not text.startswith(("http://", "https://")):
        text = f"http://{text}"
    return text


def _form_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    values = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_BASE_URL, default=values.get(CONF_BASE_URL, DEFAULT_BASE_URL)): str,
            vol.Optional(CONF_COMMAND_TOKEN, default=values.get(CONF_COMMAND_TOKEN, "")): str,
            vol.Required(CONF_ENTITY_PREFIX, default=values.get(CONF_ENTITY_PREFIX, DEFAULT_ENTITY_PREFIX)): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS),
            ): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
            vol.Required(
                CONF_ENABLE_CONTROLS,
                default=values.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS),
            ): cv.boolean,
            vol.Required(
                CONF_ENABLE_BACKGROUND_CONTROLS,
                default=values.get(CONF_ENABLE_BACKGROUND_CONTROLS, DEFAULT_ENABLE_BACKGROUND_CONTROLS),
            ): cv.boolean,
        }
    )


def _entry_defaults(entry: config_entries.ConfigEntry) -> dict[str, Any]:
    defaults = dict(entry.data)
    defaults.update(entry.options)
    return defaults


class GuideVaultConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle GuideVault config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return GuideVaultOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = _normalize_base_url(str(user_input[CONF_BASE_URL]))
            command_token = str(user_input.get(CONF_COMMAND_TOKEN) or "").strip()
            session = aiohttp_client.async_get_clientsession(self.hass)
            api = GuideVaultApiClient(session, base_url, command_token)
            try:
                await api.async_get_status()
            except GuideVaultApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(base_url.lower())
                self._abort_if_unique_id_configured()
                data = {
                    CONF_BASE_URL: api.base_url,
                    CONF_COMMAND_TOKEN: command_token,
                    CONF_ENTITY_PREFIX: str(user_input.get(CONF_ENTITY_PREFIX) or DEFAULT_ENTITY_PREFIX).strip()
                    or DEFAULT_ENTITY_PREFIX,
                    CONF_SCAN_INTERVAL: int(user_input.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL_SECONDS),
                    CONF_ENABLE_CONTROLS: bool(user_input.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS)),
                    CONF_ENABLE_BACKGROUND_CONTROLS: bool(
                        user_input.get(CONF_ENABLE_BACKGROUND_CONTROLS, DEFAULT_ENABLE_BACKGROUND_CONTROLS)
                    ),
                }
                return self.async_create_entry(title=NAME, data=data)

        return self.async_show_form(step_id="user", data_schema=_form_schema(), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Allow Home Assistant's reconfigure flow to update the connection details."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        defaults = _entry_defaults(entry) if entry else {}
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = _normalize_base_url(str(user_input[CONF_BASE_URL]))
            command_token = str(user_input.get(CONF_COMMAND_TOKEN) or "").strip()
            session = aiohttp_client.async_get_clientsession(self.hass)
            api = GuideVaultApiClient(session, base_url, command_token)
            try:
                await api.async_get_status()
            except GuideVaultApiError:
                errors["base"] = "cannot_connect"
            else:
                if entry is not None:
                    return self.async_update_reload_and_abort(
                        entry,
                        data={
                            CONF_BASE_URL: api.base_url,
                            CONF_COMMAND_TOKEN: command_token,
                            CONF_ENTITY_PREFIX: str(user_input.get(CONF_ENTITY_PREFIX) or DEFAULT_ENTITY_PREFIX).strip()
                            or DEFAULT_ENTITY_PREFIX,
                            CONF_SCAN_INTERVAL: int(user_input.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL_SECONDS),
                            CONF_ENABLE_CONTROLS: bool(user_input.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS)),
                            CONF_ENABLE_BACKGROUND_CONTROLS: bool(
                                user_input.get(CONF_ENABLE_BACKGROUND_CONTROLS, DEFAULT_ENABLE_BACKGROUND_CONTROLS)
                            ),
                        },
                    )
        return self.async_show_form(step_id="reconfigure", data_schema=_form_schema(defaults), errors=errors)


class GuideVaultOptionsFlow(config_entries.OptionsFlow):
    """Handle GuideVault options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        defaults = _entry_defaults(self._config_entry)
        if user_input is not None:
            base_url = _normalize_base_url(str(user_input[CONF_BASE_URL]))
            command_token = str(user_input.get(CONF_COMMAND_TOKEN) or "").strip()
            session = aiohttp_client.async_get_clientsession(self.hass)
            api = GuideVaultApiClient(session, base_url, command_token)
            try:
                await api.async_get_status()
            except GuideVaultApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_BASE_URL: api.base_url,
                        CONF_COMMAND_TOKEN: command_token,
                        CONF_ENTITY_PREFIX: str(user_input.get(CONF_ENTITY_PREFIX) or DEFAULT_ENTITY_PREFIX).strip()
                        or DEFAULT_ENTITY_PREFIX,
                        CONF_SCAN_INTERVAL: int(user_input.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL_SECONDS),
                        CONF_ENABLE_CONTROLS: bool(user_input.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS)),
                        CONF_ENABLE_BACKGROUND_CONTROLS: bool(
                            user_input.get(CONF_ENABLE_BACKGROUND_CONTROLS, DEFAULT_ENABLE_BACKGROUND_CONTROLS)
                        ),
                    },
                )

        return self.async_show_form(step_id="init", data_schema=_form_schema(defaults), errors=errors)
