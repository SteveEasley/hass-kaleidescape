"""Kaleidescape Media Player."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import TYPE_CHECKING

from kaleidescape import const as kaleidescape_const

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
)
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import utcnow

from .const import DOMAIN as KALEIDESCAPE_DOMAIN, NAME as KALEIDESCAPE_NAME

if TYPE_CHECKING:
    from kaleidescape import Device as KaleidescapeDevice, Kaleidescape

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

SUPPORTED_FEATURES = (
    SUPPORT_TURN_ON |
    SUPPORT_TURN_OFF |
    SUPPORT_PLAY |
    SUPPORT_PAUSE |
    SUPPORT_STOP |
    SUPPORT_NEXT_TRACK |
    SUPPORT_PREVIOUS_TRACK
)

KALEIDESCAPE_CONTROLLER_EVENTS = [
    kaleidescape_const.EVENT_CONTROLLER_CONNECTED,
    kaleidescape_const.EVENT_CONTROLLER_DISCONNECTED,
]

KALEIDESCAPE_DEVICE_EVENTS = [
    kaleidescape_const.DEVICE_POWER_STATE,
    kaleidescape_const.FRIENDLY_NAME,
    kaleidescape_const.PLAY_STATUS,
    kaleidescape_const.MOVIE_LOCATION,
    kaleidescape_const.SCREEN_MASK,
    kaleidescape_const.VIDEO_COLOR,
]

KALEIDESCAPE_PLAYING_STATES = [
    kaleidescape_const.PLAY_STATUS_PLAYING,
    kaleidescape_const.PLAY_STATUS_FORWARD,
    kaleidescape_const.PLAY_STATUS_REVERSE,
]

KALEIDESCAPE_PAUSED_STATES = [kaleidescape_const.PLAY_STATUS_PAUSED]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the platform from a config entry."""
    controller: Kaleidescape = hass.data[KALEIDESCAPE_DOMAIN][entry.entry_id]
    entities = [
        KaleidescapeMediaPlayer(p)
        for p in await controller.get_devices()
        if p.is_movie_player
    ]
    async_add_entities(entities, True)


