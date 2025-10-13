"""Setting uop my sensor entities."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .configentry import MyConfigEntry
from .entities import MyClimateEntity
from .gira_device import GiraDevice

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""

    _useless = hass
    # start with an empty list of entries
    entries = []

    giraAPI: GiraDevice = config_entry.runtime_data.gira_api
    for climate in giraAPI.gira_climates.values():
        myclimate = MyClimateEntity(myGiraDevice=giraAPI, myGiraLight=climate)
        entries.append(myclimate)

    async_add_entities(
        entries,
        update_before_add=True,
    )
