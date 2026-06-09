"""Setting up Gira HS4 scene entities."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .configentry import MyConfigEntry
from .entities import MyScene
from .gira_device import GiraDevice

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the scene platform."""
    _useless = hass
    entries: list[MyScene] = []

    giraAPI: GiraDevice = config_entry.runtime_data.gira_api
    for scene in giraAPI.gira_scenes.values():
        myscene = MyScene(myGiraDevice=giraAPI, myGiraScene=scene)
        entries.append(myscene)

    async_add_entities(entries)
