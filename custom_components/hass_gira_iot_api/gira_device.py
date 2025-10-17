"""Gira IOT Device Class."""

import builtins
import contextlib
import logging
from typing import Any

import aiohttp

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


class GiraDevice:
    """Gira IOT Device Class."""

    def __init__(self, host: str, user: str, password: str) -> None:
        """Gira IOT Device Class Constructor."""
        self._host: str = host
        self._user: str = user
        self._password: str = password
        self._token: str | None = None
        self._ui = {}
        self._functions = []
        self.all_values: dict[str, dict[str, Any]] = {}
        self.gira_lights: dict[str, GiraLight] = {}
        self.gira_climates: dict[str, GiraClimate] = {}
        self.gira_covers: dict[str, GiraCover] = {}
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()
        self._auth: aiohttp.BasicAuth = aiohttp.BasicAuth(
            login=self._user,
            password=self._password,
        )

    async def connect(self) -> None:
        """Connect to the Gira IOT Device."""

        payload = '{"client":"de.madone.x1client"}'
        url: str = f"https://{self._host}/api/clients"
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
        # log.warning(msg=json)

    async def get_val(self, uid: str) -> int | None:
        """Get the UI json."""
        url = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        json = await response.json()
        log.warning(json)
        try:
            return json["values"][0]["value"]
        except:  # noqa: E722
            ...

    async def get_device_values(self, uid: str) -> dict[str, str | int | float]:
        """Get the UI json."""
        values: dict[str, str | int | float] = {}
        url: str = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        json = await response.json()
        for value in json["values"]:
            values[value["uid"]] = value["value"]
        return values

    async def get_all_values(self):
        """Get all the values of the GiraDevice."""
        self.all_values = {}
        lights: list[str] = self._ui["trades"][0]["functions"]
        for light_uid in lights:
            values = {}
            values = await self.get_device_values(light_uid)
            self.all_values[light_uid] = values

        climates: list[str] = self._ui["trades"][3]["functions"]
        for climate_uid in climates:
            values = {}
            values = await self.get_device_values(climate_uid)
            self.all_values[climate_uid] = values

        covers: list[str] = self._ui["trades"][2]["functions"]
        for cover_uid in covers:
            values = {}
            values = await self.get_device_values(cover_uid)
            self.all_values[cover_uid] = values

    async def set_val(self, uid: str, val: int) -> None:
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

    async def register_callback(self) -> None:
        """Get the UI json."""
        ha_ip = "10.10.1.20"
        callback_port = "8124"
        payload = f"""{{\"valueCallback\":\"https://{ha_ip}:{callback_port}/value\"}}"""
        url = f"https://{self._host}/api/clients/{self._token}/callbacks"
        print(payload)
        response = await self._session.post(url=url, ssl=False, data=payload)
        print
        print(response)

    async def create_gira_lights(self):
        """Create Gira Lights."""
        gira_lights: dict[str, GiraLight] = {}

        lights = self._ui["trades"][0]["functions"]
        for light_uid in lights:
            light = self._functions[light_uid]
            name: str = ""
            OnOffUid: str = ""
            OnOffVal: bool = False
            DimmUid: str = ""
            DimmVal: int = 0
            TuneUid: str = ""
            TuneVal: int = 0
            for dataPoint in light["dataPoints"]:
                match dataPoint["name"]:
                    case "OnOff":
                        OnOffUid: str = dataPoint["uid"]
                        OnOffVal_Number: str = self.all_values[light_uid][OnOffUid]
                        if OnOffVal_Number == "1":
                            OnOffVal: bool = True
                        else:
                            OnOffVal: bool = False
                    case "Brightness":
                        DimmUid: str = dataPoint["uid"]
                        with contextlib.suppress(builtins.BaseException):
                            DimmVal: int = int(
                                float(self.all_values[light_uid][DimmUid]) / 100 * 255
                            )
                        # print(DimmVal)
                    case "Color-Temperature":
                        TuneUid: str = dataPoint["uid"]
                        with contextlib.suppress(builtins.BaseException):
                            TuneVal: int = int(self.all_values[light_uid][TuneUid])
                        # print(DimmVal)
            name: str = light["displayName"]
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
        self.gira_lights: dict[str, GiraLight] = gira_lights

    def create_gira_climates(self):
        """Create Gira Lights."""
        gira_climates = {}

        climates = self._ui["trades"][3]["functions"]
        for climate_uid in climates:
            climate = self._functions[climate_uid]
            name: str = ""
            CurrentUid: str = ""
            SetPointUid: str = ""
            ModeUid: str = ""
            for dataPoint in climate["dataPoints"]:
                match dataPoint["name"]:
                    case "Current":
                        CurrentUid: str = dataPoint["uid"]
                    case "Set-Point":
                        SetPointUid: str = dataPoint["uid"]
                    case "Mode":
                        ModeUid: str = dataPoint["uid"]
            name: str = climate["displayName"]
            gira_climates[climate_uid] = GiraClimate(
                uid=climate_uid,
                name=name,
                CurrentUid=CurrentUid,
                SetPointUid=SetPointUid,
                ModeUid=ModeUid,
            )
        self.gira_climates = gira_climates

    def create_gira_covers(self):
        """Create Gira Lights."""
        gira_covers = {}

        covers = self._ui["trades"][2]["functions"]
        for cover_uid in covers:
            cover = self._functions[cover_uid]
            name: str = ""
            StepUpDownUid: str = ""
            UpDownUid: str = ""
            PositionUid: str = ""
            SlatPositionUid: str = ""
            for dataPoint in cover["dataPoints"]:
                match dataPoint["name"]:
                    case "Step-Up-Down":
                        StepUpDownUid: str = dataPoint["uid"]
                    case "Up-Down":
                        UpDownUid: str = dataPoint["uid"]
                    case "Position":
                        PositionUid: str = dataPoint["uid"]
                    case "Slat-Position":
                        SlatPositionUid: str = dataPoint["uid"]
            name: str = cover["displayName"]
            gira_covers[cover_uid] = GiraCover(
                uid=cover_uid,
                name=name,
                StepUpDownUid=StepUpDownUid,
                UpDownUid=UpDownUid,
                PositionUid=PositionUid,
                SlatPositionUid=SlatPositionUid,
            )
        self.gira_covers = gira_covers

    def create_functions(self):
        """Create a dict with the functions."""
        functions = {}
        for function in self._ui["functions"]:
            functions[function["uid"]] = function
        self._functions = functions
        # log.warning(functions)

    async def init(self):
        """Do some stuff to get the api ready for HA."""
        await self.connect()
        await self.get_ui()
        await self.get_all_values()
        self.create_functions()
        await self.create_gira_lights()
        self.create_gira_climates()
        self.create_gira_covers()


