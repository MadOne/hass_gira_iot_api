"""Setting uop my sensor entities."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .configentry import MyConfigEntry
from .entities import MyLightEntity
from .gira_device import GiraDevice


logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    _useless = hass
    # start with an empty list of entries
    entries = []

    giraAPI: GiraDevice = config_entry.runtime_data.gira_api
    for light in giraAPI.gira_lights.values():
        mylight = MyLightEntity(myGiraDevice=giraAPI, myGiraLight=light)
        entries.append(mylight)

    async_add_entities(
        entries,
        update_before_add=True,
    )
