"""Config flow for GuideVault."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client

from .api import GuideVaultApiClient, GuideVaultApiError
from .const import CONF_BASE_URL, CONF_COMMAND_TOKEN, DEFAULT_BASE_URL, DOMAIN, NAME


class GuideVaultConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle GuideVault config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = str(user_input[CONF_BASE_URL]).strip().rstrip("/")
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
                return self.async_create_entry(
                    title=NAME,
                    data={CONF_BASE_URL: api.base_url, CONF_COMMAND_TOKEN: command_token},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Optional(CONF_COMMAND_TOKEN, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
