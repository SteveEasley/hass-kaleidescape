"""Tests for Kaleidescape config entry."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from kaleidescape import const as kaleidescape_const
import pytest

from homeassistant.components.kaleidescape.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState

from .conftest import create_kaleidescape_device

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from tests.common import MockConfigEntry


async def test_unload_config_entry(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test config entry loading and unloading."""
    mock_config_entry = mock_integration
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_kaleidescape.connect.call_count == 1
    assert mock_kaleidescape.disconnect.call_count == 0

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_kaleidescape.disconnect.call_count == 1
    assert not hass.data.get(DOMAIN)


async def test_config_entry_not_ready(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test config entry not ready."""
    mock_kaleidescape.connect.side_effect = ConnectionError

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize("mock_kaleidescape", [[("123", True)]], indirect=True)
async def test_discover_single_device(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test discovering a single device."""
    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device is not None
    assert device.identifiers == {("kaleidescape", "123")}


@pytest.mark.parametrize(
    "mock_kaleidescape", [[("123", True), ("234", False)]], indirect=True
)
async def test_discover_multiple_devices(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test discovering multiple devices."""
    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device is not None
    assert device.identifiers == {("kaleidescape", "123")}
    device = device_registry.async_get_device(identifiers={("kaleidescape", "234")})
    assert device is not None
    assert device.identifiers == {("kaleidescape", "234")}


@pytest.mark.parametrize(
    "mock_kaleidescape", [[("123", True), ("234", False)]], indirect=True
)
async def test_discover_no_movie_zone(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test devices with no movie zone don't get a media_player platform."""
    kaleidescape_device = await mock_kaleidescape.get_device()
    kaleidescape_device.capabilities.movies = False
    kaleidescape_device.capabilities.movie_zones = 0

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device is None
    device = device_registry.async_get_device(identifiers={("kaleidescape", "234")})
    assert device is not None
    assert device.identifiers == {("kaleidescape", "234")}


@pytest.mark.parametrize("mock_kaleidescape", [[("123", True)]], indirect=True)
async def test_discover_new_device(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test discovering new device added after startup."""
    device_registry = await hass.helpers.device_registry.async_get_registry()

    # Assert starting with a single device (123)
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device is not None
    device = device_registry.async_get_device(identifiers={("kaleidescape", "234")})
    assert device is None

    # Setup to add a new device (234)
    mock_kaleidescape.get_devices = AsyncMock(
        return_value=[
            create_kaleidescape_device(mock_kaleidescape, "123", True),
            create_kaleidescape_device(mock_kaleidescape, "234", False),
        ]
    )

    # Trigger discovery process
    mock_kaleidescape.dispatcher.send(
        kaleidescape_const.SIGNAL_CONTROLLER_EVENT,
        kaleidescape_const.EVENT_CONTROLLER_UPDATED,
    )

    async def check():
        """Loops until device is added."""
        while True:
            await asyncio.sleep(0)
            if (
                device_registry.async_get_device(identifiers={("kaleidescape", "234")})
                is not None
            ):
                break

    # Wait until signals fire, events process, and device is created.
    await asyncio.wait_for(check(), 0.5)

    # Assert new device added (234)
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device is not None
    device = device_registry.async_get_device(identifiers={("kaleidescape", "234")})
    assert device is not None


@pytest.mark.parametrize("mock_kaleidescape", [[("123", True)]], indirect=True)
async def test_name_change(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock,
    mock_integration: MockConfigEntry,
) -> None:
    """Test changing device name."""
    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device.name == "Device 123 Kaleidescape"

    # Change device name
    kaleidescape_device = await mock_kaleidescape.get_device()
    kaleidescape_device.system.name = "Device ABC"

    # Trigger discovery process
    mock_kaleidescape.dispatcher.send(
        kaleidescape_const.SIGNAL_CONTROLLER_EVENT,
        kaleidescape_const.EVENT_CONTROLLER_UPDATED,
    )

    await hass.async_block_till_done()

    # Assert name was changed
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device.name == "Device ABC Kaleidescape"
