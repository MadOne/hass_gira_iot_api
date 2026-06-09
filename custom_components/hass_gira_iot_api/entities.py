"""Entity classes used in this integration."""

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.components.light import (
    DEFAULT_MAX_KELVIN,
    DEFAULT_MIN_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.components.scene import Scene
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONST
from .coordinator import MyCoordinator
from .gira_device import GiraClimate, GiraCover, GiraDevice, GiraLight, GiraScene

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

        # OnOff Device
        if myGiraLight.DimmUid == "" and myGiraLight.TuneUid == "":
            self.supported_color_modes: set[ColorMode] = {ColorMode.ONOFF}
            self.color_mode: ColorMode = ColorMode.ONOFF

        # Dimmable Device
        elif myGiraLight.DimmUid != "":
            self.supported_color_modes: set[ColorMode] = {ColorMode.BRIGHTNESS}
            self.color_mode: ColorMode = ColorMode.BRIGHTNESS
        # Tunable device
        elif myGiraLight.TuneUid != "":
            self.supported_color_modes: set[ColorMode] = {ColorMode.COLOR_TEMP}
            self.color_mode: ColorMode = ColorMode.COLOR_TEMP
            self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN
            self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
        else:
            # Colored light (not implemented yet)
            pass

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
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = 5.0
    _attr_max_temp = 30.0
    _attr_target_temperature_step = 0.5

    def __init__(
        self,
        myGiraDevice: GiraDevice,
        myGiraClimate: GiraClimate,
        coordinator: MyCoordinator,
    ) -> None:
        """MyClimate Entity Class init."""
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self.uid = myGiraClimate.uid
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraClimate: GiraClimate = myGiraClimate
        self._attr_name = myGiraClimate.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraClimate.uid

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get("temperature")
        if temp is None or not self._GiraClimate.SetPointUid:
            return
        await self._GiraDevice.set_val(self._GiraClimate.SetPointUid, temp)

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
                    print(f"{value}")
        self.async_write_ha_state()


class MyCoverEntity(CoverEntity, CoordinatorEntity):
    """MyCover Entity Class."""

    _attr_should_poll: bool = True
    _attr_has_entity_name: bool = True
    _attr_entity_name: None | str = None

    def __init__(
        self,
        myGiraDevice: GiraDevice,
        myGiraCover: GiraCover,
        coordinator: MyCoordinator,
    ) -> None:
        """MyCover Entity Class init."""
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self.uid = myGiraCover.uid
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraCover: GiraCover = myGiraCover
        self._attr_name = myGiraCover.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraCover.uid
        self._attr_is_closed = None

        features = CoverEntityFeature(0)
        if myGiraCover.UpDownUid:
            features |= (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
            )
        if myGiraCover.StepUpDownUid:
            features |= CoverEntityFeature.STOP
        if myGiraCover.PositionUid:
            features |= CoverEntityFeature.SET_POSITION
        if myGiraCover.SlatPositionUid:
            features |= CoverEntityFeature.SET_TILT_POSITION
        self._attr_supported_features = features

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        # print(**kwargs)
        await self._GiraDevice.set_val(uid=self._GiraCover.UpDownUid, val=0)
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        # print(f"{self._GiraCover.UpDownUid}:1")
        await self._GiraDevice.set_val(uid=self._GiraCover.UpDownUid, val=1)
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        for key, value in kwargs.items():
            match key:
                case "position":
                    # print(f"{key}:{value}")
                    position: int = int(value)
                    position = 100 - position
                    await self._GiraDevice.set_val(
                        uid=self._GiraCover.PositionUid, val=position
                    )
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._GiraDevice.set_val(uid=self._GiraCover.StepUpDownUid, val=1)
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
                        pos = 100 - int(float(value))
                        self._attr_current_cover_position = pos
                        self._attr_is_closed = pos == 0
                case self._GiraCover.SlatPositionUid:
                    if value != "":
                        self._attr_current_cover_tilt_position = int(float(value))

        self.async_write_ha_state()


class MyScene(Scene):
    """Gira HS4 Scene entity — write to Scene datapoint to activate."""

    _attr_has_entity_name = True

    def __init__(
        self,
        myGiraDevice: GiraDevice,
        myGiraScene: GiraScene,
    ) -> None:
        """MyScene Entity Class init."""
        self._GiraDevice: GiraDevice = myGiraDevice
        self._GiraScene: GiraScene = myGiraScene
        self._attr_name = myGiraScene.name
        self._attr_unique_id = CONST.DOMAIN + "_" + myGiraScene.uid

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene by writing to its Scene datapoint."""
        if not self._GiraScene.SceneUid:
            log.warning("Scene %s has no SceneUid datapoint", self._GiraScene.name)
            return
        await self._GiraDevice.set_val(self._GiraScene.SceneUid, 1)
