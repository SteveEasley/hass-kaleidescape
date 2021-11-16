"""Tests for Kaleidescape config entry."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from homeassistant.components.kaleidescape.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_ID

from tests.common import MockConfigEntry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


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
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN)


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
    kaleidescape_device = await mock_kaleidescape.get_local_device()
    kaleidescape_device.is_server_only = True
    kaleidescape_device.is_movie_player = False

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={("kaleidescape", "123")})
    assert device is None
    device = device_registry.async_get_device(identifiers={("kaleidescape", "234")})
    assert device is not None
    assert device.identifiers == {("kaleidescape", "234")}


async def test_version_1_migration(
    hass: HomeAssistant,
    mock_kaleidescape: AsyncMock
) -> None:
    """Test migrating from version 1 to version 2 config."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456789",
        version=1,
        data={CONF_ID: "123456789", CONF_HOST: "127.0.0.1"},
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.version == 2
    assert mock_kaleidescape.connect.call_count == 2
