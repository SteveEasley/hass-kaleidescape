"""Tests for Kaleidescape media player platform."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

from kaleidescape import const as kaleidescape_const
from kaleidescape.device import Movie

from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_STOP,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from tests.common import MockConfigEntry


async def test_entity(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test entity attributes."""
    media_player = hass.states.get("media_player.device_123_kaleidescape")
    assert media_player.state == STATE_OFF
    assert media_player.attributes["friendly_name"] == "Device 123 Kaleidescape"

    # For coverage report
    mock_kaleidescape.dispatcher.send(
        kaleidescape_const.SIGNAL_CONTROLLER_EVENT,
        kaleidescape_const.EVENT_CONTROLLER_UPDATED,
    )
    await hass.async_block_till_done()


async def test_update_state(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Tests dispatched signals update player."""
    device: AsyncMock = await mock_kaleidescape.get_local_device()
    entity = hass.states.get("media_player.device_123_kaleidescape")
    assert entity.state == STATE_OFF

    # Devices turns on
    device.power.state = kaleidescape_const.DEVICE_POWER_STATE_ON
    mock_kaleidescape.dispatcher.send(
        kaleidescape_const.SIGNAL_DEVICE_EVENT,
        "#123",
        kaleidescape_const.DEVICE_POWER_STATE,
    )
    await asyncio.sleep(0)
    await hass.async_block_till_done()
    entity = hass.states.get("media_player.device_123_kaleidescape")
    assert entity.state == STATE_IDLE

    # Devices starts playing
    device.movie = Movie(
        handle="handle",
        title="title",
        cover="cover",
        cover_hires="cover_hires",
        rating="rating",
        rating_reason="rating_reason",
        year="year",
        runtime="runtime",
        actors=[],
        director="director",
        directors=[],
        genre="genre",
        genres=[],
        synopsis="synopsis",
        color="color",
        country="country",
        aspect_ratio="aspect_ratio",
        media_type="media_type",
        play_status=kaleidescape_const.PLAY_STATUS_PLAYING,
        play_speed=1,
        title_number=1,
        title_length=1,
        title_location=1,
        chapter_number=1,
        chapter_length=1,
        chapter_location=1,
    )
    mock_kaleidescape.dispatcher.send(
        kaleidescape_const.SIGNAL_DEVICE_EVENT, "#123", kaleidescape_const.PLAY_STATUS
    )
    await asyncio.sleep(0)
    await hass.async_block_till_done()
    entity = hass.states.get("media_player.device_123_kaleidescape")
    assert entity.state == STATE_PLAYING

    # Devices pauses playing
    device.movie.play_status = kaleidescape_const.PLAY_STATUS_PAUSED
    mock_kaleidescape.dispatcher.send(
        kaleidescape_const.SIGNAL_DEVICE_EVENT, "#123", kaleidescape_const.PLAY_STATUS
    )
    await asyncio.sleep(0)
    await hass.async_block_till_done()
    entity = hass.states.get("media_player.device_123_kaleidescape")
    assert entity.state == STATE_PAUSED


async def test_turn_on(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test turn on service call."""
    device: AsyncMock = await mock_kaleidescape.get_local_device()
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "media_player.device_123_kaleidescape"},
        blocking=True,
    )
    assert device.leave_standby.call_count == 1


async def test_turn_off(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test turn off service call."""
    device: AsyncMock = await mock_kaleidescape.get_local_device()
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "media_player.device_123_kaleidescape"},
        blocking=True,
    )
    assert device.enter_standby.call_count == 1


async def test_play(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test play service call."""
    device: AsyncMock = await mock_kaleidescape.get_local_device()
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: "media_player.device_123_kaleidescape"},
        blocking=True,
    )
    assert device.play.call_count == 1


async def test_pause(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test pause service call."""
    device: AsyncMock = await mock_kaleidescape.get_local_device()
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PAUSE,
        {ATTR_ENTITY_ID: "media_player.device_123_kaleidescape"},
        blocking=True,
    )
    assert device.pause.call_count == 1


async def test_stop(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test stop service call."""
    device: AsyncMock = await mock_kaleidescape.get_local_device()
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_STOP,
        {ATTR_ENTITY_ID: "media_player.device_123_kaleidescape"},
        blocking=True,
    )
    assert device.stop.call_count == 1


async def test_device(
    hass: HomeAssistant,
    mock_kaleidescape: MagicMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test device attributes."""
    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device.name == "Device 123 Kaleidescape"
    assert device.model == "Strato"
    assert device.sw_version == "10.4.2-19218"
    assert device.manufacturer == "Kaleidescape"
