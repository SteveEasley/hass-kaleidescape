"""The Kaleidescape integration."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from kaleidescape import Kaleidescape, const as kaleidescape_const
from kaleidescape.error import KaleidescapeError

from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import async_get as async_get_registry
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    DOMAIN,
    KALEIDESCAPE_ADD_MEDIA_PLAYER,
    KALEIDESCAPE_UPDATE_MEDIA_PLAYERS,
    MANAGER,
    NAME as KALEIDESCAPE_NAME,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceRegistry
    from homeassistant.helpers.entity_registry import EntityRegistry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kaleidescape from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    manager = ControllerManager(hass, entry)

    hass.data[DOMAIN] = manager

    try:
        await manager.connect()
    except (KaleidescapeError, ConnectionError) as err:
        await manager.disconnect()
        hass.data[DOMAIN] = None
        _LOGGER.error("Unable to connect: %s", err)
        raise ConfigEntryNotReady from err

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    manager = hass.data[DOMAIN]  # type: ControllerManager
    await manager.disconnect()
    await hass.config_entries.async_forward_entry_unload(entry, MEDIA_PLAYER_DOMAIN)
    hass.data[DOMAIN] = None
    return True


class ControllerManager:
    """Manager for Kaleidescape controller."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initializes the ControllerManager."""
        self._hass = hass
        self._entry = entry
        self._discovered: set[str] = set()
        self._controller = Kaleidescape(entry.data[CONF_HOST])

    async def connect(self) -> None:
        """Connect to Kaleidescape controller."""
        await self._controller.connect(auto_reconnect=True)
        await self._controller.load_devices()

        self._entry.async_on_unload(
            self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.disconnect)
        )

        await self._hass.config_entries.async_forward_entry_setup(
            self._entry, MEDIA_PLAYER_DOMAIN
        )

        await self._discover(kaleidescape_const.EVENT_CONTROLLER_CONNECTED)

        self._entry.async_on_unload(
            self._controller.dispatcher.connect(
                kaleidescape_const.SIGNAL_CONTROLLER_EVENT, self._discover
            ).disconnect
        )

    async def disconnect(self, *args) -> None:
        """Disconnect from Kaleidescape controller."""
        await self._controller.disconnect()

    async def _discover(self, event: str) -> None:
        """Discovers changes to Kaleidescape devices in system.

        Changes include added and removed devices and device name changes.
        """
        if event in [
            kaleidescape_const.EVENT_CONTROLLER_CONNECTED,
            kaleidescape_const.EVENT_CONTROLLER_UPDATED,
        ]:
            device_registry: DeviceRegistry = async_get_registry(self._hass)

            kaleidescape_devices = await self._controller.get_devices()

            for device in kaleidescape_devices:
                # Devices like the Terra Server have no movie zone, so no media_player.
                if not device.capabilities.movies:
                    continue

                idents = {(DOMAIN, device.serial_number)}
                entry = device_registry.async_get_device(idents)

                device_name = f"{device.system.name} {KALEIDESCAPE_NAME}"

                if entry and entry.name != device_name:
                    device_registry.async_update_device(entry.id, name=device_name)
                    _LOGGER.debug(
                        "Updated device %s name from %s to %s",
                        entry.id,
                        entry.name,
                        device_name,
                    )

                if device.serial_number not in self._discovered:
                    async_dispatcher_send(
                        self._hass, KALEIDESCAPE_ADD_MEDIA_PLAYER, device
                    )
                    self._discovered.add(device.serial_number)
                    _LOGGER.debug(
                        "Added new device with serial number %s", device.serial_number
                    )

        # Send update signal to all media_players
        async_dispatcher_send(self._hass, KALEIDESCAPE_UPDATE_MEDIA_PLAYERS)


def validate_host(host: str) -> bool:
    """Returns if hostname contains valid characters."""
    return re.search(r"^[0-9A-Za-z.\-]+$", host) is not None


async def validate_connect(host: str) -> bool:
    """Returns if hostname can be connected to."""
    try:
        kaleidescape = Kaleidescape(host, timeout=5)
        await kaleidescape.connect()
        await kaleidescape.disconnect()
    except ConnectionError:
        return False
    return True
