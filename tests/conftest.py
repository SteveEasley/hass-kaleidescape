"""Fixtures for Kaleidescape integration."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

from kaleidescape import Device as KaleidescapeDevice, Dispatcher, const
from kaleidescape.connection import Connection
from kaleidescape.device import Automation, Movie, Power, System
import pytest

from homeassistant.components.kaleidescape.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_ID

from tests.common import MockConfigEntry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def create_kaleidescape_device(
    kaleidescape: AsyncMock, serial_number: str, is_local: bool = True
) -> AsyncMock:
    """Returns a mock Kaleidescape device."""
    device = AsyncMock(KaleidescapeDevice)
    device.dispatcher = kaleidescape.dispatcher
    device.disabled = False
    device.device_id = const.LOCAL_CPDID if is_local else f"#{serial_number}"
    device.serial_number = serial_number
    device.is_connected = True
    device.is_local = is_local
    device.has_device_id = lambda d: d == f"#{serial_number}"
    device.is_server_only = False
    device.is_movie_player = True
    device.system = System(
        system_id="123456789",
        system_name="Cinema",
        system_ip_address="127.0.0.1",
        device_ip_address="127.0.0.1",
        serial_number=serial_number,
        type="Strato",
        protocol=16,
        kos="10.4.2-19218",
        player_name=f"Device {serial_number}",
        movie_zones=1,
        music_zones=1,
    )
    device.power = Power(state="standby", readiness="disabled", zone=["available"])
    device.movie = Movie()
    device.automation = Automation()
    return device


@pytest.fixture(name="mock_kaleidescape")
def fixture_mock_kaleidescape(
    request: pytest.FixtureRequest,
) -> Generator[None, AsyncMock, None]:
    """Returns a mocked Kaleidescape controller."""
    with patch(
        "homeassistant.components.kaleidescape.Kaleidescape", autospec=True
    ) as mock:
        kaleidescape = mock.return_value
        kaleidescape.connection = AsyncMock(
            Connection, connected=True, state=const.STATE_CONNECTED
        )
        kaleidescape.dispatcher = Dispatcher()

        devices: list[AsyncMock] = []
        if hasattr(request, "param"):
            params = request.param
        else:
            params = [("123", True)]
        for args in params:
            devices.append(create_kaleidescape_device(kaleidescape, *args))
        kaleidescape.get_devices = AsyncMock(return_value=devices)
        if len(devices) > 0:
            kaleidescape.get_local_device = AsyncMock(return_value=devices[0])
        else:
            kaleidescape.get_local_device = AsyncMock(return_value=None)

        yield kaleidescape


@pytest.fixture(name="mock_config_entry")
async def fixture_mock_config_entry() -> Generator[None, MockConfigEntry, None]:
    """Returns a mock config entry."""
    yield MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456789",
        version=2,
        data={CONF_ID: "123456789", CONF_HOST: "127.0.0.1"},
    )


@pytest.fixture(name="mock_integration")
async def fixture_mock_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> Generator[None, MockConfigEntry, None]:
    """Returns a mock ConfigEntry setup for Kaleidescape integration."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    yield mock_config_entry
