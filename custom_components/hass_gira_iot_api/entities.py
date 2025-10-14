"""Entity classes used in this integration."""

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.components.cover import CoverEntity
from homeassistant.components.light import (
    DEFAULT_MAX_KELVIN,
    DEFAULT_MIN_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONST
from .coordinator import MyCoordinator
from .gira_device import GiraClimate, GiraCover, GiraDevice, GiraLight

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


class MyLightEntity(LightEntity, CoordinatorEntity):
    """MyLight Entity Class."""

    _attr_should_poll: bool = True
    _attr_has_entity_name: bool = True
    _attr_entity_name: None | str = None

    def __init__(
        self,
        myGiraDevice: GiraDevice,
        myGiraLight: GiraLight,
        coordinator: MyCoordinator,
    ) -> None:
        """MyLight Entity Class init."""
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraLight: GiraLight = myGiraLight
        self.uid = myGiraLight.uid
        self.name = myGiraLight.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraLight.uid
        # self._attr_is_on: bool | None = myGiraLight.OnOffVal
        # self._attr_brightness: int | None = myGiraLight.DimmVal
        # self._attr_color_temp_kelvin: int | None = myGiraLight.TuneVal
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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data: dict[str, Any] = self.coordinator.data[self.uid]
        for key, value in data.items():
            match key:
                case self._GiraLight.OnOffUid:
                    if value == "1":
                        self._attr_is_on = True
                    else:
                        self._attr_is_on = False
                case self._GiraLight.DimmUid:
                    if value != "":
                        self._attr_brightness = int(float(value) / 100 * 255)
                case self._GiraLight.TuneUid:
                    if value != "":
                        self._attr_color_temp_kelvin = int(float(value))
        self.async_write_ha_state()


class MyClimateEntity(ClimateEntity, CoordinatorEntity):
    """MyLight Entity Class."""

    _attr_should_poll: bool = True
    _attr_has_entity_name: bool = True
    _attr_entity_name: None | str = None

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.AUTO

    def __init__(
        self,
        myGiraDevice: GiraDevice,
        myGiraClimate: GiraClimate,
        coordinator: MyCoordinator,
    ) -> None:
        """MyLight Entity Class init."""
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self.uid = myGiraClimate.uid
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraClimate: GiraClimate = myGiraClimate
        self._attr_name = myGiraClimate.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraClimate.uid

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data: dict[str, Any] = self.coordinator.data[self.uid]
        for key, value in data.items():
            match key:
                case self._GiraClimate.CurrentUid:
                    if value != "":
                        self._attr_current_temperature = float(value)
                case self._GiraClimate.SetPointUid:
                    if value != "":
                        self._attr_target_temperature = float(value)
                case self._GiraClimate.ModeUid:
                    ...
                    # ToDo
        self.async_write_ha_state()


class MyCoverEntity(CoverEntity, CoordinatorEntity):
    """MyLight Entity Class."""

    _attr_should_poll: bool = True
    _attr_has_entity_name: bool = True
    _attr_entity_name: None | str = None

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.AUTO

    def __init__(
        self,
        myGiraDevice: GiraDevice,
        myGiraCover: GiraCover,
        coordinator: MyCoordinator,
    ) -> None:
        """MyLight Entity Class init."""
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self.uid = myGiraCover.uid
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraCover: GiraCover = myGiraCover
        self._attr_name = myGiraCover.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraCover.uid

        self._attr_is_closed = None

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        print(**kwargs)
        await self._GiraDevice.set_val(uid=self._GiraCover.UpDownUid, val=0)
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        print(f"{self._GiraCover.UpDownUid}:1")
        await self._GiraDevice.set_val(uid=self._GiraCover.UpDownUid, val=1)
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        for key, value in kwargs.items():
            match key:
                case "position":
                    print(f"{key}:{value}")
                    position: int = int(value)
                    await self._GiraDevice.set_val(
                        uid=self._GiraCover.PositionUid, val=position
                    )
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._GiraDevice.set_val(uid=self._GiraCover.StepUpDownUid, val=1)
        self._attr_is_closing = False
        self._attr_is_opening = False
        self.async_write_ha_state()

    async def async_open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        await self._GiraDevice.set_val(uid=self._GiraCover.StepUpDownUid, val=0)
        self.async_write_ha_state()

    async def async_close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        await self._GiraDevice.set_val(uid=self._GiraCover.StepUpDownUid, val=1)
        self.async_write_ha_state()

    async def async_set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        await self._GiraDevice.set_val(uid=self._GiraCover.SlatPositionUid, val=1)
        self.async_write_ha_state()

    async def async_stop_cover_tilt(self, **kwargs):
        """Stop the cover."""
        await self._GiraDevice.set_val(uid=self._GiraCover.StepUpDownUid, val=1)
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data: dict[str, Any] = self.coordinator.data[self.uid]
        for key, value in data.items():
            match key:
                case self._GiraCover.PositionUid:
                    if value != "":
                        self._attr_current_cover_position = int(float(value))
                case self._GiraCover.SlatPositionUid:
                    if value != "":
                        self._attr_current_cover_tilt_position = int(float(value))

        self.async_write_ha_state()
