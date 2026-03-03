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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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
    return data.system_status.get("kismet.system.packets.rate")


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
