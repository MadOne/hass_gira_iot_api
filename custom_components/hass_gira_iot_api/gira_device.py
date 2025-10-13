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
        self._all_values = None
        self.gira_lights = None
        self.gira_climates = None
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
        log.warning(json)

    async def get_val(self, uid: str) -> int:
        """Get the UI json."""
        url = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        json = await response.json()
        log.warning(json)
        try:
            val = json["values"][0]["value"]
            return val
        except:
            return None

    async def get_device_values(self, uid: str):
        """Get the UI json."""
        values = {}
        url = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        json = await response.json()
        for value in json["values"]:
            values[value["uid"]] = value["value"]
        return values

    async def get_all_values(self):
        """Get all the values of the GiraDevice."""
        all_values = {}
        lights = self._ui["trades"][0]["functions"]
        for light_uid in lights:
            values = {}
            values = await self.get_device_values(light_uid)
            all_values.update(values)
        self._all_values = all_values

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

    async def get_values(self):
        values = {}

    async def create_gira_lights(self):
        """Create Gira Lights."""
        gira_lights = {}

        lights = self._ui["trades"][0]["functions"]
        for light_uid in lights:
            light = self._functions[light_uid]
            name = None
            OnOffUid = None
            OnOffVal = None
            DimmUid = None
            DimmVal = None
            TuneUid = None
            TuneVal = None
            for dataPoint in light["dataPoints"]:
                match dataPoint["name"]:
                    case "OnOff":
                        OnOffUid = dataPoint["uid"]
                        OnOffVal_Number = self._all_values[OnOffUid]
                        if OnOffVal_Number == "1":
                            OnOffVal = True
                        else:
                            OnOffVal = False
                    case "Brightness":
                        DimmUid = dataPoint["uid"]
                        try:
                            DimmVal = int(float(self._all_values[DimmUid]) / 100 * 255)
                        except:
                            ...
                        # print(DimmVal)
                    case "Color-Temperature":
                        TuneUid = dataPoint["uid"]
                        try:
                            TuneVal = int(self._all_values[TuneUid])
                        except:
                            ...
                        # print(DimmVal)
            name = light["displayName"]
            gira_lights[light_uid] = GiraLight(
                uid=light_uid,
                name=name,
                OnOffUid=OnOffUid,
                OnOffVal=OnOffVal,
                DimmUid=DimmUid,
                DimmVal=DimmVal,
                TuneUid=TuneUid,
                TuneVal=TuneVal,
            )
        self.gira_lights = gira_lights

    def create_gira_climates(self):
        """Create Gira Lights."""
        gira_climates = {}

        climates = self._ui["trades"][3]["functions"]
        for climate_uid in climates:
            climate = self._functions[climate_uid]
            name = None
            CurrentUid = None
            SetPointUid = None
            ModeUid = None
            for dataPoint in climate["dataPoints"]:
                match dataPoint["name"]:
                    case "Current":
                        CurrentUid = dataPoint["uid"]
                    case "Set-Point":
                        SetPointUid = dataPoint["uid"]
                    case "Mode":
                        ModeUid = dataPoint["uid"]
            name = climate["displayName"]
            gira_climates[climate_uid] = GiraClimate(
                uid=climate_uid,
                name=name,
                CurrentUid=CurrentUid,
                SetPointUid=SetPointUid,
                ModeUid=ModeUid,
            )
        self.gira_climates = gira_climates

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
        OnOffVal: bool | None = None,
        DimmUid: str | None = None,
        DimmVal: int | None = None,
        TuneUid: str | None = None,
        TuneVal: int | None = None,
    ) -> None:
        """Init."""
        self.uid = uid
        self.name = name
        self.OnOffUid = OnOffUid
        self.OnOffVal = OnOffVal
        self.DimmUid = DimmUid
        self.DimmVal = DimmVal
        self.TuneUid = TuneUid
        self.TuneVal = TuneVal


class GiraClimate:
    """Gira Light Class."""

    def __init__(
        self,
        uid: str,
        name: str,
        CurrentUid: str,
        SetPointUid: str | None = None,
        ModeUid: str | None = None,
    ) -> None:
        """Init."""
        self.uid = uid
        self.name = name
        self.CurreentUid = CurrentUid
        self.SetPointUid = SetPointUid
        self.ModeUid = ModeUid
