"""Config flow for Kaleidescape."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import HomeAssistantError

from . import validate_connect, validate_host
from .const import DEFAULT_HOST, DOMAIN

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


@config_entries.HANDLERS.register(DOMAIN)
class KaleidescapeConfigFlow(config_entries.ConfigFlow):
    """Config flow for Kaleidescape integration"""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the user step."""
        errors = {}
        host = DEFAULT_HOST

        if user_input is not None:
            try:
                host = user_input[CONF_HOST].strip()

                if validate_host(host) is False:
                    raise HostError

                if await validate_connect(host) is False:
                    raise ConnectError

                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Kaleidescape", data={CONF_HOST: host}
                )
            except HostError:
                errors["base"] = "invalid_host"
            except ConnectError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST, default=host): str}),
            errors=errors,
        )


class HostError(HomeAssistantError):
    """Error to indicate invalid host value."""


class ConnectError(HomeAssistantError):
    """Error to indicate unable to connect to host."""
