"""Config flow for Kaleidescape."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_ID
from homeassistant.exceptions import HomeAssistantError

from . import get_system_info, validate_host
from .const import DEFAULT_HOST, DOMAIN

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


@config_entries.HANDLERS.register(DOMAIN)
class KaleidescapeConfigFlow(config_entries.ConfigFlow):
    """Config flow for Kaleidescape integration"""

    VERSION = 2

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the user step."""
        errors = {}
        host = DEFAULT_HOST

        if user_input is not None:
            try:
                host = user_input[CONF_HOST].strip()

                if validate_host(host) is False:
                    raise HostnameError

                system = await get_system_info(host)

                await self.async_set_unique_id(system.system_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Kaleidescape ({system.friendly_name})",
                    data={CONF_ID: system.system_id, CONF_HOST: system.ip_address},
                )
            except HostnameError:
                errors["base"] = "invalid_host"
            except (ConnectionError, ConnectionRefusedError):
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST, default=host): str}),
            errors=errors,
        )


class HostnameError(HomeAssistantError):
    """Error to indicate invalid host value."""
