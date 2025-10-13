"""Entity classes used in this integration."""

import logging

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.components.light import (
    DEFAULT_MAX_KELVIN,
    DEFAULT_MIN_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.const import UnitOfTemperature

from .const import CONST
from .gira_device import GiraClimate, GiraDevice, GiraLight

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


class MyLightEntity(LightEntity):
    """MyLight Entity Class."""

    _attr_should_poll: bool = True
    _attr_has_entity_name: bool = True
    _attr_entity_name: None | str = None

    def __init__(self, myGiraDevice: GiraDevice, myGiraLight: GiraLight) -> None:
        """MyLight Entity Class init."""
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraLight: GiraLight = myGiraLight
        self.name = myGiraLight.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraLight.uid
        self._attr_is_on: bool | None = myGiraLight.OnOffVal
        self._attr_brightness: int | None = myGiraLight.DimmVal
        self._attr_color_temp_kelvin: int | None = myGiraLight.TuneVal
        # print(myGiraLight.OnOffVal)
        supported_color_modes: set[ColorMode] = {ColorMode.ONOFF}
        color_mode: ColorMode = ColorMode.ONOFF

        if myGiraLight.DimmUid != "":
            supported_color_modes: set[ColorMode] = {ColorMode.BRIGHTNESS}
            color_mode: ColorMode = ColorMode.BRIGHTNESS
        if myGiraLight.TuneUid != "":
            supported_color_modes: set[ColorMode] = {ColorMode.COLOR_TEMP}
            color_mode: ColorMode = ColorMode.COLOR_TEMP
            self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN
            self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
        self.supported_color_modes = supported_color_modes
        self.color_mode = color_mode

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        for key, value in kwargs.items():
            match key:
                case "brightness":
                    brightness: int = value / 255 * 100
                    await self._GiraDevice.set_val(self._GiraLight.DimmUid, brightness)
                case "color_temp_kelvin":
                    await self._GiraDevice.set_val(self._GiraLight.TuneUid, value)
        await self._GiraDevice.set_val(self._GiraLight.OnOffUid, 1)

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self._GiraDevice.set_val(self._GiraLight.OnOffUid, 0)


class MyClimateEntity(ClimateEntity):
    """MyLight Entity Class."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.AUTO

    def __init__(self, myGiraDevice: GiraDevice, myGiraClimate: GiraClimate) -> None:
        """MyLight Entity Class init."""
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraClimate: GiraClimate = myGiraClimate
        self._attr_name = myGiraClimate.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraClimate.uid

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
