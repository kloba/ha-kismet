"""Constants for the Kismet integration."""

from typing import Final

DOMAIN: Final = "kismet"

# Defaults
DEFAULT_PORT: Final = 2501
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_ACTIVE_WINDOW: Final = 300  # 5 minutes
DEFAULT_SCHEME: Final = "http"
DEFAULT_SIGNAL_THRESHOLD: Final = -60
WIFI_PRESENCE_WINDOW: Final = 86400  # 24 hours in seconds

# Signal quality thresholds (dBm)
SIGNAL_STRONG: Final = -50
SIGNAL_GOOD: Final = -55
SIGNAL_FAIR: Final = -70
SIGNAL_QUALITY_OPTIONS: Final = ["Strong", "Good", "Fair", "Weak"]


def signal_to_quality(dbm: int) -> str:
    """Map dBm value to a signal quality label."""
    if dbm >= SIGNAL_STRONG:
        return "Strong"
    if dbm >= SIGNAL_GOOD:
        return "Good"
    if dbm >= SIGNAL_FAIR:
        return "Fair"
    return "Weak"

# Config keys
CONF_API_KEY: Final = "api_key"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_ACTIVE_WINDOW: Final = "active_window"
CONF_TRACKED_MACS: Final = "tracked_macs"
CONF_ENABLE_DEVICE_TRACKER: Final = "enable_device_tracker"
CONF_SIGNAL_THRESHOLD: Final = "signal_threshold"

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
]

# PHY types
PHY_WIFI: Final = "IEEE802.11"
PHY_BLE: Final = "Bluetooth"

# Device types to include in nearby list (clients only, no APs/infra)
NEARBY_DEVICE_TYPES: Final = {"Wi-Fi Client", "Wi-Fi Device"}

# Readable PHY names
PHY_DISPLAY_NAMES: Final = {
    "IEEE802.11": "WiFi",
    "Bluetooth": "BLE",
}

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor"]
