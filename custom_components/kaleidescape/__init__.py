"""The Kaleidescape integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple

from kaleidescape import Device as KaleidescapeDevice, KaleidescapeError

from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, Event

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.REMOTE]


class DeviceInfo(NamedTuple):
    """Metadata for a Kaleidescape device"""

    host: str
    serial: str
    name: str
    model: str
    server_only: bool


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kaleidescape from a config entry."""
    device = KaleidescapeDevice(
        entry.data[CONF_HOST], timeout=5, reconnect=True, reconnect_delay=5
    )

    try:
        await device.connect()
    except (KaleidescapeError, ConnectionError) as err:
        await device.disconnect()
        _LOGGER.error("Unable to connect: %s", err)
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    async def disconnect(event: Event):
        await device.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, disconnect)
    )

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class UnsupportedError(HomeAssistantError):
    """Error for unsupported device types."""


async def validate_host(host: str) -> DeviceInfo:
    """Validate device host."""
    device = KaleidescapeDevice(host)
    try:
        await device.connect()
        return DeviceInfo(
            host=device.host,
            serial=device.system.serial_number,
            name=device.system.friendly_name,
            model=device.system.type,
            server_only=device.is_server_only,
        )
    finally:
        await device.disconnect()
