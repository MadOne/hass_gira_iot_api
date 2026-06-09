"""init."""

import logging

from .coordinator import MyCoordinator
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
    "scene",
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
        callback_host=entry.data.get(CONF.CALLBACK_HOST),
        callback_port=entry.data.get(CONF.PORT, "8124"),
    )
    coordinator: MyCoordinator = MyCoordinator(hass=hass, gira_api=giraApi)

    entry.runtime_data = MyData(gira_api=giraApi, hass=hass, coordinator=coordinator)

    mycallbackserver: CallBackServer = CallBackServer(
        entry=entry,
        giraApi=giraApi,
        coordinator=coordinator,
        hass=hass,
    )

    await mycallbackserver.start()

    await giraApi.init()

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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry=entry, platforms=PLATFORMS
    )
    if unload_ok and getattr(entry, "runtime_data", None) is not None:
        gira_api = getattr(entry.runtime_data, "gira_api", None)
        if gira_api is not None:
            await gira_api.close()
    return unload_ok
