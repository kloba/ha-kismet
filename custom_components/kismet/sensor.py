"""Sensor platform for Kismet integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfInformation
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SIGNAL_QUALITY_OPTIONS
from .coordinator import KismetCoordinator, KismetData
from .entity import KismetEntity


@dataclass(frozen=True, kw_only=True)
class KismetSensorEntityDescription(SensorEntityDescription):
    """Describe a Kismet sensor."""

    value_fn: Callable[[KismetData], Any]
    extra_attrs_fn: Callable[[KismetData], dict[str, Any]] | None = None


def _uptime(data: KismetData) -> datetime | None:
    start = data.system_status.get("kismet.system.timestamp.start_sec")
    if start is None:
        return None
    return datetime.fromtimestamp(start, tz=timezone.utc)


def _memory_mb(data: KismetData) -> float | None:
    rss = data.system_status.get("kismet.system.memory.rss")
    if rss is None:
        return None
    return round(rss / 1024, 1)


def _total_devices(data: KismetData) -> int | None:
    return data.system_status.get("kismet.system.devices.count")


def _packet_rate(data: KismetData) -> float | None:
    return data.packet_rate


def _nearby_count(data: KismetData) -> int:
    return len(data.nearby_devices)


def _nearby_attrs(data: KismetData) -> dict[str, Any]:
    return {"devices": data.nearby_devices}


def _alert_attrs(data: KismetData) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    if data.last_alert_text:
        attrs["last_alert"] = data.last_alert_text
    return attrs


SENSOR_DESCRIPTIONS: tuple[KismetSensorEntityDescription, ...] = (
    KismetSensorEntityDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_uptime,
    ),
    KismetSensorEntityDescription(
        key="memory",
        translation_key="memory",
        native_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_memory_mb,
    ),
    KismetSensorEntityDescription(
        key="total_devices",
        translation_key="total_devices",
        state_class=SensorStateClass.TOTAL,
        value_fn=_total_devices,
    ),
    KismetSensorEntityDescription(
        key="active_devices",
        translation_key="active_devices",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.total_active_count,
    ),
    KismetSensorEntityDescription(
        key="wifi_devices",
        translation_key="wifi_devices",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.wifi_device_count,
    ),
    KismetSensorEntityDescription(
        key="ble_devices",
        translation_key="ble_devices",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ble_device_count,
    ),
    KismetSensorEntityDescription(
        key="alerts",
        translation_key="alerts",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.alert_count,
        extra_attrs_fn=_alert_attrs,
    ),
    KismetSensorEntityDescription(
        key="packet_rate",
        translation_key="packet_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="pkt/s",
        value_fn=_packet_rate,
    ),
    KismetSensorEntityDescription(
        key="nearby_devices",
        translation_key="nearby_devices",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_nearby_count,
        extra_attrs_fn=_nearby_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kismet sensors."""
    coordinator: KismetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        KismetSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )

    # Dynamic WiFi signal quality sensors
    tracker = _WifiSignalTracker(coordinator, async_add_entities)
    entry.async_on_unload(tracker.unsubscribe)


class KismetSensor(KismetEntity, SensorEntity):
    """Representation of a Kismet sensor."""

    entity_description: KismetSensorEntityDescription

    def __init__(
        self,
        coordinator: KismetCoordinator,
        description: KismetSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.extra_attrs_fn:
            return self.entity_description.extra_attrs_fn(self.coordinator.data)
        return None


# ---------------------------------------------------------------------------
# Dynamic WiFi signal quality sensors
# ---------------------------------------------------------------------------


class _WifiSignalTracker:
    """Discover WiFi devices and create signal quality sensors dynamically."""

    def __init__(
        self,
        coordinator: KismetCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._known_macs: set[str] = set()
        self._unsub: CALLBACK_TYPE = coordinator.async_add_listener(
            self._on_update
        )
        self._on_update()

    def _on_update(self) -> None:
        if not self._coordinator.data:
            return
        new_entities: list[SensorEntity] = []
        for mac in self._coordinator.data.wifi_presence:
            if mac not in self._known_macs:
                self._known_macs.add(mac)
                new_entities.append(
                    KismetWifiSignal(self._coordinator, mac)
                )
        if new_entities:
            self._async_add_entities(new_entities)

    def unsubscribe(self) -> None:
        self._unsub()


class KismetWifiSignal(
    CoordinatorEntity[KismetCoordinator], SensorEntity
):
    """Sensor showing WiFi client signal quality (Strong/Good/Fair/Weak)."""

    _attr_has_entity_name = False
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SIGNAL_QUALITY_OPTIONS

    def __init__(
        self, coordinator: KismetCoordinator, mac: str
    ) -> None:
        """Initialize the WiFi signal sensor."""
        super().__init__(coordinator)
        self._mac = mac
        entry = coordinator.config_entry
        self._attr_unique_id = (
            f"{entry.entry_id}_wifi_{mac.replace(':', '_').lower()}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
        )
        info = coordinator.data.wifi_presence.get(mac, {})
        self._attr_name = self._make_label(mac, info)

    @staticmethod
    def _make_label(mac: str, info: dict) -> str:
        """Build a unique label: Manufacturer (XXYY) or full MAC."""
        mac_short = mac.replace(":", "")[-4:].upper()
        manuf = info.get("manufacturer", "")
        if manuf and manuf not in ("Unknown", ""):
            short = manuf.split(",")[0].strip()
            for suffix in (
                " Inc.", " LLC", " Ltd.", " Ltd",
                " Co.", " Corp.", " Corporation",
                " Technology", " Technologies",
                " International", " Holdings",
                " Limited", " Group",
            ):
                short = short.removesuffix(suffix)
            if len(short) > 12:
                short = short[:12]
            return f"{short} ({mac_short})"
        return mac

    @property
    def available(self) -> bool:
        """Return False when device is not active (renders grey in history)."""
        if not self.coordinator.data:
            return False
        info = self.coordinator.data.wifi_presence.get(self._mac)
        if info is None:
            return False
        return info.get("is_active", False)

    @property
    def native_value(self) -> str | None:
        """Return signal quality label."""
        if not self.coordinator.data:
            return None
        info = self.coordinator.data.wifi_presence.get(self._mac)
        if info is None or not info.get("is_active", False):
            return None
        return info.get("signal_quality", "Weak")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs: dict[str, Any] = {"mac": self._mac}
        if self.coordinator.data:
            info = self.coordinator.data.wifi_presence.get(self._mac, {})
            attrs["manufacturer"] = info.get("manufacturer", "")
            sig = info.get("signal", 0)
            dbm = sig if sig < 0 else -100
            attrs["signal_dbm"] = dbm
            # Positive 0-100 scale for auto-entities sorting (higher=stronger)
            attrs["signal_strength"] = max(0, min(100, 100 + dbm))
        return attrs
