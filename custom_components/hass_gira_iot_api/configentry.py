"""my config entry."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


@dataclass
class MyData:
    """My config data."""

    gira_api: any
    hass: HomeAssistant


type MyConfigEntry = ConfigEntry[MyData]
