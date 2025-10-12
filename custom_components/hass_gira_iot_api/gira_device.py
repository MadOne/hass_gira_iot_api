"""Gira IOT Device Class."""

import logging

import aiohttp

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


class GiraDevice:
    """Gira IOT Device Class."""

    def __init__(self, host: str, user: str, password: str) -> None:
        """Gira IOT Device Class Constructor."""
        self._host = host
        self._user = user
        self._password = password
        self._token = None
        self._ui = None
        self._functions = None
        self.gira_lights = None
        self._session = aiohttp.ClientSession()
        self._auth = aiohttp.BasicAuth(
            login=self._user,
            password=self._password,
        )

    async def connect(self) -> None:
        """Connect to the Gira IOT Device."""

        payload = '{"client":"de.madone.x1client"}'
        url = f"https://{self._host}/api/clients"
        response = await self._session.post(
            url=url, auth=self._auth, data=payload, ssl=False
        )
        json = await response.json()
        token = json["token"]
        self._token = token

    async def get_ui(self):
        """Get the UI json."""
        url = f"https://{self._host}/api/v2/uiconfig?expand=[dataPointFlasgs,parameters,locations,trades&token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        json = await response.json()
        self._ui = json
        # log.warning(json)

    async def get_val(self, uid: str) -> int:
        """Get the UI json."""
        url = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        json = await response.json()
        return json["values"][0]["value"]
        # log.warning(json)

    async def set_val(self, uid, val) -> int:
        """Get the UI json."""
        payload = f"""{{
                \"values\": [
                    {{
                        \"uid\": \"{uid}\",
                        \"value\": {val}
                    }}
                ]
            }}"""
        url = f"https://{self._host}/api/v2/values?token={self._token}"
        _response = await self._session.put(
            url=url, auth=self._auth, ssl=False, data=payload
        )

    def create_gira_lights(self):
        """Create Gira Lights."""
        gira_lights = {}

        lights = self._ui["trades"][0]["functions"]
        for light_uid in lights:
            light = self._functions[light_uid]
            name = None
            OnOffUid = None
            DimmUid = None
            TuneUid = None
            for dataPoint in light["dataPoints"]:
                match dataPoint["name"]:
                    case "OnOff":
                        OnOffUid = dataPoint["uid"]
                    case "Brightness":
                        DimmUid = dataPoint["uid"]
                    case "Color-Temperature":
                        TuneUid = dataPoint["uid"]
            name = light["displayName"]
            gira_lights[light_uid] = GiraLight(
                uid=light_uid,
                name=name,
                OnOffUid=OnOffUid,
                DimmUid=DimmUid,
                TuneUid=TuneUid,
            )
        self.gira_lights = gira_lights

    def create_functions(self):
        """Create a dict with the functions."""
        functions = {}
        for function in self._ui["functions"]:
            functions[function["uid"]] = function
        self._functions = functions
        # log.warning(functions)


class GiraLight:
    """Gira Light Class."""

    def __init__(
        self,
        uid: str,
        name: str,
        OnOffUid: str,
        DimmUid: str | None = None,
        TuneUid: str | None = None,
    ) -> None:
        """Init."""
        self.uid = uid
        self.name = name
        self.OnOffUid = OnOffUid
        self.DimmUid = DimmUid
        self.TuneUid = TuneUid
