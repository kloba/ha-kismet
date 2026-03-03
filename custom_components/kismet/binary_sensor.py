"""Binary sensor platform for Kismet integration."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KismetCoordinator
from .entity import KismetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kismet binary sensors."""
    coordinator: KismetCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        KismetServerOnline(coordinator),
        KismetAlertsActive(coordinator),
    ]

    # Add per-datasource binary sensors
    if coordinator.data and coordinator.data.datasources:
        for source in coordinator.data.datasources:
            uuid = source.get("kismet.datasource.uuid", "")
            name = source.get(
                "kismet.datasource.name",
                source.get("kismet.datasource.interface", uuid),
            )
            if uuid:
                entities.append(
                    KismetDatasourceOnline(coordinator, uuid, name)
                )

    async_add_entities(entities)

    # Dynamic WiFi presence tracking
    tracker = _WifiPresenceTracker(coordinator, async_add_entities)
    entry.async_on_unload(tracker.unsubscribe)


class _WifiPresenceTracker:
    """Discover WiFi devices and create binary sensors dynamically."""

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
        new_entities: list[BinarySensorEntity] = []
        for mac in self._coordinator.data.wifi_presence:
            if mac not in self._known_macs:
                self._known_macs.add(mac)
                new_entities.append(
                    KismetWifiPresence(self._coordinator, mac)
                )
        if new_entities:
            self._async_add_entities(new_entities)

    def unsubscribe(self) -> None:
        self._unsub()


class KismetWifiPresence(
    CoordinatorEntity[KismetCoordinator], BinarySensorEntity
):
    """Binary sensor tracking presence of a WiFi client device."""

    _attr_has_entity_name = False
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(
        self, coordinator: KismetCoordinator, mac: str
    ) -> None:
        """Initialize the WiFi presence sensor."""
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
        self._attr_name = self._make_label(info)

    @staticmethod
    def _make_label(info: dict) -> str:
        manuf = info.get("manufacturer", "")
        name = info.get("name", "")
        mac = info.get("mac", "") or name
        mac_short = mac.replace(":", "")[-4:].upper() if mac else ""
        if manuf and manuf not in ("Unknown", ""):
            return f"{manuf} ({mac_short})" if mac_short else manuf
        if name and ":" in name:
            return name[-8:]
        return name or mac or "Unknown"

    @property
    def is_on(self) -> bool:
        """Return true if device is currently active."""
        if not self.coordinator.data:
            return False
        info = self.coordinator.data.wifi_presence.get(self._mac)
        if info is None:
            return False
        return info.get("is_active", False)

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        attrs = {"mac": self._mac}
        if self.coordinator.data:
            info = self.coordinator.data.wifi_presence.get(self._mac, {})
            attrs["manufacturer"] = info.get("manufacturer", "")
            sig = info.get("signal", 0)
            if sig < 0:
                attrs["signal_dbm"] = sig
        return attrs


class KismetServerOnline(KismetEntity, BinarySensorEntity):
    """Binary sensor for Kismet server online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "server_online"

    def __init__(self, coordinator: KismetCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, "server_online")

    @property
    def is_on(self) -> bool:
        """Return true if server is online."""
        return self.coordinator.data.online if self.coordinator.data else False


class KismetAlertsActive(KismetEntity, BinarySensorEntity):
    """Binary sensor for whether any alerts are active."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "alerts_active"

    def __init__(self, coordinator: KismetCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, "alerts_active")

    @property
    def is_on(self) -> bool:
        """Return true if new alerts arrived since last poll."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.new_alert_count > 0


class KismetDatasourceOnline(KismetEntity, BinarySensorEntity):
    """Binary sensor for datasource online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: KismetCoordinator,
        source_uuid: str,
        source_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, f"datasource_{source_uuid}")
        self._source_uuid = source_uuid
        self._attr_translation_key = "datasource_online"
        self._attr_name = f"Datasource {source_name}"

    @property
    def is_on(self) -> bool:
        """Return true if datasource is running."""
        if not self.coordinator.data:
            return False
        for source in self.coordinator.data.datasources:
            if source.get("kismet.datasource.uuid") == self._source_uuid:
                return bool(source.get("kismet.datasource.running", False))
        return False
