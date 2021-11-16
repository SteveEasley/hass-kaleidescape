"""Tests for Kaleidescape config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from homeassistant.components.kaleidescape.const import DEFAULT_HOST, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_ID
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from tests.common import MockConfigEntry


async def test_config_flow_success(
    hass: HomeAssistant, mock_kaleidescape: AsyncMock
) -> None:
    """Test config flow success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.1"}
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert "data" in result
    assert result["data"][CONF_ID] == "123456789"
    assert result["data"][CONF_HOST] == "127.0.0.1"


async def test_config_flow_host_default(
    hass: HomeAssistant, mock_kaleidescape: AsyncMock
) -> None:
    """Test config flow default host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert "data" in result
    assert result["data"][CONF_ID] == "123456789"
    assert result["data"][CONF_HOST] == "127.0.0.1"


async def test_config_flow_host_empty(
    hass: HomeAssistant, mock_kaleidescape: AsyncMock
) -> None:
    """Test errors when host is an empty string."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"host": ""}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}


async def test_config_flow_host_bad_characters(
    hass: HomeAssistant, mock_kaleidescape: AsyncMock
) -> None:
    """Test errors when host has bad characters."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"host": "b@d"}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}


async def test_config_flow_host_bad_connect(
    hass: HomeAssistant, mock_kaleidescape: AsyncMock
) -> None:
    """Test errors when cant connect to host."""
    mock_kaleidescape.connect.side_effect = ConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"host": "127.0.0.1"}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_config_flow_device_exists_abort(
    hass: HomeAssistant, mock_kaleidescape: AsyncMock, mock_integration: MockConfigEntry
) -> None:
    """Test flow aborts if device already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "127.0.0.1"}
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