class KaleidescapeMediaPlayer(MediaPlayerEntity):
    """Representation of a Kaleidescape device."""

    def __init__(self, device) -> None:
        """Initialize media player."""
        self._device: KaleidescapeDevice = device

    async def async_added_to_hass(self) -> None:
        # Handle update signals coming from Kaleidescape controller
        @callback
        def _controller_update(event: str) -> None:
            """Handle controller state changes."""
            self.async_write_ha_state()

        self.async_on_remove(
            self._device.dispatcher.connect(
                kaleidescape_const.SIGNAL_CONTROLLER_EVENT, _controller_update
            ).disconnect
        )

        # Handle update signals coming from Kaleidescape devices
        @callback
        def _device_update(device_id: str, event: str) -> None:
            """Handle device state changes."""
            if self._device.has_device_id(device_id):
                if event in KALEIDESCAPE_DEVICE_EVENTS:
                    self.async_write_ha_state()

        self.async_on_remove(
            self._device.dispatcher.connect(
                kaleidescape_const.SIGNAL_DEVICE_EVENT, _device_update
            ).disconnect
        )

    async def async_turn_on(self) -> None:
        """Send leave standby command."""
        await self._device.leave_standby()

    async def async_turn_off(self) -> None:
        """Send enter standby command."""
        await self._device.enter_standby()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self._device.pause()

    async def async_media_play(self) -> None:
        """Send play command."""
        await self._device.play()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self._device.stop()

    async def async_media_next_track(self):
        """Send track next command."""
        await self._device.next()

    async def async_media_previous_track(self):
        """Send track previous command."""
        await self._device.previous()

    async def async_replay(self):
        """Send scan forward command."""
        await self._device.replay()

    async def async_scan_forward(self):
        """Send scan forward command."""
        await self._device.scan_forward()

    async def async_scan_reverse(self):
        """Send scan reverse command."""
        await self._device.scan_reverse()

    async def async_select(self):
        """Send scan reverse command."""
        await self._device.select()

    async def async_up(self):
        """Send up command."""
        await self._device.up()

    async def async_down(self):
        """Send down command."""
        await self._device.down()

    async def async_left(self):
        """Send left command."""
        await self._device.left()

    async def async_right(self):
        """Send right command."""
        await self._device.right()

    @property
    def available(self) -> bool:
        """Returns if device is available."""
        return self._device.is_connected

    @property
    def device_info(self) -> DeviceInfo:
        """Returns device specific attributes."""
        return DeviceInfo(
            identifiers={(KALEIDESCAPE_DOMAIN, self._device.serial_number)},
            name=self.name,
            model=self._device.system.type,
            manufacturer=KALEIDESCAPE_NAME,
            sw_version=f"{self._device.system.kos_version}",
            suggested_area="Theater",
            configuration_url=f"http://{self._device.connection.ip_address}",
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Returns additional attributes about the state."""
        return {
            "media_location": self._device.automation.movie_location,
            "video_mode": self._device.automation.video_mode,
            "video_color_eotf": self._device.automation.video_color_eotf,
            "video_color_space": self._device.automation.video_color_space,
            "video_color_depth": self._device.automation.video_color_depth,
            "video_color_sampling": self._device.automation.video_color_sampling,
            "screen_mask_ratio": self._device.automation.screen_mask_ratio,
            "screen_mask_top_trim_rel": self._device.automation.screen_mask_top_trim_rel,
            "screen_mask_bottom_trim_rel": self._device.automation.screen_mask_bottom_trim_rel,
            "screen_mask_conservative_ratio": self._device.automation.screen_mask_conservative_ratio,
            "screen_mask_top_mask_abs": self._device.automation.screen_mask_top_mask_abs,
            "screen_mask_bottom_mask_abs": self._device.automation.screen_mask_bottom_mask_abs,
            "cinemascape_mask": self._device.automation.cinemascape_mask,
            "cinemascape_mode": self._device.automation.cinemascape_mode,
        }

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return f"{self._device.system.friendly_name} {KALEIDESCAPE_NAME}"

    @property
    def should_poll(self) -> bool:
        """No polling needed for this device."""
        return False

    @property
    def state(self) -> str:
        """State of device."""
        if self._device.power.state == kaleidescape_const.DEVICE_POWER_STATE_STANDBY:
            return STATE_OFF
        if self._device.movie.play_status in KALEIDESCAPE_PLAYING_STATES:
            return STATE_PLAYING
        if self._device.movie.play_status in KALEIDESCAPE_PAUSED_STATES:
            return STATE_PAUSED
        return STATE_IDLE

    @property
    def supported_features(self) -> int:
        """Flag media device features that are supported."""
        return SUPPORTED_FEATURES

    @property
    def unique_id(self) -> str:
        """Return a unique ID for device."""
        return self._device.serial_number

    @property
    def media_content_id(self) -> str | None:
        """Content ID of current playing media."""
        if self._device.movie.handle:
            return self._device.movie.handle
        return None

    @property
    def media_content_type(self) -> str | None:
        """Content type of current playing media."""
        if self._device.movie.media_type:
            return self._device.movie.media_type
        return None

    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        if self._device.movie.title_length:
            return self._device.movie.title_length
        return None

    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        if self._device.movie.title_location:
            return self._device.movie.title_location
        return None

    @property
    def media_position_updated_at(self) -> datetime | None:
        """When was the position of the current playing media valid."""
        if self._device.movie.play_status in KALEIDESCAPE_PLAYING_STATES:
            return utcnow()
        return None

    @property
    def media_image_url(self) -> str:
        """Image url of current playing media."""
        return self._device.movie.cover

    @property
    def media_title(self) -> str:
        """Title of current playing media."""
        return self._device.movie.title
