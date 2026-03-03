"""Device tracker platform for Kismet integration."""

from __future__ import annotations

import time

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KismetCoordinator
from .entity import KismetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kismet device trackers."""
    coordinator: KismetCoordinator = hass.data[DOMAIN][entry.entry_id]

    if not coordinator.device_tracker_enabled:
        return

    entities = [
        KismetTrackedDevice(coordinator, mac)
        for mac in coordinator.tracked_macs
    ]
    async_add_entities(entities)


class KismetTrackedDevice(KismetEntity, ScannerEntity):
    """Tracked device via Kismet."""

    _attr_source_type = SourceType.ROUTER

    def __init__(self, coordinator: KismetCoordinator, mac: str) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, f"tracker_{mac.replace(':', '_')}")
        self._mac = mac.upper()
        self._attr_name = f"Kismet {mac}"

    @property
    def mac_address(self) -> str:
        """Return the MAC address."""
        return self._mac

    @property
    def is_connected(self) -> bool:
        """Return true if device was seen within active window."""
        if not self.coordinator.data:
            return False
        device = self.coordinator.data.tracked_devices.get(self._mac)
        if not device:
            return False
        last_time = device.get("kismet.device.base.last_time", 0)
        return (time.time() - last_time) < self.coordinator.active_window

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return extra attributes about the tracked device."""
        if not self.coordinator.data:
            return {}
        device = self.coordinator.data.tracked_devices.get(self._mac)
        if not device:
            return {}
        return {
            "name": device.get("kismet.device.base.name"),
            "common_name": device.get("kismet.device.base.commonname"),
            "manufacturer": device.get("kismet.device.base.manuf"),
            "type": device.get("kismet.device.base.type"),
            "phy": device.get("kismet.device.base.phyname"),
            "channel": device.get("kismet.device.base.channel"),
            "signal": device.get(
                "kismet.device.base.signal/kismet.common.signal.last_signal"
            ),
            "last_time": device.get("kismet.device.base.last_time"),
            "packets": device.get("kismet.device.base.packets.total"),
        }
