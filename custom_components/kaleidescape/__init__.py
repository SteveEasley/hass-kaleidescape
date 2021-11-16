"""The Kaleidescape integration."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from kaleidescape import Kaleidescape
from kaleidescape.error import KaleidescapeError

from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import CONF_HOST, CONF_ID, EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, MANAGER, NAME as KALEIDESCAPE_NAME

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kaleidescape from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    controller = Kaleidescape(entry.data[CONF_HOST], timeout=5)

    try:
        await controller.connect(entry.data[CONF_ID], auto_reconnect=True)
        await controller.load_devices()
    except (KaleidescapeError, ConnectionError) as err:
        await controller.disconnect()
        _LOGGER.error("Unable to connect: %s", err)
        raise ConfigEntryNotReady from err

    async def disconnect(event: str):
        await controller.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, disconnect)
    )

    hass.data[DOMAIN][entry.entry_id] = controller

    await hass.config_entries.async_forward_entry_setup(entry, MEDIA_PLAYER_DOMAIN)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    controller: Kaleidescape = hass.data[DOMAIN][entry.entry_id]
    await controller.disconnect()
    await hass.config_entries.async_forward_entry_unload(entry, MEDIA_PLAYER_DOMAIN)
    del hass.data[DOMAIN][entry.entry_id]
    return True


async def async_migrate_entry(hass, entry: ConfigEntry):
    """Migrate old entries."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        system = await get_system_info(entry.data[CONF_HOST])
        entry.version = 2
        hass.config_entries.async_update_entry(
            entry,
            unique_id=system["id"],
            title=f"Kaleidescape ({system['name']})",
            data={CONF_ID: system["id"], CONF_HOST: system["ip"]},
        )

    _LOGGER.info("Migration to version %s successful", entry.version)

    return True


def validate_host(host: str) -> bool:
    """Returns if hostname contains valid characters."""
    return re.search(r"^[0-9A-Za-z.\-]+$", host) is not None


async def get_system_info(host: str) -> dict[str, str]:
    """Returns system info if host is valid."""
    controller = Kaleidescape(host, timeout=5)
    await controller.connect()
    device = await controller.get_local_device()
    await controller.disconnect()
    return {
        "id": device.system.system_id,
        "ip": device.system.system_ip_address,
        "name": device.system.system_name,
    }
