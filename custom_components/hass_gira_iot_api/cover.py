"""Setting uop my sensor entities."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .configentry import MyConfigEntry
from .entities import MyCoverEntity
from .gira_device import GiraDevice

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""

    coordinator = config_entry.runtime_data.coordinator
    _useless = hass
    # start with an empty list of entries
    entries: list[MyCoverEntity] = []

    giraAPI: GiraDevice = config_entry.runtime_data.gira_api
    for cover in giraAPI.gira_covers.values():
        mycover: MyCoverEntity = MyCoverEntity(
            myGiraDevice=giraAPI, myGiraCover=cover, coordinator=coordinator
        )
        entries.append(mycover)

    async_add_entities(
        entries,
        update_before_add=True,
    )
