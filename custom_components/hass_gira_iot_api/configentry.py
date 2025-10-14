"""my config entry."""

from dataclasses import dataclass

from config.custom_components.hass_gira_iot_api.coordinator import MyCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .gira_device import GiraDevice


@dataclass
class MyData:
    """My config data."""

    gira_api: GiraDevice
    hass: HomeAssistant
    coordinator: MyCoordinator


type MyConfigEntry = ConfigEntry[MyData]
