"""init."""

import http.server
import json
import logging
import ssl

from aiohttp import web

# from pathlib import Path
from config.custom_components.hass_gira_iot_api.coordinator import MyCoordinator
from config.custom_components.hass_gira_iot_api.ssl_helper import (
    generate_selfsigned_cert,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .callback_server import CallBackServer
from .configentry import MyConfigEntry, MyData
from .const import CONF
from .gira_device import GiraDevice

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)

PLATFORMS: list[str] = [
    "climate",
    "cover",
    "light",
]


# Return boolean to indicate that initialization was successful.
# return True
async def async_setup_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:
    """Set up entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub.Hub(hass, entry.data["host"])

    giraApi: GiraDevice = GiraDevice(
        host=entry.data[CONF.HOST],
        user=entry.data[CONF.USERNAME],
        password=entry.data[CONF.PASSWORD],
    )
    await giraApi.connect()
    await giraApi.get_ui()
    await giraApi.get_all_values()
    giraApi.create_functions()
    await giraApi.create_gira_lights()
    giraApi.create_gira_climates()
    giraApi.create_gira_covers()

    # server = callback_server_run()
    # hass.async_add_executor_job(server.start_server())
    # thread = Thread(target=server.start_server)
    # thread.start()
    # await server.start_server()

    # await restapi.login()

    coordinator: MyCoordinator = MyCoordinator(hass=hass, gira_api=giraApi)

    entry.runtime_data = MyData(gira_api=giraApi, hass=hass, coordinator=coordinator)

    mycallbackserver: CallBackServer = CallBackServer(
        entry=entry,
        giraApi=giraApi,
        coordinator=coordinator,
        hass=hass,
    )
    mycallbackserver.start()

    await giraApi.register_callback()

    # see https://community.home-assistant.io/t/config-flow-how-to-update-an-existing-entity/522442/8
    entry.async_on_unload(func=entry.add_update_listener(listener=update_listener))

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    #    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    log.info(msg="Setup entities")

    await hass.config_entries.async_forward_entry_setups(
        entry=entry, platforms=PLATFORMS
    )

    log.info(msg="Init done")

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(
        entry_id=entry.entry_id
    )  # list of entry_ids created for file


async def async_migrate_entry(hass: HomeAssistant, config_entry: MyConfigEntry):
    """Migrate old entry."""

    new_data = {**config_entry.data}

    if config_entry.version > 1:
        # This means the user has downgraded from a future version
        return True

    # to ensure all update paths we have to check every version to not overwrite existing entries
    if config_entry.version < 1:
        log.warning(msg="Old Version detected")

    if config_entry.version < 2:
        log.warning(msg="Version <2 detected")

    hass.config_entries.async_update_entry(
        entry=config_entry, data=new_data, minor_version=1, version=2
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    entry.runtime_data.rest_api.close()
    return await hass.config_entries.async_unload_platforms(
        entry=entry, platforms=PLATFORMS
    )