class GiraLight:
    """Gira Light Class."""

    def __init__(
        self,
        uid: str,
        name: str,
        OnOffUid: str,
        OnOffVal: bool = False,
        DimmUid: str = "",
        DimmVal: int = 0,
        TuneUid: str = "",
        TuneVal: int = 0,
    ) -> None:
        """Init."""
        self.uid: str = uid
        self.name: str = name
        self.OnOffUid: str = OnOffUid
        self.OnOffVal: bool = OnOffVal
        self.DimmUid: str = DimmUid
        self.DimmVal: int = DimmVal
        self.TuneUid: str = TuneUid
        self.TuneVal: int = TuneVal


class GiraClimate:
    """Gira Light Class."""

    def __init__(
        self,
        uid: str,
        name: str,
        CurrentUid: str = "",
        SetPointUid: str = "",
        ModeUid: str = "",
    ) -> None:
        """Init."""
        self.uid: str = uid
        self.name: str = name
        self.CurrentUid: str = CurrentUid
        self.SetPointUid: str = SetPointUid
        self.ModeUid: str = ModeUid


class GiraCover:
    """Gira Light Class."""

    def __init__(
        self,
        uid: str,
        name: str,
        StepUpDownUid: str = "",
        UpDownUid: str = "",
        PositionUid: str = "",
        SlatPositionUid: str = "",
    ) -> None:
        """Init."""
        self.uid: str = uid
        self.name: str = name
        self.StepUpDownUid: str = StepUpDownUid
        self.UpDownUid: str = UpDownUid
        self.PositionUid: str = PositionUid
        self.SlatPositionUid: str = SlatPositionUid
