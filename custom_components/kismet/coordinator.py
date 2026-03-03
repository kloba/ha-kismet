"""DataUpdateCoordinator for Kismet."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KismetApiClient, KismetAuthError, KismetConnectionError
from .const import (
    CONF_ACTIVE_WINDOW,
    CONF_ENABLE_DEVICE_TRACKER,
    CONF_SCAN_INTERVAL,
    CONF_TRACKED_MACS,
    DEFAULT_ACTIVE_WINDOW,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PHY_BLE,
    PHY_WIFI,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class KismetData:
    """Data returned by the coordinator."""

    system_status: dict[str, Any] = field(default_factory=dict)
    datasources: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    active_devices: list[dict[str, Any]] = field(default_factory=list)
    tracked_devices: dict[str, dict[str, Any]] = field(default_factory=dict)
    wifi_device_count: int = 0
    ble_device_count: int = 0
    total_active_count: int = 0
    alert_count: int = 0
    last_alert_text: str | None = None
    online: bool = False


class KismetCoordinator(DataUpdateCoordinator[KismetData]):
    """Coordinator to poll Kismet REST API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: KismetApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=__import__("datetime").timedelta(seconds=scan_interval),
        )
        self.client = client
        self.config_entry = entry
        self._last_alert_ts: int = 0
        self._all_alerts: list[dict[str, Any]] = []

    @property
    def active_window(self) -> int:
        """Return the active device window in seconds."""
        return self.config_entry.options.get(
            CONF_ACTIVE_WINDOW, DEFAULT_ACTIVE_WINDOW
        )

    @property
    def tracked_macs(self) -> list[str]:
        """Return list of tracked MAC addresses."""
        raw = self.config_entry.options.get(CONF_TRACKED_MACS, "")
        if not raw:
            return []
        return [m.strip().upper() for m in raw.split(",") if m.strip()]

    @property
    def device_tracker_enabled(self) -> bool:
        """Return whether device tracker is enabled."""
        return self.config_entry.options.get(CONF_ENABLE_DEVICE_TRACKER, False)

    async def _async_update_data(self) -> KismetData:
        """Fetch all data from Kismet in a single poll cycle."""
        data = KismetData()
        try:
            # System status
            data.system_status = await self.client.async_get_system_status()
            data.online = True

            # Datasources
            data.datasources = await self.client.async_get_datasources()

            # Alerts
            if self._last_alert_ts > 0:
                new_alerts = await self.client.async_get_alerts_since(
                    self._last_alert_ts
                )
                self._all_alerts.extend(new_alerts)
            else:
                self._all_alerts = await self.client.async_get_all_alerts()

            data.alerts = self._all_alerts
            data.alert_count = len(self._all_alerts)
            if self._all_alerts:
                last = self._all_alerts[-1]
                data.last_alert_text = last.get(
                    "kismet.alert.text", last.get("kismet.alert.header", "")
                )

            self._last_alert_ts = int(time.time())

            # Active devices
            active_since = int(time.time()) - self.active_window
            data.active_devices = await self.client.async_get_active_devices(
                active_since
            )
            data.total_active_count = len(data.active_devices)
            data.wifi_device_count = sum(
                1
                for d in data.active_devices
                if d.get("kismet.device.base.phyname") == PHY_WIFI
            )
            data.ble_device_count = sum(
                1
                for d in data.active_devices
                if d.get("kismet.device.base.phyname") == PHY_BLE
            )

            # Tracked devices
            macs = self.tracked_macs
            if macs and self.device_tracker_enabled:
                tracked = await self.client.async_get_devices_by_mac(macs)
                for device in tracked:
                    mac = device.get("kismet.device.base.macaddr", "")
                    if mac:
                        data.tracked_devices[mac.upper()] = device

        except KismetAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except KismetConnectionError as err:
            data.online = False
            raise UpdateFailed(f"Connection failed: {err}") from err

        return data
