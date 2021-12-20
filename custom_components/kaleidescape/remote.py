"""Support for the DIRECTV remote."""
from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import TYPE_CHECKING, Any

from kaleidescape import const as kaleidescape_const

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN as KALEIDESCAPE_DOMAIN, NAME as KALEIDESCAPE_NAME

if TYPE_CHECKING:
    from kaleidescape import Device as KaleidescapeDevice, Kaleidescape

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the platform from a config entry."""
    controller: Kaleidescape = hass.data[KALEIDESCAPE_DOMAIN][entry.entry_id]
    entities = [
        KaleidescapeRemote(p)
        for p in await controller.get_devices()
        if p.is_movie_player
    ]
    async_add_entities(entities, True)


class KaleidescapeRemote(RemoteEntity):
    """Representation of a Kaleidescape device."""

    def __init__(self, device) -> None:
        """Initialize remote."""
        self._device: KaleidescapeDevice = device

    @property
    def unique_id(self) -> str:
        """Return a unique ID for device."""
        return self._device.serial_number

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return f"{self._device.system.friendly_name} {KALEIDESCAPE_NAME}"

    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._device.power.state == kaleidescape_const.DEVICE_POWER_STATE_ON

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to a device."""
        for single_command in command:
            if single_command == "select":
                await self._device.select()
            elif single_command == "up":
                await self._device.up()
            elif single_command == "down":
                await self._device.down()
            elif single_command == "left":
                await self._device.left()
            elif single_command == "right":
                await self._device.right()
            elif single_command == "cancel":
                await self._device.cancel()
            elif single_command == "replay":
                await self._device.replay()
            elif single_command == "scan_forward":
                await self._device.scan_forward()
            elif single_command == "scan_reverse":
                await self._device.scan_reverse()
            elif single_command == "go_movie_list":
                await self._device.go_movie_list()
