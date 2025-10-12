"""Entity classes used in this integration."""

import logging

from homeassistant.components.light import ColorMode, LightEntity

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
        self.supported_color_modes = [
            ColorMode.ONOFF,
            ColorMode.BRIGHTNESS,
            ColorMode.COLOR_TEMP,
        ]
        self.color_mode = ColorMode.COLOR_TEMP

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        for key, value in kwargs.items():
            match key:
                case "brightness":
                    brightness = value / 255 * 100
                    await self._GiraDevice.set_val(self._GiraLight.DimmUid, brightness)
                case "color_temp_kelvin":
                    await self._GiraDevice.set_val(self._GiraLight.TuneUid, value)
        await self._GiraDevice.set_val(self._GiraLight.OnOffUid, 1)

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self._GiraDevice.set_val(self._GiraLight.OnOffUid, 0)
