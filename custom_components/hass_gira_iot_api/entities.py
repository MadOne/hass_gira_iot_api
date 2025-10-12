"""Entity classes used in this integration."""

import logging

from homeassistant.components.light import LightEntity

from .const import CONST
from .gira_device import GiraDevice, GiraLight

logging.basicConfig()
log = logging.getLogger(__name__)


class MyLightEntity(LightEntity):
    """MyLight Entity Class."""

    _attr_should_poll = True
    _attr_has_entity_name = True
    _attr_entity_name = None

    def __init__(self, myGiraDevice: GiraDevice, myGiraLight: GiraLight) -> None:
        """MyLight Entity Class init."""
        self._GiraDevice = myGiraDevice
        self._GiraLight = myGiraLight
        self.name = myGiraLight.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraLight.uid

    async def async_turn_on(self, **kwargs):
        """Turn device on."""

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
