"""The Update Coordinator for the ModbusItems."""

import asyncio
from datetime import timedelta
import logging
from typing import Any

from config.custom_components.hass_gira_iot_api.gira_device import GiraDevice
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class MyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Gira IOT API."""

    def __init__(
        self,
        hass: HomeAssistant,
        gira_api: GiraDevice,
    ) -> None:
        """Initialize Gira IOT API coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="gira_iot_api",
            update_interval=timedelta(seconds=60),
            always_update=True,
        )
        self.gira_api = gira_api

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        await self.gira_api.get_all_values()

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from WebIF endpoint."""
        return self.gira_api.all_values
