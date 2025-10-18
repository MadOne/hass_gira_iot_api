"""Callback server."""

import ssl

from aiofiles import ospath
from aiohttp import web

from config.custom_components.hass_gira_iot_api.configentry import MyConfigEntry
from config.custom_components.hass_gira_iot_api.coordinator import MyCoordinator
from config.custom_components.hass_gira_iot_api.ssl_helper import (
    generate_selfsigned_cert,
)
from homeassistant.core import HomeAssistant

from .const import CONF
from .gira_device import GiraDevice


class CallBackServer:
    """CallbackServer Class."""

    def __init__(
        self,
        entry: MyConfigEntry,
        giraApi: GiraDevice,
        coordinator: MyCoordinator,
        hass: HomeAssistant,
    ) -> None:
        """Init of CallBackServer."""
        self._entry = entry
        self._giraApi = giraApi
        self._coordinator = coordinator
        self._hass = hass

    async def start(self):
        """Start the callback server."""
        app = web.Application()
        app.add_routes([web.post("/value", self.value)])
        server = web.AppRunner(app)
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        if not await ospath.exists("domain_srv.crt") or not await ospath.exists(
            "domain_srv.key"
        ):
            await generate_selfsigned_cert(
                "test.de", [self._entry.data[CONF.CALLBACK_HOST]]
            )
        await self._hass.async_add_executor_job(
            ssl_context.load_cert_chain, "domain_srv.crt", "domain_srv.key"
        )
        # ssl_context.load_cert_chain("domain_srv.crt", "domain_srv.key")

        self._entry.async_create_background_task(
            hass=self._hass, target=server.setup(), name="server.setup"
        )
        site = web.TCPSite(
            server, "0.0.0.0", self._entry.data[CONF.PORT], ssl_context=ssl_context
        )
        self._entry.async_create_background_task(
            hass=self._hass, target=site.start(), name="site.start"
        )

    async def value(self, request):
        """Callback function to handle an incomming POST request."""
        data = await request.json()
        # print(data)
        written_to_dev = None
        for event in data["events"]:
            uid = event["uid"]
            value = event["value"]
            for dev_uid, dev in self._giraApi.all_values.items():
                if uid in dev:  # if uid in dev.keys():
                    dev[uid] = value
                    written_to_dev = dev_uid
                    # print(f"updated values in {dev_uid}")
            if written_to_dev is not None:
                self._coordinator.async_set_updated_data(self._giraApi.all_values)
            else:
                ...
                # print("uid not found")

        return web.json_response({"status": "ok"})
