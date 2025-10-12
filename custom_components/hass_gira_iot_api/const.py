"""Constants."""

from dataclasses import dataclass

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME


@dataclass(frozen=True)
class ConfConstants:
    """Constants used for configurastion."""

    HOST = CONF_HOST
    PASSWORD = CONF_PASSWORD
    USERNAME = CONF_USERNAME
    DEVICE_POSTFIX = "Device-Postfix"


CONF = ConfConstants()


@dataclass(frozen=True)
class MainConstants:
    """Main constants."""

    DOMAIN = "hass_gira_iot_api"
    SCAN_INTERVAL = "60"  # timedelta(seconds=60))
    UNIQUE_ID = "unique_id"
    APPID = 100


CONST = MainConstants()


@dataclass(frozen=True)
class FormatConstants:
    """Format constants."""

    NUMBER = "number"
    TEXT = "text"
    STATUS = "status"
    UNKNOWN = "unknown"
    SWITCH = "Switch"
    BUTTON = "Button"
    TIMESTAMP = "Timestamp"
    SW_VERSION = "SW_Version"


FORMATS = FormatConstants()
