"""Constants for the Kismet integration."""

from typing import Final

DOMAIN: Final = "kismet"

# Defaults
DEFAULT_PORT: Final = 2501
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_ACTIVE_WINDOW: Final = 300  # 5 minutes
DEFAULT_SCHEME: Final = "http"

# Config keys
CONF_API_KEY: Final = "api_key"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_ACTIVE_WINDOW: Final = "active_window"
CONF_TRACKED_MACS: Final = "tracked_macs"
CONF_ENABLE_DEVICE_TRACKER: Final = "enable_device_tracker"

# API endpoints
ENDPOINT_SYSTEM_STATUS: Final = "/system/status.json"
ENDPOINT_DATASOURCES: Final = "/datasource/all_sources.json"
ENDPOINT_ALL_ALERTS: Final = "/alerts/all_alerts.json"
ENDPOINT_ALERTS_LAST_TIME: Final = "/alerts/wrapped/last-time/{ts}/alerts.json"
ENDPOINT_ACTIVE_DEVICES: Final = "/devices/last-time/{ts}/devices.json"
ENDPOINT_DEVICES_BY_MAC: Final = "/devices/multimac/devices.json"

# Field simplification for device queries (minimize payload)
DEVICE_FIELDS: Final = [
    "kismet.device.base.macaddr",
    "kismet.device.base.name",
    "kismet.device.base.commonname",
    "kismet.device.base.type",
    "kismet.device.base.phyname",
    "kismet.device.base.last_time",
    "kismet.device.base.first_time",
    "kismet.device.base.signal/kismet.common.signal.last_signal",
    "kismet.device.base.channel",
    "kismet.device.base.manuf",
    "kismet.device.base.packets.total",
]

# System status fields
STATUS_FIELDS: Final = [
    "kismet.system.version",
    "kismet.system.memory.rss",
    "kismet.system.devices.count",
    "kismet.system.timestamp.start_sec",
    "kismet.system.packets.rate",
]

# PHY types
PHY_WIFI: Final = "IEEE802.11"
PHY_BLE: Final = "BTLE"

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor"]
