"""my config entry."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .gira_device import GiraDevice


@dataclass
class MyData:
    """My config data."""

    gira_api: GiraDevice
    hass: HomeAssistant


type MyConfigEntry = ConfigEntry[MyData]
