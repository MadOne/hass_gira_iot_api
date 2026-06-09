"""Gira IOT Device Class."""

import builtins
import contextlib
import json
import logging
from typing import Any

import aiohttp

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


class GiraDevice:
    """Gira IOT Device Class."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        callback_host: str | None = None,
        callback_port: str | int = 8124,
    ) -> None:
        """Gira IOT Device Class Constructor."""
        self._host: str = host
        self._user: str = user
        self._password: str = password
        self._callback_host: str | None = callback_host
        self._callback_port: str = str(callback_port)
        self._token: str | None = None
        self._ui: dict[str, Any] = {}
        self._functions_dict: dict[str, Any] = {}
        self.all_values: dict[str, dict[str, Any]] = {}
        self.gira_lights: dict[str, GiraLight] = {}
        self.gira_climates: dict[str, GiraClimate] = {}
        self.gira_covers: dict[str, GiraCover] = {}
        self.gira_scenes: dict[str, GiraScene] = {}
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()
        self._auth: aiohttp.BasicAuth = aiohttp.BasicAuth(
            login=self._user,
            password=self._password,
        )

    async def connect(self) -> None:
        """Register client on HS4, store token for subsequent calls."""
        payload = '{"client":"de.madone.x1client"}'
        url: str = f"https://{self._host}/api/v2/clients"
        response = await self._session.post(
            url=url, auth=self._auth, data=payload, ssl=False,
        )
        data = await response.json()
        self._token = data["token"]

    async def get_ui(self):
        """Get the UI json (functions, trades, locations)."""
        url = (
            f"https://{self._host}/api/v2/uiconfig"
            f"?expand=dataPointFlags,parameters,locations,trades"
            f"&token={self._token}"
        )
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        self._ui = await response.json()

    def _functions_by_type(self, *types: str) -> list[dict]:
        """Return function-dicts that match any of the given functionTypes."""
        return [
            f for f in self._ui.get("functions", [])
            if f.get("functionType") in types
        ]

    async def get_val(self, uid: str) -> int | None:
        """Read single value."""
        url = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        data = await response.json()
        try:
            return data["values"][0]["value"]
        except Exception:  # noqa: BLE001
            return None

    async def get_device_values(self, uid: str) -> dict[str, str | int | float]:
        """Read all values for a function-uid."""
        values: dict[str, str | int | float] = {}
        url: str = f"https://{self._host}/api/v2/values/{uid}?token={self._token}"
        response = await self._session.get(url=url, auth=self._auth, ssl=False)
        data = await response.json()
        for value in data.get("values", []):
            values[value["uid"]] = value["value"]
        return values

    async def get_all_values(self):
        """Fetch values for every function the integration cares about."""
        self.all_values = {}
        wanted_types = (
            "de.gira.schema.functions.KNX.Light",
            "de.gira.schema.functions.Switch",
            "de.gira.schema.functions.KNX.HeatingCooling",
            "de.gira.schema.functions.Covering",
            "de.gira.schema.functions.Scene",
        )
        for func in self._functions_by_type(*wanted_types):
            values = await self.get_device_values(func["uid"])
            self.all_values[func["uid"]] = values

    async def set_val(self, uid: str, val: int | float | str) -> None:
        """Write a value via API. Values must be strings per Gira API v2."""
        payload = json.dumps({
            "values": [{"uid": uid, "value": str(val)}]
        })
        url = f"https://{self._host}/api/v2/values?token={self._token}"
        await self._session.put(
            url=url, auth=self._auth, ssl=False, data=payload,
        )

    async def register_callback(self) -> None:
        """Register the callback URL with HS4 so push-events arrive at HA."""
        if not self._callback_host:
            log.warning(
                "No callback_host configured, skipping callback registration"
            )
            return
        payload = json.dumps({
            "valueCallback": (
                f"https://{self._callback_host}:{self._callback_port}/value"
            )
        })
        url = f"https://{self._host}/api/v2/clients/{self._token}/callbacks"
        await self._session.post(url=url, ssl=False, data=payload)

    async def create_gira_lights(self):
        """Create Gira Lights (incl. Switch-functions exposed as on/off lights)."""
        gira_lights: dict[str, GiraLight] = {}
        for light in self._functions_by_type(
            "de.gira.schema.functions.KNX.Light",
            "de.gira.schema.functions.Switch",
        ):
            light_uid = light["uid"]
            OnOffUid = ""
            OnOffVal = False
            DimmUid = ""
            DimmVal = 0
            TuneUid = ""
            TuneVal = 0
            for dp in light.get("dataPoints", []):
                if dp["name"] == "OnOff":
                    OnOffUid = dp["uid"]
                    raw = self.all_values.get(light_uid, {}).get(OnOffUid)
                    OnOffVal = raw == "1"
                elif dp["name"] == "Brightness":
                    DimmUid = dp["uid"]
                    with contextlib.suppress(builtins.BaseException):
                        DimmVal = int(
                            float(self.all_values[light_uid][DimmUid]) / 100 * 255
                        )
                elif dp["name"] == "Color-Temperature":
                    TuneUid = dp["uid"]
                    with contextlib.suppress(builtins.BaseException):
                        TuneVal = int(self.all_values[light_uid][TuneUid])
            gira_lights[light_uid] = GiraLight(
                uid=light_uid,
                name=light.get("displayName", ""),
                OnOffUid=OnOffUid,
                OnOffVal=OnOffVal,
                DimmUid=DimmUid,
                DimmVal=DimmVal,
                TuneUid=TuneUid,
                TuneVal=TuneVal,
            )
        self.gira_lights = gira_lights

    def create_gira_climates(self):
        """Create Gira Climates."""
        gira_climates: dict[str, GiraClimate] = {}
        for climate in self._functions_by_type(
            "de.gira.schema.functions.KNX.HeatingCooling",
        ):
            CurrentUid = ""
            SetPointUid = ""
            ModeUid = ""
            StatusUid = ""
            for dp in climate.get("dataPoints", []):
                if dp["name"] == "Current":
                    CurrentUid = dp["uid"]
                elif dp["name"] == "Set-Point":
                    SetPointUid = dp["uid"]
                elif dp["name"] == "Mode":
                    ModeUid = dp["uid"]
                elif dp["name"] == "Status":
                    StatusUid = dp["uid"]
            gira_climates[climate["uid"]] = GiraClimate(
                uid=climate["uid"],
                name=climate.get("displayName", ""),
                CurrentUid=CurrentUid,
                SetPointUid=SetPointUid,
                ModeUid=ModeUid,
                StatusUid=StatusUid,
            )
        self.gira_climates = gira_climates

    def create_gira_covers(self):
        """Create Gira Covers."""
        gira_covers: dict[str, GiraCover] = {}
        for cover in self._functions_by_type(
            "de.gira.schema.functions.Covering",
        ):
            StepUpDownUid = ""
            UpDownUid = ""
            PositionUid = ""
            SlatPositionUid = ""
            for dp in cover.get("dataPoints", []):
                if dp["name"] == "Step-Up-Down":
                    StepUpDownUid = dp["uid"]
                elif dp["name"] == "Up-Down":
                    UpDownUid = dp["uid"]
                elif dp["name"] == "Position":
                    PositionUid = dp["uid"]
                elif dp["name"] == "Slat-Position":
                    SlatPositionUid = dp["uid"]
            gira_covers[cover["uid"]] = GiraCover(
                uid=cover["uid"],
                name=cover.get("displayName", ""),
                StepUpDownUid=StepUpDownUid,
                UpDownUid=UpDownUid,
                PositionUid=PositionUid,
                SlatPositionUid=SlatPositionUid,
            )
        self.gira_covers = gira_covers

    def create_gira_scenes(self):
        """Create Gira Scenes (HS4-Logik orchestrated lighting moods etc.)."""
        gira_scenes: dict[str, GiraScene] = {}
        for scene in self._functions_by_type(
            "de.gira.schema.functions.Scene",
        ):
            SceneUid = ""
            for dp in scene.get("dataPoints", []):
                if dp["name"] == "Scene":
                    SceneUid = dp["uid"]
            gira_scenes[scene["uid"]] = GiraScene(
                uid=scene["uid"],
                name=scene.get("displayName", ""),
                SceneUid=SceneUid,
            )
        self.gira_scenes = gira_scenes

    def create_functions(self):
        """Create a dict with the functions (kept for backwards compat)."""
        self._functions_dict = {
            f["uid"]: f for f in self._ui.get("functions", [])
        }

    async def init(self):
        """Do some stuff to get the api ready for HA."""
        await self.connect()
        await self.get_ui()
        await self.get_all_values()
        self.create_functions()
        await self.create_gira_lights()
        self.create_gira_climates()
        self.create_gira_covers()
        self.create_gira_scenes()
        await self.register_callback()

    async def close(self) -> None:
        """De-register client on HS4 and close aiohttp session."""
        if self._token:
            with contextlib.suppress(Exception):
                url = f"https://{self._host}/api/v2/clients/{self._token}"
                await self._session.delete(url=url, ssl=False)
            self._token = None
        with contextlib.suppress(Exception):
            await self._session.close()


class GiraLight:
    """Gira Light."""

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
        self.uid = uid
        self.name = name
        self.OnOffUid = OnOffUid
        self.OnOffVal = OnOffVal
        self.DimmUid = DimmUid
        self.DimmVal = DimmVal
        self.TuneUid = TuneUid
        self.TuneVal = TuneVal


class GiraClimate:
    """Gira Climate."""

    def __init__(
        self,
        uid: str,
        name: str,
        CurrentUid: str = "",
        SetPointUid: str = "",
        ModeUid: str = "",
        StatusUid: str = "",
    ) -> None:
        """Init."""
        self.uid = uid
        self.name = name
        self.CurrentUid = CurrentUid
        self.SetPointUid = SetPointUid
        self.ModeUid = ModeUid
        self.StatusUid = StatusUid


class GiraCover:
    """Gira Cover."""

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
        self.uid = uid
        self.name = name
        self.StepUpDownUid = StepUpDownUid
        self.UpDownUid = UpDownUid
        self.PositionUid = PositionUid
        self.SlatPositionUid = SlatPositionUid


class GiraScene:
    """Gira Scene."""

    def __init__(
        self,
        uid: str,
        name: str,
        SceneUid: str = "",
    ) -> None:
        """Init."""
        self.uid = uid
        self.name = name
        self.SceneUid = SceneUid
